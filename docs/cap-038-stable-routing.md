# CAP-038.1 — Stable Routing Contract

## Status
Implemented in the CAP-037 verified baseline package.

## Purpose
CAP-038.1 establishes the stable logical URL contract for live deployments without introducing DNS, TLS, external hosting, or provider-specific public infrastructure.

## Contract
- Canonical current website entry point: `/api/live/{project_id}/...`
- Explicit deployment entry point: `/api/live/{project_id}/deployment/{deployment_id}/...`
- Docker host ports and container IDs are runtime implementation details and are never the product URL.
- A current live request resolves the durable `CURRENT` deployment from `website_deployments`. It does not select the newest deployment merely by creation time.
- Once a deployment is selected, generated runtime-relative links are rewritten into the deployment-aware stable namespace so browser navigation cannot silently fall back to another deployment.

## Architectural flow
```text
/api/live/{project}/...
        -> Studio route
        -> internal live-proxy API
        -> durable CURRENT deployment
        -> deployment runtime / snapshot reconciliation
        -> Docker :3000
```

The explicit deployment namespace follows the same flow while pinning `deployment_id`.

## Why this follows CAP-037
CAP-037 established durable deployment identity, lifecycle roles, immutable snapshots, and disposable runtime identity. CAP-038.1 makes those semantics visible at the routing boundary instead of exposing runtime addresses. Opening an explicit historical deployment therefore remains deployment-scoped and does not mutate currentness.

## Non-goals
- DNS or custom domains
- TLS termination
- CDN
- cloud hosting
- public internet ingress

Those belong to a later capability layered on top of this stable routing contract.

## Regression requirements
The CAP-037 navigation-isolation tests remain mandatory. CAP-038.1 additionally requires: current stable entry, explicit deployment entry, deep-link path preservation, and proof that current resolution follows `lifecycle_role=CURRENT`.

## Endpoint reconciliation

The repository-wide CAP-038.1 audit separates browser-facing Studio routes from canonical FastAPI contracts. New Studio deployment links use `/api/live/...`; FIX-31 `/api/live-preview/deployment/...` remains a compatibility alias. Canonical lifecycle and proxy contracts remain under `/api/v1`.

See `docs/cap-038-endpoint-contract.md` for the complete Studio -> proxy -> canonical API interaction matrix, authorization/error behavior and compatibility policy.

## Control plane vs live-content plane

Studio deployment CRUD/history calls the canonical FastAPI `/api/v1/deployments...` API directly through `NEXT_PUBLIC_API_URL`. Generated website traffic uses the Studio `/api/live/...` routes, which proxy privately to `/api/v1/website-preview/live-proxy/...` with `X-AWE-Preview-Proxy`. This split is intentional and documented in `docs/cap-038-endpoint-contract.md`.
