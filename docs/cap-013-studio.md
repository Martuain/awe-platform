# CAP-013 — Project Lifecycle & Workspace UX

## Status
Implementation candidate for repository validation.

## Goal
Turn CAP-012 persistence into a usable project/workspace experience. AWE Studio should make it obvious which project is open, where that project is in the capability pipeline, what has been completed, what comes next, and whether the project is active or archived.

## Product outcome
CAP-013 adds a lightweight workspace dashboard without introducing authentication, tenancy, collaboration, billing, or a separate project-management subsystem.

### API

```text
GET   /api/v1/projects
GET   /api/v1/projects/{project_id}
PATCH /api/v1/projects/{project_id}
GET   /api/v1/projects/{project_id}/workspace
```

`PATCH` currently supports the lifecycle status values:

```text
active
archived
```

The workspace response now exposes:

- current stage;
- next capability;
- completed capabilities;
- latest capability versions;
- deployment count/status;
- last activity timestamp.

## Lifecycle model

```text
                 ┌───────────┐
                 │   Active  │
                 └─────┬─────┘
                       │ archive
                       ▼
                 ┌───────────┐
                 │ Archived  │
                 └─────┬─────┘
                       │ restore
                       └──────────────► Active
```

Archiving is deliberately reversible. CAP-013 does not delete project data.

## Workspace progression

```text
Discovery
   ↓ approved
Strategy
   ↓ approved
Design
   ↓ approved
Specification
   ↓ approved
Generation
   ↓
Preview
   ↓ deployed
Deployment
```

The API derives progress from persisted capability artifacts rather than storing a second, independently mutable workflow state. This prevents the workspace status from drifting away from the actual capability artifacts.

## Studio UX

The Studio now presents a compact workspace summary containing:

- active project name;
- project lifecycle status;
- current stage;
- next capability;
- completed capability count;
- deployment count;
- last activity.

The existing project selector remains the project switching mechanism. The browser local-storage value identifies the last selected project, while the API remains the source of truth for the project's persisted state.

## Technology decisions

### Keep project lifecycle in the existing Projects API

**Chosen:** extend `/projects` rather than create a separate workspace service.

**Why:** a project is already the persistence root established by CAP-012. A separate service would add networking, deployment and data-consistency complexity without proving additional product value.

### Derive progress instead of storing workflow state

**Chosen:** derive `current_stage`, `next_capability` and `completed_capabilities` from capability artifacts.

**Why:** the artifacts already contain authoritative versions and approval states. Duplicating these states creates synchronization risk.

### Keep PostgreSQL + SQLAlchemy

**Chosen:** preserve the CAP-012 persistence stack.

**Why:** CAP-013 is a product/workflow capability, not a reason to change persistence technology. PostgreSQL provides the shared durable store; SQLAlchemy keeps the Repository boundary intact.

### Keep localStorage for last-opened project

**Chosen:** browser-local selection state only.

**Why:** it improves resume UX without pretending that localStorage is durable application state. The API remains authoritative.

### Archive instead of delete

**Chosen:** reversible `archived` status.

**Why:** deleting a project would conflict with the persistence, provenance and future audit direction of AWE. Hard deletion can be introduced later with explicit retention requirements.

## Security boundary

CAP-013 does not imply authorization. Any authenticated/tenant-aware project access model remains a future capability. Until then, the lifecycle API is suitable for the current single-user/local development environment only.

## Deferred

- authentication and authorization;
- multi-tenancy and project ownership;
- collaborators/roles;
- project deletion and retention policies;
- search/filtering across large project collections;
- project activity/event timeline;
- notifications;
- project-level settings and integrations.

## Validation gate

The repository owner should validate with:

```bash
pnpm lint && pnpm build && pnpm test
```

The API test suite adds lifecycle and workspace assertions while preserving all previous CAP tests.
