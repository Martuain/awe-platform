# CAP-038.1 — Endpoint & Interaction Contract

## Status
Reconciled after repository-wide Studio/API endpoint audit.

## Purpose
CAP-038.1 separates three concerns that had been conflated during FIX-31:

1. **Studio/browser-facing URLs** used by users and browser navigation.
2. **Studio proxy routes** that protect the private API network and attach the internal proxy secret.
3. **Canonical API contracts** under `/api/v1` that own deployment lifecycle, authorization and runtime reconciliation.

Docker host ports and container IDs are never part of the public product contract.

## Canonical interaction model

CAP-038.1 has two intentionally different request paths.

### Control plane — Studio data/actions

```text
Studio React client
    -> NEXT_PUBLIC_API_URL (normally http://localhost:8000)
    -> canonical FastAPI /api/v1/deployments... and other /api/v1 contracts
    -> normal authentication/scope/resource authorization
```

Deployment CRUD, history, stop/restore and other Studio data operations do **not** traverse the Next.js live-content proxy today. They are direct browser-to-FastAPI calls protected by the API authentication/authorization middleware and CORS policy.

### Live-content plane — generated website traffic

```text
Browser / generated website navigation
        |
        | /api/live/... or Preview compatibility namespace
        v
Studio Next.js proxy
        |
        | X-AWE-Preview-Proxy + project/deployment identity
        v
Canonical FastAPI website-preview proxy contract
        |
        | deployment lookup + runtime reconciliation
        v
Generated website runtime :3000
```

The internal proxy secret is used only for the private live-content proxy boundary. It is not a replacement for the normal deployment API authorization model.

## Browser-facing Studio routes

| Purpose | Canonical route | Notes |
|---|---|---|
| Current live website | `/api/live/{project_id}/...` | Resolves the durable `CURRENT` deployment. No runtime port is exposed. |
| Explicit deployment | `/api/live/{project_id}/deployment/{deployment_id}/...` | Pins navigation to exactly one deployment. Used for previous/historical inspection. |
| Editable Preview | `/api/live-preview/preview/{project_id}/...` | Separate disposable Preview runtime; not a deployment URL. |
| FIX-31 compatibility | `/api/live-preview/deployment/{project_id}/...` and deployment-scoped variant | Retained as compatibility aliases. New Studio deployment links must not be generated through these routes. |
| Port-based legacy preview | `/api/live-preview/{port}/...` | Compatibility/internal fallback only. Runtime ports are not a stable product URL. |

## Canonical API contracts

### Deployment lifecycle

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/deployments?project_id={project_id}` | Create a new versioned deployment. |
| `GET` | `/api/v1/deployments?project_id={project_id}` | List deployment history. |
| `GET` | `/api/v1/deployments/{deployment_id}` | Read one deployment. |
| `POST` | `/api/v1/deployments/{deployment_id}/stop` | Explicitly stop a deployment runtime. |
| `POST` | `/api/v1/deployments/{deployment_id}/restore?project_id={project_id}` | Restore the immutable deployment snapshot without promotion. |

### Runtime/content proxying

| Method | Endpoint | Purpose |
|---|---|---|
| `GET/HEAD/POST/PUT/PATCH/DELETE/OPTIONS` | `/api/v1/website-preview/live-proxy/{project_id}/{path}` | Canonical CAP-038 live proxy. No `deployment_id` means `CURRENT`; explicit `deployment_id` pins a deployment. |
| same | `/api/v1/website-preview/deployment-proxy/{project_id}/{path}` | FIX-31 compatibility proxy used by the legacy Studio live-preview namespace. |
| same | `/api/v1/website-preview/preview-proxy/{project_id}/{path}` | Disposable editable Preview runtime. |
| same | `/api/v1/website-preview/proxy/{port}/{path}` | Legacy port-addressed Preview compatibility path. |

The proxy endpoints are private API-network contracts. Studio attaches `X-AWE-Preview-Proxy`; callers should not expose or depend on that secret.

## Studio/API interaction sequences

### Load deployment history / deploy / stop / restore

```text
Studio React client
  -> GET/POST NEXT_PUBLIC_API_URL + /api/v1/deployments...
  -> FastAPI AuthenticationMiddleware
  -> scope + project/deployment ownership authorization
  -> DeploymentService / repository
```

These are control-plane calls. They do not pass through `/api/live/...` or the Next.js live-content proxy.


### Open live website

```text
User clicks Open live website
  -> Studio emits /api/live/{project_id}/
  -> Studio route calls /api/v1/website-preview/live-proxy/{project_id}/
  -> API resolves lifecycle_role=CURRENT and status=DEPLOYED
  -> runtime is reused or restored from the CURRENT deployment snapshot
  -> runtime-relative links remain under /api/live/{project_id}/...
```

### Open previous/historical deployment

```text
User selects deployment_id D
  -> Studio emits /api/live/{project_id}/deployment/{D}/
  -> Studio route calls /api/v1/website-preview/live-proxy/{project_id}/...?deployment_id=D
  -> API validates D belongs to project_id
  -> D is reused/restored from its immutable snapshot
  -> runtime-relative links are rewritten to /api/live/{project_id}/deployment/{D}/...
  -> D is not promoted to CURRENT
```

### Editable Preview

```text
Studio Preview stage
  -> /api/live-preview/preview/{project_id}/...
  -> /api/v1/website-preview/preview-proxy/{project_id}/...
  -> disposable current-generation preview runtime
```

Preview and Deployment are intentionally separate runtime identities.

## Identity and authorization rules

- `deployment_id` is the durable deployment identity.
- `project_id` scopes access; an explicit deployment must belong to that project.
- Invalid deployment IDs return `404`; they never fall back to `CURRENT`.
- A deployment ID belonging to another project returns `404`; no cross-project fallback occurs.
- Omitting `deployment_id` is the only supported way to request the canonical `CURRENT` deployment.
- Runtime ID, runtime host port and restore-volume name are implementation details.

## Compatibility policy

The FIX-31 `/api/live-preview/deployment/...` routes remain available so previously generated links/bookmarks continue to function during CAP-038 migration. They are **compatibility aliases**, not the preferred product URL.

New Studio live/current and previous/historical links use `/api/live/...` exclusively. The compatibility routes can be removed only in a later explicit deprecation capability after telemetry/backward-compatibility requirements are defined.

## Error contract

- malformed project/deployment path parameter -> `400`
- missing/non-restorable deployment -> `404`
- cross-project deployment mismatch -> `404`
- runtime/proxy infrastructure failure -> `502`
- canonical API authorization failure -> `401`/`403` according to authentication/tenant membership state

There is no silent fallback from an explicitly requested deployment to `CURRENT`.

## CAP-038.1 regression contract

1. `/api/live/{project}/` serves the durable `CURRENT` deployment.
2. `/api/live/{project}/deployment/{V7}/` remains V7 across navigation, refresh and deep links.
3. V7 and V8 may use different disposable runtime IDs and host ports without changing either stable URL.
4. Invalid deployment ID -> `404`.
5. Valid deployment ID paired with another project -> `404`.
6. Studio data/control calls use canonical `/api/v1` endpoints.
7. Studio generated deployment links use `/api/live/...`, not `/api/live-preview/deployment/...`.
8. Legacy FIX-31 routes remain functional compatibility aliases.
