# Changelog

## 1.0.2 — Executable MVP end-to-end verification

- Added a fresh-project end-to-end smoke test covering Discovery through a running deployed website.
- Added `pnpm e2e:mvp` as the canonical local executable-flow verification command.
- Verified that the strict Discovery API contract remains intact while Studio owns session initialization.
- Added the local Docker CLI/socket boundary required for the API build and disposable preview adapters to execute from Docker Compose.
- Added documentation for the end-to-end verification contract and the explicit local-only Docker socket trade-off.
- Kept hosted/scalable execution, production cloud deployment and stronger multi-tenant isolation outside the MVP scope.


## 1.0.1 — Discovery lifecycle hardening

- Rebased the release candidate on the complete Genesis implementation rather than a reduced reconstruction.
- Preserved PostgreSQL/SQLAlchemy persistence, Redis configuration, the full capability API surface, Studio workflow, Docker Compose stack and existing test suite.
- Added idempotent Studio `ensureDiscovery(projectId)` initialization for project creation, saved-project restoration and project switching.
- Kept `/business-discovery/message` strict so missing sessions are not silently created by a mutation endpoint.
- Hardened Discovery composer rendering so it is unavailable until a persisted Discovery context exists.
- Preserved CAP-014 duplication semantics: a duplicate gets a new project identity and clean capability state; Discovery is initialized independently rather than copied.
- Added regression coverage for duplicate → missing Discovery context → initialization → successful Discovery message.
- Added ADR-0015 documenting the lifecycle invariant.
- Removed generated dependency/cache/macOS metadata from the release source tree.
- Tidied release metadata and aligned root/Studio versions to 1.0.1 / 1.8.1.

## Unreleased

### Build execution hardening

- Split isolated website-build timeouts into dependency-install and production-build budgets; dependency installation defaults to 300 seconds and the offline production build to 180 seconds, with API-level bounds up to 600 seconds.
- Exposed the build phase timeout controls through the execution API and updated the canonical E2E runner to use the explicit budgets.
- Hardened preview execution to use the same phase budgets and report timeout failures as preview diagnostics.

### Website generation quality

- Added hospitality-aware strategy and Website Specification vocabulary, including menu/coffee/visit language for café and restaurant workflows.
- Removed implementation-oriented specification labels from visitor-facing generated copy.
- Improved generated metadata, page copy, CTAs and business-context propagation while avoiding unsupported prices, addresses, testimonials and other invented facts.
- Added regression coverage for hospitality strategy vocabulary, generated visitor copy and phase-specific build timeouts.


## CAP-001 — Business Discovery v1.1 Hardening

- Reworked deterministic Discovery extraction to recognize natural-language business goals instead of relying only on fixed keywords.
- Preserve Business Knowledge across conversation turns rather than replacing previously captured goals.
- Added extraction for target audience and value proposition when explicitly provided.
- Made Discovery open questions dynamic; the API no longer repeats a hard-coded primary-goal question after every message.
- Keep industry + at least one goal as the MVP approval gate; optional audience/value proposition evidence is retained without unnecessarily blocking approval.
- Added regression coverage for natural-language goals, multi-turn accumulation, optional knowledge capture and post-approval immutability.
- Added Python 3.9-safe future annotations to API modules using PEP 604 union syntax; Docker remains on Python 3.12.
- API test suite: 18 passed.


### Added
- CAP-004 Website Specification capability and Studio review/approval flow.
- Structured page-level implementation requirements, global components, SEO, accessibility, responsive, technical and acceptance criteria.
- Strategy/design source-version traceability for Website Specification artifacts.

- CAP-003 Studio integration for Brand & Design Direction review and approval.
- Studio persistence/reload of CAP-003 state.
- Visual direction presentation covering palette, typography, imagery, components, accessibility and rationale.

# Changelog

## CAP-002 — Strategy revision hardening

- Fixed natural-language Website Strategy revisions so supported positioning and primary CTA requests change the generated strategy rather than only recording feedback.
- Preserved explicit `CTA: ...` revision syntax for backwards compatibility.
- Kept strategy revisions versioned and re-evaluated against the approved Business Discovery context.
- Synchronized homepage/contact CTAs when the primary conversion action is revised.
- Added regression coverage for natural-language and explicit CTA revision flows.

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


## CAP-015 — Executable Website Build & MVP Runtime Gate

- Added first-class Studio Build stage and explicit execution gate.
- Reused existing Docker isolation boundary; no new infrastructure introduced.

## CAP-018 + MVP v1.0 — Executable MVP Release Gate

- Added a canonical `pnpm mvp:gate` release verification command.
- Added `pnpm mvp:up` and `pnpm mvp:down` local runtime commands.
- Defined the first executable MVP release criteria.
- Documented MVP technology decisions and explicit post-MVP deferrals.
- Added ADR-0014 for the MVP release-gate decision.
- Root package version advanced to 1.0.0; Studio advanced to 1.8.0.
