# CAP-013 Change Log

## v1.3.0 — Project Lifecycle & Workspace UX

- Added project lifecycle status: `active` and reversible `archived`.
- Added `PATCH /api/v1/projects/{project_id}`.
- Extended workspace summary with completed capabilities, next capability and last activity.
- Derived workflow progress from persisted capability artifacts.
- Added Studio workspace summary for current project status and progress.
- Preserved browser localStorage only as the last-opened-project convenience layer.
- Added lifecycle/workspace API test coverage.
- Added ADR-0011 and CAP-013 documentation.
- Kept PostgreSQL, SQLAlchemy and the Repository abstraction unchanged.
- Deferred authentication, multi-tenancy, deletion/retention and collaboration.
