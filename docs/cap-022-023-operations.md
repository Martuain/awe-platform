# CAP-022 + CAP-023 — Deployment Operations

## Objective

Complete the next coherent M4 increment by adding deterministic generated-artifact performance checks and lightweight service/deployment monitoring without selecting a permanent cloud provider.

## CAP-022 — Performance checks

The API exposes `POST /api/v1/website-performance/check`. It analyzes the validated/generated artifact for file count, total source bytes, JavaScript/TypeScript bytes, CSS bytes, and page entry points. The checks are advisory budget gates and do not claim browser Lighthouse/Core Web Vitals measurements.

## CAP-023 — Monitoring

The API exposes `GET /api/v1/monitoring`, returning service status plus project/deployment counts and failed/deployed deployment counts. This is intentionally a minimal MVP observability surface; external metrics/logging backends remain deferred.

## Studio integration

The Deployment stage exposes Performance check and Monitoring actions and presents the resulting operational data alongside deployment history.

## Verification

- API regression suite: 58 passed.
- New CAP-022/023 tests: 3 passed.
- Studio lint/build: requires the local Node/pnpm dependency installation and is part of the local acceptance gate.

## Deliberately deferred

- Lighthouse/browser-based performance scoring
- Real-user monitoring
- Prometheus/OpenTelemetry backend
- alerting and SLOs
- hosted/scalable workers
- permanent cloud deployment provider
