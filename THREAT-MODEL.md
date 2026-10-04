# Threat Model

## Status

This is an initial public threat model. It defines review questions and
deployment gates; it does not claim that any AppArmor policy is deployed or
effective.

## Objective

Reduce the effect of compromised or unexpectedly behaving workstation
processes without making normal development, communication, capture, recovery,
or package-management workflows unreliable.

The policy must remain inspectable, attributable to exact source revisions, and
recoverable without relying on the policy it is recovering from.

## Protected asset classes

- Authentication agents, password stores, browser sessions, and desktop
  keyrings.
- SSH, OpenPGP, package-signing, release-signing, and deployment credentials.
- Wallets, recovery material, encrypted backups, and backup credentials.
- Source repositories, unpublished work, production configuration, and build
  provenance.
- Package-manager configuration, repository trust roots, boot configuration,
  system services, and policy files.
- Microphone, camera, screen-capture, clipboard, notification, and portal
  authority.
- Agent and local-tool configuration, credentials, persistent data, and
  subprocess authority.

This public document intentionally describes classes of assets rather than
private paths, account names, device identifiers, or inventory.

## Threats in scope

- Exploitation of browsers, renderers, Electron applications, document
  previewers, media parsers, and archive tools.
- Malicious or compromised dependencies, build scripts, AUR recipes, source
  repositories, plugins, extensions, and downloaded executables.
- Untrusted code launched by development tools or agents.
- Application updates that silently broaden filesystem, network, IPC, device,
  or execution access.
- Upstream policy changes that broaden authority or invalidate downstream
  assumptions.
- Incorrect conflict resolution, stale local additions, renamed profiles, and
  unconfined execution transitions.
- Compromise of the policy build or distribution path.
- Over-restrictive policy that breaks login, networking, audio, display,
  package management, backup, or recovery.

## Trust boundaries

1. Untrusted content must not imply access to credentials or signing material.
2. Development execution must not silently acquire production or identity
   authority.
3. Capture applications must receive microphone, camera, screen, and portal
   access only through documented workflows.
4. Provisioning tools may modify system state only through explicit,
   authenticated operations.
5. Policy source, package construction, signing, publication, installation, and
   enforcement are separate trust edges.
6. Recovery must remain possible when a new policy prevents the normal desktop
   or network from starting.

## Out of scope

AppArmor does not by itself provide:

- source authenticity or package provenance;
- protection from a compromised kernel;
- complete containment of every user application;
- assurance that permitted access is used safely;
- replacement for discretionary permissions, process sandboxing, systemd
  hardening, seccomp, cryptographic signing, backups, or recovery media;
- proof of safety from a clean merge or successful parser run.

## Policy acceptance rule

An access rule is acceptable only when:

1. a documented supported workflow requires it;
2. the permitted resource and operation are no broader than necessary;
3. narrower mechanisms have been considered;
4. the rule does not cross an unrelated asset boundary;
5. a test or observation can detect loss of the required workflow; and
6. recovery remains available if the judgment is wrong.

Audit output is evidence of attempted access, not evidence that access should
be authorized.
