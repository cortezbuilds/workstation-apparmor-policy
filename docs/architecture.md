# Architecture

## Components

### Policy source repository

This repository records upstream provenance, the public threat model,
downstream policy, review evidence, packaging instructions, and promotion
rules.

### Candidate package channel

Future signed packages that have built successfully but have not completed
observation and promotion. Candidate publication is not authorization to
install.

### Stable package channel

Future signed packages explicitly promoted after the required evidence and
approval. Repository metadata must also be signed.

### Private evidence store

Host inventories, raw audit logs, sensitive path mappings, and other evidence
that should not be public. Public reviews may reference sanitized receipts but
must not copy private evidence into this repository.

## Trust flow

```text
upstream commit
      +
downstream commit
      +
pinned build inputs
      |
      v
clean build and policy checks
      |
      v
signed candidate artifact
      |
      v
isolated and complain-mode observation
      |
      v
explicit promotion
      |
      v
signed stable repository
      |
      v
installation and independent readback
```

Every arrow is a distinct trust edge. A receipt proves only the edge it
directly observes.
