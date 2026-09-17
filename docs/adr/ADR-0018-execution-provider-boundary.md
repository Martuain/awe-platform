# ADR-0018 — Scalable Execution Provider Boundary

## Context
Local Docker execution is appropriate for the MVP but cannot be the long-term scaling mechanism for an internet-facing service. Build and deployment workloads should be delegable without changing capability or Studio contracts.

## Decision
Define provider-neutral execution interfaces and retain local Docker/local deployment as the default. Add opt-in HTTP adapters for separately scalable build and deployment services. Provider choice is environment configuration and failures are explicit; there is no silent fallback.

## Consequences
The API can move heavy work to independent workers/services later while preserving current local development. A hosted service must implement the documented HTTP contracts and supply its own authentication, isolation, queueing and autoscaling.

## Deferred
A production worker fleet, durable queue, artifact registry, cloud provider integration, autoscaling, secrets platform and zero-downtime deployment orchestration remain future work.
