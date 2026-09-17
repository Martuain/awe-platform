# CAP-006 — Change Log

## Added

- Website Validation domain model.
- Validation service with deterministic structural checks.
- `POST /api/v1/website-validation/validate` endpoint.
- CAP-006 API integration test.
- Studio Preview stage with validation results.
- Safe iframe browser preview generated from validation metadata.
- CAP-006 documentation.

## Boundary decision

The first CAP-006 implementation does not execute generated JavaScript or run an untrusted Next.js project inside the API/Studio process. Isolated execution is intentionally deferred until a dedicated sandbox/build runner is designed.


## CAP-036 fix-16
- Prevent the static validation artifact iframe from rendering during Preview validation/publish transitions.
- Show a neutral loading state until the interactive Preview runtime is ready, eliminating stale first-render content.
