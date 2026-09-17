# CAP-035 — Studio Content Management + Live Preview Consumption

## Objective
Allow customers to edit persistent website copy in Studio without regenerating the website pipeline, then publish the saved content into an already-running disposable Live Preview.

## Delivered
- Studio content editor for generated website pages.
- Persistent draft/published content continues to use the CAP-034 API and version history.
- Generated pages read `/workspace/awe-content.json` at request time and are forced dynamic, so published content is consumed without regenerating the application.
- Preview startup seeds the runtime workspace with currently published content.
- Publishing content synchronizes the running preview workspace immediately.
- Content synchronization is scoped to the project's labeled preview runtime.
- Existing project/tenant authorization remains enforced by the CAP-034 content boundary.

## Deliberate boundary
Draft content is persisted but is not injected into the visitor-facing runtime until publish. Production deployment content synchronization and a full CMS/DAM are outside this increment.
