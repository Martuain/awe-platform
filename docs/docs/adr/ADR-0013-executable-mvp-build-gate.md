# ADR-0013 — Use the Existing Docker Build Boundary as the MVP Execution Gate

## Context

AWE already generates a deterministic Next.js artifact, validates it and can start a disposable runtime. The remaining product gap is an explicit, user-visible build step proving that the generated artifact is actually executable before preview/deployment.

## Decision

Expose the existing `website-build` planning and execution services through a dedicated Studio Build stage. Keep Docker as the MVP execution boundary.

## Alternatives rejected

- **Kubernetes:** premature operational complexity for a single-user/local MVP.
- **Hosted CI/build provider:** introduces external dependency and cost before validating the product loop.
- **Persistent worker queue:** unnecessary until concurrent builds become a demonstrated requirement.
- **Direct host execution:** rejected because generated code must never execute in the Studio/API process.

## Consequence

AWE can demonstrate a complete executable product path locally while preserving the provider/adapter boundary needed for later scale-out.
