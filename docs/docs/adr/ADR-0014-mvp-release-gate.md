# ADR-0014 — MVP v1.0 Release Gate

**Status:** Accepted  
**Date:** 2026-08-25

## Context

AWE has accumulated enough capabilities to prove the core website-creation workflow. Continuing to add infrastructure before establishing a complete executable baseline would increase complexity and delay product validation.

## Decision

Define MVP v1.0 as a **local executable product baseline** with a single repository gate:

```text
pnpm mvp:gate
```

The gate runs lint, production build and tests. Docker Compose remains the local integration/runtime boundary.

## Why

- Fast feedback.
- Reproducibility.
- Minimal operational complexity.
- Clear definition of done.
- Keeps infrastructure decisions reversible.
- Focuses the project on validating the product rather than building a platform before demand is proven.

## Rejected alternatives

### Kubernetes for MVP

Rejected as premature operational complexity.

### Hosted CI/CD as the product runtime

Rejected because CI is a validation mechanism, not the core AWE execution architecture.

### Multiple supported website frameworks

Rejected until one framework's generation/build/preview lifecycle is validated.

### Authentication/multi-tenancy before the executable loop

Deferred because they do not prove the core product hypothesis.
