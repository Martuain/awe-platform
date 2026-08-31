# ADR-0010 — Project Persistence & Workspace Model

## Status
Accepted for CAP-012.

## Context
AWE already persisted capability artifacts behind a repository boundary, but Studio treated the active project as a browser-local session. Users could not reliably discover existing projects, resume a project from another browser session, or inspect a compact workspace state.

## Decision
CAP-012 formalizes the project as the persistent workspace root. The API exposes project listing and a workspace summary, while capability artifacts remain behind the existing Repository abstraction. PostgreSQL remains the selected shared persistence technology for the current containerized environment. SQLAlchemy provides the data-access boundary. Versioned capability payloads continue to be stored as JSON text behind typed Pydantic models rather than prematurely normalizing every capability-specific field.

## Why PostgreSQL
PostgreSQL is already part of the project's Docker Compose baseline, supports transactional persistence, indexing, JSON-capable data models, and provides a credible path to multi-user production. SQLite was considered for local-only persistence but would introduce a second persistence topology without solving the shared-environment requirement.

## Why SQLAlchemy
SQLAlchemy is already used by the API and provides an async repository boundary. Replacing it would create migration cost without improving the CAP-012 product outcome.

## Deferred
Authentication/authorization, multi-tenancy, migrations tooling, object storage for generated files, full event sourcing, and production backup/retention policy remain future concerns.

## Revisit triggers
Revisit the storage model when project volume, concurrent writers, artifact size, tenant isolation, or audit requirements exceed the current repository design.
