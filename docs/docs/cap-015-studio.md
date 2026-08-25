# CAP-015 — Executable Website Build & MVP Runtime Gate

**Status:** Implemented.

CAP-015 closes the most important remaining gap before the first full executable AWE MVP: generated website artifacts can now be explicitly planned and executed through the existing isolated build boundary from Studio.

## Product outcome

The core path is now:

`Discovery → Strategy → Design → Specification → Generation → Build → Preview → Deployment`

The Build stage is an explicit product gate rather than an implicit backend capability. A user can see the build plan, isolation policy, diagnostics and execution result before continuing to Preview.

## API

Existing CAP-007 build endpoints are surfaced directly by Studio:

- `POST /api/v1/website-build/plan?project_id=...`
- `POST /api/v1/website-build/execute?project_id=...`

No new build technology was introduced. CAP-015 reuses the existing Docker-based disposable execution adapter.

## Safety boundary

- Generated source is written to an ephemeral workspace.
- Dependency installation is constrained and scripts are disabled.
- The build phase runs with network disabled.
- Generated application code is never executed inside Studio or the API process.
- Unsupported runtime dependencies are rejected by the existing build planner.

## Technology decision

CAP-015 deliberately does **not** add Kubernetes, a hosted build service, a queue, a persistent worker fleet or a second runtime. Those technologies would solve scale problems before the MVP has demonstrated product value. Docker already provides the required isolation boundary for the local executable MVP and preserves a clean adapter boundary for future hosted execution.

## Deferred

- Hosted/scalable build workers
- Build artifact registry
- Authentication/authorization
- Multi-tenancy
- Framework expansion
- Production cloud deployment provider
- Build cancellation and streaming logs

## Validation

The existing API build-plan tests remain the contract for dependency allowlisting and sandbox behavior. The local repository gate remains `pnpm lint && pnpm build && pnpm test`.
