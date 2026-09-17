# ADR-0019 — Pin live-preview navigation to a deployment identity

- **Status:** Accepted
- **Date:** 2026-09-14
- **Scope:** CAP-036 live deployment / historical deployment preview
- **Related:** CAP-036 FIX-30, FIX-31

## Context

AWE supports a canonical latest deployment and historical deployment snapshots. The Studio must allow users to open the current deployment and, for comparison/testing, the immediately previous deployment.

The original stable deployment preview endpoint was project-scoped:

```text
/api/live-preview/deployment/<project-id>/
```

A `deployment_id` query parameter could select a historical deployment at entry time. However, generated customer-site links were not inherently deployment-scoped. If the browser followed a project-only path after the first render, the API had no deployment identity and correctly fell back to the project's latest deployed version.

This produced a severe semantic mismatch: the browser address/action represented historical V7 while the rendered document after navigation could be V8.

The failure demonstrated that a query parameter used only on the initial request is not a sufficient identity boundary for an interactive deployed website.

## Decision

A selected deployment receives its own stable browser navigation namespace:

```text
/api/live-preview/deployment/<project-id>/<deployment-id>/...
```

The deployment ID is authoritative whenever it is explicitly present.

The routing rules are:

1. Project-scoped deployment URL without `deployment_id` resolves the canonical latest `deployed` deployment.
2. Explicit `deployment_id` resolves exactly that deployment after project ownership validation.
3. A deployment-scoped response rewrites internal generated links/assets and relevant Next.js navigation payloads into the same deployment namespace.
4. The selected deployment remains the identity for the complete browser navigation lifecycle.
5. Historical deployment restoration is allowed without promoting the historical deployment.
6. Runtime host ports remain disposable implementation details and are not exposed as the browser identity contract.

## Consequences

### Positive

- Historical deployment navigation cannot silently become the latest deployment.
- Current and historical Studio actions converge on the same identity-safe URL model.
- Runtime replacement/restoration does not invalidate browser links.
- The deployment snapshot/runtime relationship remains explicit and inspectable.
- The latest deployment remains canonical while historical versions remain testable.

### Trade-offs

- Generated HTML must be rewritten at the proxy boundary so internal links and assets carry deployment identity.
- The Studio needs a dedicated deployment-scoped route in addition to the canonical project route.
- Debugging must distinguish routing identity from disposable runtime host ports.
- Existing clients/bookmarks using only the project-level stable URL intentionally continue to mean “latest deployed version,” not a historical version.

## Rejected alternatives

### Keep only `?deployment_id=...` on the entry URL

Rejected because client-side navigation can drop query parameters. The identity is not guaranteed to survive the application's own generated links and Next.js navigation.

### Keep every deployment runtime running

Rejected because it creates unnecessary Docker resource consumption and does not solve identity correctness. Immutable snapshots already provide restoration on demand.

### Make the historical deployment the project's latest deployment while viewing it

Rejected because opening a historical version is a read/test/restore operation, not a promotion. Promotion semantics must remain explicit.

### Route historical pages directly to their dynamic Docker host port

Rejected because host ports are disposable and change across runtime restoration. The stable API proxy is the durable browser boundary.

## Invariants

```text
explicit deployment ID → exact deployment
no deployment ID      → canonical latest deployed deployment
selected deployment   → stable deployment-scoped navigation
runtime port          → disposable implementation detail
snapshot              → immutable historical source
historical restore    → never implicit promotion
```

## Verification

FIX-31 was deployed locally and verified with V7 and V8. Direct server responses rendered different version-specific content, generated links were deployment-scoped, and browser navigation remained pinned to the selected deployment. The focused API regression suite passed with 24 tests passing.
