# CAP-014 — Project Duplication & Fresh Workspace Templates

## Objective
Allow users to duplicate an existing project as a new, clean workspace without copying mutable capability artifacts.

## Product decision
Duplication creates a new project with a new identity and empty capability state. The source remains unchanged. This gives users a safe starting point for variants while avoiding hidden coupling between artifact histories.

## API
- `POST /api/v1/projects/{project_id}/duplicate`
- Optional body: `{ "name": "..." }`
- Returns a new `Project` with a new UUID.

## Technology decision
No new database or framework was introduced. Duplication is implemented through the existing Repository abstraction and therefore works with both the in-memory and SQLAlchemy repositories.

## Explicit non-goal
CAP-014 does not clone discovery, strategy, design, specification, generation, preview, or deployment records. A future template/versioning capability can provide controlled artifact reuse without conflating project identity.
