# ADR-0012 — Project Duplication Creates a Fresh Workspace

## Status
Accepted — CAP-014

## Context
Users need a quick way to create a variant of an existing project. Copying every persisted artifact would also copy lifecycle state, deployment history, and mutable version relationships.

## Decision
Duplicate only project metadata. Create a new UUID and active status; leave all capability artifacts empty.

## Alternatives rejected
- Deep database clone: too coupled to current schema and risks copying deployment/runtime state.
- Export/import archive: premature before a stable portable artifact format exists.
- Client-side duplication: violates API-first ownership of persistence.

## Consequences
The operation is deterministic, simple, repository-compatible, and safe. Reusable templates can be added later as an explicit artifact feature.
