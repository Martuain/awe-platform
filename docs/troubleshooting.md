# AWE Troubleshooting Guide

## API unavailable / project selector missing

1. Check service state:
   ```bash
   docker compose ps -a
   ```
2. Inspect the API exit status:
   ```bash
   docker inspect awe-platform-genesis-v010-api-1      --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}} Error={{.State.Error}} OOMKilled={{.State.OOMKilled}} RestartCount={{.RestartCount}}'
   ```
3. Inspect startup logs:
   ```bash
   docker compose logs --tail=300 api
   ```
4. Confirm the database user from Compose configuration. AWE uses:
   ```text
   DATABASE_URL=postgresql+asyncpg://awe:awe@postgres:5432/awe
   POSTGRES_USER=awe
   POSTGRES_DB=awe
   ```
   Therefore use:
   ```bash
   docker compose exec postgres psql -U awe -d awe -c "SELECT id, name, created_at FROM projects ORDER BY created_at;"
   ```
   Do not assume the PostgreSQL role is `postgres`.
5. If startup stops immediately after Alembic initialization, inspect migration heads:
   ```bash
   docker compose run --rm api sh -lc 'python -m alembic current && python -m alembic heads'
   ```
   `alembic heads` should report one effective head. Multiple heads can make `alembic upgrade head` fail during API startup.

## Preview iframe empty/stale

The Preview Refresh control must recover the runtime, not merely reload the browser document.

Expected recovery sequence:

```text
Refresh
  -> POST /api/v1/website-preview/refresh
  -> hide existing iframe
  -> wait for status=started
  -> increment iframe refresh key
  -> mount /api/live-preview/preview/<project-id>/
```

If the iframe remains empty:

1. Check API availability:
   ```bash
   curl -i http://localhost:8000/health
   ```
2. Inspect API logs:
   ```bash
   docker compose logs --since=5m api
   ```
3. Inspect Docker runtimes:
   ```bash
   docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Labels}}'
   ```
4. Confirm the project Preview runtime has the expected project label and is reachable.
5. Do not switch the Preview iframe to the deployment endpoint. Preview and Deployment have separate stable proxies.

Browser-extension messages such as `contentscript.js ... Resetting the streams` and `Unchecked runtime.lastError: Could not establish connection` are generally extension noise unless the same failure reproduces with extensions disabled.

## Deployment runtime / snapshot troubleshooting

For deployment restoration problems:

```bash
docker volume ls | grep awe-deployment
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Labels}}'
docker compose logs --since=5m api
```

A successful local deployment must have a persistent `awe-deployment-<deployment-id>` volume. A snapshot failure must leave the deployment failed rather than marking it deployed.

## Regression discipline

When a repository revision is generated:

1. Start from the latest known-good archive.
2. Make the smallest capability-scoped change possible.
3. Preserve the migration graph and existing persistent data.
4. Run focused tests first.
5. Run available broader tests.
6. Update `docs/defect-register.md` and this guide for every defect discovered or fixed.
7. Re-test all adjacent working behavior before declaring the revision verified.

## Workflow stage/state integrity

When a workflow issue appears to show the wrong stage, stale content, an unexpected version, or an invalid forward/backward transition, diagnose state identity before changing runtime code.

1. Identify the project ID and current Studio stage.
2. Identify the exact website/content/generation/deployment version represented by the screen.
3. Check whether the transition's upstream prerequisite is actually satisfied.
4. Check whether the source stage was edited after the downstream artifact was produced.
5. Treat affected downstream state as stale until regeneration/revalidation proves otherwise.
6. Do not use the latest deployment/runtime as a fallback for a historical or explicitly selected version.
7. Preserve immutable historical artifacts while correcting the current workflow state.

The canonical transition rules and invariants are in `docs/workflow-state-machine.md`.

## Studio rebuild fails on `test-mock-preview-isolation.ts` explicit `.ts` import

**Symptom**

`next build` fails during type checking with: `An import path can only end with a .ts extension when allowImportingTsExtensions is enabled.` The failing file is the standalone mock-isolation regression script.

**Cause**

The script is intentionally executed directly by Node with `--experimental-strip-types`, but the Next.js TypeScript build also discovers `.ts` files under `apps/studio/scripts/`. The explicit `.ts` runtime import is valid for the standalone Node test but is rejected by the application compiler.

**Fix**

Keep the standalone test outside the application TypeScript build input by using the `.mts` extension and update the package script/documentation accordingly. Do not enable `allowImportingTsExtensions` globally merely to accommodate a test harness.

**Verification**

```
cd apps/studio
node --experimental-strip-types scripts/test-mock-preview-isolation.mts
```

Expected output: `Customer Website Mock navigation isolation: PASS`.

## Customer Website Mock iframe navigates back to AWE Studio

The Customer Website Mock is a static, non-executable review surface. It is intentionally not the interactive Preview runtime.

If the mock initially renders correctly but clicking a navigation item causes the iframe to display AWE Studio, treat this as a mock-document isolation defect rather than a Preview/deployment runtime problem.

Expected behavior:

```text
Customer Website Mock
  -> iframe srcDoc
  -> generated visual artifact remains isolated
  -> internal links/forms are inert
  -> parent AWE Studio document is unchanged
```

Do not change the Preview proxy or deployment runtime to correct this symptom. The mock sanitizer in `apps/studio/app/lib/safe-artifact-preview.ts` is the authoritative boundary.

Regression check:

```bash
cd apps/studio
node --experimental-strip-types scripts/test-mock-preview-isolation.mts
```

Expected output:

```text
Customer Website Mock navigation isolation: PASS
```

## Customer Website Mock shows canonical/stale content or links are inert

A Customer Website Mock must represent the latest persisted website content applicable to the project, not the original generation-time canonical preview. It must also support internal website navigation without ever navigating the AWE Studio application into the iframe.

If the Mock shows the first/canonical version after the user has edited and saved content, diagnose the Mock renderer rather than Preview/Deployment:

1. Confirm the project ID and current generation/mock version.
2. Check `/api/v1/website-content/<project-id>` and verify the latest persisted values and versions.
3. Check `/api/v1/website-mock/<project-id>` and verify the returned HTML contains the latest persisted values.
4. Confirm internal anchors use `#awe-mock-page-*` fragments rather than root-relative URLs such as `/about`.
5. Clicking Home/About/Services/Contact must change the page within the Mock iframe while leaving the parent AWE Studio document unchanged.
6. Do not change the Preview proxy or deployment runtime to correct a Mock-only stale-content/navigation defect.

The authoritative implementation boundaries are:

- `apps/api/app/services/mock.py` — current-content Mock rendering and isolated page views.
- `apps/studio/app/lib/safe-artifact-preview.ts` — iframe navigation/executable-content sanitization.
- `apps/studio/scripts/test-mock-preview-isolation.mts` — focused isolation regression.

Expected behavior:

```text
latest persisted content
        ↓
Customer Website Mock
        ↓
self-contained iframe document
        ├─ internal links → same-document mock page
        ├─ external/root-relative navigation → blocked
        ├─ forms/scripts → non-executable
        └─ parent AWE Studio → unchanged
```

## CAP-036 Customer Website Mock opens AWE Studio inside the iframe

If the Customer Website Mock initially renders but clicking a website link causes an AWE Studio page to appear inside the iframe, distinguish this from parent-window escape. The iframe may be correctly sandboxed while the `srcDoc` navigation target still resolves against Studio's fallback base.

For fix-27 and later, verify all of the following:

1. The sanitized mock contains `<base href="about:srcdoc">`.
2. Customer-site paths such as `/about` are rewritten to `#awe-mock-page-about`.
3. External absolute URLs are removed from the review artifact.
4. The iframe retains `sandbox="allow-same-origin"` without top-navigation, scripts, forms or popup permissions.
5. Clicking Home/About/Services/Contact changes only the mock document and never renders an AWE Studio route inside the iframe.

Do not compensate for this defect by granting broader iframe permissions. The correct boundary is deterministic mock navigation plus restrictive sandboxing.

## Draft edits appear in Customer Website Mock or Preview Refresh falls back to canonical content

This symptom indicates a content-version authority defect, not an iframe problem.

The platform has three deliberately different content states:

```text
current editable row       = Draft
last published version     = Runtime authority for Mock + Preview
immutable deployment       = Official deployed snapshot
```

After a user edits already-published content, the current editable row correctly becomes `draft`. That operation must **not** erase the last published version from the runtime-facing view.

For CAP-036 fix-28 and later:

1. `GET /api/v1/website-content/<project-id>` without a status filter shows the current editable rows, including drafts.
2. `GET /api/v1/website-content/<project-id>?status=published` resolves the latest published version from `website_content_versions`.
3. Customer Website Mock consumes only the published view.
4. Preview Refresh consumes only the published view and writes it to `awe-content.json` in the disposable Preview runtime.
5. `Publish content → Live Preview` is the boundary that makes the draft runtime-visible.
6. Deployment creates/retains an immutable deployment snapshot and must not be changed by subsequent draft edits.

### Regression scenario

```text
publish v1
  ↓
edit v2 as draft
  ↓
Mock = v1
Preview Refresh = v1
Deployment = v1
  ↓
publish v2
  ↓
Mock = v2
Preview = v2
Deployment remains v1 until Deploy
```

If Mock or Preview shows the draft before publication, inspect the published-version query first. Do not fix this by changing iframe behavior, Preview proxy routing, or deployment snapshot handling.


### CAP-036 — Deploy shows an older content version after Publish
If Mock and Live Preview show the newly published content but a newly created deployment still shows older content, treat this as a deployment snapshot-boundary defect rather than a Preview defect. Do not delete the external `com.awe.preview=true` Node runtimes. Verify that the deployment operation succeeds and that the snapshot source workspace is synchronized from `WebsiteContentStatus.PUBLISHED` immediately before snapshot creation. An unpublished draft must never be used as the deployment source.

## CAP-036 FIX-31 — Historical deployment changes version after navigation

### Symptom

A historical deployment opens with the expected version-specific content, but clicking Home/About/Services/Contact causes the site to render the latest deployment instead. Example: V7 opens as `Coyote - Sylvester`, then returns as `Coyote - Tweety` after navigation.

### Meaning

This is a deployment-identity regression, not necessarily a bad deployment snapshot. The first request can prove the selected snapshot/runtime is correct while a later project-scoped request silently resolves the latest deployed version.

### Diagnostic sequence

1. Query `website_deployments` for the affected project and compare `version`, `status`, `runtime_id`, `url` and `stopped_at`.
2. Directly curl the selected deployment runtime and verify its version-specific HTML.
3. Curl the stable deployment URL with the explicit `deployment_id` and verify the initial HTML.
4. Inspect the returned `href`/`src` values. They must use:

   ```text
   /api/live-preview/deployment/<project-id>/<deployment-id>/...
   ```

5. If links fall back to `/api/live-preview/deployment/<project-id>/...`, deployment identity is being lost.
6. Verify the API deployment proxy resolves an explicit `deployment_id` directly and only uses latest-deployment lookup when no deployment ID is supplied.
7. Verify Docker runtime labels include `com.awe.deployment_id=<deployment-id>` and the matching `awe-deployment-<deployment-id>` snapshot exists when restoration is required.

### Expected behavior after FIX-31

- V7 remains V7 through browser navigation.
- V8 remains V8 through browser navigation.
- Opening V7 does not promote V7.
- The current live deployment remains canonical.
- Runtime ports may change after restoration; browser URLs must not depend on those ports.

See `docs/cap-036-fix-31-deployment-pinned-live-preview.md` and `docs/adr/ADR-0019-deployment-pinned-live-preview.md` for the full root-cause and architectural record.


## CAP-037 deployment lifecycle diagnostics

If two deployment versions appear to show the same site after navigation,
verify the database lifecycle role and the generated deployment-pinned links.
The browser URL must contain the selected deployment ID; runtime host ports
are not product identity.

Useful checks:

```bash
docker compose exec postgres psql -U awe -d awe -c "
SELECT version, status, lifecycle_role, url, runtime_id, snapshot_ref
FROM website_deployments
WHERE project_id = '<PROJECT_ID>'
ORDER BY version;
"
```

For a stopped historical version, `status=stopped` is not evidence that its
artifact is lost. If `snapshot_ref` is present, the deployment is restorable.
Restore is intentionally not promotion: the restored runtime must carry the
same deployment ID while the project's `current` role remains unchanged.

The CAP-036/FIX-31 browser isolation check remains the fastest regression:
fetch/open V7, navigate internally, then fetch/open V8 and verify that each
deployment stays inside its own deployment-scoped namespace.

## CAP-038.1 — Stable live URL returns 404 or falls back to another deployment

1. Confirm the deployed Studio build contains `apps/studio/app/api/live/[projectId]/[[...path]]/route.ts`. A 404 on `/api/live/<project>/...` from a pre-CAP-038 Studio build does not test the CAP-038 route.
2. Confirm Studio-generated deployment links use `/api/live/<project>/...` for current and `/api/live/<project>/deployment/<deployment>/...` for explicit versions.
3. Confirm the Studio route delegates to `/api/v1/website-preview/live-proxy/<project>/...` and attaches `X-AWE-Preview-Proxy`.
4. For an explicit deployment, confirm `deployment_id` reaches the API and belongs to the same `project_id`; mismatch or unknown deployment must return 404 and must never fall back to CURRENT.
5. Confirm Docker labels `com.awe.project_id` and `com.awe.deployment_id` match the database deployment row. Runtime port/container ID may change after restore and is not part of the stable URL contract.
6. Use `/api/live-preview/deployment/...` only when verifying FIX-31 compatibility. New Studio links should not be generated through that namespace.
