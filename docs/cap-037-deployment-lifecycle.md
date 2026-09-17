# CAP-037 — Deployment Lifecycle & Current/Previous Version Management

**Status:** Implemented in CAP-037 package; local acceptance pending

## 1. Purpose

CAP-037 formalizes deployment lifecycle semantics after CAP-036/FIX-31 established deployment identity as a durable browser navigation boundary.

The capability must let users reliably manage the current deployment and the immediately previous deployment while keeping older deployments recoverable from immutable snapshots without requiring every historical version to consume a live runtime.

## 2. Core architectural principle

> A deployment is a durable, versioned website artifact. A runtime is disposable infrastructure that serves that artifact.

Therefore:

- deployment ID is immutable and durable;
- deployment version is monotonic within a project;
- runtime ID and host port are ephemeral;
- snapshot identity is derived from deployment ID;
- replacing a runtime never changes deployment identity;
- restoring a historical deployment never implicitly promotes it to current;
- browser navigation remains pinned to the selected deployment.

## 3. Target lifecycle

```text
                    deploy
                      │
                      ▼
                  DEPLOYING
                      │
                 success/fail
                  ┌───┴────┐
                  ▼        ▼
              CURRENT    FAILED
                  │
          newer deployment
                  │
                  ▼
              PREVIOUS
                  │
          retention exceeded
                  │
                  ▼
          HISTORICAL / RESTORABLE
                  │
          explicit restore/open
                  │
                  ▼
             RUNTIME STARTED
```

`STOPPED` is a runtime state and must not by itself mean that the deployment artifact is lost. A stopped deployment with a valid snapshot remains restorable.

## 4. User-visible policy

For each project:

| Version class | Runtime policy | User access |
|---|---|---|
| Current/latest deployed | Keep running | Full live access |
| Immediately previous | Keep running where provider capacity permits and policy requires | Full historical access |
| Older successful versions | Snapshot-backed; runtime may be stopped | Explicit restore/open |
| Failed deployment | No live runtime required | Diagnostics only |
| In-progress deployment | No canonical live status until success | Progress/diagnostics |

The initial local-provider policy is deliberately limited to **current + immediately previous**. Older versions are not deleted merely because their runtime is stopped.

## 5. State semantics

The existing `queued`, `deploying`, `deployed`, `failed`, and `stopped` values are insufficient to express the product distinction between current and historical successful deployments.

CAP-037 should introduce a durable currentness concept without conflating it with runtime health. The preferred design is either:

1. retain deployment status for lifecycle compatibility and add a `role`/`is_current` field; or
2. introduce explicit `current`, `previous`, and `historical` lifecycle states while retaining a separate runtime state.

The implementation decision must preserve backward compatibility with existing persisted rows and API consumers.

### Required invariants

1. At most one deployment per project is canonical current.
2. A current deployment must be successful and have a valid immutable snapshot.
3. A previous deployment is never canonical current merely because it is opened or restored.
4. A historical deployment can have no runtime and still be restorable.
5. A deployment ID maps to one deployment version for the life of the record.
6. Runtime replacement updates `runtime_id`/`url` only; it does not create a new deployment version.
7. Snapshot deletion is prohibited while the deployment is marked restorable unless an explicit retention policy permits it.
8. Browser URLs containing an explicit deployment ID always resolve to that deployment, never to the latest deployment.

## 6. Current deployment resolution

A project-level live URL without `deployment_id` resolves to the unique current successful deployment.

An explicit deployment URL resolves to the requested deployment after project ownership/authorization checks.

The canonical current link and the deployment-history link for the current version must point to the same deployment ID. Runtime ports must never be embedded as the product identity.

## 7. Runtime retention and reconciliation

The local provider should reconcile runtimes after every successful deployment:

1. identify current deployment;
2. identify immediately previous successful deployment;
3. ensure current runtime is healthy;
4. ensure previous runtime is healthy/runnable according to retention policy;
5. stop surplus deployment runtimes;
6. never stop a runtime belonging to another deployment during historical restore;
7. remove orphaned runtimes only when their deployment association is absent or explicitly retired.

Runtime discovery must rely on immutable Docker labels such as `com.awe.deployment_id` and `com.awe.project_id`.

## 8. Historical restore

Opening an older deployment should use its `awe-deployment-<deployment-id>` snapshot.

Restoration is an infrastructure operation, not a promotion operation. The restored deployment:

- keeps its original deployment ID and version;
- remains historical/previous according to lifecycle policy;
- gets a new runtime ID and possibly a new host port;
- remains deployment-scoped in browser navigation;
- must not stop or mutate the current deployment runtime.

If product requirements later add an explicit **Rollback/Promote** action, that must be a separate operation with its own authorization, audit trail and atomic currentness transition.

## 9. Failure and recovery

Deployment success must be atomic from the user's perspective:

- snapshot creation succeeds;
- deployment runtime is healthy;
- database state is persisted as successful/current;
- only then is the prior current deployment demoted.

A failed new deployment must not leave the project without a current successful deployment.

If runtime startup fails after a valid snapshot exists, the deployment remains restorable but is not current until explicitly promoted by a future operation.

## 10. Concurrency and idempotency

Deployment and restore operations must be serialized per project/deployment where required.

Repeated requests for the same deployment must reuse a healthy runtime rather than creating duplicates. Duplicate runtime reconciliation must retain one valid keeper.

Concurrent deployment requests must not create two canonical current deployments. The database transition must provide the final authority even if API workers race.

## 11. API contract

Existing endpoints remain compatible. CAP-037 may add explicit lifecycle actions such as:

- `GET /deployments?project_id=...`
- `GET /deployments/{deployment_id}`
- `POST /deployments`
- `POST /deployments/{deployment_id}/restore`
- `POST /deployments/{deployment_id}/stop`
- optionally later `POST /deployments/{deployment_id}/promote`

`restore` must not mean `promote`.

Responses should expose enough information for Studio to distinguish:

- current;
- previous;
- historical/restorable;
- runtime running/stopped;
- snapshot available/unavailable.

## 12. Database design

The preferred migration should make currentness explicit and enforceable at project scope. A candidate design is:

```text
website_deployments
  deployment id       immutable primary key
  project id          indexed
  version             monotonic per project
  status              deployment operation/result
  lifecycle_role      current | previous | historical
  provider            local | hosted
  url                 current runtime endpoint, nullable
  runtime_id          disposable runtime identity, nullable
  snapshot_ref        immutable snapshot identifier
  diagnostics        structured diagnostics
  created_at
  deployed_at
  stopped_at
```

A partial unique index or equivalent database constraint should enforce one `current` deployment per project. Version allocation must be concurrency-safe.

If adding `snapshot_ref` would duplicate the deterministic existing Docker naming convention, it may be deferred; the design must nevertheless make snapshot availability observable rather than inferring it only from a runtime.

## 13. Security

All deployment operations must remain behind the existing project authorization boundary established by CAP-025.

Historical deployment access must not become a way to bypass project membership, tenant boundaries or API-key restrictions.

Runtime/container identifiers and host ports are internal implementation details and must not become authorization credentials.

## 14. Studio UX

Deployment history should communicate two separate concepts:

- **Current / live** — the project's canonical version.
- **Previous / historical** — a specific version that can be opened/restored without changing the canonical live version.

A stopped historical deployment should not be presented as broken when a valid snapshot exists. It should be presented as **restorable**.

The current live CTA and the current deployment-history CTA must resolve to the same deployment ID.

## 15. Regression matrix

### Identity

- current direct entry → current content;
- explicit V7 direct entry → V7 content;
- explicit V8 direct entry → V8 content;
- V7 navigation never becomes V8;
- V8 navigation never becomes V7;
- refresh preserves selected deployment.

### Lifecycle

- deploy V8 demotes V7 from current;
- V8 remains current after V7 restore/open;
- previous V7 can be opened without stopping V8;
- older V6 remains restorable without a permanent runtime;
- runtime replacement does not change deployment ID/version.

### Runtime

- duplicate restore requests converge on one runtime;
- unhealthy current runtime can be recreated from its snapshot;
- stopped previous runtime can be recreated;
- surplus runtimes are reconciled;
- orphaned runtimes are cleaned safely.

### Failure

- failed deployment does not replace current;
- snapshot failure does not produce a current deployment;
- runtime startup failure leaves a recoverable artifact when snapshot exists;
- concurrent deploys cannot create two current records.

## 16. Acceptance criteria

CAP-037 is accepted when:

1. one and only one deployment is canonical current per project;
2. the immediately previous successful deployment is independently addressable;
3. current and previous deployments can coexist without cross-navigation;
4. opening/restoring previous or historical versions does not alter currentness;
5. older deployments remain restorable from snapshots without permanently running runtimes;
6. runtime IDs/ports can change without changing deployment identity;
7. failed deployments cannot displace a valid current deployment;
8. current/history Studio links converge on the intended deployment ID;
9. API, database and browser regressions pass;
10. CAP-036/FIX-31 navigation isolation remains green.

## 17. Explicit non-goals

- cloud autoscaling;
- multi-region deployment;
- CDN management;
- arbitrary number of permanently warm historical runtimes;
- automatic rollback after every failure;
- treating restore as promotion;
- changing the immutable deployment snapshot model established by CAP-036.

## 18. Implementation order

1. Add lifecycle role/currentness model and migration.
2. Make deployment promotion atomic and concurrency-safe.
3. Refactor local provider runtime reconciliation to current + previous policy.
4. Add explicit historical restore semantics.
5. Update Studio deployment history and live CTA resolution.
6. Add API/runtime/browser regression matrix.
7. Update architecture, Project Master, changelog and troubleshooting records.
8. Run full local Docker acceptance before release packaging.


## 19. Implementation notes

The implementation preserves the CAP-036/FIX-31 deployment-pinned namespace and
introduces currentness as a separate durable concern.

The local provider now follows this ordering:

1. allocate a monotonic deployment version;
2. create the deployment in `deploying`/historical state;
3. build/start the candidate runtime;
4. materialize published content into the deployment workspace;
5. persist the immutable deployment snapshot;
6. activate a runtime carrying the immutable deployment ID label;
7. persist `deployed` + `snapshot_ref`;
8. atomically promote the candidate to `current`;
9. reconcile deployment runtimes to current + immediately previous.

The old current deployment is therefore never stopped before the candidate has
become a valid snapshot-backed deployment. This closes the failure window where
a failed deployment could leave a project without its previous live version.

PostgreSQL advisory locking serializes deployment-version allocation and
currentness promotion across API workers; the partial unique index is the final
database authority preventing multiple current deployments.

Historical restore is exposed separately from deployment/promotion. It reuses
the original deployment ID, creates a disposable runtime when needed, and does
not alter `lifecycle_role`.

### FIX-31 relationship

CAP-036 established the immutable deployment browser namespace. CAP-037 builds
on that boundary rather than replacing it. The generated HTML/RSC navigation
continues to be rewritten to the selected deployment prefix, so navigation
from one deployment cannot silently fall back to the project's current
deployment.
