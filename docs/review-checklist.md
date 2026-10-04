# Review Checklist

## Provenance

- [ ] Old and new upstream commits are recorded.
- [ ] The source is pinned by commit and independently hashed.
- [ ] Upstream signature/provenance availability is recorded.
- [ ] Build inputs and environment are identified.

## Policy semantics

- [ ] Added or widened filesystem globs are justified.
- [ ] New write, link, lock, or executable-mapping permissions are justified.
- [ ] Execution transitions, especially unconfined transitions, are reviewed.
- [ ] Capability, network, mount, namespace, ptrace, signal, Unix-socket, and
      D-Bus changes are reviewed.
- [ ] Removed deny rules are reviewed.
- [ ] Shared abstraction and tunable changes are traced to all consumers.
- [ ] Renamed or removed profiles do not orphan downstream additions.
- [ ] Rules touching protected asset classes have negative tests.

## Compatibility

- [ ] Policy parses against the target userspace and feature ABI.
- [ ] Profiles load in an isolated test kernel.
- [ ] Required workstation workflows pass.
- [ ] Recovery works without relying on the candidate policy.
- [ ] Complain-mode observations have been reviewed.

## Supply chain

- [ ] Clean package build succeeded.
- [ ] Package contents match the reviewed source.
- [ ] Candidate and stable channels remain distinct.
- [ ] Package and repository signatures are verified.
- [ ] No secret, private inventory, or raw audit log is in the diff.

## Decision

- [ ] Uncertainty and residual risk are written down.
- [ ] Human approval is explicit.
- [ ] The approved state—merge, candidate publication, installation,
      enforcement, or stable promotion—is unambiguous.
