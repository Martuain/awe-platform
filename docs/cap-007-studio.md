# CAP-007 — Isolated Build & Runtime Contract v0.7.0

## Objective

Establish the security and lifecycle boundary between AWE and generated
websites before AWE executes any generated code.

## What this capability adds

- `POST /api/v1/website-build/plan`
- A deterministic `WebsiteBuildPlan` artifact
- Explicit sandbox requirement
- Ephemeral-workspace strategy
- Allowlisted runtime commands (`next build`, `next start`)
- Network access disabled by default
- Diagnostics for incomplete generated artifacts
- API test proving that CAP-007 plans execution without executing generated code

## Important security decision

CAP-007 does **not** execute generated JavaScript, install generated
dependencies, or run arbitrary package scripts inside the AWE API or Studio
process.

That is intentional.

A real execution adapter must provide an OS/container/VM-level isolation
boundary, resource limits, timeout enforcement, filesystem isolation,
network policy and process cleanup.

CAP-007 therefore establishes the contract first. A later implementation can
back the contract with Docker, a dedicated sandbox service, Firecracker,
Kubernetes or another isolated execution substrate without changing Studio's
API contract.

## Lifecycle

```text
CAP-005 Generation
      ↓
CAP-006 Validation
      ↓
CAP-007 Build Plan
      ↓
[future sandbox adapter]
      ↓
Build
      ↓
Runtime
      ↓
Live Preview
```

## Acceptance criteria

- A generation artifact is required.
- The generated artifact must contain `package.json`.
- The generated artifact must contain a Next.js App Router file.
- No generated code is executed by the API.
- Build commands are explicitly allowlisted.
- Network access is disabled by default.
- The plan is deterministic and testable.

## Next step

CAP-008 should implement the first real isolated execution adapter and
produce a disposable preview runtime while preserving the CAP-007 security
contract.
