# CAP-011 — Deployment UX & Lifecycle

## Objective

Turn the CAP-010 deployment contract into a user-visible deployment lifecycle
in Studio.

## Lifecycle

`queued → deploying → deployed → stopped`

A failed provider operation produces `failed` with diagnostics.

## API

- `POST /api/v1/deployments?project_id={id}`
- `GET /api/v1/deployments?project_id={id}`
- `GET /api/v1/deployments/{deployment_id}`
- `POST /api/v1/deployments/{deployment_id}/stop`

## MVP provider

CAP-011 uses the CAP-010 local provider. It promotes the isolated CAP-009
runtime into a versioned deployment record. This intentionally avoids selecting
a permanent cloud provider.

## Product behavior

Studio should expose:

- Deploy Website
- deployment status
- provider
- deployment version
- live URL
- deployment history
- Stop deployment
- failure diagnostics

## Security boundary

Deployment orchestration remains in the API/service layer. Generated code is
never executed directly by Studio.

## Deferred

Custom domains, DNS/TLS automation, production secrets, multi-region
deployment, provider-specific autoscaling, automatic promotion and billing.
