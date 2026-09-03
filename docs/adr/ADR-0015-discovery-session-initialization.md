# ADR-0015 — Discovery Session Initialization Lifecycle

**Status:** Accepted  
**Date:** 2026-09-01

## Context

Project persistence and duplication intentionally separate project identity from capability state. A newly duplicated project therefore has no copied Business Discovery session.

The Studio previously tolerated a project without a Discovery context during restore. The Discovery composer could still render because its visibility condition treated an undefined context as not approved. A subsequent `/business-discovery/message` call correctly rejected the request, producing a confusing dead-end in the UI.

## Decision

Keep the API strict and repair the lifecycle at the Studio boundary.

Studio owns an idempotent `ensureDiscovery(projectId)` helper:

1. Read the persisted Discovery context.
2. If it exists, reuse it.
3. If it does not exist, initialize Discovery for that project.
4. Never copy Discovery state across project duplication.

The helper is used when creating, restoring and switching projects. The composer is rendered only when a Discovery context is present and is not approved.

The API `/business-discovery/message` endpoint remains strict and does not create sessions implicitly.

## Consequences

- Fresh and duplicated projects can always enter Discovery through the intended Studio flow.
- Duplicate projects retain clean capability state and independent Discovery sessions.
- API behavior remains explicit and predictable.
- A missing Discovery context is no longer hidden by the Studio UI.
- Server-side infrastructure is not required to infer UI lifecycle state.

## Regression contract

The API suite verifies the duplicate lifecycle:

```text
duplicate project
  -> no Discovery context
  -> initialize Discovery
  -> send Discovery message successfully
```

The Studio path additionally uses the same initialization helper for restore and project switching.
