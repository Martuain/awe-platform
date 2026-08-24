# CAP-009 — Disposable Live Preview Runtime v0.9.0

## Objective

Turn the CAP-008 isolated build boundary into a usable live-preview capability without executing generated website code inside AWE Studio or the API process.

## What CAP-009 adds

- `POST /api/v1/website-preview/start`
- `POST /api/v1/website-preview/stop`
- disposable Docker preview runtime
- validated-generation prerequisite
- dependency acquisition with lifecycle scripts disabled
- build phase with network disabled
- resource-limited runtime container
- dynamically allocated localhost preview port
- explicit runtime lifecycle and cleanup
- Studio controls to start/stop and open the live preview

## Runtime lifecycle

```text
Approved Website Specification
        ↓
CAP-005 Generation
        ↓
CAP-006 Validation
        ↓
CAP-007 Build Contract
        ↓
CAP-008 Isolated Build
        ↓
CAP-009 Disposable Runtime
        ├── install dependencies
        ├── build with network disabled
        └── start `next start` in isolated container
                ↓
        localhost live preview
                ↓
             stop/cleanup
```

## Security boundary

The AWE host process never imports or executes generated website code. The runtime is launched as a separate Docker container with CPU, memory and PID limits, a read-only container root filesystem and an ephemeral writable project workspace.

The build phase remains network-disabled. The live runtime uses Docker bridge networking because it must accept browser traffic through the published localhost port. This is an intentional MVP trade-off: the preview runtime is local/developer-facing, not yet a production multi-tenant execution substrate.

Production hardening should add explicit egress control and stronger isolation before exposing generated runtimes to untrusted external users.

## Why this technology now

Docker remains the smallest practical substrate that lets AWE demonstrate a real generated-site runtime while keeping the host process isolated. Kubernetes Jobs and microVMs remain deferred until there is evidence of multi-tenant scale or stronger isolation requirements.

## What CAP-009 does not yet do

- public internet preview URLs;
- production multi-tenant isolation;
- persistent preview sessions across API restarts;
- arbitrary npm dependencies;
- browser automation or visual regression;
- deployment to a hosting provider;
- production-grade runtime egress policy.

## Acceptance criteria

- Only a generated artifact that passes the existing build plan can start a runtime.
- Generated code is executed only inside Docker.
- The build phase has no network access.
- Runtime resources are bounded.
- Preview uses an ephemeral workspace and disposable container.
- Studio can open and stop the live preview.
- Tests do not require Docker to pass.
- `pnpm lint && pnpm build && pnpm test` remains green.

## Technology decision

**ADR-0007: Disposable Docker runtime for local live preview.**

The decision is deliberately narrower than production deployment: prove the end-to-end generation → build → runtime path first, then select a production execution/deployment substrate from actual scale and threat-model evidence.
