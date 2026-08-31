# CAP-012 — Project Persistence & Workspace Model

## Outcome
Projects are now explicit persistent workspace roots. Studio/API can list projects and retrieve a resumable workspace summary showing the latest capability versions and deployment state.

## API
- `GET /api/v1/projects` — list projects newest first.
- `GET /api/v1/projects/{project_id}` — retrieve a project.
- `GET /api/v1/projects/{project_id}/workspace` — retrieve workspace state and current stage.

## Persistence
The existing Repository abstraction is preserved. In-memory storage remains useful for isolated tests; the SQLAlchemy repository persists projects and capability artifacts to PostgreSQL in the containerized environment.

## Versioning
Discovery, strategy, design, specification, and generation retain explicit version numbers. Deployment history remains independently versioned.

## Security boundary
CAP-012 does not introduce authentication or tenant isolation. Those are deliberately deferred rather than implied by the workspace model.

## Validation
The CAP must pass the standard `pnpm lint && pnpm build && pnpm test` gate.
