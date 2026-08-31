# ADR-0007 — Disposable Docker Runtime for Live Preview

## Status

Accepted for the MVP/local preview boundary.

## Context

CAP-008 proves that generated websites can be built outside the AWE host process. Users now need to inspect the actual generated Next.js application rather than only an HTML artifact.

## Decision

Run the validated generated site in a disposable Docker container and expose a dynamically allocated localhost port to the developer. The build remains network-disabled; the runtime accepts browser traffic through Docker's published port.

## Alternatives considered

| Approach | Decision | Reason |
|---|---|---|
| Docker disposable runtime | Selected | Lowest-complexity continuation of CAP-008 with real browser preview |
| Host `npm start` | Rejected | Executes generated code inside the host environment |
| Kubernetes Job/Service | Deferred | Operationally excessive for the current local/MVP proof |
| Firecracker/microVM | Deferred | Stronger isolation candidate for a later production threat model |
| Static HTML preview only | Insufficient | Does not validate the actual Next.js runtime behavior |

## Consequence

CAP-009 establishes the end-to-end runtime path but is not a production multi-tenant sandbox. Before public execution, runtime egress and isolation must be strengthened and the lifecycle must move out of process memory into durable orchestration.
