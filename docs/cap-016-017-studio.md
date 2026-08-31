# CAP-016 + CAP-017 — End-to-End Executable Flow & Website Quality Baseline

**Status:** Combined implementation candidate

## Why combine CAP-016 and CAP-017

CAP-016 is the product-flow problem: move from generated artifact to an executable, validated website without forcing the user through backend-oriented steps.

CAP-017 is the output-quality problem: make the generated website visibly reflect the approved Strategy and Brand & Design Direction rather than producing only a technical skeleton.

They are intentionally shipped together because neither provides a convincing MVP alone. A fast build of an unconvincing site is not enough; a polished generated site that still requires manual backend operations is not enough either.

## Product outcome

The intended MVP path is now:

`Discovery → Strategy → Design → Specification → Generation → Build & Validation → Preview → Deployment`

From Studio, the user can use **Build & Preview Website** after generation. Studio plans the build, executes it through the existing isolated Docker boundary, validates the generated artifact, and then opens the Preview stage.

## CAP-016 implementation

- Added a Studio orchestration action for build → validation → preview.
- Reuses the existing CAP-015 build-plan and execution endpoints.
- Keeps generated code outside the Studio/API process.
- Stops on failed build or failed validation and surfaces diagnostics.
- Does not introduce a new queue, worker fleet, hosted build provider or orchestration platform.

### Deliberately deferred

- Streaming build logs
- Build cancellation
- Hosted/scalable workers
- Artifact registry
- Authentication and multi-tenancy

Those are scale/productization concerns rather than prerequisites for proving the MVP loop.

## CAP-017 implementation

The deterministic generator now consumes approved strategy/design data to produce a stronger Next.js baseline:

- responsive layout foundation;
- semantic navigation;
- strategy positioning carried into page content;
- design-derived visual tokens;
- accessible focus treatment;
- mobile breakpoint behavior;
- page metadata/title and description;
- clearer typography hierarchy;
- reusable card/section treatment;
- traceability checks back to the approved Strategy and Design versions.

The generator remains deterministic. AI-generated arbitrary source code is deliberately deferred until the execution contract is sufficiently mature.

## Technology decision

No new technology was added.

Next.js App Router remains the single supported generated framework because it is already the project baseline, has a straightforward build/start lifecycle, and keeps the MVP implementation narrow.

Docker remains the execution boundary because CAP-015 already established the isolated build contract.

The Studio remains a Next.js client and the API remains the capability boundary.

## Validation

Run:

```bash
pnpm install
pnpm lint && pnpm build && pnpm test
```

The release is green only when all three gates pass.
