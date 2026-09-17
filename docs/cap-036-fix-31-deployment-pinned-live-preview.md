# CAP-036 FIX-31 — Deployment-pinned live preview navigation

## Status

**Accepted / verified locally after deployment.**

FIX-31 is the deployment identity and navigation-isolation correction that closes a CAP-036 regression in which an explicitly selected historical deployment could render correctly on first request and then silently switch to the project's latest deployment after browser navigation.

The fix was deployed locally and verified end-to-end against deployment v7 and v8. V7 remained the V7 website (`Coyote - Sylvester`) while navigating Home → About → Services → Contact → Home; V8 independently remained the V8 website (`Coyote - Tweety`).

## Problem statement

CAP-036 introduced a stable live-deployment entry point so the browser does not depend on a disposable runtime's dynamic host port. The stable project URL was initially sufficient for opening the canonical current deployment, and the historical deployment entry point accepted a `deployment_id` query parameter.

That query-parameter contract was not strong enough to define the identity of the browser navigation session. The first HTML document could be rendered from the requested deployment, but generated application links and Next.js navigation could omit the query parameter. A subsequent request therefore returned to the project-level deployment proxy without an explicit deployment identity. The server correctly interpreted that request as “current/latest deployed deployment,” which meant a historical V7 page could become V8 after navigation.

The user-visible failure was especially misleading:

```text
Open V7
  initial Home → Coyote - Sylvester
  click About
  click Home
  Home → Coyote - Tweety   # incorrect
```

This was not a content-generation defect and was not caused by the V7 snapshot containing V8 content. Direct access to the V7 runtime and initial V7 server render both proved that the V7 snapshot/runtime was correct. The defect was deployment identity loss across navigation.

## Evidence that isolated the defect

Before FIX-31, the local deployment records showed:

```text
v7  stopped   runtime 20fb3a3f1215
v8  deployed  runtime cebbb1af7474
```

The stopped V7 runtime was still directly reachable after historical restore, and its direct HTTP response rendered:

```text
<title>Home
<h1>Coyote - Sylvester
```

The V8 runtime rendered:

```text
<title>Home
<h1>Coyote - Tweety
```

The stable Studio URL for V7 also returned V7 on its initial request. The failure appeared after browser navigation, demonstrating that the snapshot and runtime selection were individually correct while the navigation boundary was not.

## Root cause

There were two related routing contracts:

1. **Project-scoped stable deployment proxy** — if no `deployment_id` was present, it resolved the latest `deployed` deployment.
2. **Explicit deployment selection** — if `deployment_id` was present, the API could resolve that exact deployment.

Generated website links were still project-scoped. A URL such as:

```text
/api/live-preview/deployment/<project-id>/about
```

contained no durable deployment identity. Consequently, the proxy had to fall back to the latest deployed deployment. The query parameter had been an entry-point selector, not a navigation-scoped identity.

The same problem affected generated asset URLs and Next.js serialized navigation state: even when the initial HTML was produced from V7, browser/client requests could escape the selected deployment namespace.

## Architectural correction

FIX-31 establishes a stronger invariant:

> **Once a live deployment is selected, every browser-visible route and generated resource for that live deployment is pinned to the selected `deployment_id`.**

The stable project route remains useful as the canonical “latest live deployment” entry point, but it is now an entry point into a deployment-specific namespace rather than the namespace itself.

The resulting model is:

```text
Project
│
├── canonical latest entry
│      /api/live-preview/deployment/<project-id>/
│      └── resolve latest DEPLOYED deployment
│
├── V7 selected deployment
│      /api/live-preview/deployment/<project-id>/<v7-deployment-id>/...
│      └── V7 snapshot/runtime
│
└── V8 selected deployment
       /api/live-preview/deployment/<project-id>/<v8-deployment-id>/...
       └── V8 snapshot/runtime
```

The important distinction is between **selection** and **identity**:

- The project-level URL selects the current deployment when no deployment was specified.
- The deployment-scoped URL identifies the deployment for the remainder of the browser navigation lifecycle.
- Historical deployment status does not make its content invalid; a stopped deployment can be restored from its immutable snapshot and viewed without becoming the project's canonical deployment.

## Implementation changes

### 1. Deployment-scoped Studio route

Added:

```text
/api/live-preview/deployment/{projectId}/{deploymentId}/...
```

The Next.js route validates both UUIDs and forwards the explicit `deployment_id` to the API proxy.

This route is now the public browser-facing namespace for a selected deployment.

### 2. Explicit deployment ID remains authoritative

`WebsitePreviewService.proxy_deployment_request()` now follows this rule:

- If the request contains `deployment_id`, resolve exactly that deployment.
- Verify that the deployment belongs to the requested project.
- Accept only `deployed` or `stopped` deployments as restorable deployment states.
- Restore/reuse the runtime associated with that deployment.
- Do **not** substitute the latest deployment.

Only requests without `deployment_id` resolve the project's latest `deployed` record.

### 3. Deployment runtime remains independently identified

The selected deployment is still mapped through:

```text
website_deployments
        │
        ├── deployment_id
        ├── runtime_id
        └── url
        │
        ▼
Docker runtime
        │
        ▼
Docker snapshot awe-deployment-<deployment-id>
```

The host port remains disposable. The stable Studio URL does not depend on that port. Runtime metadata is reconciled back into the deployment record when a runtime is reused or restored.

### 4. Deployment-scoped generated URLs

Once a deployment has been selected, the proxy exposes:

```text
/api/live-preview/deployment/<project-id>/<deployment-id>
```

as the public prefix used when rewriting generated website HTML.

Relative/internal links, static assets and relevant Next.js serialized navigation data are rewritten into that namespace. This prevents a generated `/about` link from losing deployment identity.

### 5. Current/live and historical Studio links

Studio's `livePreviewUrl()` now accepts the deployment ID and includes it when building the stable live-preview URL.

Therefore both entry points are explicit:

- **Website is live · deployment vN → Open live website**
- **vN · deployed/stopped → Open live deployment / Open previous version**

They no longer rely on an ambiguous project-only URL when the UI is opening a specific deployment.

### 6. Runtime lifecycle intentionally preserved

FIX-31 does **not** change the CAP-036 snapshot or runtime lifecycle established by FIX-30:

- deployment snapshots remain immutable Docker named volumes;
- the latest deployment remains canonical;
- the immediately previous deployment remains restorable;
- older deployments remain snapshot-backed history;
- historical restore does not promote the historical deployment;
- historical restore does not stop the current live deployment runtime;
- duplicate runtime reconciliation and per-deployment restore serialization remain in force.

FIX-31 is therefore a **routing/identity boundary correction**, not a runtime lifecycle rewrite.

## Why the two links now converge correctly

The product exposes two visually different actions because they serve different UX purposes:

1. The completion/live summary says the website is live and offers the current deployment.
2. Deployment history exposes a particular version and allows the user to open that version.

Both are now converted into the same deployment-scoped URL contract:

```text
current live v8
→ /api/live-preview/deployment/<project>/<v8-id>/

historical v7
→ /api/live-preview/deployment/<project>/<v7-id>/
```

The UI wording can remain different, but the routing identity is no longer different or ambiguous.

## Deployment lifecycle policy clarified by this work

The runtime policy remains:

- **Latest deployment:** canonical and normally running.
- **Immediately previous deployment:** available as a restorable comparison/testing version.
- **Older deployments:** stopped/snapshot-only by default.
- **Any historical deployment:** can be restored on demand from its immutable snapshot without replacing the canonical live deployment.

This gives users practical access to the current and immediately previous versions without keeping an unbounded number of Docker runtimes alive.

## Regression tests

FIX-31 adds/retains focused API coverage for:

- stable deployment proxy resolving the latest deployed deployment when no ID is supplied;
- explicit historical deployment selection;
- deployment-scoped public prefix generation;
- historical snapshot restoration;
- runtime reuse for the selected deployment;
- concurrent opens converging on one runtime;
- duplicate ready-runtime reconciliation;
- preservation of the current deployment while historical deployment state is handled.

The focused API test suite passed during FIX-31 acceptance:

```text
24 passed in 0.16s
```

The source-level regression also asserts that deployment-scoped public prefixes are present in the deployment proxy implementation.

## Local acceptance evidence

After deploying FIX-31, the following direct requests were verified:

```text
V7
HTTP 200
<title>Home
<h1>Coyote - Sylvester

V8
HTTP 200
<title>Home
<h1>Coyote - Tweety
```

The rendered V7 links were deployment-scoped, for example:

```text
/api/live-preview/deployment/<project-id>/<v7-deployment-id>/about
```

The rendered V8 links independently used:

```text
/api/live-preview/deployment/<project-id>/<v8-deployment-id>/about
```

The browser regression then passed completely: V7 remained Sylvester through navigation, while V8 remained Tweety.

## Acceptance criteria

FIX-31 is considered accepted when all of the following hold:

- [x] Direct V7 request renders V7 content.
- [x] Direct V8 request renders V8 content.
- [x] V7 generated navigation links retain V7 deployment identity.
- [x] V8 generated navigation links retain V8 deployment identity.
- [x] V7 Home → About → Home remains V7.
- [x] V7 navigation through the other generated pages remains V7.
- [x] V8 navigation remains V8.
- [x] Opening/restoring V7 does not promote V7 over V8.
- [x] The latest deployment remains canonical.
- [x] The previous deployment remains available for comparison/testing.
- [x] Immutable deployment snapshots remain the historical source of truth.
- [x] Focused regression tests pass.

## Operational troubleshooting

If a future regression appears as “historical deployment opens correctly, then changes to latest deployment after clicking a link,” inspect these layers in order:

1. **Entry URL** — verify the selected `deployment_id` is present.
2. **Rendered links** — verify links contain `/api/live-preview/deployment/<project>/<deployment-id>/...`.
3. **Next.js serialized navigation** — verify client navigation does not reintroduce project-only paths.
4. **API proxy resolution** — verify explicit `deployment_id` is used instead of latest-deployment fallback.
5. **Deployment record** — verify `deployment_id`, `project_id`, `runtime_id`, status and snapshot identity agree.
6. **Docker labels** — verify the runtime carries `com.awe.deployment_id=<deployment-id>`.
7. **Snapshot** — verify `awe-deployment-<deployment-id>` exists if runtime restoration is required.

A dynamic runtime port mismatch is not, by itself, evidence of a routing defect. The browser must use the stable deployment-scoped proxy URL; the runtime host port is disposable implementation metadata.

## Related records

- `docs/cap-036-live-deployment-snapshot.md` — CAP-036 snapshot/runtime lifecycle and prior fixes.
- `docs/defect-register.md` — permanent defect history and troubleshooting governance.
- `docs/adr/ADR-0019-deployment-pinned-live-preview.md` — architectural decision establishing deployment identity as a navigation boundary.
- `apps/api/app/services/preview.py` — deployment proxy/runtime reconciliation implementation.
- `apps/studio/app/api/live-preview/deployment/[projectId]/[deploymentId]/[[...path]]/route.ts` — deployment-scoped Studio proxy route.
- `apps/studio/app/page.tsx` — deployment link generation and live completion/history actions.
- `apps/api/tests/test_preview.py` — focused deployment proxy/runtime regression coverage.
