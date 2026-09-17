# CAP-024 — Hosted/Scalable Execution & Production Deployment Boundary

## Status
Unreleased working increment.

## Objective
Introduce explicit provider boundaries for website builds and deployments so the API can delegate expensive execution to separately scalable infrastructure without coupling Studio or capability logic to a specific cloud vendor.

## Implemented
- `BuildExecutionProvider` abstraction with the existing hardened Docker implementation retained as the default `local-docker` provider.
- Optional HTTP `hosted` build execution adapter controlled by environment configuration.
- Provider selection via `AWE_BUILD_EXECUTION_PROVIDER`.
- Optional hosted deployment provider via `AWE_DEPLOYMENT_PROVIDER=hosted`.
- Hosted deployment configuration through `AWE_DEPLOYMENT_PROVIDER_URL` and optional bearer token.
- Explicit provider failures are persisted/reported rather than silently falling back to local execution.
- Existing local deployment behavior remains the deterministic MVP default.

## Configuration
```text
AWE_BUILD_EXECUTION_PROVIDER=local-docker
AWE_BUILD_EXECUTION_PROVIDER=hosted
AWE_BUILD_EXECUTION_URL=https://build.example.internal
AWE_BUILD_EXECUTION_TOKEN=...
AWE_BUILD_EXECUTION_TIMEOUT_SECONDS=600

AWE_DEPLOYMENT_PROVIDER=local
AWE_DEPLOYMENT_PROVIDER=hosted
AWE_DEPLOYMENT_PROVIDER_URL=https://deploy.example.internal
AWE_DEPLOYMENT_PROVIDER_TOKEN=...
AWE_DEPLOYMENT_PROVIDER_TIMEOUT_SECONDS=600
```

## Deliberately not claimed
This capability does not create a cloud account, hosted worker fleet, artifact registry, Kubernetes orchestration, autoscaling policy, DNS/TLS management, or vendor-specific production provider. The HTTP adapters define the production boundary; an independently deployed service must implement that contract.
