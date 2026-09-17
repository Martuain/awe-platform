## Unreleased — CAP-036 stabilization: content publication and Mock revision authority

- Decoupled Website Content publication from disposable Preview runtime availability; publishing remains successful when no generation exists or Docker/Preview is unavailable.
- Kept Preview refresh as a best-effort downstream synchronization boundary while preserving its own persisted diagnostics/state.
- Fixed Customer Mock rendering so published Website Content remains authoritative, then current generated revision values are used before Website Specification fallbacks.
- Fixed Mock revisions to reflect deterministic headline/CTA changes made to the current Website Generation.
- Hardened API startup so orphaned Preview cleanup is skipped cleanly when Docker is not installed.
- Clarified Website Validation page-file matching and added regression coverage through the existing content, generation, Mock and Preview suites.

## CAP-038.1 — Stable Routing Contract

- Added stable `/api/live/{project_id}/...` routing for the canonical current deployment.
- Added deployment-pinned `/api/live/{project_id}/deployment/{deployment_id}/...` routing.
- Current live resolution now requires the durable `CURRENT` lifecycle role instead of assuming the newest deployed record is current.
- Kept runtime host ports/container IDs internal to the routing layer.
- Preserved CAP-037 deployment-aware navigation isolation and snapshot-backed runtime reconciliation.
- Reconciled Studio/frontend endpoint usage: new live/current and explicit deployment links now emit `/api/live/...` rather than the FIX-31 compatibility namespace.
- Documented the Studio -> Next.js proxy -> canonical `/api/v1` API chain, including deployment ownership checks, negative isolation behavior, error semantics and compatibility aliases.
- Kept `/api/live-preview/deployment/...` as an explicit backward-compatibility alias while removing it from new Studio link generation.

## Unreleased — FIX-31 deployment-pinned live deployment navigation

- Added a deployment-scoped Studio live-preview route: `/api/live-preview/deployment/{projectId}/{deploymentId}/...`.
- Made explicit `deployment_id` authoritative in the API deployment proxy; only requests without a deployment ID resolve the canonical latest deployed deployment.
- Live deployment links now pin the browser session to the explicit deployment ID, including the current/latest deployment entry and historical deployment-history entries.
- Deployment proxy HTML rewriting now scopes rendered internal links, asset URLs and relevant Next.js serialized navigation payloads to the selected deployment.
- Closed the historical-version identity leak where V7 could render correctly on first load and then silently become V8 after browser navigation.
- Preserved the existing deployment runtime/snapshot lifecycle from FIX-30: immutable deployment snapshots, disposable runtime ports, latest/previous deployment policy, historical restore without promotion, and duplicate-runtime convergence.
- Added regression coverage for explicit historical deployment resolution, deployment-scoped public prefixes, runtime reuse/restoration and concurrent deployment opens.
- Acceptance verified locally: V7 remained `Coyote - Sylvester` and V8 remained `Coyote - Tweety` through browser navigation; focused API suite passed with `24 passed in 0.16s`.
- Full architectural rationale and troubleshooting are recorded in `docs/cap-036-fix-31-deployment-pinned-live-preview.md`, `docs/adr/ADR-0019-deployment-pinned-live-preview.md`, `docs/defect-register.md`, and `docs/troubleshooting.md`.


### CAP-036 fix-28 — published-content authority and Mock Home navigation

- Fixed draft edits replacing the runtime-visible published content snapshot.
- Customer Website Mock and Preview Refresh now consume the latest published version, not the current draft row or generation-time canonical artifact.
- Preserved published version history while users continue editing drafts.
- Fixed the Customer Mock Home fragment returning to a blank screen after visiting another page.
- Added regression coverage for draft/published separation and Mock behavior.
## Unreleased — CAP-036 Preview Refresh recovery

- Preview Refresh now reconciles the disposable live-preview runtime through the API before remounting the iframe.
- Empty/stale iframe recovery no longer depends on a browser-only key increment.
- The previous iframe is hidden while runtime reconciliation is in progress, then remounted only after a started runtime is confirmed.
- Added permanent defect and troubleshooting documentation covering CAP-033/CAP-036 failures and successful recovery paths.


## CAP-033 durable execution state
- Persisted latest Build, Validation and Live Preview execution state per project.
- Workspace hydration now restores those states after Studio reloads without probing transient artifacts.
- Added Alembic migration `0002_execution_state` and repository coverage.


## CAP-036 fix-17 — deployment runtime labels at creation time

- Removed unsupported `docker update --label-add` deployment promotion.
- After snapshot persistence, AWE now starts the deployment runtime from the immutable snapshot and applies `com.awe.deployment_id` at `docker run` creation time.
- Deployment metadata now records the snapshot-backed deployment runtime rather than the disposable Preview runtime.
- Preview behavior from fix-16 is unchanged.
## CAP-035 — Studio content management + live preview

- Added Studio content editor and page-level editable copy fields.
- Added runtime content synchronization from published CAP-034 content without website regeneration.
- Generated pages now consume `/workspace/awe-content.json` dynamically.

## Unreleased — CAP-033 regression correction

- Corrected Discovery industry alias collisions by matching complete words/phrases and preferring the longest matching alias.
- Normalized generic website-goal phrasing so `help ...` is not retained as part of the stored goal.
- Updated regression expectations to the canonical `awe-preview.html` preview contract and the current isolated browser/preview runtime behavior.

## Unreleased — CAP-022 + CAP-023 Deployment Operations

### Added
- Generated-artifact performance budget checks and Studio reporting.
- Minimal API monitoring summary and Studio monitoring surface.
- Regression coverage for both operational endpoints.

### Deferred
- Browser-based Core Web Vitals, external telemetry, alerting, and hosted/scalable execution.

## Unreleased — Project Master documentation hardening

- Expanded `docs/project-master.md` into the authoritative cumulative change record for CAP-009, CAP-019 and CAP-020, including additions, changes, fixes, deliberate non-additions/removals, verification and deferred work.
- Added a standing documentation rule requiring each capability package to record its complete material delta before completion.

## Unreleased — CAP-019 deployment lifecycle

- Completed the Studio Deployment stage as the final CAP-019 pipeline boundary.
- Corrected Studio deployment API paths to `/api/v1/deployments`.
- Added validated-generation gating, per-project deployment versioning, and supersession of prior active deployments.
- Preserve deployment history while marking replaced deployments as stopped.
- Capture provider/runtime failures as failed deployment records instead of leaving them in `deploying`.
- Tightened Studio pipeline navigation so Preview and Deploy require passed validation.
- Updated the eight-stage pipeline layout.

## Unreleased — Preview runtime responsiveness

- Moved disposable preview Docker/npm execution off the FastAPI event loop.
- Reused a healthy preview runtime for the same project/generation to avoid duplicate containers.
- Kept preview cleanup and stop operations off the event loop as well.

# Changelog

## Unreleased — CAP-021 Migration Hardening

- Added Alembic as the authoritative PostgreSQL schema migration boundary.
- Added the initial MVP schema revision and migration configuration.
- Changed API startup to apply `alembic upgrade head` instead of calling SQLAlchemy `create_all()` directly.
- Added migration configuration/revision regression coverage.


## Unreleased — CAP-020 production model adapter

- Added an opt-in OpenAI-compatible model gateway with environment-based configuration while retaining the deterministic mock as the default.
- Added provider error handling and regression coverage.


## Unreleased — Studio generation loop

- Added an explicit Studio Build stage with build-plan visibility and diagnostics.
- Added an explicit validation gate between isolated build and preview.
- Added a distinct deployment stage and restored deployment history on project load.
- Strengthened root Docker context exclusions for local caches and Python artifacts.


## 1.0.3 — MVP generation and execution hardening

- Promoted the verified MVP state after successful fresh-project end-to-end validation.
- Split isolated website-build timeouts into dependency-install and production-build budgets.
- Added hospitality-aware strategy and Website Specification vocabulary.
- Removed implementation-oriented specification labels from visitor-facing generated copy.
- Improved generated metadata, page copy, CTAs and business-context propagation while avoiding unsupported facts.
- Added regression coverage for hospitality generation and phase-specific build timeouts.
- Verified the complete local flow from Business Discovery through isolated build, validation, deployment and live HTTP response.

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

## Unreleased — CAP-021 Migration Hardening

- Added Alembic as the authoritative PostgreSQL schema migration boundary.
- Added the initial MVP schema revision and migration configuration.
- Changed API startup to apply `alembic upgrade head` instead of calling SQLAlchemy `create_all()` directly.
- Added migration configuration/revision regression coverage.


## Unreleased — Studio generation loop

- Added an explicit Studio Build stage with build-plan visibility and diagnostics.
- Added an explicit validation gate between isolated build and preview.
- Added a distinct deployment stage and restored deployment history on project load.
- Strengthened root Docker context exclusions for local caches and Python artifacts.


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

## Unreleased — CAP-024 hosted/scalable execution boundary

- Added provider-neutral build execution and hosted HTTP adapter.
- Added environment-selected hosted deployment provider boundary.
- Retained deterministic local Docker/local deployment defaults.
- Documented production infrastructure deliberately not claimed.

## Unreleased — CAP-025 Security & Access Boundary

- Added explicit development/strict authentication modes.
- Added database-backed users and bearer sessions with salted scrypt password verification.
- Added hashed, scoped, revocable API keys with one-time secret disclosure.
- Added project ownership and server-side authorization, including cross-owner negative coverage.
- Added security middleware, API-key scope enforcement, auth endpoints and ADR-0018.
- Added migration `0002_auth_security` for ownership and authentication storage.
- Kept external SSO, collaboration, account recovery and billing outside this increment.

## [Unreleased] — CAP-026 / CAP-027 / CAP-028 Customer Mock Review Wave

- Added a first-class customer website mock between generation and executable build.
- Added persisted mock versions and customer feedback records.
- Added deterministic `headline:` / `cta:` refinement instructions with generation versioning.
- Added explicit mock approval as the gate into isolated build and preview.
- Added API and Studio lifecycle coverage for customer review and revision.


## Unreleased — CAP-030 team collaboration

- Added tenant-scoped team members with admin/member roles.
- Added hashed invitation tokens, seven-day expiry, and email-bound acceptance.
- Extended project authorization and listing to include authorized team members.
- Restricted team administration to authenticated user sessions.
- Added migration `0005_team_collaboration` and regression coverage.


## CAP-031 — Account Recovery & Email Verification
- Added email verification state and single-use verification tokens.
- Added password reset request/confirmation with short-lived single-use tokens.
- Tokens are hashed at rest; request endpoints use generic acceptance responses.
- Added local-only token exposure for deterministic integration testing.
\n- CAP-032 v2: mock OIDC authorization URL is fully offline; no discovery call in mock mode.\n
## Unreleased — CAP-036 End-to-End Customer Journey

- Added the customer-facing completion boundary after a successful local deployment.
- Added an explicit live-site completion summary with deployment version and live URL.
- Added a resume path from a deployed project back into Website Content editing without regenerating the website.
- Relaxed Studio Preview navigation for already-deployed projects so persisted content remains accessible after a browser refresh/reopen.
- Corrected durable workspace resume semantics: a latest successful deployment now completes the Preview/Deployment boundary and Studio reopens at Deployment instead of Build.
- Added regression coverage for the live-deployment workspace completion state.

## CAP-036 — Persistent live deployment snapshot fallback

- Persist every successful local deployment workspace as `awe-deployment-<deployment-id>`.
- Add a stable project-based live deployment endpoint that restores the latest successful snapshot when the disposable runtime is unavailable.
- Keep dynamic-port runtime behavior for active deployments.
- Preserve published CAP-035 content in deployment snapshots.
- Fail deployment promotion when snapshot persistence fails.
- Add regression coverage and deployment lifecycle documentation.

## CAP-036 follow-up — deployment history and content-preview fixes

- Fixed Studio production-build regression caused by `deploymentHistory` being scoped inside the project hydration `try` block.
- Historical deployment links now carry the selected deployment ID through the stable live-preview endpoint instead of resolving every link to the current runtime.
- Stable deployment preview can restore the exact requested historical deployment snapshot, including stopped deployments.
- Publish Content now persists unsaved editor changes before publishing, then refreshes the live preview iframe so published values are reread from the runtime workspace.

## CAP-036 follow-up — Preview stale-first-render guard

- Unmount the previous interactive Preview document before `Validate Website` or `Publish Content → Live Preview` reconciles the Preview runtime.
- Mount the live Preview iframe only after the API confirms the refreshed Preview runtime is started.
- Keep the old interactive document from being presented as current while Preview reconciliation is pending or fails.


## CAP-036 fix-16
- Prevent the static validation artifact iframe from rendering during Preview validation/publish transitions.
- Show a neutral loading state until the interactive Preview runtime is ready, eliminating stale first-render content.

### CAP-033 startup migration merge fix
- Added a schema-neutral Alembic merge revision joining `0008_website_content` and `0002_execution_state`.
- Restores a single migration head so API startup can continue using `alembic upgrade head` without changing existing project data.

## Unreleased — Workflow state governance

- Added `docs/workflow-state-machine.md` as the canonical product/architecture contract for forward and backward Studio stage transitions, prerequisites, version identity, downstream staleness and regression gates.
- Updated the Project Master, defect register and troubleshooting guide to make workflow state integrity a permanent cross-CAP requirement.

## Unreleased — CAP-036 fix-22 Customer Mock iframe isolation

- Fixed Customer Website Mock iframe navigation escaping into AWE Studio.
- Centralized static mock sanitization and made mock links/forms inert.
- Removed `<base>` and executable `<script>` content from the non-executable review surface.
- Added a focused Studio regression check for navigation isolation.
- Preview and Deployment runtime/proxy behavior is unchanged.

## CAP-036 fix-24 — Customer Mock current content + isolated navigation

- Corrected Customer Website Mock so it renders the latest persisted website content instead of reverting to the generation-time canonical preview artifact.
- Restored functional internal Mock navigation using same-document page fragments while keeping navigation isolated from the AWE Studio parent document.
- Hardened the Studio Mock sanitizer to permit only fragment navigation and continue blocking root-relative/external navigation, forms and scripts.
- Added API regression coverage for current-content rendering and isolated internal routes.
- Kept Preview, Publish/Live Preview, Deployment, migration and external runtime lifecycle code unchanged.

## CAP-036 fix-25 — Customer Mock iframe navigation boundary

- Preserved latest persisted website content from fix-24.
- Added a host-side capture boundary for internal Mock fragment navigation so links switch pages inside the existing iframe document instead of resolving against the Studio document.
- Kept the existing sanitizer restrictions on scripts, forms, base tags, external URLs and root-relative URLs.
- **Local browser result:** failed; clicking inside the Mock could still navigate the AWE Studio parent document. Fix-25 is not accepted as the final isolation fix.
- No Preview, Live Preview, Deployment, migration, or external runtime lifecycle changes.

## CAP-036 fix-26 — Customer Mock sandboxed navigation boundary

- Retained the current-content renderer and fix-25 capture boundary.
- Added `sandbox="allow-same-origin"` to the Customer Website Mock iframe, deliberately withholding top-navigation, scripts, forms and popup permissions.
- Preserved same-document fragment navigation for the mock's internal pages.
- Added regression coverage asserting the iframe sandbox boundary.
- No Preview, Live Preview, Deployment, migration, or external runtime lifecycle changes.

## CAP-036 fix-27 — Customer Mock internal navigation base isolation

- Added an explicit `about:srcdoc` base to the sanitized Customer Website Mock document so fragment navigation cannot resolve against the embedding AWE Studio document.
- Rewrote supported internal customer-site paths to deterministic mock page fragments instead of stripping them into ambiguous navigation targets.
- Continued blocking external URLs, forms, scripts and top-level navigation capabilities.
- Fixed the Studio build type-check boundary so the focused `.mts` regression script does not become part of the Next.js production type-check set.
- No Preview runtime, Publish/Live Preview, Deployment, migration or external Node runtime lifecycle changes.


## CAP-036 fix-29
- Corrected the deployment snapshot boundary so every new local deployment explicitly snapshots the latest published content set.
- Added regression coverage proving draft content cannot leak into a deployment snapshot.
- Documented the defect and troubleshooting path.

## CAP-036 fix-30 — Live deployment/runtime convergence

- Canonicalized the stable live-deployment proxy on the project's latest `deployed` deployment record.
- Serialized restore/open operations per deployment and reconciled duplicate Docker runtimes to one ready keeper.
- Corrected exact deployment runtime inspection and persisted the selected runtime ID/current host endpoint.
- Historical deployment restores no longer stop the current live deployment runtime.
- Studio exposes the immediately previous deployment as a restorable historical version; older versions remain snapshot-only.


## CAP-037 — Deployment lifecycle/current-previous policy

- Added durable `lifecycle_role` (`current`, `previous`, `historical`) and
  `snapshot_ref` to deployment persistence.
- Added a project-scoped database invariant allowing at most one canonical
  current deployment.
- Made local deployment promotion occur only after immutable snapshot creation
  and healthy runtime activation.
- Removed the previous behavior that stopped/demoted the current deployment
  before the replacement deployment had succeeded.
- Added project/deployment-aware runtime reconciliation and exact-deployment
  stop behavior.
- Added an explicit `POST /deployments/{deployment_id}/restore` API operation;
  restore starts/reuses the selected snapshot runtime without promoting it.
- Preserved CAP-036/FIX-31 deployment-pinned browser navigation.
