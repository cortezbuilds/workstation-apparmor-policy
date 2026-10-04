# Governance

## Roles of automation and review

Automation may detect an upstream change, create an integration branch,
generate a policy-oriented diff, run checks, build a candidate artifact, and
open a draft review.

Automation must not:

- silently resolve policy conflicts;
- convert denials into allow rules;
- merge an integration change;
- sign or publish a stable package;
- change a workstation repository configuration;
- install or reload profiles;
- change complain/enforce state; or
- suppress a failed or uncertain recovery check.

When human security judgment is unavailable, the workflow stops at a draft
review.

## State model

The following states are deliberately independent:

1. Upstream revision discovered.
2. Downstream patch series applies.
3. Policy syntax parses.
4. Policy loads in an isolated test kernel.
5. Required workflows pass.
6. Threat-model boundaries pass negative tests.
7. Candidate package builds.
8. Candidate package is signed and published.
9. Candidate is observed in complain mode.
10. Selected profiles are approved for enforcement.
11. Package is promoted to the stable repository.
12. Installation and loaded-policy state are independently read back.

Evidence for one state does not imply a later state.

## Change classes

### Upstream-only update

The pinned upstream commit changes without a downstream policy change. Review
still covers shared abstractions, tunables, transitions, profile renames, and
dependency changes.

### Downstream local addition

A file intended for `/etc/apparmor.d/local/` or a downstream tunable changes.
The review must identify the supported workflow and affected asset boundary.

### Direct upstream patch

A patch changes upstream policy because a local addition cannot express the
requirement. Direct patches require an explicit rationale and should be
upstreamed when generally applicable.

### Packaging or distribution change

Build inputs, clean-build environment, signing, repository metadata, or
promotion logic changes. This is a supply-chain change even when policy text is
unchanged.

## Promotion

Promotion to a stable package repository requires:

- exact source and upstream commits;
- clean-build receipt;
- package and repository signatures;
- parser and isolated test results;
- complain-mode observation appropriate to the change;
- recovery-path verification;
- unresolved denials and uncertainty recorded; and
- explicit human approval.

No signing secret belongs in this repository or its CI configuration.

## Public/private boundary

This repository may contain generic threat classes, policy, tests, packaging,
and sanitized evidence.

It must not contain secrets, private host inventories, usernames, account
identifiers, live audit logs, access tokens, private network topology, or exact
paths that disclose sensitive material. Private evidence may be referenced by a
non-secret receipt or retained in a separate protected system.
