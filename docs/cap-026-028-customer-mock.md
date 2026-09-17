# CAP-026 / CAP-027 / CAP-028 — Customer Mock Review Wave

Status: **implemented in working increment; unreleased**

## CAP-026 — Customer Website Mock

AWE now exposes a first-class customer-facing mock between deterministic generation and executable build. The mock is derived from the validated artifact preview and is persisted with generation and mock versions.

Boundary:
- safe `srcDoc` HTML only in Studio;
- generated application code is not executed inside the Studio mock;
- mock approval is required before build access;
- `v1.0.3` remains frozen.

## CAP-027 — Visual Refinement / Feedback Loop

Customers can submit review feedback and request a revision without mutating an approved mock. The first deterministic refinement contract supports:

- `headline: ...`
- `cta: ...`

The revised generation receives a new generation version and the mock receives a new mock version. Unsupported feedback is retained in review history rather than silently translated into an invented design change. This keeps the capability provider-independent and deterministic while leaving richer model-driven visual editing as a later increment.

## CAP-028 — Mock → Executable Preview

An approved mock is the explicit gate into the existing isolated build, validation and live-preview path. Existing CAP-008/CAP-006 execution boundaries are reused; no second build/runtime path is introduced.

## API

- `POST /api/v1/website-mock/create?project_id=...`
- `GET /api/v1/website-mock/{project_id}`
- `POST /api/v1/website-mock/{project_id}/feedback`
- `POST /api/v1/website-mock/{project_id}/revise`
- `POST /api/v1/website-mock/{project_id}/approve`
- `POST /api/v1/website-generation/{project_id}/revise`

## Persistence

Migrations `0003_website_mock` and `0004_website_mock_project_index` add the current mock, immutable mock-version history, feedback records, and the non-unique project index required for revisions.

## Verification

- focused CAP-026/027 API tests: **4 passed**
- full API regression: **71 passed**
- Studio dependency installation/build was not run in the isolated source snapshot because `node_modules` is not included; run `pnpm install` then `pnpm --filter @awe/studio lint` and `pnpm --filter @awe/studio build` on the development machine.
