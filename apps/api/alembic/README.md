# AWE API migrations

Alembic is the authoritative schema migration boundary for the API PostgreSQL database.

- `alembic upgrade head` applies the repository schema.
- `alembic downgrade -1` reverts the most recent migration where supported.
- Application startup applies `alembic upgrade head` when `DATABASE_URL` is configured.
- Tests without `DATABASE_URL` continue to use the in-memory repository.

The initial migration establishes the existing MVP schema. Future schema changes must be committed as new revisions; do not reintroduce `Base.metadata.create_all()` into application startup.
