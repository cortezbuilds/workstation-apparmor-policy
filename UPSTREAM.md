# Upstream Policy

## Source

- Repository: <https://github.com/roddhjav/apparmor.d>
- Production tracking branch: `stable`
- Observation-only branch: `main`
- Build input: the exact commit in [`UPSTREAM.lock`](UPSTREAM.lock)

The branch name detects candidate updates. It is never sufficient as a build
input.

## Remote layout

A working checkout should use:

```text
origin    downstream repository controlled by Cortez Builds
upstream  https://github.com/roddhjav/apparmor.d.git
```

The downstream repository is independent rather than a GitHub fork because it
contains workstation governance, packaging, and threat-model-specific material
that is not intended to replace the general upstream project.

## Update procedure

1. Read the current `stable` head without modifying downstream state.
2. If it differs from `UPSTREAM.lock`, create a draft integration change.
3. Record the old and new commit IDs.
4. Review all changed profiles, abstractions, tunables, build logic, and tests.
5. Reapply the explicit downstream patch series without silently resolving
   conflicts.
6. Check local-addition and profile-name compatibility.
7. Run parser, build, semantic checks, and isolated workflow tests.
8. Request security-oriented Codex review.
9. Leave the change in draft until explicit approval.

## Contribution boundary

Generic fixes should be proposed upstream. Host-specific paths, private
inventory, local trust decisions, and downstream packaging policy remain
downstream.

A pinned commit identifies content; it does not by itself prove the identity or
integrity of the party that supplied it. Release-signature and upstream
provenance availability must be evaluated as part of each integration review.
