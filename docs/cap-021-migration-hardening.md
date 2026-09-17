# CAP-021 — Migration Hardening

## Status

Implemented in the CAP-021 working package; pending owner local deployment/acceptance.

## Objective

Make PostgreSQL schema lifecycle reproducible and explicit by replacing application-owned `create_all()` startup behavior with Alembic migrations.

## Added

- Alembic configuration under `apps/api/alembic/`.
- Initial `0001_initial_schema` revision representing the existing MVP schema.
- API startup migration execution through `alembic upgrade head`.
- Migration regression tests.

## Changed

- `init_database()` no longer calls `Base.metadata.create_all()` directly.
- Migration execution is moved to a worker thread so synchronous Alembic work does not block the FastAPI event loop.
- Roadmap marks migration hardening complete for this increment.

## Fixed / hardened

- Empty PostgreSQL databases now have an explicit repository migration path.
- Schema lifecycle is versioned instead of being implicitly inferred at every application startup.
- Future schema changes have a required migration boundary.

## Removed / deliberately avoided

- No runtime auto-generation of new migration revisions.
- No destructive migration on startup.
- No migration framework change for the in-memory test repository.
- The initial revision uses the existing SQLAlchemy metadata to establish the baseline; future changes must be explicit revisions.

## Verification

- Migration configuration and revision tests added.
- Full API regression suite must be run before package acceptance.
- Empty-database upgrade and Docker-stack startup are package acceptance checks.

## Deferred

Migration rollback policy for every future destructive schema change, online zero-downtime migrations, backup/restore automation, and production migration orchestration remain outside this MVP increment.
