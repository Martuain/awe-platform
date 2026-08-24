# CAP-008 — Isolated Build Execution v0.8.0

## Objective

Turn the CAP-007 build-plan contract into a real, disposable execution boundary without allowing generated website code to run inside the AWE API or Studio process.

## What CAP-008 adds

- `POST /api/v1/website-build/execute`
- Docker-backed ephemeral workspaces
- CPU, memory and PID limits
- Read-only container root filesystem with a writable ephemeral workspace and `/tmp`
- dependency allowlist for the current supported Next.js runtime
- dependency installation with `--ignore-scripts`
- network-enabled dependency acquisition only
- build execution with `--network none`
- execution timeout
- bounded stdout/stderr returned as a diagnostic artifact
- deterministic rejection of unsupported dependencies

## Security model

CAP-008 deliberately separates **dependency acquisition** from **generated-code execution**. The acquisition phase is constrained to the approved runtime dependencies and disables npm lifecycle scripts. The actual `next build` phase runs with Docker networking disabled.

The generated workspace is never mounted outside the temporary project directory, and the container receives no host filesystem mount other than that workspace. The container runs with a read-only root filesystem, explicit resource limits and a disposable lifecycle.

This is an MVP execution boundary, not a claim of perfect sandbox security. A production multi-tenant deployment should consider a stronger isolation substrate such as Firecracker microVMs or a dedicated sandbox service after threat-model validation.

## Why Docker now

Docker is selected for CAP-008 because it is available across local development and CI environments, has a mature container execution model, provides practical filesystem/network/resource controls, and lets AWE prove the execution contract without introducing Kubernetes or microVM infrastructure prematurely.

Docker is therefore an implementation choice for the current evidence stage, not a permanent platform commitment.

### Alternatives considered

| Technology | Decision | Reason |
|---|---|---|
| Docker | **Selected now** | Smallest practical isolated execution boundary; reproducible locally and in CI |
| Kubernetes jobs | Deferred | Strong production orchestration, but unnecessary operational complexity for the current single-runtime proof |
| Firecracker microVM | Deferred | Stronger isolation potential, but higher implementation/operations complexity and weaker local simplicity |
| Host subprocess | Rejected | Does not provide an adequate security boundary for untrusted generated code |
| Full browser-only preview | Deferred | Useful for UI preview but does not prove that generated projects actually build |

## Current runtime constraints

- Supported framework: Next.js App Router
- Supported runtime: Node.js 22 Alpine container
- Supported dependencies: `next@15.5.21`, `react@19.1.9`, `react-dom@19.1.9`
- Build command: `npm run build`
- Network during build: disabled
- Default timeout: 120 seconds
- CPU: 1 core
- Memory: 768 MB
- PIDs: 128

The dependency allowlist is intentionally narrow. Expanding it requires an explicit architecture/security decision rather than silently accepting arbitrary packages from generated `package.json`.

## Lifecycle

```text
Approved Website Specification
        ↓
CAP-005 Website Generation
        ↓
CAP-006 Validation
        ↓
CAP-007 Build Plan
        ↓
CAP-008 Docker sandbox
        ├── constrained dependency acquisition
        └── network-disabled build
                ↓
        Build Result
                ↓
       [next: disposable runtime — next increment]
```

## What CAP-008 does not yet do

- expose a public live-preview URL;
- maintain a long-lived preview process;
- provide browser automation;
- support arbitrary npm packages;
- provide production-grade tenant isolation;
- persist build logs/artifacts;
- deploy the generated site.

These are deliberately separate concerns.

## Acceptance criteria

- CAP-007 planning remains backward compatible.
- Unsupported dependencies are rejected before execution.
- Generated build code is not executed in the AWE host process.
- Build runs in Docker with network disabled.
- Resource limits and timeout are enforced.
- Temporary workspace is cleaned up after execution.
- Tests cover the security contract without requiring Docker on the developer machine.
- `pnpm lint && pnpm build && pnpm test` remains green.

## Technology decision

**ADR-0006: Docker-backed disposable execution for CAP-008.**

The decision follows the project's evidence-driven rule: use the smallest infrastructure that proves the capability while keeping a clear migration path to stronger isolation if production threat modelling requires it.
