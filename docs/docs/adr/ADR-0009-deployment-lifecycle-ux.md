# ADR-0009 — Deployment Lifecycle in Studio

## Status

Accepted for CAP-011.

## Decision

Expose deployment as a first-class artifact with an explicit lifecycle and
history. The Studio UI consumes the provider-neutral API rather than calling
Docker or another infrastructure tool directly.

## Rationale

The user needs to understand whether a generated website is merely generated,
validated, previewed, or actually deployed. A deployment record makes that
state explicit and provides a stable seam for future hosted providers.

## Technology boundary

CAP-011 does not choose a permanent deployment provider. The local provider
reuses the already-proven isolated runtime while the product contract is
validated.

## Revisit triggers

Revisit the lifecycle/provider boundary when persistent hosted deployments,
custom domains, multi-tenancy, autoscaling, rollback guarantees or production
observability become product requirements.
