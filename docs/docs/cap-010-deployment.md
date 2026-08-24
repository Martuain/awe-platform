# CAP-010 — Deployment Abstraction

## Objective

Establish AWE's deployment contract without prematurely coupling the platform to a
specific cloud provider.

## What CAP-010 proves

An approved, validated and built website can be represented as a versioned
deployment artifact and moved through a deployment lifecycle:

`queued → deploying → deployed` or `failed`, with `stopped` available for
lifecycle management.

## Architecture

```text
Generated Website
      ↓
CAP-006 Validation
      ↓
CAP-008 Isolated Build
      ↓
CAP-009 Disposable Runtime
      ↓
CAP-010 Deployment Contract
      ↓
Deployment Provider
      ↓
Deployment URL
```

## Provider decision

CAP-010 uses a provider abstraction and a deterministic local provider for the
MVP. No cloud vendor is selected as the permanent production platform yet.

Candidates to evaluate later include Vercel, Cloudflare Workers/Pages, AWS,
and container/Kubernetes-based infrastructure.

The decision will be revisited when requirements for custom domains, persistent
deployments, scale, observability, tenancy, cost, regionality and rollback are
known.

## Security

Deployment input must originate from an AWE-generated/validated artifact.
Provider implementations must not execute arbitrary deployment commands inside
the Studio/API process.

## API

- `POST /api/v1/deployments`
- `GET /api/v1/deployments/{deployment_id}`
- `POST /api/v1/deployments/{deployment_id}/stop`

## Deliberately deferred

- Permanent cloud-provider selection
- Custom domains
- DNS automation
- TLS automation
- CDN configuration
- Production secrets management
- Multi-region deployment
- Automatic production promotion

These belong to later capabilities once the deployment contract has been
validated.
