# CAP-034 — Website Content & Data Management Foundation

## Goal
Provide persistent, tenant/project-scoped website content with draft/published state and revision history.

## Contract
- Content is identified by project + page + key.
- Upserts create a new version and return the current draft.
- Publishing promotes all current project content to published state.
- Version history is retained.
- All endpoints are protected by the existing project authorization and scopes.
- This capability does not regenerate the website.

## API
- `GET /api/v1/website-content/{project_id}`
- `PUT /api/v1/website-content/{project_id}`
- `POST /api/v1/website-content/{project_id}/publish`
- `GET /api/v1/website-content/{project_id}/{content_id}/versions`

## Deferred
Generated-site live consumption and Studio editing UX build on this foundation in the next capability increment.
