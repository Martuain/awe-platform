# CAP-018 + MVP v1.0 — Release Gate

## Purpose

CAP-018 closes the first executable AWE Studio MVP loop without introducing new production infrastructure.

The release target is a **local, executable, reproducible MVP** rather than a production SaaS launch.

## Combined scope

### CAP-018 — MVP hardening

- One canonical repository release gate: `pnpm mvp:gate`.
- Gate validates lint, production build and tests in sequence.
- Gate reports the local Node, pnpm and Python versions used.
- Existing Docker Compose stack remains the executable integration boundary.
- `pnpm mvp:up` starts the local executable stack.
- `pnpm mvp:down` stops the local stack.

### MVP v1.0 release gate

The MVP is considered releasable when:

1. `pnpm install` succeeds from a clean checkout.
2. `pnpm mvp:gate` is green.
3. Studio production build completes.
4. API tests pass under Python 3.12+.
5. Docker Compose configuration is present for API, Studio, PostgreSQL and Redis.
6. The core Studio lifecycle exists: Discovery → Strategy → Design → Specification → Generation → Build → Validation → Preview → Deployment.
7. Human approval gates remain intact for the business decisions that require user trust.
8. Generated websites remain deterministic and use the approved strategy/design inputs.
9. Build execution remains isolated and network-disabled by default.
10. No unresolved build, lint or test defect blocks the MVP path.

## Explicitly deferred

The following are **not release blockers for MVP v1.0**:

- authentication and authorization;
- multi-tenancy;
- hosted/scalable build workers;
- production cloud deployment provider;
- billing;
- collaboration;
- additional website frameworks;
- model-provider-specific optimization;
- full observability platform;
- migration tooling beyond the current repository boundary.

These remain post-MVP work because adding them now would increase operational complexity without proving the core product hypothesis.

## Technology decisions

### pnpm

Retained because the repository is a JavaScript/TypeScript monorepo and pnpm provides workspace-aware dependency management with deterministic lockfile-based installs.

### Turborepo

Retained because AWE has multiple applications/packages and needs a single command surface for lint, build and test orchestration. Remote caching remains disabled until it provides measurable value.

### Next.js / React / TypeScript

Retained as the single supported Studio and generated-site framework for MVP. Supporting multiple frameworks before the core workflow is validated would multiply generation, validation, build and preview complexity.

### FastAPI / Python

Retained for the API because the project expects AI/runtime capabilities to evolve in Python while maintaining an API-first boundary.

### Docker Compose

Retained as the local executable integration boundary. It gives the MVP a reproducible API + Studio + PostgreSQL + Redis stack without prematurely committing to Kubernetes or a hosted orchestration platform.

### PostgreSQL / Redis

Retained because the architecture already establishes persistence and cache/runtime boundaries. They are not expanded into additional infrastructure for MVP.

## Release philosophy

MVP v1.0 means **the product loop is executable**, not that the platform is production-scale.

The next major investment after this gate should be user-visible product quality and real generated-site value, followed by production readiness only when validated by usage.
