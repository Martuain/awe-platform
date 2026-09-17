# CAP-019 — Studio Generation Loop

## Objective

Make the path from generated artifact to isolated build, validation, live preview,
and deployment a first-class Studio workflow rather than a set of disconnected
API operations.

## Scope

- Explicit Build stage in the Studio pipeline.
- Build-plan visibility before execution.
- Isolated build execution and diagnostics.
- Validation as a visible gate after a successful build.
- Preview as the next explicit stage after validation, with safe artifact preview and an optional isolated live runtime.
- Deployment as an explicit pipeline stage.
- Deployment history loaded when a project is opened.

## Workflow

```text
Approved Website Specification
        ↓
Website Generation
        ↓
Build Plan
        ↓
Isolated Build
        ↓
Validation
        ↓
Preview
        ↓
Deployment
```

The Studio UI does not execute generated code itself. Build and runtime execution
remain behind the existing API/Docker isolation boundary.

## Acceptance criteria

- Studio exposes Build as a distinct stage.
- A user can inspect/refresh the build plan before execution.
- A failed build exposes useful diagnostics without falsely advancing the pipeline.
- A successful build can be explicitly validated.
- A passed validation can advance to Preview.
- Studio can start an isolated live preview runtime, render it in the Preview stage, refresh it, open it in a new tab, and stop it.
- Deployment is visible as a distinct pipeline stage.
- Existing project switching and lifecycle controls continue to work.
- Deployment history is restored when an existing project is opened.

## Non-goals

- Hosted/scalable workers.
- Cloud deployment provider selection.
- Background job orchestration.
- Collaborative editing.
### CAP-009 runtime responsiveness follow-up

The disposable preview start path runs Docker/npm work in a worker thread so long-running install/build operations do not block FastAPI's event loop. Preview start is also idempotent for an already-running runtime of the same generation, preventing repeated retries from creating duplicate containers.


## Deployment lifecycle hardening

The local deployment provider now treats deployment as a versioned lifecycle:

- deployment requires a validated Website Generation;
- versions increment per project (`v1`, `v2`, ...);
- a new deployment supersedes any queued, deploying, or deployed predecessor;
- superseded deployments are retained in history with `stopped` status and a diagnostic;
- runtime/provider failures are captured as `failed` deployments instead of leaving a deployment stuck in `deploying`;
- Studio calls the canonical `/api/v1/deployments` API and only enables Preview/Deploy after a passed validation.

This remains an MVP local provider. Hosted infrastructure and production cloud deployment are intentionally deferred.
