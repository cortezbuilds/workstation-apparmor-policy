# Rollout

No rollout is currently authorized.

## Proposed stages

1. **Governance scaffold** — public documents and an observation-only upstream
   pin.
2. **Isolated build** — parser, linter, clean package build, and disposable VM
   tests.
3. **Recovery rehearsal** — demonstrate boot and policy rollback without the
   candidate desktop policy.
4. **Complain-mode canary** — observe representative daily workflows and review
   every material denial. Explicit deny rules require special attention because
   complain mode is not equivalent to no enforcement.
5. **Selective enforcement** — promote narrowly scoped profiles one boundary at
   a time.
6. **Stable publication** — publish only the exact reviewed and observed
   package.

## Minimum workflow coverage

- KDE/SDDM login and logout.
- Network and VPN recovery.
- Package installation and upgrade.
- Browser, portal, clipboard, download, and upload workflows.
- Audio, microphone, camera, screen capture, and OBS workflows.
- Terminal, editor, Git, language package managers, build and test tools.
- Credential agents without exposing credential material to the test record.
- Backup, restore, removable-media, and emergency-recovery operations.

## Stop conditions

Stop promotion when:

- the desktop or recovery path is unproven;
- a profile unexpectedly becomes unconfined;
- a shared abstraction broadens unrelated profiles;
- required access cannot be explained;
- policy behavior differs between the test and target feature ABI;
- private evidence would need to be published to justify the change; or
- human threat-model review is unavailable.
