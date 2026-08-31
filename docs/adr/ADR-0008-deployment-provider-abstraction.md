# ADR-0008 — Deployment Provider Abstraction

## Status

Accepted for CAP-010.

## Context

AWE now generates, validates, builds and previews websites. The next requirement
is to establish a deployment lifecycle without allowing an early infrastructure
choice to constrain the product.

## Decision

Create a provider-neutral deployment interface and ship a deterministic local
provider for the first implementation.

## Alternatives considered

### Vercel

Excellent Next.js integration and fast deployment experience, but introduces
vendor coupling before production requirements are established.

### Cloudflare

Strong edge/runtime capabilities and attractive economics, but its execution
model can diverge from a standard Next.js deployment.

### AWS

Maximum flexibility and broad infrastructure coverage, but significantly higher
operational complexity for the current stage.

### Kubernetes

Useful when AWE needs broad container orchestration, but premature before
deployment scale and tenancy requirements are established.

## Rationale

The abstraction lets AWE validate its product lifecycle first:

build → deploy → status → URL → stop/rollback concept.

The infrastructure can be selected later using actual evidence rather than
assumptions.

## Revisit triggers

Reassess the provider choice when AWE requires any combination of:

- production multi-tenancy
- custom domains
- persistent deployments
- autoscaling
- regional placement
- advanced observability
- deployment rollback guarantees
- predictable production cost
