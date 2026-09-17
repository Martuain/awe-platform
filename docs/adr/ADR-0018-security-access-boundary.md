# ADR-0018 — Security & Access Boundary

## Status
Accepted — CAP-025

## Decision
AWE separates human authentication from programmatic API authentication while applying the same server-side project ownership boundary to both.

- Human users authenticate with short-lived bearer sessions created after password verification.
- API clients authenticate with opaque `awe_` API keys.
- API keys are stored only as SHA-256 hashes and are returned in plaintext only at creation time.
- API keys carry explicit scopes and can be revoked.
- Projects have an owner identity; project-scoped resources authorize against that owner on the server.
- Development mode uses one deterministic synthetic identity and must not be mistaken for production authentication.
- Strict mode requires persistent authentication storage and credentials.

## Rationale
This avoids coupling the product to an identity vendor while providing a clear boundary for future SSO/OIDC, teams, CI/CD and external integrations.

## Consequences
- Existing local Studio flows continue to work in explicit development mode.
- Production deployments must set `AWE_AUTH_MODE=strict` and configure persistent database-backed authentication.
- Existing projects are assigned to the deterministic development owner during migration; production installations should establish real ownership before exposing the product to multiple users.
- Authentication alone is insufficient: negative authorization tests are required for project isolation.
