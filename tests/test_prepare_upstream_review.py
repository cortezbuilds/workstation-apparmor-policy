from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOL = PROJECT_ROOT / "tools" / "prepare_upstream_review.py"


def run(
    command: list[str], *, cwd: Path, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


class PrepareUpstreamReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.upstream = self.root / "upstream"
        self.upstream.mkdir()
        run(["git", "init", "-b", "stable"], cwd=self.upstream)
        run(["git", "config", "user.name", "Test"], cwd=self.upstream)
        run(
            ["git", "config", "user.email", "test.invalid"],
            cwd=self.upstream,
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def commit(self, message: str) -> str:
        run(["git", "add", "."], cwd=self.upstream)
        run(["git", "commit", "-m", message], cwd=self.upstream)
        return run(["git", "rev-parse", "HEAD"], cwd=self.upstream).stdout.strip()

    def write_lock(self, commit: str) -> Path:
        lock = self.root / "UPSTREAM.lock"
        lock.write_text(
            "---\n"
            "schema: 1\n"
            "repository: https://example.invalid/apparmor.d.git\n"
            "tracking_branch: stable\n"
            f"commit: {commit}\n"
            "source_sha256: null\n"
            "last_reviewed: null\n"
            "deployment_status: not_deployed\n"
            "note: Test observation pin.\n",
            encoding="utf-8",
        )
        return lock

    def invoke(
        self, old: str, new: str, lock: Path, output: Path
    ) -> subprocess.CompletedProcess[str]:
        return run(
            [
                sys.executable,
                str(TOOL),
                "--upstream-dir",
                str(self.upstream),
                "--repository-url",
                "https://example.invalid/apparmor.d.git",
                "--branch",
                "stable",
                "--old",
                old,
                "--new",
                new,
                "--output",
                str(output),
                "--lock",
                str(lock),
            ],
            cwd=PROJECT_ROOT,
            check=False,
        )

    def test_generates_inventory_and_pending_lock_for_fast_forward(self) -> None:
        profile = self.upstream / "apparmor.d" / "profiles-a-f" / "demo"
        profile.parent.mkdir(parents=True)
        profile.write_text("/usr/bin/demo {\n  /tmp/demo r,\n}\n", encoding="utf-8")
        old = self.commit("base")

        profile.write_text(
            "/usr/bin/demo {\n"
            "  capability net_admin,\n"
            "  network inet stream,\n"
            "  deny /private/** rw,\n"
            "}\n",
            encoding="utf-8",
        )
        new = self.commit("policy change")
        lock = self.write_lock(old)
        output = self.root / "review"

        result = self.invoke(old, new, lock, output)

        self.assertEqual(result.returncode, 0, result.stderr)
        metadata = json.loads((output / "metadata.json").read_text())
        self.assertEqual(metadata["old_commit"], old)
        self.assertEqual(metadata["new_commit"], new)

        signals = json.loads((output / "security-signals.json").read_text())
        self.assertEqual(signals["capability_rule"]["added"], 1)
        self.assertEqual(signals["network_rule"]["added"], 1)
        self.assertEqual(signals["deny_rule"]["added"], 1)

        summary = (output / "SUMMARY.md").read_text()
        self.assertIn("verified fast-forward", summary)
        self.assertIn("Codex Security review", summary)

        updated_lock = lock.read_text()
        self.assertIn(f"commit: {new}", updated_lock)
        self.assertIn(f"previous_commit: {old}", updated_lock)
        self.assertIn("review_status: pending", updated_lock)
        self.assertIn("deployment_status: not_deployed", updated_lock)

    def test_rejects_non_fast_forward_update_without_writing(self) -> None:
        tracked = self.upstream / "tracked"
        tracked.write_text("root\n", encoding="utf-8")
        root = self.commit("root")

        tracked.write_text("stable\n", encoding="utf-8")
        old = self.commit("stable change")

        run(["git", "switch", "-c", "diverged", root], cwd=self.upstream)
        tracked.write_text("diverged\n", encoding="utf-8")
        new = self.commit("diverged change")

        lock = self.write_lock(old)
        output = self.root / "review"
        result = self.invoke(old, new, lock, output)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a fast-forward", result.stderr)
        self.assertFalse(output.exists())
        self.assertIn(f"commit: {old}", lock.read_text())

    def test_rejects_lock_that_does_not_match_expected_old_commit(self) -> None:
        tracked = self.upstream / "tracked"
        tracked.write_text("old\n", encoding="utf-8")
        old = self.commit("old")
        tracked.write_text("new\n", encoding="utf-8")
        new = self.commit("new")

        lock = self.write_lock("0" * 40)
        output = self.root / "review"
        result = self.invoke(old, new, lock, output)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not contain the expected old commit", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
