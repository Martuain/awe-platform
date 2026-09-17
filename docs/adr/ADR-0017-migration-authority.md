# ADR-0017 — Alembic Migration Authority

## Status
Accepted for the MVP working baseline.

## Decision
PostgreSQL schema changes are managed by Alembic. API startup may apply committed migrations with `alembic upgrade head`, but the application must not create or mutate schema through `Base.metadata.create_all()`.

## Rationale
An explicit migration history makes empty-database initialization reproducible, exposes schema drift as a versioned artifact, and provides a controlled boundary for future schema evolution without prematurely introducing a separate migration service.

## Consequences
The API image includes Alembic and migration scripts. Future schema changes require a new revision. The initial MVP revision establishes the existing schema and is intentionally simple; later revisions should contain explicit operations appropriate to the change.
