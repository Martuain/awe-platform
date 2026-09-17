# CAP-036 — Persistent latest deployment snapshot

> **Current navigation contract:** CAP-036 FIX-31 makes a selected deployment a first-class live-preview navigation identity. See `docs/cap-036-fix-31-deployment-pinned-live-preview.md` for the complete incident, architectural correction, evidence and acceptance record.

## Purpose

Keep the last successfully deployed website available after the disposable runtime is stopped or the API process restarts. `Open live website` uses a stable project URL and restores the latest successful deployment snapshot when no live runtime is available.

## Runtime lifecycle

1. A validated deployment starts the existing disposable Next.js runtime.
2. Published CAP-035 content is already synchronized into that runtime workspace.
3. Before the deployment is marked `deployed`, the complete built workspace is copied to `awe-deployment-<deployment-id>`.
4. If snapshot persistence fails, the runtime is stopped and the deployment remains `failed`.
5. The existing dynamic-port URL remains available for compatibility and current runtime behavior.
6. `Open live website` now uses `/api/live-preview/deployment/<project-id>/` for local deployments.
7. The stable endpoint reuses an alive project runtime; otherwise it starts a new runtime directly from the latest successful snapshot volume.

## Persistence

Deployment snapshots are Docker named volumes and are independent of the disposable preview workspace. Stopping a deployment removes its disposable workspace but does not remove `awe-deployment-<deployment-id>`.

Snapshots are versioned by deployment ID, preserving rollback/history potential. Cleanup policy for old snapshots is intentionally deferred so a successful deployment is never silently lost.

## Security

The stable Studio route forwards to the API using the existing `X-AWE-Preview-Proxy` internal secret. The API's stable deployment proxy is therefore not an unauthenticated public API surface.

## Regression coverage

Deployment tests verify successful deployments require snapshot persistence and that snapshot failures cannot produce a `deployed` status. Existing preview/deployment tests continue to pass.


## Preview/runtime separation

The interactive AWE-Preview iframe uses a dedicated stable project preview proxy (`/api/live-preview/preview/<project-id>/`). Deployment URLs continue to use `/api/live-preview/deployment/<project-id>/`. This prevents Preview from accidentally rendering the latest deployment snapshot and ensures published CAP-035 content is served by the disposable Preview runtime.

## Preview stale-first-render guard

Studio now unmounts the previous interactive Preview document before `Validate Website` or content publication reconciles the Preview runtime. The live iframe is mounted again only after the API confirms a started Preview runtime, preventing an older document from being briefly displayed while the refreshed runtime is becoming ready. If reconciliation fails, the old interactive document is not silently shown as current.


## Defect and troubleshooting record

CAP-036 implementation and regression defects are tracked permanently in `docs/defect-register.md`, with reproducible diagnostics and recovery procedures in `docs/troubleshooting.md`. The Preview Refresh recovery is intentionally isolated from deployment snapshot/runtime code.

## CAP-036 fix-23 — Studio build regression guard

The first fix-22 local rebuild exposed a packaging defect in the regression harness: Next.js type-checking included `apps/studio/scripts/test-mock-preview-isolation.ts`, while the test intentionally used a `.ts` extension in a Node `--experimental-strip-types` import. Next.js correctly rejected that explicit `.ts` import during `next build`.

Fix-23 changes only the test harness file extension from `.ts` to `.mts` and updates its package/test documentation references. This keeps the regression test executable with Node while preventing the standalone test from being part of the Next.js application build input. No Preview, Deployment, database, or runtime lifecycle code is changed.

## CAP-036 fix-22 — Customer Mock iframe isolation

The Customer Website Mock is a static review artifact and must not navigate into the AWE Studio application. Because the mock uses `iframe srcDoc`, its navigation targets require explicit isolation from the embedding document.

Fix-22 centralizes this sanitization in `apps/studio/app/lib/safe-artifact-preview.ts`. Anchor navigation and form submission targets are removed, base elements are removed, and scripts are stripped. The interactive Preview runtime and persistent Deployment runtime remain separate and are not modified by this increment.

Regression coverage is provided by `apps/studio/scripts/test-mock-preview-isolation.mts`.

## CAP-036 fix-24 — Customer Mock current-content and navigation correction

Fix-22 successfully stopped Customer Website Mock navigation from escaping into AWE Studio, but its deliberately inert-link strategy exposed two requirements that must both hold: the Mock must show the latest persisted user content, and internal navigation must remain functional inside the Mock.

Fix-24 therefore keeps the isolation boundary while changing the Mock renderer. The API now composes the Mock view from the current persisted website-content rows and the approved specification, rather than returning the generation-time canonical `awe-preview.html` unchanged. Each specified page is represented inside the same HTML document, with internal links using same-document fragments. The Studio sanitizer permits those fragments but removes non-fragment navigation targets, base elements, scripts and form navigation.

This increment does not modify interactive Preview runtime routing, content publication synchronization, Deployment snapshots, migrations, or the external `node:22-alpine` runtime containers.

## CAP-036 fix-27 — Customer Mock navigation base isolation

Fix-27 follows the browser finding from fix-26: the iframe was navigable and sandboxed, but mock links could still resolve to AWE Studio content inside the iframe. The correction is limited to the non-executable Customer Website Mock artifact sanitizer: it declares `about:srcdoc` as the document base and maps internal website paths to mock-page fragments. Preview, Live Preview, Deployment, migrations and disposable runtime lifecycle remain unchanged.

## CAP-036 fix-28 — Published-content authority boundary

Fix-28 closes the content-version boundary exposed during regression. The latest editable `website_content` row may legitimately be `draft` after a user changes copy without publishing, but runtime consumers must continue to see the last published version.

The authoritative rules are now:

1. **Studio editor:** shows the current editable draft row.
2. **Customer Website Mock:** renders the latest published content only.
3. **Preview / Refresh:** synchronizes the latest published content only.
4. **Publish Content:** creates the new published version and refreshes Live Preview.
5. **Deployment:** captures the successfully deployed version in its immutable deployment snapshot.
6. **Unpublished drafts:** never mutate an existing deployment and never become visible in Mock or Preview merely because the iframe is refreshed.

For SQL persistence, `website_content_versions` is now the source for the published view. This preserves the last published snapshot even while the current editable row has returned to `draft`. The in-memory repository follows the same semantic contract so tests do not validate a weaker lifecycle than production.

This increment also corrects the Mock's Home fragment CSS so returning from another mock page to Home cannot result in a blank document.


## CAP-036 fix-29 — Deployment must snapshot the latest published content

Local regression exposed a content-version promotion defect after fix-28: Customer Website Mock and Live Preview correctly reflected the newly published content, but Deploy could create a new deployment snapshot from a workspace whose dynamic `awe-content.json` was not guaranteed to contain that same published set at the exact snapshot boundary.

Fix-29 makes the deployment boundary explicit. Immediately before `create_deployment_snapshot`, the deployment provider retrieves `WebsiteContentStatus.PUBLISHED` and writes that exact set into the deployment source workspace. The subsequent immutable snapshot therefore contains the same published content that the user just promoted through Publish Content. Editable draft rows are never copied into the deployment snapshot.

The fix is deliberately scoped to the deployment snapshot boundary. Preview publication, Customer Mock rendering, historical deployment restore, generated artifacts, migrations, and external disposable Node runtime lifecycle are unchanged.

Regression contract:

- publish v2;
- verify Mock/Live Preview v2;
- Deploy;
- the new deployment must render v2;
- create an unpublished draft v3;
- the existing deployment remains v2;
- Deploying again without publishing must not promote v3.

## CAP-036 fix-30 — Canonical live deployment/runtime convergence

The live deployment entry points now resolve through the canonical latest `deployed`
`website_deployments` record. An explicit `deployment_id` continues to address a
historical deployment snapshot, but restoring one deployment never tears down another
deployment's runtime. Restore/open requests for the same deployment are serialized,
reuse an already-ready runtime, and reconcile duplicate runtimes down to one keeper.
The selected runtime ID and disposable host URL are persisted back to the deployment
record.

Studio exposes the immediately previous stopped deployment as an explicitly restorable
historical version while retaining older deployments as snapshot-only history. Opening
the previous version does not promote it or change the project's canonical live version.

Regression coverage includes stable live resolution, runtime metadata reconciliation,
historical-runtime reuse, duplicate-runtime cleanup, and preservation of the current
live runtime while a historical deployment is restored.

## CAP-036 FIX-31 — Deployment-pinned live-preview navigation

FIX-31 establishes deployment identity as a browser navigation boundary. The previous historical-preview contract accepted `deployment_id` as an entry-point query parameter, but generated customer-site links remained project-scoped. A historical V7 document could therefore render correctly on first load and then fall back to the project's latest V8 deployment after browser navigation dropped the query parameter.

The correction adds the deployment-scoped route:

```text
/api/live-preview/deployment/<project-id>/<deployment-id>/...
```

and makes an explicit deployment ID authoritative in `WebsitePreviewService.proxy_deployment_request()`. Only requests without a deployment ID resolve the canonical latest `deployed` record. The deployment proxy now exposes a deployment-specific public prefix so generated `href`, `src`/asset paths and relevant Next.js serialized navigation state remain inside the selected deployment namespace.

Studio deployment actions now build the stable URL with the explicit deployment ID. Consequently the live completion action and deployment-history action may have different product wording, but both converge on the same deployment-identity contract.

This is a routing/identity correction, not a runtime lifecycle rewrite. CAP-036 FIX-30 runtime reconciliation, immutable `awe-deployment-<deployment-id>` snapshots, latest/previous deployment policy, duplicate-runtime convergence, and historical restore semantics remain unchanged.

### FIX-31 acceptance

Local acceptance proved:

- V7 initial render → `Coyote - Sylvester`;
- V8 initial render → `Coyote - Tweety`;
- V7 generated links contain the V7 deployment ID;
- V8 generated links contain the V8 deployment ID;
- V7 Home → About → Services → Contact → Home remains V7;
- V8 navigation remains V8;
- historical V7 access does not promote V7 over canonical V8.

The focused API suite passed with `24 passed in 0.16s` during acceptance. Permanent defect and architectural records are maintained in `docs/defect-register.md` and `docs/adr/ADR-0019-deployment-pinned-live-preview.md`.
