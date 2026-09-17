# CAP-034 — Website Content & Data Management Foundation

## Implemented
- Persistent website content items.
- Draft/published status.
- Per-item versioning and history.
- Project-scoped content CRUD/upsert and publish APIs.
- SQLAlchemy persistence and in-memory repository support.
- Alembic migration `0008_website_content`.
- Existing authentication, scopes, and tenant/project authorization apply.

## Verification
- API Python modules compile successfully.
- Local Docker/API regression remains required before deployment.

## Next increment
Connect the published content model to the generated website runtime and provide Studio editing/publish UX.
