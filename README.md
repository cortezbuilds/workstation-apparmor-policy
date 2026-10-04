# Workstation AppArmor Policy

Public governance and provenance for threat-model-driven AppArmor policy on
developer workstations.

> [!IMPORTANT]
> This repository is currently a **governance scaffold only**. It contains no
> deployable profiles or packages, does not enable AppArmor, and does not
> automatically merge, publish, install, reload, or enforce policy.

## Purpose

This project is intended to turn workstation AppArmor policy into a reviewable
supply chain:

```text
apparmor.d stable commit
        |
        v
draft integration change
        |
        +-- provenance and semantic policy review
        +-- parser, build, and isolated workflow tests
        +-- downstream overlay compatibility
        |
        v
signed candidate package
        |
        v
complain-mode observation and recovery testing
        |
        v
explicit human promotion to a self-controlled stable repository
```

The community [apparmor.d](https://github.com/roddhjav/apparmor.d) project is
an upstream input, not an automatically trusted deployment source. A moving
branch is used only to detect updates; builds must use the exact commit recorded
in [`UPSTREAM.lock`](UPSTREAM.lock).

## Current status

| State | Value |
|---|---|
| Repository phase | Governance scaffold |
| Upstream tracking branch | `stable` |
| Approved deployment baseline | None |
| Deployable policy | None |
| Published package | None |
| Automatic deployment | Prohibited |
| Enforcement authorization | None |

The implemented upstream workflow checks `apparmor.d/stable` weekly. When the
branch advances by a verified fast-forward, it creates a draft integration PR
containing an updated observation pin and machine-readable security-semantic
inventory. It requests Codex Security review with
`@codex security review`. Repository access must be enabled separately in
Codex Security for that request to produce a review.

## Documents

- [Threat model](THREAT-MODEL.md)
- [Governance and promotion gates](GOVERNANCE.md)
- [Upstream tracking policy](UPSTREAM.md)
- [Architecture](docs/architecture.md)
- [Rollout model](docs/rollout.md)
- [Recovery requirements](docs/recovery.md)
- [Review checklist](docs/review-checklist.md)
- [Security reporting](SECURITY.md)

## Design principles

1. Prefer downstream `local/` additions and tunables over editing upstream
   profiles.
2. Keep unavoidable upstream modifications as an explicit, ordered patch
   series.
3. Treat a clean rebase, a successful parse, a successful test, publication,
   installation, and observed enforcement as separate states.
4. Never translate an audit denial directly into an allow rule without deciding
   whether the attempted access is legitimate.
5. Never place credentials, private host inventory, raw audit logs, or signing
   keys in this public repository.
6. Stop at a draft review when human security judgment is unavailable.

## Local verification

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile tools/prepare_upstream_review.py
```

## License

Copyright 2026 Cortez Builds.

Unless a file states otherwise, this repository is licensed under
GPL-2.0-only. See [`LICENSE`](LICENSE).
