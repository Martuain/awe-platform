## Unreleased

### Added
- CAP-004 Website Specification capability and Studio review/approval flow.
- Structured page-level implementation requirements, global components, SEO, accessibility, responsive, technical and acceptance criteria.
- Strategy/design source-version traceability for Website Specification artifacts.

- CAP-003 Studio integration for Brand & Design Direction review and approval.
- Studio persistence/reload of CAP-003 state.
- Visual direction presentation covering palette, typography, imagery, components, accessibility and rationale.

# Changelog

## CAP-003 v0.1.1 — Deployment Hardening

- Upgrade Next.js from 15.4.6 to 15.5.21.
- Upgrade React and React DOM from 19.1.1 to 19.1.9.
- Upgrade eslint-config-next to 15.5.21.
- Fix the ESM import for `eslint-config-next/core-web-vitals.js`.
- Explicitly allow `sharp` and `unrs-resolver` build scripts via pnpm `onlyBuiltDependencies`.
- Add deployment-hardening documentation and release-gate rules.
- Preserve `docs/project-master.md` as the living project record.
- Lockfile regeneration is intentionally deferred to the repository owner because this environment cannot access the pnpm registry.


## CAP-003 v0.1.2 — local validation hardening

- Moved pnpm `onlyBuiltDependencies` from deprecated `package.json#pnpm` to `pnpm-workspace.yaml`.\n- Reworked Next.js ESLint configuration to use `@next/eslint-plugin-next` directly, avoiding the `nextVitals is not iterable` incompatibility observed with `eslint-config-next@15.5.21`.\n- Added `@next/eslint-plugin-next@15.5.21` as an explicit Studio dev dependency.\n- Made the Python API test command explicit as `python3 -m pytest`.\n- Updated GitHub CI to provision Python 3.12, install API requirements, and run the test suite.

These changes address the local `pnpm lint` and `pnpm test` failures reported after the CAP-003 deployment-hardening patch.\n
## CAP-005 — Website Generation

- Added approved-specification-gated website generation.
- Added `WebsiteGeneration` artifact and persistence contract.
- Added deterministic Next.js App Router file generator.
- Added generation API and tests.


## CAP-006 — Preview & Validation

- Added deterministic Website Validation artifact and API endpoint.
- Added structural checks for generated Next.js project files and page coverage.
- Added safe HTML preview rendered in Studio without executing generated application code.
- Added CAP-006 Studio Preview stage and API test coverage.
- Deferred isolated generated-project execution to a future sandbox/build-runner capability.


## CAP-012 — Project Persistence & Workspace Model

- Added persistent project listing and workspace summary API.
- Formalized projects as the persistent workspace root.
- Preserved Repository abstraction and SQLAlchemy/PostgreSQL boundary.
- Added ADR-0010 and CAP-012 documentation.
- Deferred authentication, tenancy, object storage and migration tooling.


## CAP-013 — Project Lifecycle & Workspace UX

- Added active/archived project lifecycle state.
- Added project lifecycle update API.
- Extended workspace summaries with progress, next capability and last activity.
- Added Studio workspace status/progress presentation.
- Added CAP-013 documentation and ADR-0011.


## CAP-014 — Project Duplication & Fresh Workspace Templates
- Added project duplication endpoint and repository support.
- Duplication creates a clean workspace with a new identity.
- Added API regression coverage and ADR-0012.
