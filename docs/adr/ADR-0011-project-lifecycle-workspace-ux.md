# ADR-0011 — Project Lifecycle & Workspace UX

## Status
Accepted for CAP-013.

## Context
CAP-012 made projects persistent and exposed a workspace summary, but Studio still treated the project mostly as a selected browser session. Users need a concise representation of project progress and a safe way to archive work without deleting persisted artifacts.

## Decision
Extend the existing Projects API and Repository abstraction with project lifecycle status and derived workspace progress. Add a Studio workspace summary above the capability pipeline.

The API derives workflow progress from persisted capability artifacts instead of storing a second mutable workflow state machine.

## Why not a separate workflow service?
The product has not demonstrated enough complexity to justify another service boundary. The capability artifacts already expose the state required to derive progress.

## Why derived progress?
A duplicated `current_stage` field could become stale when capabilities are created, revised or approved through different API paths. Derivation gives the workspace a single source of truth.

## Why archive instead of delete?
AWE's direction includes provenance, reproducibility and future auditability. Reversible archival protects those properties and is safer than introducing irreversible deletion before retention requirements are known.

## Why localStorage remains?
The browser only needs to remember the last project the user opened. Durable project state belongs in the API/database. This keeps localStorage as a convenience rather than a persistence mechanism.

## Revisit triggers
Revisit the lifecycle model when authentication, multi-tenancy, collaboration, retention/legal requirements, large project collections or asynchronous workflow orchestration are introduced.
