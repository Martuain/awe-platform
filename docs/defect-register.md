# AWE Defect Register

This register is a permanent record of defects found during capability implementation and regression verification. A defect is only closed when its fix and regression behavior are recorded.

## Status definitions

- **Open** — reproduced and awaiting a fix.
- **Deferred** — known, bounded issue intentionally left for a later increment.
- **Fixed** — code change implemented.
- **Regression Verified** — fixed and verified against the relevant workflow.

## CAP-033 / CAP-036 defects

### DEF-033-001 — Multiple Alembic heads prevented API startup

- **Status:** Regression Verified
- **Introduced by:** CAP-033 durable execution state
- **Symptom:** API exited with code 3 during startup; Studio could not load `/api/v1/projects`; project selector disappeared.
- **Evidence:** Startup stopped after Alembic initialized. `docker inspect` showed `ExitCode=3`, `OOMKilled=false`.
- **Root cause:** `0002_execution_state` and `0008_website_content` were independent Alembic heads while application startup executes `alembic upgrade head`.
- **Fix:** Added a schema-neutral merge revision joining the two existing branches.
- **Data impact:** None. Existing PostgreSQL data was preserved.
- **Verification:** API remained up and `/api/v1/projects` returned the existing project set; project dropdown restored.
- **Troubleshooting:** See `docs/troubleshooting.md` → API startup / Alembic multiple heads.

### DEF-036-001 — Preview iframe could display stale/empty content during runtime reconciliation

- **Status:** Regression Verified
- **Symptom:** After Validate Website or Publish Content → Live Preview, the iframe could briefly show an older version, remain empty while the disposable runtime was being reconciled, or require reopening the preview.
- **Root cause:** Studio treated an iframe remount/cache-busting key change as sufficient refresh. That does not recover an alive-but-stale or unreachable Preview runtime.
- **Fix:** Preview Refresh now calls the authoritative `/api/v1/website-preview/refresh` endpoint, hides the old iframe, waits for a `started` runtime, then mounts a new cache-distinct iframe.
- **Verification target:** Refresh from an empty/stale iframe must recover the current published Preview without another Publish or Validate operation; iframe navigation and Open in new tab must remain functional.
- **Regression scope:** No deployment, snapshot, migration, or project-selector code is changed by this fix.


## CAP-036-F01b — Customer Website Mock navigation isolation

- **Status:** Open; fix-25 browser verification failed; fix-26 prepared.
- **Observed after fix-24:** The Customer Website Mock correctly rendered the latest persisted content and exposed internal fragment links, but clicking inside the mock could still navigate the AWE Studio parent document. Fix-25's host-side click handler did not provide a sufficient browser-level navigation boundary.
- **Root cause:** `iframe srcDoc` navigation can retain the embedding document as its fallback navigation context. A JavaScript click handler alone is therefore not an adequate isolation guarantee for this review surface.
- **Fix-25 result:** The capture-phase click boundary was retained, but the user's local browser regression reproduced the parent-document navigation. Fix-25 is therefore not accepted as the final fix.
- **Fix-26 strategy:** Add an iframe sandbox boundary with `allow-same-origin` only. This explicitly withholds `allow-top-navigation`, `allow-top-navigation-by-user-activation`, scripts, forms and popups while preserving the mock document's own fragment navigation. The existing click boundary remains as a defense-in-depth mechanism.
- **Safety:** This change does not enable generated scripts, external navigation, forms, Preview runtime routing, Live Preview, Deployment, or external Node runtime lifecycle.
- **Expected invariant:** `latest persisted user content → isolated Customer Mock → internal link changes only Mock document`; never `Mock → AWE Studio parent/document`.
- **Regression:** The Studio regression now asserts the sandbox boundary in addition to sanitizer and click-boundary coverage. Browser verification is required to close the defect.

## CAP-036 historical defects

### DEF-036-002 — Missing `restore_deployment_snapshot`

- **Status:** Fixed / Regression Verified
- **Symptom:** Stable latest deployment returned `name 'restore_deployment_snapshot' is not defined`.
- **Root cause:** Deployment stable-endpoint path referenced a restore helper that was not defined in the deployed service revision.
- **Fix:** Restored the service-level snapshot restoration path.
- **Verification:** Latest deployment reopened from its persistent snapshot.

### DEF-036-003 — Live preview runtime unreachable / connection timeout

- **Status:** Regression Verified
- **Symptom:** Stable and historical deployment links could return runtime-unreachable or timeout errors before the runtime became reachable.
- **Root cause:** Disposable runtime startup/restore was asynchronous relative to browser navigation.
- **Fix:** Stable deployment and Preview proxy paths reconcile/reuse/restore runtimes before proxying; Studio does not rely on stale dynamic ports.
- **Verification:** Latest and historical deployments open successfully; first-open latency can be higher while a runtime is restored.

### DEF-036-004 — Preview stale generation / iframe 404 navigation

- **Status:** Regression Verified
- **Symptom:** Preview iframe could show an earlier generated version and internal links could produce 404 or route back into Studio.
- **Root cause:** Preview URL/runtime ownership and content synchronization were not consistently separated from deployment routing.
- **Fix:** Dedicated project Preview proxy, runtime refresh after publication, and generated-site runtime navigation through the proxy.
- **Verification:** Published content appears in iframe and new tab; iframe navigation works.

### DEF-036-005 — Unsupported `docker update --label-add`

- **Status:** Regression Verified
- **Symptom:** Deployment failed with `unknown flag: --label-add`.
- **Root cause:** Docker CLI on the target environment does not support that `docker update` option.
- **Fix:** Deployment labels are applied when the runtime container is created from the immutable snapshot rather than by post-creation label mutation.
- **Verification:** Local deployment succeeds and persists its snapshot.

## Maintenance rule

Every newly discovered defect must be added here before the corresponding capability is considered complete. Resolved defects retain their troubleshooting and verification history; they are not deleted from the register.

## Workflow governance record

### DEF-WORKFLOW-001 — Stage-transition/state-integrity risk

- **Status:** Preventive control established; ongoing regression requirement
- **Risk:** Independent stage navigation can create contradictory workflow state if users move forward or backward without explicit prerequisite and invalidation rules.
- **Required control:** `docs/workflow-state-machine.md` defines the canonical transition, prerequisite, version-identity and downstream-staleness rules.
- **Scope:** Discovery → Strategy → Design → Specification → Build → Validation → Preview → Deploy, including backward navigation.
- **Verification:** Future CAP acceptance must include the workflow regression gate defined by the state-machine document.
- **Maintenance:** Any CAP changing stage navigation or state semantics must update the state-machine document and add/update regression coverage.

### DEF-036-006 — Customer Website Mock iframe navigation escaped into Studio

- **Status:** Open under CAP-036-F01b; fix-22/24/25 were intermediate mitigations, with fix-26 prepared
- **Symptom:** The Customer Website Mock could render correctly on first load, but clicking an internal mock link could navigate the `srcDoc` iframe back to the AWE Studio document instead of remaining an isolated customer-facing mock.
- **Root cause:** The mock is rendered through `iframe srcDoc`. Its document does not have an independent application origin, so ordinary navigation targets can resolve against the embedding Studio document. The previous sanitizer only rewrote root-relative `href` values to `#`; that still permits the browser to resolve the navigation against the `srcDoc` fallback base in some cases.
- **Fix:** Fix-22 centralized the mock sanitizer and stopped anchor/form navigation, removing `<base>` elements and scripts. Fix-24 retains that security boundary but restores supported internal navigation as same-document fragments.
- **Scope:** Customer Website Mock only. Interactive Preview and Deployment runtime/proxy paths are unchanged.
- **Regression:** `apps/studio/scripts/test-mock-preview-isolation.mts` verifies fragment navigation is retained while root-relative/external navigation, form targets, base tags and scripts cannot escape the mock document.

### DEF-036-007 — Customer Website Mock rendered stale canonical content and inert navigation after isolation hardening

- **Status:** Fixed in fix-24; local browser regression pending.
- **Observed:** Customer Website Mock rendered the original canonical website proposal rather than the latest persisted user-modified content. After fix-22, internal navigation was intentionally disabled to prevent iframe escape, leaving Home/About/Services/Contact inert.
- **Root cause:** The mock persisted `validation.preview.html`, which is a generation-time canonical artifact and does not consume CAP-035 content. The isolation fix then removed anchor `href` values entirely, preventing both the Studio escape and legitimate mock navigation.
- **Fix:** The Mock service now renders its review view from the latest persisted website-content rows (draft or published), preserving the current generation/mock boundary. Internal routes are represented as same-document fragments and rendered as isolated page views. The sanitizer permits only fragment navigation, while removing external/root-relative URLs, scripts, base tags and form navigation.
- **Expected invariant:** `latest persisted user content → Customer Mock → same-document internal navigation`; never `canonical v1 → inert links` and never `mock → AWE Studio`.
- **Scope:** Customer Website Mock only. Interactive Preview, Publish/Live Preview, Deployment, migration and external runtime lifecycle code are unchanged.
- **Regression:** API tests cover current-content rendering and isolated internal route generation; Studio sanitizer regression covers fragment preservation and external/root-relative navigation removal. Browser verification remains required before closing CAP-036-F01b.

### DEF-036-008 — Customer Mock internal fragments resolved against Studio fallback base

- **Status:** Open; fix-27 prepared for browser verification.
- **Observed after fix-26:** The Customer Website Mock iframe became independently navigable, but clicking a mock link could still load an AWE Studio route inside the iframe. The iframe was therefore isolated from parent escape while its navigation target was still wrong.
- **Root cause:** `srcDoc` documents can use the embedding document as their fallback base URL. Fragment-only links are consequently unsafe as the sole navigation contract when the review artifact does not declare its own base.
- **Fix-27 strategy:** Explicitly set the mock document base to `about:srcdoc` and rewrite supported internal customer-site paths to deterministic `#awe-mock-page-*` fragments. External absolute URLs remain blocked. Forms and scripts remain disabled.
- **Expected invariant:** `customer mock link → mock document fragment → customer mock page`; never `customer mock link → AWE Studio route`.
- **Regression:** Extend the focused Studio sanitizer test to assert the explicit `about:srcdoc` base and internal path-to-fragment rewriting. Browser verification remains mandatory before closure.

## CAP-036 fix-28 — Draft content must not replace the last published website

- **Observed:** After a user edited website content as a draft, Customer Website Mock could display that unpublished value, while Preview Refresh could fall back to the original canonical generation-time website. This made the Mock and Preview disagree with the latest deployed/published website and made an explicit draft edit appear executable before publication.
- **Root cause:** `website_content` stores the latest editable row as `draft`, so editing a previously published row intentionally clears its current-row `published` state. The existing `status=published` query therefore returned no row for that content key. Preview then had no published overlay to write into the runtime and could expose the canonical generated artifact.
- **Fix-28:** Published content is now treated as an immutable versioned snapshot for runtime consumers. The SQL repository resolves `status=published` from `website_content_versions` using the latest published version per content key; the in-memory repository mirrors that contract. Customer Website Mock consumes only the published view. Draft editing therefore changes the editor state without changing Mock, Preview Refresh, or the deployed website.
- **Related navigation fix:** The Mock home fragment selector now excludes the targeted home article from the generic `first-of-type` hide rule, preventing the previously observed blank Home screen after navigating away and back.
- **Expected invariant:** `draft edit → editor only`; `publish → latest published Mock/Preview`; `deploy → immutable deployment snapshot`. A draft must never appear in Customer Website Mock, Preview Refresh, or an existing deployment.


### CAP-036-F02 — Deploy snapshot can lag latest published content
- **Status:** Fix-29 prepared; awaiting local browser/runtime verification.
- **Observed:** Mock and Live Preview show the newly published content, but a newly created live deployment can still render an older content snapshot.
- **Boundary:** deployment snapshot creation.
- **Root cause:** the deployment flow relied on the Preview workspace already containing the correct dynamic published-content file at snapshot time. That implicit synchronization was not a sufficient promotion contract.
- **Correction:** immediately before snapshot persistence, explicitly write the repository's `PUBLISHED` content set into the exact source workspace, then snapshot it.
- **Non-goals:** do not alter draft editing, Publish behavior, Preview runtime routing, historical deployment restore, or disposable Node runtime lifecycle.
- **Verification:** focused unit regression asserts only published content is materialized at the deployment snapshot boundary.

### DEF-036-009 — Historical live deployment lost identity during browser navigation

- **Status:** Fixed and regression verified in FIX-31.
- **Severity:** High — version integrity / customer-visible deployment correctness.
- **Symptom:** Opening historical deployment V7 initially rendered V7 content, but navigating to another generated page and returning could silently render the latest deployment V8 content. The browser therefore appeared to be viewing V7 while actually serving V8.
- **Root cause:** The historical deployment ID was carried as an entry-point query parameter, while generated HTML links, assets and Next.js navigation remained project-scoped. Once the query parameter was dropped, the deployment proxy had no explicit deployment identity and intentionally resolved the project's latest `deployed` record.
- **Evidence:** Before FIX-31, direct V7 runtime access returned `Coyote - Sylvester`, direct V8 access returned `Coyote - Tweety`, and the initial historical proxy response returned V7. The version changed only after browser navigation, proving the snapshot/runtime content was correct and deployment identity was being lost at the navigation boundary.
- **Fix:** Added the deployment-scoped Studio route `/api/live-preview/deployment/{projectId}/{deploymentId}/...`; made explicit `deployment_id` authoritative in the API deployment proxy; rewrote generated internal links/assets and relevant Next.js serialized navigation data into the selected deployment namespace; updated Studio deployment links to pass the explicit deployment ID.
- **Architectural consequence:** A selected deployment is now a stable browser navigation identity. The project-level route remains the canonical latest-deployment entry point, while historical deployments use an immutable deployment-specific namespace. Runtime host ports remain disposable and snapshots remain the durable historical source.
- **Runtime policy:** Latest deployment remains canonical/running; immediately previous deployment remains restorable for comparison/testing; older deployments remain snapshot-only by default. Historical restore does not promote or tear down the current live deployment.
- **Regression:** Direct V7/V8 HTTP checks, deployment-scoped link inspection, focused API tests, and browser navigation through Home/About/Services/Contact all passed after FIX-31 deployment. V7 remained `Coyote - Sylvester`; V8 remained `Coyote - Tweety`.
- **Troubleshooting:** If reproduced, inspect the deployment-scoped URL, generated `href/src` values, Next.js navigation payloads, API `deployment_id` resolution, deployment/runtime IDs and the corresponding `awe-deployment-<deployment-id>` snapshot.
