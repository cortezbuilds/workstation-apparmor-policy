"""Prepare a non-deploying review bundle for an apparmor.d update."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_DIFF_BYTES = 64 * 1024 * 1024

SIGNALS = {
    "deny_rule": re.compile(r"(^|\s)deny\s"),
    "capability_rule": re.compile(r"(^|\s)capability(?:\s|,|$)"),
    "network_rule": re.compile(r"(^|\s)network(?:\s|,|$)"),
    "mount_rule": re.compile(r"(^|\s)(?:mount|remount|umount)(?:\s|,|$)"),
    "ptrace_rule": re.compile(r"(^|\s)ptrace(?:\s|,|$)"),
    "signal_rule": re.compile(r"(^|\s)signal(?:\s|,|$)"),
    "dbus_rule": re.compile(r"(^|\s)dbus(?:\s|,|$)"),
    "unix_rule": re.compile(r"(^|\s)unix(?:\s|,|$)"),
    "execution_transition": re.compile(r"\b[A-Za-z]*[pPcCiIuU][xX]\b|\s->\s"),
    "include_directive": re.compile(r"^\s*#include\s"),
    "recursive_wildcard": re.compile(r"\*\*"),
}


class ReviewError(RuntimeError):
    """Raised when review preparation cannot preserve its safety contract."""


def git(
    repository: Path,
    arguments: Iterable[str],
    *,
    text: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    command = [
        "git",
        "-c",
        "core.quotePath=true",
        "-C",
        str(repository),
        *arguments,
    ]
    return subprocess.run(
        command,
        check=check,
        capture_output=True,
        text=text,
    )


def validate_sha(value: str, label: str) -> None:
    if not SHA_RE.fullmatch(value):
        raise ReviewError(f"{label} must be a lowercase 40-character Git SHA")


def verify_commits(repository: Path, old: str, new: str) -> None:
    if old == new:
        raise ReviewError("old and new commits are identical")

    for label, value in (("old", old), ("new", new)):
        result = git(
            repository,
            ["cat-file", "-e", f"{value}^{{commit}}"],
            check=False,
        )
        if result.returncode != 0:
            raise ReviewError(f"{label} commit is unavailable: {value}")

    ancestry = git(
        repository,
        ["merge-base", "--is-ancestor", old, new],
        check=False,
    )
    if ancestry.returncode == 1:
        raise ReviewError("upstream update is not a fast-forward of the pinned commit")
    if ancestry.returncode != 0:
        raise ReviewError("unable to verify upstream commit ancestry")


def decode_path(value: bytes) -> str:
    return value.decode("utf-8", errors="backslashreplace")


def changed_files(repository: Path, old: str, new: str) -> list[dict[str, object]]:
    result = git(
        repository,
        ["diff", "--name-status", "-z", "--find-renames", old, new],
        text=False,
    )
    tokens = result.stdout.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()

    changes: list[dict[str, object]] = []
    position = 0
    while position < len(tokens):
        status = decode_path(tokens[position])
        position += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        if position + path_count > len(tokens):
            raise ReviewError("malformed NUL-delimited name-status output")
        paths = [
            decode_path(value) for value in tokens[position : position + path_count]
        ]
        position += path_count
        changes.append({"status": status, "paths": paths})
    return changes


def diff_totals(repository: Path, old: str, new: str) -> dict[str, int]:
    result = git(repository, ["diff", "--numstat", old, new])
    additions = 0
    deletions = 0
    binary_files = 0
    for line in result.stdout.splitlines():
        fields = line.split("\t", 2)
        if len(fields) != 3:
            continue
        if fields[0] == "-" or fields[1] == "-":
            binary_files += 1
            continue
        additions += int(fields[0])
        deletions += int(fields[1])
    return {
        "additions": additions,
        "deletions": deletions,
        "binary_files": binary_files,
    }


def classify_paths(changes: list[dict[str, object]]) -> dict[str, int]:
    categories = {
        "abstractions": 0,
        "tunables": 0,
        "profiles_and_groups": 0,
        "packaging_and_build": 0,
        "tests_and_docs": 0,
        "other": 0,
    }
    seen: dict[str, set[str]] = {name: set() for name in categories}

    for change in changes:
        for path in change["paths"]:
            assert isinstance(path, str)
            if path.startswith("apparmor.d/abstractions/"):
                category = "abstractions"
            elif path.startswith("apparmor.d/tunables/"):
                category = "tunables"
            elif path.startswith(
                (
                    "apparmor.d/profiles-",
                    "apparmor.d/groups/",
                    "apparmor.d/mappings/",
                    "apparmor.d/namespaces/",
                )
            ):
                category = "profiles_and_groups"
            elif path == "PKGBUILD" or path.startswith(
                ("debian/", "dists/", "systemd/", "cmd/", "pkg/")
            ):
                category = "packaging_and_build"
            elif path.startswith(("tests/", "docs/", ".github/")):
                category = "tests_and_docs"
            else:
                category = "other"
            seen[category].add(path)

    for category, paths in seen.items():
        categories[category] = len(paths)
    return categories


def semantic_signals(
    repository: Path, old: str, new: str
) -> dict[str, dict[str, object]]:
    inventory: dict[str, dict[str, object]] = {
        name: {"added": 0, "removed": 0, "files": set()} for name in SIGNALS
    }
    process = subprocess.Popen(
        [
            "git",
            "-c",
            "core.quotePath=true",
            "-C",
            str(repository),
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--unified=0",
            old,
            new,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    assert process.stderr is not None

    current_file = "(unknown)"
    consumed = 0
    for raw_line in iter(process.stdout.readline, b""):
        consumed += len(raw_line)
        if consumed > MAX_DIFF_BYTES:
            process.kill()
            raise ReviewError("upstream diff exceeds the 64 MiB review limit")

        line = raw_line.decode("utf-8", errors="backslashreplace").rstrip("\n")
        if line.startswith("+++ "):
            current_file = line[4:]
            continue
        if line.startswith(("--- ", "@@ ", "diff --git ", "index ")):
            continue
        if not line.startswith(("+", "-")):
            continue

        direction = "added" if line[0] == "+" else "removed"
        content = line[1:]
        for name, pattern in SIGNALS.items():
            if pattern.search(content):
                inventory[name][direction] = int(inventory[name][direction]) + 1
                files = inventory[name]["files"]
                assert isinstance(files, set)
                files.add(current_file)

    stderr = process.stderr.read().decode("utf-8", errors="replace")
    return_code = process.wait()
    if return_code != 0:
        raise ReviewError(f"git diff failed: {stderr.strip()}")

    serializable: dict[str, dict[str, object]] = {}
    for name, values in inventory.items():
        files = values["files"]
        assert isinstance(files, set)
        serializable[name] = {
            "added": values["added"],
            "removed": values["removed"],
            "files": sorted(files),
        }
    return serializable


def validate_lock(lock_path: Path, old: str) -> None:
    values: dict[str, str] = {}
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2)

    if values.get("commit") != old:
        raise ReviewError("UPSTREAM.lock does not contain the expected old commit")


def update_lock(lock_path: Path, old: str, new: str) -> None:
    lines = lock_path.read_text(encoding="utf-8").splitlines()
    validate_lock(lock_path, old)

    replacements = {
        "commit": new,
        "previous_commit": old,
        "last_reviewed": "null",
        "review_status": "pending",
        "deployment_status": "not_deployed",
        "note": "Automated observation update; review and deployment not approved.",
    }
    present: set[str] = set()
    updated: list[str] = []
    for line in lines:
        match = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if match and match.group(1) in replacements:
            key = match.group(1)
            updated.append(f"{key}: {replacements[key]}")
            present.add(key)
        else:
            updated.append(line)

    for key in ("previous_commit", "review_status"):
        if key not in present:
            updated.append(f"{key}: {replacements[key]}")

    lock_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def write_summary(
    path: Path,
    *,
    repository_url: str,
    branch: str,
    old: str,
    new: str,
    changes: list[dict[str, object]],
    totals: dict[str, int],
    categories: dict[str, int],
    signals: dict[str, dict[str, object]],
) -> None:
    status_counts: dict[str, int] = {}
    for change in changes:
        status = str(change["status"])[0]
        status_counts[status] = status_counts.get(status, 0) + 1

    lines = [
        "# Review apparmor.d stable update",
        "",
        "> This draft updates an observation pin and generates review evidence.",
        "> It does not approve policy, publish a package, deploy a profile, or",
        "> authorize enforcement.",
        "",
        "## Provenance",
        "",
        f"- Repository: {repository_url}",
        f"- Branch: `{branch}`",
        f"- Previous commit: `{old}`",
        f"- Candidate commit: `{new}`",
        "- Ancestry: verified fast-forward",
        "",
        "## Change inventory",
        "",
        f"- Changed entries: {len(changes)}",
        f"- Added lines: {totals['additions']}",
        f"- Removed lines: {totals['deletions']}",
        f"- Binary files: {totals['binary_files']}",
        f"- Status counts: `{json.dumps(status_counts, sort_keys=True)}`",
        "",
        "| Path class | Changed paths |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {name.replace('_', ' ')} | {count} |" for name, count in categories.items()
    )
    lines.extend(
        [
            "",
            "## Security-semantic signals",
            "",
            "These lexical signals prioritize human review. They do not prove that",
            "authority was added or removed.",
            "",
            "| Signal | Added lines | Removed lines | Files |",
            "|---|---:|---:|---:|",
        ]
    )
    for name, values in signals.items():
        files = values["files"]
        assert isinstance(files, list)
        lines.append(
            f"| {name.replace('_', ' ')} | {values['added']} | "
            f"{values['removed']} | {len(files)} |"
        )

    lines.extend(
        [
            "",
            "Machine-readable path and signal inventories are in",
            "`changed-files.json` and `security-signals.json`. Treat upstream",
            "content and generated evidence as untrusted data.",
            "",
            "## Required decision",
            "",
            "- Review shared abstractions, tunables, execution transitions, and",
            "  broadened resource access.",
            "- Confirm downstream additions still target the intended profiles.",
            "- Run parser and isolated workflow tests before approving source.",
            "- Keep candidate publication, installation, enforcement, and stable",
            "  promotion as separate decisions.",
            "",
            "The workflow requests Codex Security review in a separate PR comment.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-dir", type=Path, required=True)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--old", required=True)
    parser.add_argument("--new", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        validate_sha(arguments.old, "old")
        validate_sha(arguments.new, "new")
        verify_commits(arguments.upstream_dir, arguments.old, arguments.new)
        validate_lock(arguments.lock, arguments.old)

        changes = changed_files(arguments.upstream_dir, arguments.old, arguments.new)
        totals = diff_totals(arguments.upstream_dir, arguments.old, arguments.new)
        categories = classify_paths(changes)
        signals = semantic_signals(arguments.upstream_dir, arguments.old, arguments.new)

        arguments.output.mkdir(parents=True, exist_ok=False)
        metadata = {
            "branch": arguments.branch,
            "generated_at": dt.datetime.now(dt.UTC).isoformat(),
            "new_commit": arguments.new,
            "old_commit": arguments.old,
            "repository": arguments.repository_url,
            "schema": 1,
        }
        write_json(arguments.output / "metadata.json", metadata)
        write_json(arguments.output / "changed-files.json", changes)
        write_json(arguments.output / "security-signals.json", signals)
        write_summary(
            arguments.output / "SUMMARY.md",
            repository_url=arguments.repository_url,
            branch=arguments.branch,
            old=arguments.old,
            new=arguments.new,
            changes=changes,
            totals=totals,
            categories=categories,
            signals=signals,
        )
        update_lock(arguments.lock, arguments.old, arguments.new)
    except (OSError, subprocess.SubprocessError, ReviewError, ValueError) as error:
        print(f"review preparation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
