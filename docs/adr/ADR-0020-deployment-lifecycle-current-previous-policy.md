# ADR-0020 — Deployment lifecycle and current/previous runtime policy

**Status:** Accepted for CAP-037 implementation

## Context

CAP-036/FIX-31 established that deployment identity must be preserved across browser navigation. CAP-036/FIX-30 also established canonical latest deployment resolution and safe historical restore. The remaining ambiguity is lifecycle: a deployment can be stopped while its immutable snapshot remains valid, and runtime state must not be confused with product version state.

## Decision

AWE will treat deployment identity, deployment lifecycle and runtime state as separate concepts.

- Deployment ID/version identifies an immutable logical website version.
- Currentness identifies the project's canonical live version.
- Runtime ID/host port identifies a disposable serving process.
- Snapshot identifies the durable source from which a deployment runtime can be recreated.

The local provider will retain the current deployment and immediately previous successful deployment as the warm/runnable window. Older successful deployments remain snapshot-backed and restorable but do not require permanently running containers.

Opening/restoring a deployment never promotes it. Promotion/rollback, if introduced, is a separate explicit operation.

## Rationale

This policy gives users useful access to the current and immediately previous versions while bounding local resource consumption. It also preserves unlimited historical identity without coupling history to Docker container lifetime.

## Alternatives rejected

### Keep every deployment running

Rejected because runtime count grows without bound and turns historical browsing into a resource-management problem.

### Keep only the latest deployment running

Rejected because the immediately previous version is the most useful comparison/recovery target and should be readily accessible.

### Treat `stopped` as equivalent to deleted/unavailable

Rejected because CAP-036 snapshots make stopped deployments recoverable.

### Make restore implicitly promote

Rejected because opening a historical version must be safe and non-destructive. Promotion needs an explicit user intent and atomic lifecycle transition.

## Consequences

- Database schema must express currentness independently of runtime status.
- Runtime reconciliation becomes a first-class provider responsibility.
- Studio must distinguish current, previous and historical/restorable versions.
- Regression tests must cover both browser identity and runtime replacement.
- Historical versions remain available without unlimited running containers.

## Invariants

1. At most one current deployment exists per project.
2. Currentness is not derived from Docker runtime existence.
3. Runtime replacement does not create a new deployment version.
4. Explicit deployment URLs remain pinned to their deployment ID.
5. Historical restore does not stop or mutate the current deployment.
6. A valid snapshot makes a stopped deployment potentially restorable.
