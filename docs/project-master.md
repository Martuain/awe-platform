## Current product status

- CAP-001 Business Discovery: implemented and evaluated.
- CAP-002 Website Strategy: implemented with human approval.
- CAP-003 Brand & Design Direction: implemented with Studio review and approval.
- CAP-004 Website Specification: implemented with Studio review and approval.
- CAP-005 Website Generation: implemented with deterministic Next.js App Router generation.
- CAP-006 Preview & Validation: implemented with deterministic artifact validation and safe browser preview.
- CAP-007 Isolated Build & Runtime Contract: implemented with an explicit execution boundary and disposable local runtime; hosted/scalable execution remains post-MVP.

# AWE Platform / AWE Studio --- Master Project Record

**Genesis baseline:** v1.0.3 --- release candidate\
**Current milestone:** CAP-025 --- Security & Access Boundary\
**Status:** Living master document

### Latest Discovery hardening

CAP-001 Discovery v1.1 addresses the first real end-to-end Studio issue found
during MVP validation: the Discovery loop could repeatedly ask for the
primary business goal even when the user had already supplied it in natural
language.

The deterministic mock gateway now extracts evidence from natural-language
goal statements, accumulates knowledge across turns, retains previously
captured goals, and captures audience/value-proposition information when
explicitly supplied. Open questions are derived from the minimum required
Discovery fields rather than a hard-coded prompt.

For the MVP gate, **industry + at least one business goal** remain the minimum
required fields. Audience and value proposition are useful evidence but do
not block approval when unavailable.

The API regression suite validates these behaviors and the existing full
suite passes locally in the validation environment.

### Latest project lifecycle hardening

CAP-014 duplication deliberately creates a clean project identity without copying
Discovery or downstream capability artifacts. Studio now closes the resulting
lifecycle gap by calling an idempotent `ensureDiscovery(projectId)` boundary on
create, restore and project switch. The Discovery message endpoint remains
strict and the composer is hidden until a Discovery context exists.

The duplicate-project regression covers the complete API contract: a duplicate
starts without a Discovery context, can initialize an independent session, and
can then accept its first Discovery message.

## Current post-v1.0.3 Studio workflow increment

The v1.0.3 release remains frozen. The next Studio increment completes the
project workspace loop at the UI boundary:

- project selection is available even when no project is currently selected;
- a new project can be started without manually clearing browser state;
- projects can be duplicated into an independent clean workspace;
- projects can be archived and restored through the existing lifecycle API;
- archived projects remain visible for recovery but their capability pipeline
  is disabled until restored;
- active-project selection continues to initialize Discovery idempotently.

This increment builds on CAP-012/CAP-013/CAP-014 rather than introducing a new
persistence model or capability contract.

## Master-document change-control rule

The Project Master is the authoritative cumulative record of the repository's evolution. Every capability package must update this document before the package is considered complete. The record must cover, for each increment, the baseline, additions, modifications, fixes, removals/deprecations, files or boundaries materially affected, API/data/configuration changes, architectural decisions and trade-offs, verification performed, known limitations, deferred work, and release/tag status.

A capability-specific document may contain detailed design notes, but it does not replace the Project Master. The Project Master records the cumulative product and engineering state and the reason for each material transition.

**Release discipline:** `v1.0.3` is frozen. Subsequent CAP-009, CAP-019 and CAP-020 work is unreleased working history unless explicitly tagged later. No capability package may move or rewrite the frozen tag.

## Current working baseline

The current unreleased working baseline is the cumulative sequence:

```text
v1.0.3 frozen
    ↓
CAP-009 Preview Runtime Responsiveness
    ↓
CAP-019 Studio Generation Loop + Deployment Lifecycle
    ↓
CAP-020 Production Model Adapter
    ↓
CAP-021 Migration Hardening
    ↓
CAP-022 + CAP-023 Deployment Operations
    ↓
CAP-024 Hosted/Scalable Execution & Production Deployment Boundary
    ↓
CAP-025 Security & Access Boundary
```

All increments after v1.0.3 are working history unless explicitly tagged later. The repository must not imply that hosted execution, cloud deployment, or production SaaS readiness is complete merely because provider-neutral boundaries exist.

## Capability package audit records

### CAP-009 — Preview Runtime Responsiveness

- **Baseline:** v1.0.3 working source after the first Preview UX implementation.
- **Added:** asynchronous execution boundary for disposable preview work; reuse of a healthy runtime for the same project/generation; Studio start/stop state handling and live preview controls.
- **Changed:** preview Docker/npm install/build/stop operations no longer occupy the FastAPI event loop; preview start behavior became idempotent for an existing healthy runtime.
- **Fixed:** repeated Start Live Preview actions no longer needlessly create duplicate runtimes; the apparent Studio hang caused by synchronous Docker/npm work in an async endpoint was removed.
- **Removed / deliberately avoided:** no external hosting dependency; no unsafe direct filesystem serving; no claim that a preview runtime is a production deployment.
- **Affected boundaries:** `apps/api/app/services/preview.py`, preview route, Studio Preview stage, preview tests and CAP-009 documentation.
- **Verification:** preview endpoint/runtime behavior was exercised against a real generated Next.js site; runtime returned HTTP 200 and generated HTML; regression coverage retained.
- **Deferred:** durable hosted preview workers, cloud runtime orchestration and production-grade runtime health management.
- **Release status:** unreleased; v1.0.3 untouched.

### CAP-019 — Studio Generation Loop + Deployment Lifecycle

- **Baseline:** CAP-009 preview-capable Studio and provider-neutral deployment API.
- **Added:** explicit Studio Build and Deployment stages; build-plan visibility; isolated build execution diagnostics; validation gate; deployment history; versioned deployment lifecycle; deployment supersession and failure persistence.
- **Changed:** Studio navigation became Generation → Build Plan → Isolated Build → Validation → Preview → Deployment; deployment calls use canonical `/api/v1/deployments` routes; deployment requires a validated generation.
- **Fixed:** incorrect preview/deployment ternary rendering, successful build incorrectly jumping directly to Preview, and deployment history not being restored on project load.
- **Removed / deliberately avoided:** no direct cloud provider coupling; no deployment before validation.
- **Affected boundaries:** Studio pipeline, build/deployment routes and services, deployment persistence, CAP-019 docs/roadmap/changelog.
- **Verification:** Studio lint/build passed; API regression passed; Docker Studio image built and served HTTP 200; deployment lifecycle regression covered versioning, supersession and failures.
- **Deferred:** production cloud deployment, durable workers, artifact registry and autoscaling.
- **Release status:** unreleased; v1.0.3 untouched.

### CAP-020 — Production Model Adapter

- **Baseline:** deterministic model gateway and CAP-019 pipeline.
- **Added:** OpenAI-compatible HTTP model adapter; environment-driven provider/name/base-URL/timeout selection; provider-specific failure normalization.
- **Changed:** model gateway can opt into a real HTTP provider while deterministic mock behavior remains the default for reproducible local development/tests.
- **Fixed / hardened:** missing credentials, unsupported provider, timeout/network failure, provider HTTP error and malformed/empty model responses receive explicit handling.
- **Removed / deliberately avoided:** no provider API key embedded in source, generated artifacts or documentation; no mandatory external provider; no vendor-specific domain model contract.
- **Affected boundaries:** model gateway, discovery integration, configuration documentation, provider tests.
- **Verification:** API regression passed including provider adapter tests; deterministic default retained.
- **Deferred:** provider fleet management, model routing policy, spend controls and hosted inference infrastructure.
- **Release status:** unreleased; v1.0.3 untouched.

### CAP-021 — Migration Hardening

- **Baseline:** SQLAlchemy persistence with Alembic introduced as the authoritative schema lifecycle.
- **Added:** initial migration revision/configuration and migration regression coverage.
- **Changed:** API startup now runs `alembic upgrade head` in a worker thread rather than directly invoking SQLAlchemy `create_all()`.
- **Fixed / hardened:** schema initialization now has an explicit versioned migration boundary and startup does not block the async event loop with migration work.
- **Removed / deliberately avoided:** direct runtime schema creation as the production lifecycle; no claim that downgrade is universally safe for destructive future migrations.
- **Affected boundaries:** `apps/api/alembic`, API startup/database initialization, migration tests and docs.
- **Verification:** 55 API tests passed at package acceptance.
- **Deferred:** zero-downtime migration orchestration, production migration approval workflow and complex data backfills.
- **Release status:** unreleased; v1.0.3 untouched.

### CAP-022 + CAP-023 — Deployment Operations

- **Baseline:** CAP-021 migration-hardened deployment workflow.
- **Added:** generated-artifact performance budget checks; Studio performance reporting; API monitoring summary; Studio monitoring surface.
- **Changed:** operational state is visible without requiring an external observability vendor.
- **Fixed / hardened:** performance and monitoring became explicit contracts instead of implicit assumptions about production readiness.
- **Removed / deliberately avoided:** no fake Lighthouse/Core Web Vitals measurements; no external telemetry claims; no mandatory alerting vendor.
- **Affected boundaries:** performance/monitoring API routes, Studio operations UI, regression suite and documentation.
- **Verification:** 58 API tests passed, including the new operational checks.
- **Deferred:** browser Core Web Vitals, external metrics/alerting and hosted observability.
- **Release status:** unreleased; v1.0.3 untouched.

### CAP-024 — Hosted/Scalable Execution & Production Deployment Boundary

- **Baseline:** local Docker execution and deterministic local deployment provider.
- **Added:** provider-neutral build execution interface; opt-in hosted HTTP build adapter; provider-neutral deployment selection; opt-in hosted HTTP deployment adapter.
- **Changed:** execution/deployment providers can be selected without changing capability contracts; local Docker remains the default.
- **Fixed / hardened:** provider failures are explicit and do not silently fall back to local execution, preventing hidden production behavior.
- **Removed / deliberately avoided:** no cloud vendor lock-in; no invented cloud infrastructure; no claim of an actual worker fleet or autoscaling implementation.
- **Affected boundaries:** execution/deployment services, configuration, provider tests and CAP-024 docs.
- **Verification:** 62 API tests passed, including hosted adapter boundary tests.
- **Deferred:** durable queue, production worker fleet, artifact registry, autoscaling, zero-downtime orchestration and concrete cloud provider integration.
- **Release status:** unreleased; v1.0.3 untouched.

### CAP-025 — Security & Access Boundary

- **Baseline:** CAP-024 with authentication/authorization and multi-tenant ownership still incomplete.
- **Added:** explicit development/strict authentication modes; database-backed users and bearer sessions; salted scrypt password hashing; opaque `awe_` API keys; API-key scopes/revocation/last-used metadata; project ownership; authentication middleware; server-side project authorization; auth endpoints; ADR-0018.
- **Changed:** project creation assigns the authenticated owner; project listing/monitoring are owner-scoped; project resources and deployments require server-side ownership checks; programmatic clients are constrained by scopes.
- **Fixed / hardened:** cross-owner project access by UUID manipulation; unrestricted API-key behavior; plaintext API-key persistence; unauthenticated access in strict mode.
- **Removed / deliberately avoided:** no external identity vendor, no plaintext credentials, no assumption that development mode is production authentication, no team/collaboration/billing model in this increment.
- **Affected boundaries:** `apps/api/app/security.py`, `middleware.py`, auth routes, project model/repository, migration `0002_auth_security`, tests, roadmap, changelog and ADR-0018.
- **Data changes:** `projects.owner_id`; `users`; `auth_sessions`; `api_keys`.
- **API changes:** `/api/v1/auth/register`, `/login`, `/me`, `/api-keys`, `/api-keys/{id}/revoke`; project endpoints now require authenticated ownership in the main application.
- **Configuration:** `AWE_AUTH_MODE=development|strict`; `AWE_SESSION_TTL_HOURS`; strict mode requires persistent authentication storage.
- **Verification:** 69 API tests passed, including security-specific negative authorization and scope tests. Docker/Studio full-stack verification was not available in the packaging environment and remains a local deployment acceptance step.
- **Known limitations:** account recovery/email verification, OIDC/SAML/SSO, team roles, invitations, dedicated API-key rotation and ownership review for pre-existing production data remain incomplete.
- **Release status:** unreleased; v1.0.3 untouched.

## 1. Executive status

AWE is being developed as an AI-powered platform for automated website
creation for SMBs. The ambition is not to become another
prompt-to-website wrapper, but to make website creation substantially
easier by understanding the business before building the website.

**AWE Framework** is the underlying runtime, capability, context,
evaluation, API and orchestration architecture.

**AWE Studio** is the user-facing product built on that framework.

This distinction is mandatory.

Genesis v1.0.3 is the current release candidate after the repository MVP gate and Discovery lifecycle hardening.
CAP-001 is the first capability to exercise the architecture through a
real end-to-end vertical slice.

------------------------------------------------------------------------

## 2. Origin

The original problem was that SMBs and entrepreneurs face coding
complexity, agency costs, long delivery cycles, high iteration cost and
vendor lock-in when creating websites.

The original product hypothesis was an AI/no-code SaaS platform that
transformed high-level user input into production-ready websites.

The original MVP focused on e-commerce catalog websites and envisioned
specialized agents for layout, content, design, e-commerce and code
generation.

The original technical direction included FastAPI, Pydantic, SQLAlchemy,
Alembic, PostgreSQL, Redis, Next.js, React, TypeScript, TailwindCSS,
Docker, GitHub Actions and provider-agnostic LLM integration.

------------------------------------------------------------------------

## 3. Innovation-thinking evolution

The project evolved through:

**Observe → Define → Ideate → Select → Prototype → Test → Learn →
Iterate**

### Observe

The market already contains many AI website builders. Therefore "AI
generates websites" is not enough to differentiate AWE.

### Define

The stronger problem became:

> Existing tools optimize for immediate generation; AWE should optimize
> for understanding, alignment, quality and iterative improvement.

### Ideate

The system should progressively understand the business rather than
force the user to provide a complete specification.

### Select

The chosen product loop became:

``` text
User
 ↓
Understand
 ↓
Identify gaps
 ↓
Ask / infer
 ↓
Structure
 ↓
Evaluate
 ↓
User review
 ↓
Revise
 ↓
Approve
 ↓
Next capability
```

### Why this direction

It improves ease of use, quality, consistency, trust, iteration,
extensibility and potentially cost.

------------------------------------------------------------------------

## 4. Alternatives rejected

### Generic prompt-to-site

Rejected as the core thesis because it is crowded, easy to commoditize
and weakly differentiated.

### Form-heavy wizard

Rejected because it forces users to understand requirements before the
system does.

### Fully autonomous website agent

Rejected for the initial architecture because business assumptions need
transparency and validation.

### Multi-agent swarm from day one

Rejected for CAP-001 because it introduces orchestration complexity
before the core capability model is proven.

### Complete Context Engine first

Rejected because the project should exercise abstractions through real
capabilities before building every theoretical layer.

------------------------------------------------------------------------

## 5. Product thesis

The project moved from:

> Can AI generate websites?

to:

> Can AI make website creation dramatically easier?

and finally to:

> Can an AI platform understand an SMB's business, collaborate with its
> owner, establish trustworthy context, make complex website decisions
> progressively, and execute those decisions through reusable
> capabilities at a cost and level of simplicity that makes
> professional-quality websites accessible to ordinary businesses?

That is the current product thesis.

------------------------------------------------------------------------

## 6. AWE Framework vs AWE Studio

### AWE Framework

Provides:

-   capability contracts;
-   context management;
-   AI runtime;
-   prompt execution;
-   model abstraction;
-   evaluation;
-   artifact management;
-   provenance;
-   orchestration;
-   persistence;
-   API contracts.

### AWE Studio

Provides:

-   project creation;
-   guided discovery;
-   visual interaction;
-   website strategy;
-   website creation;
-   preview;
-   editing;
-   publishing.

Relationship:

``` text
AWE Studio
    ↓
AWE API
    ↓
AWE Framework
    ├── Context
    ├── Runtime
    ├── Evaluation
    └── Capabilities
```

------------------------------------------------------------------------

## 7. API-first decision

AWE is API-first.

Studio is a client of AWE capabilities, not the location where
capability business logic lives.

Reasons:

1.  Reusability.
2.  Clean boundaries.
3.  Future integrations.
4.  Independent evolution of Studio.
5.  Potential partner/developer access.
6.  Testability.

------------------------------------------------------------------------

## 8. Open-source-first decision

The project prefers mature open-source technology wherever practical.

This applies to frameworks, databases, infrastructure, testing,
observability, orchestration and developer tooling.

Commercial model providers remain replaceable behind an abstraction.

------------------------------------------------------------------------

## 9. Provider-agnostic runtime

The runtime should depend on an abstraction such as:

``` text
LLMProvider
 ├── complete()
 ├── count_tokens()
 └── get_pricing()
```

The project originally contemplated OpenAI and Anthropic and a unified
provider abstraction.

The stronger current rule is:

> The capability contract belongs to AWE; the model provider is an
> implementation detail.

This enables model substitution, cost optimization, mock testing and
future open-weight models.

------------------------------------------------------------------------

## 10. Capability model

A capability is the primary product abstraction.

``` text
Capability
 ├── Input contract
 ├── Context
 ├── Runtime / Agent
 ├── Prompt
 ├── Tools
 ├── Artifact
 ├── Evaluation
 ├── Human checkpoint
 └── Persistence
```

An **agent** describes how AI performs work.

A **capability** describes what the product can do.

One capability may use one agent today and multiple agents or
deterministic functions later.

------------------------------------------------------------------------

## 11. Context and provenance

Context is a first-class reusable asset.

Important information should distinguish:

``` text
KNOWN
INFERRED
ASSUMED
UNKNOWN
USER-APPROVED
USER-REJECTED
```

Important values should eventually carry provenance, confidence and
approval state.

Example:

``` json
{
  "value": "Early-stage SaaS founders",
  "source": "agent_inference",
  "confidence": 0.78,
  "approved": false
}
```

versus user-confirmed information.

This is a central part of the AWE trust model.

------------------------------------------------------------------------

## 12. Human-in-the-loop

AWE is not designed around eliminating humans from meaningful business
decisions.

The principle is:

> AI executes reasoning and synthesis; humans validate consequential
> business decisions.

The interaction is:

``` text
AI proposes
 ↓
User reviews
 ↓
User corrects or approves
 ↓
Artifact becomes authoritative
```

------------------------------------------------------------------------

## 13. Genesis baseline

Genesis established the initial AWE monorepo/Turborepo foundation,
including packages such as:

-   `@awe/capability-sdk`
-   `@awe/context-engine`
-   `@awe/evaluation`
-   `@awe/knowledge-engine`
-   `@awe/plugin-sdk`
-   `@awe/prompt-runtime`
-   `@awe/shared`
-   `@awe/studio`

The Studio application is part of this architecture.

### Genesis CI lessons

The repository went through several CI stabilization issues:

1.  Missing TypeScript type dependencies (`@types/react`,
    `@types/node`).
2.  Missing committed `pnpm-lock.yaml`.
3.  Duplicate pnpm version declarations between GitHub Actions and
    `package.json`.
4.  Node 20 deprecation warnings on GitHub-hosted runners.

The first three caused actual workflow problems and were corrected. The
Node warning was not treated as the root cause.

Once CI passed, Genesis was tagged:

``` text
v0.1.1
```

This baseline is immutable.

### Engineering environment and configuration baseline

The repository subsequently went through a local environment/tooling
stabilization cycle covering ESLint flat configuration, pnpm workspace
installation state, Python runtime selection, pytest execution and Turbo
task output configuration. The final known-good state is documented in the
following engineering baseline:

[Environment & Configuration Baseline](environment-configuration-baseline.md)

This document records the problems encountered, the diagnostic evidence,
the successful recovery steps, the rationale for ESLint/pnpm/Turborepo, the
validated toolchain versions, and the remaining non-blocking improvements.
It should be treated as the technical reference for environment/tooling
issues rather than repeated in this master record.

------------------------------------------------------------------------

# 14. CAP-001 --- Business Discovery

CAP-001 is the first real AWE capability.

Its purpose:

> Transform an unstructured business description into a structured,
> traceable, evaluated and user-approved Business Brief.

This capability was selected because it tests the most important product
thesis:

> AWE can understand before it builds.

------------------------------------------------------------------------

## 15. Why discovery comes first

A website depends on business understanding.

``` text
Wrong business understanding
 ↓
Wrong audience
 ↓
Wrong positioning
 ↓
Wrong content
 ↓
Wrong UX
 ↓
Wrong website
```

Therefore the preferred sequence is:

``` text
Business Discovery
 ↓
Business Brief
 ↓
Website Strategy
 ↓
Design
 ↓
Content
 ↓
Implementation
 ↓
Deployment
```

------------------------------------------------------------------------

## CAP-004 --- Website Specification

CAP-004 translates the approved Strategy and approved Brand & Design Direction into an implementation-ready Website Specification.

The artifact is intentionally not generated code. It defines the deterministic contract that the future generation capability must satisfy.

### Inputs

```text
Approved Discovery
      ↓
Approved Strategy
      ↓
Approved Design Direction
```

### Outputs

- page-level objectives;
- required sections;
- content requirements;
- component requirements;
- global components;
- SEO requirements;
- accessibility requirements;
- responsive requirements;
- technical requirements;
- acceptance criteria;
- provenance through source strategy/design versions.

The Studio exposes the specification as a reviewable artifact and requires explicit human approval before the next generation stage.

Detailed implementation reference: [CAP-004 Studio experience](cap-004-studio.md).

## 16.1 CAP-002 Studio experience

The Studio now exposes the first coherent Discovery → Strategy product flow. After Business Discovery is explicitly approved, the user can generate a Website Strategy, inspect its evaluation dimensions, request a revision, and approve the resulting strategy before CAP-003.

Detailed implementation reference: [CAP-002 Studio experience](cap-002-studio.md).

## 16. CAP-001 experience

A user can start naturally:

> "I run a small architecture studio in Madrid. We mainly work with
> residential renovations and want a website that generates qualified
> enquiries from homeowners."

AWE extracts what is known and identifies what remains uncertain.

It should ask only questions that materially affect the outcome.

Question priority is:

``` text
Business impact
×
Uncertainty
×
Downstream dependency
```

This directly supports the ease-of-use objective.

------------------------------------------------------------------------

## 17. Business Brief

Initial structure:

``` text
Business
Audience
Offering
Positioning
Goals
Brand
Constraints
Assumptions
Open Questions
```

Conceptually:

``` json
{
  "business": {},
  "audience": {},
  "offering": {},
  "positioning": {},
  "goals": {},
  "brand": {},
  "constraints": [],
  "assumptions": [],
  "open_questions": []
}
```

The artifact is versioned.

Example:

``` text
Business Brief v1
 ↓
User correction
 ↓
Business Brief v2
 ↓
Evaluation
 ↓
Approval
```

------------------------------------------------------------------------

## 18. Discovery session states

Initial lifecycle:

``` text
ACTIVE
 ↓
DISCOVERING
 ↓
READY_FOR_REVIEW
 ↓
REVISION_REQUIRED
 ↓
READY_FOR_REVIEW
 ↓
APPROVED
```

The state model is intentionally small.

------------------------------------------------------------------------

## 19. Discovery AI loop

``` text
User input
 ↓
Read context
 ↓
Interpret
 ↓
Identify gaps
 ↓
Ask or draft
 ↓
User response
 ↓
Update context
 ↓
Generate artifact
 ↓
Evaluate
 ↓
User review
 ↓
Revise or approve
```

The loop is bounded and purposeful.

It is not an uncontrolled autonomous recursion.

------------------------------------------------------------------------

## 20. Discovery Agent responsibilities

The Discovery Agent:

1.  interprets input;
2.  extracts facts;
3.  identifies gaps;
4.  detects contradictions;
5.  makes labelled inferences;
6.  asks high-value questions;
7.  proposes Business Brief changes;
8.  incorporates corrections;
9.  preserves approved decisions;
10. exposes important assumptions.

It does not own website code, visual design, deployment or arbitrary
external actions.

------------------------------------------------------------------------

## 21. Evaluation

CAP-001 evaluates:

  Dimension             Question
  --------------------- --------------------------------------------
  Completeness          Is enough information known?
  Consistency           Are there contradictions?
  Provenance            Can important claims be traced?
  Confidence            Are important conclusions reliable enough?
  Business usefulness   Can downstream capabilities use the brief?

Evaluation does not replace user approval.

------------------------------------------------------------------------

## 22. API contract

Initial API concept:

``` http
POST /api/v1/projects/{project_id}/discovery
POST /api/v1/discovery/{session_id}/messages
GET  /api/v1/discovery/{session_id}
GET  /api/v1/discovery/{session_id}/brief
POST /api/v1/discovery/{session_id}/feedback
POST /api/v1/discovery/{session_id}/approve
```

Exact routing must be reconciled with the actual Genesis repository
before implementation.

------------------------------------------------------------------------

## 23. CAP-001 runtime

``` text
AWE Studio
    ↓
AWE API
    ↓
Business Discovery Capability
    ├── Context Engine
    ├── Prompt Runtime
    ├── Discovery Agent
    └── Evaluation
    ↓
Business Brief
    ↓
Persistence
```

Studio must not contain the core discovery logic.

------------------------------------------------------------------------

## 24. CAP-001 model testing

The first implementation should be testable without a live commercial
model.

``` text
Discovery Capability
       ↓
LLMProvider
       ├── Mock provider
       ├── Provider A
       └── Provider B
```

The mock provider allows deterministic unit and integration tests.

The real model becomes a provider implementation.

------------------------------------------------------------------------

## 25. CAP-001 implementation sequence

``` text
CAP-001.01  Inspect Genesis interfaces
CAP-001.02  Define domain types
CAP-001.03  Define BusinessBrief
CAP-001.04  Define provenance model
CAP-001.05  Define session state machine
CAP-001.06  Define DiscoveryAgent interface
CAP-001.07  Implement mock LLM provider
CAP-001.08  Implement Discovery capability
CAP-001.09  Implement evaluator
CAP-001.10  Implement persistence
CAP-001.11  Implement REST API
CAP-001.12  Add integration tests
CAP-001.13  Add end-to-end test
CAP-001.14  Connect Studio
CAP-001.15  Run CI
CAP-001.16  Freeze CAP-001 baseline
```

------------------------------------------------------------------------

## 26. CAP-001 acceptance scenario

Reference scenario:

User:

> "I run a boutique digital marketing agency in Madrid. We help
> restaurants increase bookings through Instagram and Google."

AWE identifies the agency, location, audience and outcome.

It asks focused questions about customer type and primary conversion.

The user answers.

AWE creates Business Brief v1.

The user adds:

> "Our real differentiator is that we only charge when bookings
> increase."

AWE produces Business Brief v2.

Evaluation runs again.

The user approves.

The approved artifact is persisted and retrievable through the API.

This is the canonical CAP-001 acceptance flow.

------------------------------------------------------------------------

## 27. Original architecture vs current architecture

### Original

``` text
User
 ↓
Website configuration
 ↓
Agent orchestration
 ↓
WebsiteState
 ↓
Layout
 ↓
Content
 ↓
Design
 ↓
E-commerce
 ↓
Code
 ↓
Deployment
```

### Current

``` text
User
 ↓
Business Discovery
 ↓
Business Context
 ↓
Approved Business Brief
 ↓
Website Strategy
 ↓
Design / Content / Build capabilities
 ↓
Quality
 ↓
Deployment
```

The major change is a change in the product's unit of intelligence.

------------------------------------------------------------------------

## 28. Original agent model vs current capability model

Original:

``` text
Agent = primary abstraction
```

Current:

``` text
Capability = primary product abstraction
Agent = implementation mechanism
```

This is one of the major architectural evolutions.

------------------------------------------------------------------------

## 29. Long-term capability roadmap (strategic baseline)

### CAP-001 --- Business Discovery

Understand the business.

### CAP-002 --- Website Strategy / Information Architecture

Generate sitemap, page objectives, information architecture and
conversion architecture.

### CAP-003 --- Brand & Design Direction

Generate visual identity and design tokens.

### CAP-004 --- Content Strategy & Generation

Generate content, CTAs and SEO structure.

### CAP-005 --- Website Composition

Compose the actual site.

### CAP-006 --- Code / Runtime Generation

Produce maintainable implementation.

### CAP-007 --- Quality Assurance

Evaluate accessibility, responsiveness, SEO, consistency, performance
and content quality.

### CAP-008 --- Deployment

Publish.

### CAP-009 --- Continuous Improvement (original strategic roadmap; not the implementation sequence)

Use feedback and analytics to improve the website.

------------------------------------------------------------------------

## 30. Product flywheel

``` text
Business understanding
 ↓
Better website
 ↓
User feedback
 ↓
Performance data
 ↓
Better context
 ↓
Better recommendations
 ↓
Better website
```

This is a potential long-term moat.

------------------------------------------------------------------------

## 31. Differentiation hypothesis

AWE's intended differentiation combines:

1.  Business-first AI.
2.  Progressive discovery.
3.  Structured context.
4.  Provenance.
5.  Human alignment.
6.  Capability architecture.
7.  Model independence.
8.  Low-friction UX.
9.  Cost-aware execution.
10. Open-source-first technology.

These are hypotheses to validate, not unsupported claims that AWE is
already market-leading.

------------------------------------------------------------------------

## 32. Cost philosophy

Cost is a product requirement.

The runtime should eventually understand:

``` text
capability
model
tokens
latency
cost
retries
user
project
```

This enables model routing, caching, cost budgets and use of cheaper
models for simpler tasks.

------------------------------------------------------------------------

## 33. Observability

The platform should eventually answer:

> What capability ran, with what context, using what model, producing
> what artifact, at what cost, with what evaluation result, and what did
> the user decide?

The original planning already included structured logs, correlation IDs,
agent execution metrics, token usage, cost, latency and failure
monitoring. The newer architecture extends these concepts from
agent-level to capability-level observability.

------------------------------------------------------------------------

## 34. Testing strategy

### Unit

Schemas, state transitions, capability logic, prompts and evaluators.

### Integration

API, context, runtime, persistence and mock model.

### End-to-end

Complete user/capability lifecycle.

### Real-model evaluation

Selective validation after deterministic tests pass.

This keeps the platform testable without making the whole suite
dependent on live model behavior.

------------------------------------------------------------------------

## 35. Security and trust

The system must not:

-   expose API keys;
-   represent AI assumptions as confirmed facts;
-   silently overwrite approved decisions;
-   execute arbitrary tools without defined permissions;
-   log credentials.

Future tool execution should use explicit permission boundaries.

------------------------------------------------------------------------

## 36. Governance

Every significant capability should have:

``` text
spec.md
plan.md
tasks.md
ADR-xxx.md
```

The master document records the historical reasoning and evolution.

The documentation should be updated during implementation, not
reconstructed at the end.

------------------------------------------------------------------------

## 37. What is frozen

Currently stable:

-   AWE Framework vs AWE Studio distinction.
-   Genesis v0.1.1.
-   API-first direction.
-   Capability-first architecture.
-   Provider-agnostic runtime.
-   Business Discovery as CAP-001.
-   Structured Business Brief.
-   Provenance/assumption distinction.
-   Evaluation before approval.
-   Human checkpoint.
-   No premature multi-agent swarm.
-   No premature complete Context Engine.
-   Open-source-first preference.
-   Model-provider abstraction.

------------------------------------------------------------------------

## 38. What remains flexible

Not permanently frozen:

-   exact API route naming;
-   exact persistence implementation;
-   exact LLM provider/model;
-   whether future capabilities use one or multiple agents;
-   orchestration implementation;
-   UI visual design;
-   deployment provider;
-   individual open-source component choices.

These can be changed through explicit ADRs when implementation evidence
warrants it.

------------------------------------------------------------------------

## 39. Historical MVP documents and reconciliation

The original `plan.md`, `spec.md` and `tasks.md` describe an AI-powered
website-builder SaaS MVP centered on e-commerce generation.

They contain valuable foundations such as:

-   FastAPI;
-   Next.js/React;
-   PostgreSQL;
-   Redis;
-   Docker;
-   GitHub Actions;
-   LLM abstraction;
-   `WebsiteState`;
-   `ExecutionContext`;
-   `AgentBase`;
-   `AgentExecution`;
-   REST/WebSocket APIs;
-   monitoring;
-   testing;
-   deployment.

However, those documents should be treated as the historical foundation
rather than silently overriding the newer AWE capability architecture.

The old e-commerce pipeline remains useful as a future implementation
target, but Business Discovery now precedes it.

------------------------------------------------------------------------

## 40. Current implementation rule

Before adding infrastructure:

> Does CAP-001 require it?

Before adding an abstraction:

> Has an actual capability demonstrated the need for it?

Before adding an agent:

> Is a separate agent necessary, or is this better represented as a
> capability operation?

This is the project's evidence-driven engineering rule.

------------------------------------------------------------------------

## 41. Master decision log

  --------------------------------------------------------------------------------------------
  ID                Decision                    Status            Rationale
  ----------------- --------------------------- ----------------- ----------------------------
  D-001             AI website creation for     Accepted          Core product problem
                    SMBs                                          

  D-002             Ease of use as product      Accepted          Non-technical target users
                    requirement                                   

  D-003             Low cost as product         Accepted          Competitive positioning
                    requirement                                   

  D-004             Differentiate beyond        Accepted          Crowded market
                    generic AI generation                         

  D-005             Business-first discovery    Accepted          Better downstream quality

  D-006             AWE Framework ≠ AWE Studio  Frozen            Architectural/product
                                                                  distinction

  D-007             Capability-first            Frozen            Product-level abstraction
                    architecture                                  

  D-008             API-first                   Frozen            Reusability and separation

  D-009             Model-provider abstraction  Frozen            Avoid vendor lock-in

  D-010             Open-source-first           Accepted          Cost/control/composability
                    preference                                    

  D-011             Human approval for          Frozen            Trust
                    consequential artifacts                       

  D-012             Provenance for important    Frozen            Transparency
                    information                                   

  D-013             No initial agent swarm      Frozen for        Avoid premature complexity
                                                CAP-001           

  D-014             No complete Context Engine  Frozen for        Evidence-driven design
                    before use                  CAP-001           

  D-015             Genesis v0.1.1 frozen       Frozen            Known-good baseline

  D-016             CAP-001 = Business          Frozen            First proving capability
                    Discovery                                     

  D-017             Mock/provider-independent   Accepted          Deterministic validation
                    testing                                       

  D-018             Versioned artifacts         Frozen for        Traceability
                                                CAP-001           
  --------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 42. Current project state

``` text
PRODUCT
AWE Studio
    ↓
FRAMEWORK
AWE Framework
    ↓
GENESIS
v0.1.1 — FROZEN / CI GREEN
    ↓
CAP-001
Business Discovery
    ├── Design: FROZEN
    ├── API: DEFINED
    ├── Runtime: DEFINED
    ├── Evaluation: DEFINED
    ├── Persistence: DEFINED
    └── Implementation: NEXT
```

------------------------------------------------------------------------

## 43. Immediate engineering action

The first source-level implementation task is:

**CAP-001.01 --- Inspect Genesis interfaces**

Review:

``` text
packages/capability-sdk
packages/context-engine
packages/evaluation
packages/prompt-runtime
packages/shared
apps/studio
```

Determine:

-   existing exports;
-   existing types;
-   existing API boundaries;
-   runtime contracts;
-   persistence strategy;
-   testing strategy.

Then implement CAP-001 inside those boundaries.

The current File Library contains the earlier `spec.md`, `plan.md` and
`tasks.md`, but not the complete current repository source tree.
Therefore source-level modifications should not be fabricated until the
exact Genesis repository is available for inspection.

------------------------------------------------------------------------

## 44. Living-document protocol

After every milestone:

1.  Implement.
2.  Test.
3.  Review.
4.  Record deviations.
5.  Update this document.
6.  Update the decision log.
7.  Update the roadmap.
8.  Tag the resulting baseline.
9.  Start the next capability.

------------------------------------------------------------------------

# Appendix --- Historical source record

The available historical project documents are:

-   `plan.md`
-   `spec.md`
-   `tasks.md`

The original `plan.md` described an AI-powered no-code website builder
focused initially on e-commerce catalog sites, with specialized layout,
content, design, code and e-commerce agents.

The original `spec.md` defined REST/WebSocket APIs, authentication,
project management, website generation, `WebsiteState`, `AgentBase`,
`ExecutionContext`, `LLMProvider`, agent execution records, design
systems, testing and monitoring.

The original `tasks.md` translated those concepts into implementation
tasks, including repository setup, PostgreSQL, FastAPI, authentication,
provider abstraction, context layer, project APIs, generation APIs,
agent implementation, WebSocket progress, monitoring, API documentation
and E2E testing.

These documents are retained as historical design evidence and
reconciled with the newer AWE capability architecture.

------------------------------------------------------------------------

# Final project principle

> **Build the smallest real capability that proves the architecture,
> document what we learn, and let evidence---not abstraction
> enthusiasm---drive the next layer of the platform.**

# CAP-001 Implementation Update — 2026-08-20

## Source baseline inspected

The supplied `awe-platform-genesis-v0.1.1(1).zip` is confirmed as the repository baseline. It contains the frozen Genesis architecture, CI workflow, ADRs and CAP-001 specification/plan/tasks.

The actual repository confirms that Genesis already established:

- FastAPI API skeleton;
- Next.js Studio skeleton;
- PostgreSQL/Redis Docker environment;
- capability SDK boundary;
- context engine boundary;
- evaluation boundary;
- knowledge engine boundary;
- provider-neutral `ModelGateway` boundary;
- API-first ADR;
- capability-driven ADR;
- open-source-first ADR;
- human-approval ADR;
- model-agnostic ADR;
- CAP-001 specification, implementation plan and task list.

## CAP-001 implementation decisions

### 1. Preserve Genesis boundaries

The implementation extends the existing API, context and runtime boundaries instead of introducing a second architecture.

### 2. Persistence

CAP-001 now has a repository abstraction with:

- `InMemoryRepository` for deterministic tests/local lightweight execution;
- `SqlAlchemyRepository` for the configured PostgreSQL runtime.

The PostgreSQL model introduces:

- `projects`;
- `discovery_sessions`;
- `context_versions`;
- `source_messages`.

### 3. Knowledge structure

The previous flat discovery context was replaced with structured Business Knowledge fields carrying:

- value;
- confidence;
- source references.

Unknown information remains represented as `null`/empty rather than being invented.

### 4. Lifecycle

CAP-001 now explicitly supports:

```text
collecting → awaiting_approval → approved
```

Approval is a separate API action and cannot occur while the capability is still incomplete.

### 5. AI boundary

A deterministic `MockModelGateway` was introduced first. This is intentional: CAP-001 can be tested without depending on a live model provider.

The existing `ModelGateway` concept remains the architectural boundary for future provider adapters.

### 6. Evaluation / completeness

The first vertical slice calculates a minimal completeness score from critical discovery information and produces an open question when required information is missing.

This is deliberately a minimal evaluator, not the final quality/evaluation framework.

### 7. Tests

A complete API lifecycle test was added covering:

```text
create project
→ start discovery
→ add partial information
→ add information completing the minimum context
→ reach awaiting_approval
→ explicitly approve
```

The API test passes locally with Python dependencies available.

## Validation limitation

The execution environment used for source inspection does not contain `pnpm`, so the JavaScript/Turborepo build could not be executed locally in this pass.

The repository retains the previously successful GitHub Actions configuration using Node 22 and pnpm 10. The next CI run is therefore required to validate the complete monorepo after these changes.

This is recorded as a validation limitation, not as a claim that CI is already green for the CAP-001 changes.

## Deviations from the original CAP-001 plan

The specification/plan calls for PostgreSQL, provider abstraction, structured output, confidence/evidence, the AI loop, approval and evaluation. The first implementation deliberately establishes these as a vertical slice rather than attempting every production-hardening detail at once.

Deferred from this implementation pass:

- Alembic migration history;
- real LiteLLM adapter;
- production structured-output enforcement against a live model;
- sophisticated completeness/consistency/unsupported-claim evaluators;
- Studio discovery UI;
- competitor/document ingestion;
- advanced observability.

These remain in the CAP-001 backlog and are not silently considered complete.

## New engineering rule confirmed

> Every CAP implementation should first establish a deterministic end-to-end vertical slice, then replace individual development/test doubles with production infrastructure behind the same contract.

This keeps the project aligned with the Constitution's `Simplicity Before Scale`, `Model Agnostic`, `Evaluation First` and `Traceability` principles.

# CAP-002 Implementation Update — 2026-08-20

## Scope

CAP-002 — Website Strategy is the next capability after approved Business Discovery.
Its purpose is to transform the approved Business Knowledge into a reviewable Website Strategy containing:

- initial sitemap;
- page objectives;
- conversion/CTA direction;
- content positioning and key messages;
- tone guidance;
- design principles;
- responsive and accessibility priorities;
- rationale and source context version.

## Architectural decision

CAP-002 consumes only **approved CAP-001 context**. It cannot generate a strategy from an unapproved discovery session.

This establishes the intended capability chain:

```text
CAP-001 Business Discovery
        ↓
Approved Business Knowledge
        ↓
CAP-002 Website Strategy
        ↓
Review
        ↓
Approval
```

## First vertical slice

The implementation establishes:

- `WebsiteStrategy` domain model;
- sitemap page model;
- content strategy model;
- design direction model;
- strategy lifecycle (`draft → ready_for_review → approved`);
- repository contract;
- in-memory persistence;
- PostgreSQL persistence row;
- API endpoints for generation, retrieval and approval;
- deterministic strategy generation service;
- end-to-end API test.

## Deliberate simplification

CAP-002 initially uses deterministic rules rather than a live model. This preserves the vertical-slice rule established in CAP-001 and keeps the capability testable independently of provider availability.

The production model adapter remains behind the existing provider boundary and will be introduced after the contract and evaluation behavior are proven.

## Initial strategy output

The first slice generates four foundational pages:

- Home;
- About;
- Services;
- Contact.

This is intentionally not presented as the final website information architecture. It is a minimal baseline that can later expand from actual business evidence.

## Acceptance behavior

The API test verifies:

```text
Project
  ↓
CAP-001 Discovery
  ↓
CAP-001 Approval
  ↓
CAP-002 Generate
  ↓
READY_FOR_REVIEW
  ↓
CAP-002 Approval
  ↓
APPROVED
```

It also verifies that CAP-002 cannot be generated without an existing discovery context and that generation is based on the approved context.

## Validation

Python compilation succeeded and the API test suite currently passes:

```text
2 passed
```

The full Turborepo/GitHub CI build remains the authoritative monorepo validation because this environment does not provide the complete pnpm execution environment.

## CAP-002 remaining backlog

The current slice is intentionally incomplete. Next hardening work includes:

- richer information architecture generation;
- explicit audience/persona mapping;
- page-to-goal traceability;
- content requirements per page;
- SEO intent and metadata strategy;
- stronger design-token direction;
- strategy evaluation;
- revision workflow;
- real model adapter;
- Studio strategy review UI;
- PostgreSQL migration management;
- immutable version history rather than single-row replacement;
- CAP-002 CI validation and baseline freeze.

## New decision

> CAP-002 must be derived from an approved Business Brief/Knowledge artifact and must remain independently reviewable before website generation begins.

This preserves the business-first principle and prevents later website-generation capabilities from bypassing the alignment checkpoint established by CAP-001.

## CAP-002 Hardening Cycle — 2026-08-20

The first CAP-002 vertical slice was hardened before advancing to CAP-003.

### Changes implemented

1. Added deterministic `StrategyEvaluation` with four dimensions:
   - completeness;
   - business alignment;
   - traceability to approved Discovery context;
   - actionability.
2. Approval now requires the evaluation to be ready.
3. Added explicit strategy revision API using user feedback.
4. Revisions increment strategy version and preserve prior versions in the in-memory repository.
5. Approved strategies cannot be revised.
6. PostgreSQL persistence now maintains the current strategy plus append-only strategy-version records.
7. Added an end-to-end test for generation, evaluation, revision, approval and post-approval immutability.

### Why these changes

The first slice proved that CAP-002 could consume approved CAP-001 context and produce a strategy. The hardening cycle addresses the next risk: allowing a strategy artifact to become authoritative without a repeatable quality gate or version history.

The decision is deliberately incremental. We did not introduce a full semantic evaluator, a model-based revision agent, or a complex workflow engine yet. The deterministic evaluator establishes the contract first; richer intelligence can be placed behind the same boundary once its behavior can be tested.

### Validation

Local API tests: `2 passed`.
Python compilation: successful.
Full GitHub CI/Turborepo validation remains required before the CAP-002 baseline can be frozen.

### New decision

> A strategy becomes approvable only after deterministic structural evaluation, and every revision creates a new version rather than mutating an existing artifact.

# CAP-003 implementation record

CAP-003 — Brand & Design Direction has entered implementation after CAP-002 was validated and frozen through GitHub CI.

The first vertical slice deliberately requires approved CAP-001 Business Discovery and approved CAP-002 Website Strategy. CAP-003 produces a versioned, reviewable Brand & Design Direction artifact containing brand attributes, visual principles, semantic color palette, typography direction, imagery guidance, component guidance, accessibility requirements, rationale and source strategy version.

Key decisions:
- Do not generate arbitrary visual design disconnected from approved strategy.
- Use semantic palette guidance until real brand assets exist.
- Treat accessibility and responsive behavior as first-class design requirements.
- Keep human approval before downstream website composition.
- Keep the approved artifact immutable.

Deferred intentionally: logo generation, exact brand-asset extraction, font procurement, final design-token package, visual editor, image-generation provider and pixel-level design files. These require evidence from the capability rather than premature infrastructure.

CAP-003 initial API:
- POST `/api/v1/brand-design/generate?project_id=...`
- GET `/api/v1/brand-design/{project_id}`
- POST `/api/v1/brand-design/{project_id}/approve`

The implementation is backed by repository abstractions for both in-memory deterministic testing and SQLAlchemy persistence. The next validation gate is the repository CI pipeline.

## CAP-003 Deployment Hardening — v0.1.1

CAP-003 initially passed GitHub CI but its first Vercel deployment exposed production-environment differences. The deployment compiled and generated pages successfully, but Vercel reported a broken ESLint module resolution and flagged Next.js 15.4.6 as vulnerable. pnpm also reported ignored lifecycle scripts for `sharp` and `unrs-resolver`.

The hardening decision is deliberately narrow: remain on the Next.js 15 Maintenance LTS line, upgrade Next.js to 15.5.21, upgrade React/React DOM from 19.1.1 to 19.1.9, make the ESLint ESM import explicit, and explicitly allow only the two observed native/build-script dependencies through pnpm's `onlyBuiltDependencies` mechanism.

We will not hand-edit `pnpm-lock.yaml`. Because the implementation environment does not have registry access or pnpm installed, the lockfile must be regenerated by the repository owner using the pinned pnpm version and committed with the manifest changes. This is an intentional integrity rule.

### New release-gate lesson

CI-green is necessary but not sufficient. A milestone is not frozen until it passes:

```text
Repository CI
→ deployment build
→ dependency/security validation
→ production/preview deployment
```

This deployment issue therefore remains part of CAP-003 history and is not treated as an unrelated infrastructure incident.


## CAP-003 deployment hardening follow-up

The first deployment-hardening patch upgraded Next.js/React and fixed the extension-based ESLint import, but local validation exposed two further issues:

1. pnpm 10 ignores the `pnpm` settings field in `package.json`; `onlyBuiltDependencies` therefore belongs in `pnpm-workspace.yaml`.\n2. With `eslint-config-next@15.5.21`, the imported `core-web-vitals.js` value was not iterable in this repository's ESLint runtime. The configuration was therefore made explicit through `@next/eslint-plugin-next`, preserving the same Next.js recommended/Core Web Vitals rules without depending on that module shape.\n3. `pnpm test` previously invoked `pytest` without provisioning Python dependencies. The API test command is now explicit and CI provisions Python 3.12 plus `apps/api/requirements.txt`.

This reinforces the release principle: local developer validation, CI validation and Vercel validation must exercise the same dependency/runtime assumptions.\n
## CAP-005 reference

See [`cap-005-studio.md`](./cap-005-studio.md) for the Website Generation capability. CAP-005 consumes only approved Website Specifications and produces a deterministic Next.js App Router generation artifact.


## CAP-006 reference

See [`cap-006-studio.md`](./cap-006-studio.md) for the Preview & Validation capability. CAP-006 validates generated project structure and provides a safe preview boundary without executing generated code inside Studio.


---

# Chronological Capability Record — CAP-001 → CAP-009

This section is the canonical chronological implementation record. Each capability records what was actually proven, what was deliberately deferred, and the technology decisions that resulted from evidence. Earlier sections remain the strategic baseline; this section prevents later milestones from obscuring historical reasoning.

## CAP-001 — Business Discovery

**Outcome:** established the business-first product loop, structured Business Brief, provenance/assumption distinction, evaluation-before-approval and human checkpoint.

**Key decision:** capability-first architecture replaces the original agent-first product abstraction. Agents remain implementation mechanisms.

**Technology implication:** deterministic/mock provider testing is mandatory before live-model dependence.

## CAP-002 — Website Strategy

**Outcome:** consumes approved Discovery context and produces a versioned Website Strategy with information architecture, sitemap and content strategy. Deterministic structural evaluation and revision/approval workflow were added.

**Key decision:** downstream capabilities cannot bypass approved upstream artifacts.

**Technology implication:** persistence and evaluation abstractions are introduced only where versioning and approval actually require them.

## CAP-003 — Brand & Design Direction

**Outcome:** produces a reviewable design-direction artifact derived from approved strategy, including semantic visual guidance, typography direction, accessibility and responsive principles. Deployment hardening upgraded the Studio toolchain to the known-good Next.js/React/ESLint baseline.

**Key decisions:** keep design semantic and deterministic before introducing visual generation infrastructure; keep approved artifacts immutable.

**Technology implication:** Next.js 15.5.21, React 19.1.9, ESLint 9.39.5 and explicit ESM configuration were retained after deployment evidence.

## CAP-004 — Website Specification

**Outcome:** translates approved strategy and design direction into an implementation-ready Website Specification.

**Key decision:** separate product intent from generated implementation. The specification is a durable handoff artifact.

**Technology implication:** TypeScript/Pydantic contracts remain the boundary representation; no code execution is introduced at this stage.

## CAP-005 — Website Generation

**Outcome:** deterministic generation produces a concrete Next.js App Router artifact from an approved specification.

**Key decision:** start with reproducible templates rather than live-model code generation.

**Technology implication:** Next.js App Router is the single supported generated framework while the architecture is being proven. Additional frameworks are deferred until there is evidence of demand.

## CAP-006 — Validation / Preview Boundary

**Outcome:** validates generated artifacts and establishes a safe preview boundary without executing generated code inside AWE.

**Key decision:** validation and preview must not become an accidental execution path.

**Technology implication:** browser/UI preview is kept separate from build/runtime execution.

## CAP-007 — Isolated Build Contract

**Outcome:** formalized the build-plan artifact, ephemeral workspace strategy, allowlisted runtime commands and network-disabled-by-default policy. No generated code was executed.

**Key decision:** define the security boundary before implementing execution.

**Technology implication:** the execution substrate remains replaceable; Docker, Kubernetes jobs and microVMs were explicitly kept as implementation alternatives.

## CAP-008 — Isolated Build Execution

**Outcome:** implements the first real execution adapter using disposable Docker containers. Generated artifacts are materialized into a temporary workspace; dependency acquisition is constrained and lifecycle scripts are disabled; the actual Next.js build runs with Docker networking disabled and resource limits.

**Key decision:** Docker is selected as the smallest practical substrate that proves the execution contract locally and in CI. It is not frozen as the ultimate production sandbox.

**Deferred:** long-lived preview runtime, public preview URL, arbitrary npm dependency support, production multi-tenant isolation, deployment.

## CAP-009 — Disposable Live Preview Runtime

**Outcome:** extends the CAP-008 execution boundary into a real, disposable Next.js runtime. Studio can start and stop the runtime and open a dynamically allocated localhost preview URL.

**Chronology:** CAP-009 deliberately follows CAP-008. AWE first proved that generated code can be built outside the host process; only then was actual application runtime execution introduced.

**Key decisions:** reuse Docker; require a valid CAP-007 build plan; disable lifecycle scripts during dependency acquisition; keep the build phase network-disabled; run `next start` only inside the container; apply CPU, memory and PID limits; clean up the runtime and workspace explicitly.

**Security trade-off:** the runtime needs to accept browser traffic, so the MVP uses Docker bridge networking with a localhost-only published port. This is weaker than a production no-egress sandbox and is explicitly not approved as a public multi-tenant execution model.

**Technology implication:** Docker remains the selected proof substrate. Kubernetes Jobs and Firecracker/microVMs remain deferred until scale, threat-model and compliance evidence justify the additional operational complexity.

**Deferred:** persistent preview sessions, public preview URLs, arbitrary npm dependencies, browser automation, production egress control, production-grade multi-tenant isolation and deployment.

---

# Technology Decision Register

The project now records technology choices by evidence rather than by the original MVP plan alone. A technology is **selected** when it solves a demonstrated problem with acceptable complexity; **deferred** when the problem is real but premature; **rejected** when it violates the architecture/security requirement.

| Technology / approach | Decision | Evidence / rationale | Revisit trigger |
|---|---|---|---|
| pnpm workspaces | Selected | Efficient monorepo dependency management; deterministic lockfile; workspace filtering | Material monorepo scale/performance issue |
| Turborepo | Selected | Coordinates package-level lint/build/test and caches work as packages grow | Workflow complexity exceeds benefit |
| ESLint 9 + Next rules | Selected | Catches Studio code-quality issues and integrates with the chosen Next.js line | Toolchain incompatibility or stronger lint standard |
| Next.js App Router | Selected for generated sites | Matches current Studio stack and gives a single deterministic generation target | Customer demand for another framework |
| React + TypeScript | Selected | Strong component model and compile-time contracts for Studio | Evidence of a materially better alternative |
| FastAPI | Selected | Async Python API, simple typing and strong testability; already proven by CAP tests | API scale or operational constraints |
| Pydantic | Selected | Clear typed API/domain contracts and validation | Contract model becomes insufficient |
| SQLAlchemy | Selected / incremental | Keeps persistence replaceable and supports async relational storage without forcing DB complexity into capabilities | Persistence scale/requirements justify another layer |
| PostgreSQL | Planned, not yet mandatory for every local capability | Durable relational persistence is appropriate for project/artifact/version data | Production persistence milestone |
| Redis | Deferred | Useful for queues/cache/realtime, but no current capability requires it | Async jobs, distributed coordination or caching become real requirements |
| LiteLLM / provider gateway | Deferred until live-model requirement | Provider abstraction is required, but deterministic capability proofs should precede commercial-model coupling | First production model-backed capability |
| Host subprocess | Rejected for generated code | Insufficient isolation boundary | Never, for untrusted execution |
| Docker | Selected for CAP-008 | Practical filesystem/network/resource controls with low operational overhead and local/CI reproducibility | Threat model requires stronger isolation |
| Kubernetes Jobs | Deferred | Strong orchestration but premature operational complexity | Production-scale execution fleet |
| Firecracker / microVM | Deferred | Higher-assurance isolation candidate but higher implementation complexity | Multi-tenant public execution/compliance requirements |
| Browser-only preview | Deferred as execution mechanism | Preview is valuable, but it cannot prove the generated project builds | After build/runtime contract is stable |
| Celery | Deferred | No demonstrated queue workload yet | Long-running distributed jobs require it |
| Docker Compose | Selected for local supporting services | Low-friction local orchestration | Production orchestration requirement |

## Decision discipline

For every new technology the project should record:

1. the problem it solves;
2. why the current stack cannot solve it adequately;
3. alternatives considered;
4. security and operational consequences;
5. whether the decision is temporary or frozen;
6. the evidence that would trigger a revisit.

This register complements ADRs. The master records the chronological product/engineering reasoning; ADRs capture decisions that materially constrain architecture.

---

# Current State after CAP-009

```text
AWE Studio
   ↓
AWE API / Framework
   ↓
Approved Website Specification
   ↓
CAP-005 Generation
   ↓
CAP-006 Validation
   ↓
CAP-007 Build Contract
   ↓
CAP-008 Docker-Isolated Build
   ↓
CAP-009 Disposable Live Preview Runtime
   ↓
Deployment
```

**Known-good engineering gate:** `pnpm lint && pnpm build && pnpm test` remains mandatory after each capability.

**Latest implementation milestone:** CAP-013 Project Lifecycle & Workspace UX.

**Current security rule:** generated code must never execute in the AWE host process.

**Current architecture rule:** choose the smallest technology that proves the next capability; preserve migration boundaries rather than prematurely building production-scale infrastructure.


## CAP-010 — Deployment Abstraction

**Status:** Implemented / validated in its repository gate.

CAP-010 establishes a provider-neutral deployment contract and a deterministic
local deployment provider. It intentionally does not freeze AWE to Vercel,
Cloudflare, AWS, Kubernetes or another production provider.

**What it proves:** a validated/buildable website can enter a versioned
deployment lifecycle and expose deployment status and URL through a stable API.

**Technology decision:** local provider + abstraction now; permanent cloud
provider deferred until production requirements justify the choice.

**Alternatives considered:** Vercel, Cloudflare, AWS, Kubernetes.

**Deferred:** custom domains, DNS/TLS automation, CDN configuration, production
secrets, multi-region deployment and automatic production promotion.

See `docs/cap-010-deployment.md` and
`docs/adr/ADR-0008-deployment-provider-abstraction.md`.


------------------------------------------------------------------------

## CAP-011 — Deployment UX & Lifecycle

**Status:** Implemented / validated in its repository gate.

CAP-011 turns the CAP-010 deployment abstraction into a first-class product
workflow. Deployment is now represented as a versioned artifact with explicit
status, URL, provider, runtime reference, diagnostics and timestamps.

### Lifecycle

```text
queued → deploying → deployed → stopped
                    ↘ failed
```

### API

```text
POST /api/v1/deployments
GET  /api/v1/deployments/{deployment_id}
GET  /api/v1/deployments
POST /api/v1/deployments/{deployment_id}/stop
```

### Technology decision

The Studio/API talks to a provider-neutral deployment service. CAP-011 uses
the local provider, which promotes the proven CAP-009 isolated runtime into a
deployment lifecycle. No permanent cloud provider is selected yet.

### Why this decision

The product contract needs to be validated before infrastructure is frozen.
Vercel, Cloudflare, AWS and Kubernetes remain candidates for a later hosted
provider decision. The deployment abstraction limits vendor coupling and keeps
Studio independent of Docker or cloud-specific APIs.

### Deferred

Custom domains, DNS/TLS automation, production secrets, multi-region
deployment, autoscaling, production observability and automatic promotion.

See [CAP-011 deployment UX](cap-011-deployment-ux.md) and
[ADR-0009](adr/ADR-0009-deployment-lifecycle-ux.md).


------------------------------------------------------------------------

## CAP-012 — Project Persistence & Workspace Model

**Status:** Implemented / validated in the CAP-012 API test suite.

CAP-012 formalizes the project as AWE's persistent workspace root. Studio/API can list projects and retrieve a resumable workspace summary containing the latest capability versions, deployment count and current workflow stage.

### API

```text
GET /api/v1/projects
GET /api/v1/projects/{project_id}
GET /api/v1/projects/{project_id}/workspace
```

### Technology decision

PostgreSQL remains the selected shared persistence technology because it is already part of the containerized baseline and provides transactions, indexing and a credible production path. SQLAlchemy remains the data-access boundary because it is already integrated and keeps persistence behind the Repository abstraction. SQLite was considered but deferred to avoid maintaining a second persistence topology.

Capability payloads remain versioned behind typed Pydantic models. Full normalization of every capability-specific field and object storage for generated artifacts are deferred until evidence justifies the added complexity.

### Deferred

Authentication/authorization, multi-tenancy, migrations tooling, object/blob storage, backup/retention policy and full event sourcing.

See [CAP-012](cap-012-studio.md) and [ADR-0010](adr/ADR-0010-project-persistence.md).


------------------------------------------------------------------------

## CAP-013 — Project Lifecycle & Workspace UX

**Status:** Implemented in the CAP-013 package; repository validation pending.

CAP-013 turns CAP-012 persistence into a usable project lifecycle and workspace experience. Studio now exposes a compact workspace summary while the API remains the source of truth for project state and capability progress.

### API

```text
GET   /api/v1/projects
GET   /api/v1/projects/{project_id}
PATCH /api/v1/projects/{project_id}
GET   /api/v1/projects/{project_id}/workspace
```

### Workspace state

The workspace now reports:

- current stage;
- next capability;
- completed capabilities;
- latest capability versions;
- deployment count/status;
- last activity timestamp.

### Lifecycle

```text
Active ⇄ Archived
```

Archival is reversible and does not delete persisted project artifacts.

### Technology decision

CAP-013 deliberately does **not** introduce a new workflow service, project-management database, state machine or client-side persistence layer. Progress is derived from the existing capability artifacts behind the Repository abstraction. PostgreSQL + SQLAlchemy remain unchanged from CAP-012. Browser localStorage is retained only for the last-opened project convenience.

### Why this matters

The project is moving from a sequence of capability demos toward a coherent product workspace. Users can now understand where a project is, what AWE has completed and what AWE expects to do next without creating a second source of truth.

### Deferred

Authentication/authorization, multi-tenancy, collaborators/roles, deletion and retention policy, large-scale project search/filtering, activity/event timelines and project settings remain deferred.

See [CAP-013](cap-013-studio.md) and [ADR-0011](adr/ADR-0011-project-lifecycle-workspace-ux.md).


## CAP-014 — Project Duplication & Fresh Workspace Templates
**Status:** Implemented / pending local green gate

CAP-014 adds `POST /api/v1/projects/{project_id}/duplicate`. Duplication creates a new project identity and clean workspace while leaving the source unchanged. We deliberately do not deep-clone capability artifacts or deployment history. This avoids coupling duplication to the current persistence schema and prevents accidental reuse of deployment/runtime state. The existing Repository abstraction is retained; no new technology was introduced. See ADR-0012.


## CAP-015 — Executable Website Build & MVP Runtime Gate

**Status:** Implemented; local green gate pending.

CAP-015 closes the key MVP execution gap by making the existing isolated website build capability a first-class Studio stage. The product path is now Discovery → Strategy → Design → Website Specification → Generation → Build → Preview → Deployment.

### Product implementation

Studio now exposes the existing build planner and executor, shows isolation and diagnostics, and prevents Preview/Deployment navigation until a build succeeds. No generated code executes in the Studio/API process.

### Architecture and technology decision

CAP-015 intentionally reuses the existing Docker disposable execution boundary rather than adding Kubernetes, hosted CI, a worker queue or another runtime. Docker is sufficient for the first executable MVP and preserves the existing adapter boundary for future hosted execution. Direct host execution remains prohibited.

### Documentation

See [CAP-015](cap-015-studio.md) and [ADR-0013](adr/ADR-0013-executable-mvp-build-gate.md).

## CAP-016 + CAP-017 — End-to-End Executable Flow & Website Quality Baseline

- [x] Studio build → validation → preview orchestration
- [x] Build remains behind existing isolated Docker boundary
- [x] Failed build/validation blocks progression
- [x] Generated output consumes approved Strategy and Design artifacts
- [x] Responsive website baseline
- [x] SEO metadata baseline
- [x] Design/strategy traceability checks
- [x] Improved navigation, typography, sections and CTA presentation
- [ ] Hosted/scalable build workers
- [ ] Streaming/cancellable builds
- [ ] Artifact registry

See `docs/cap-016-017-studio.md` for the complete decision record and `docs/changelog-cap-016-017.md` for the implementation delta.

------------------------------------------------------------------------

## CAP-018 + MVP v1.0 — Executable MVP Release Gate

CAP-018 consolidates MVP hardening and the first release gate rather than creating another isolated capability.

### Release objective

The MVP definition is now **a complete executable local product loop**, not production-scale SaaS infrastructure.

### Canonical validation

```text
pnpm mvp:gate
    ├── pnpm lint
    ├── pnpm build
    └── pnpm test
```

### Local executable stack

```text
docker compose up --build
        │
        ├── Studio :3000
        ├── API :8000
        ├── PostgreSQL :5432
        └── Redis :6379
```

### MVP release criteria

- Clean install succeeds.
- Lint, build and tests are green.
- Studio production build succeeds.
- API tests pass on Python 3.12+.
- Core lifecycle is executable from Discovery through Deployment.
- Human approval gates remain in place.
- Build execution remains isolated.
- No unresolved release-blocking defects.

### Deferred by decision

Authentication, multi-tenancy, hosted/scalable workers, production cloud deployment, billing, collaboration, additional frameworks and full production observability are explicitly post-MVP.

See `docs/cap-018-mvp-v1.0-release-gate.md` and ADR-0014 for the complete decision record.

## CAP-002 Revision Semantics Hardening — 2026-08-29

The CAP-002 revision endpoint was revalidated against the real natural-language feedback contract. The previous implementation created a new strategy version and recorded feedback, but only applied CTA changes when feedback used the special `CTA: ...` syntax. Natural-language requests therefore produced a new version without changing the requested strategy content.

The revision path now applies a deterministic, provider-independent subset of actionable feedback before re-evaluation:

- natural-language B2B positioning requests update the positioning and audience-facing key message;
- natural-language consultation requests update the primary CTA;
- the revised CTA is synchronized to the Home and Contact sitemap pages;
- the existing explicit `CTA: ...` syntax remains supported;
- every revision still receives a new `strategy_id`, increments the version and preserves the approved Discovery source-context version;
- approved strategies remain immutable and reject later revisions with HTTP 409.

Regression coverage now includes both explicit and natural-language revision paths and verifies that the relevant strategy content actually changes, rather than merely recording the feedback. This remains deterministic for CAP-002; a future model-based revision agent can be introduced behind the same transformation boundary once its behavior is testable.


------------------------------------------------------------------------

## CAP-009 — Preview Runtime Responsiveness Follow-up

**Status:** Implemented in the post-v1.0.3 working baseline; locally validated.

### Problem found

The first live-preview implementation executed disposable Docker/npm install/build work synchronously from an `async` FastAPI endpoint. Although the endpoint contract was correct, long-running subprocess work could occupy the API event loop and make Studio appear hung while a preview was being prepared.

Repeated starts could also create multiple disposable runtime containers for the same project/generation.

### Added

- Preview start execution moved to a worker thread so Docker/npm install/build does not block the FastAPI event loop.
- Preview stop and cleanup work also moved off the event loop.
- Preview start recognizes a healthy existing runtime for the same project and generation and reuses it.
- Studio exposes explicit live-preview lifecycle controls: start, refresh, open in a new tab and stop.
- The Preview UI keeps safe generated-artifact preview separate from the optional disposable live runtime.

### Changed

- The preview API remains the orchestration boundary; generated code is not executed by Studio itself.
- The disposable runtime continues to use the existing Docker isolation model.
- A cold start remains potentially slow because the disposable runtime may need dependency installation and a production build.

### Fixed

- Apparent Studio hangs caused by blocking preview subprocesses.
- Duplicate runtime creation caused by repeated preview-start attempts.

### Removed / deliberately avoided

- No direct host execution of generated code.
- No Kubernetes, hosted worker queue or persistent production runtime.
- No second preview execution architecture.

### Verification

- API regression coverage was added for preview runtime behavior.
- The generated runtime was manually verified to return valid Next.js HTML over its mapped localhost port.
- The runtime was verified as healthy and serving `next start` output.

### Deferred

Persistent artifact caching, hosted/scalable preview workers, cancellation/streaming, remote runtime orchestration and production observability remain outside the MVP/local-runtime boundary.

See `docs/cap-019-studio-generation-loop.md`, `docs/cap-009-studio.md` and `docs/adr/ADR-0007-disposable-preview-runtime.md`.

------------------------------------------------------------------------

## CAP-019 — Studio Generation Loop and Deployment Lifecycle

**Status:** Implemented in the post-v1.0.3 working baseline; locally deployed/validated.

### Objective

Turn the previously separate generation, build, validation, preview and deployment API operations into one explicit Studio workflow with visible gates and diagnostics.

### Added

Studio now exposes an eight-stage pipeline:

```text
01 Discovery
02 Strategy
03 Design
04 Website Specification
05 Generate
06 Build
07 Preview
08 Deploy
```

The Build stage exposes:

- build-plan status;
- isolation information;
- plan diagnostics;
- build stdout/stderr diagnostics;
- refresh/build-plan actions;
- isolated build execution;
- explicit validation after a successful build.

The Preview stage exposes:

- passed-validation gating;
- safe generated-artifact preview;
- optional disposable live runtime;
- runtime status;
- refresh;
- open-in-new-tab;
- stop-runtime controls.

The Deploy stage exposes the local deployment lifecycle and deployment history.

### Deployment lifecycle additions

- Deployment requires a validated Website Generation.
- Deployment versions increment per project (`v1`, `v2`, `v3`, ...).
- A new deployment supersedes queued, deploying or deployed predecessors.
- Superseded records remain in history and become `stopped`.
- Runtime/provider failures become explicit `failed` deployment records instead of remaining stuck in `deploying`.
- Studio uses the canonical `/api/v1/deployments` routes.
- Deployment history is loaded when an existing project is opened.

### Changed

- Preview and Deploy navigation is gated by passed validation.
- Successful isolated build no longer silently advances directly to Preview; Studio remains on Build until the user explicitly validates.
- The Studio pipeline became the visible orchestration surface while execution remains behind the API/Docker boundary.
- Existing project selection, duplication, archive/restore and Discovery initialization remain compatible with the new pipeline.

### Fixed

- Incorrect deployment API path usage in Studio.
- Missing explicit Build boundary in the Studio pipeline.
- False progression after build/validation failures.
- Deployment records that could remain `deploying` after runtime/provider failure.
- Loss of deployment history when reopening a project.
- Preview-stage navigation that could bypass the validation gate.

### Removed / deliberately avoided

- No direct generated-code execution in Studio.
- No hosted/scalable worker system.
- No cloud provider abstraction.
- No background job orchestration.
- No collaborative editing system.
- No replacement of the existing Docker disposable execution boundary.

### Architecture decision

The MVP continues to use Docker as the disposable execution boundary. CAP-019 improves the product workflow without prematurely introducing Kubernetes, hosted CI, a worker queue or a second execution architecture.

### Verification

- API regression suite reached 48 passing tests at the CAP-019 completion baseline.
- Studio lint and production build passed.
- Docker Studio image built successfully and the production container returned HTTP 200.
- The complete local Studio generation/build/validation/preview/deployment loop was manually exercised.

### Deferred

Hosted/scalable workers, cancellable/streaming builds, artifact registry, cloud deployment providers and production-scale observability remain deferred.

See `docs/cap-019-studio-generation-loop.md` and the deployment ADRs under `docs/adr/`.

------------------------------------------------------------------------

## CAP-020 — Production Model Adapter

**Status:** Implemented in the post-v1.0.3 working baseline; locally deployed/validated.

### Objective

Introduce a real provider boundary without coupling AWE capabilities to a vendor SDK while preserving deterministic local development and tests.

### Added

- An OpenAI-compatible HTTP model adapter using the Python standard library.
- Environment-driven provider selection.
- Provider base URL, model name and timeout configuration.
- Explicit provider/gateway error handling.
- Regression coverage for provider selection and request handling.

Supported configuration:

```text
AWE_MODEL_PROVIDER=mock
AWE_MODEL_PROVIDER=openai-compatible
AWE_MODEL_API_KEY=...
AWE_MODEL_BASE_URL=https://api.openai.com/v1
AWE_MODEL_NAME=gpt-4o-mini
AWE_MODEL_TIMEOUT_SECONDS=60
```

### Changed

- The capability-facing `ModelGateway` contract remains stable while provider implementation is selected behind it.
- Discovery can use the configured model gateway without embedding vendor-specific SDK logic in the capability.
- Provider calls execute outside the FastAPI event loop.
- The deterministic mock remains the default when no provider is configured.

### Fixed / hardened

- Missing credentials are reported explicitly.
- Unsupported provider values fail explicitly.
- Provider HTTP failures, timeouts and malformed/empty responses become explicit gateway failures.
- Strict response validation prevents malformed provider output from silently corrupting structured Discovery state.

### Removed / deliberately avoided

- No vendor SDK is required.
- No provider credential is persisted in project/capability state.
- No API key is committed to the repository.
- No change to the Discovery structured-output contract.
- No claim of production SaaS readiness.

### Architecture decision

The AWE capability contract remains provider-neutral. An OpenAI-compatible HTTP adapter is an implementation detail, not a new product-level dependency. The same boundary can support compatible hosted providers or future local/open-weight adapters.

### Verification

- API regression suite reached 53 passing tests at the CAP-020 baseline.
- Deterministic mock behavior remains available for local/test execution.
- Provider configuration and failure paths are covered by regression tests.
- The CAP-020 baseline was locally deployed by the project workflow.

### Deferred

Credential management/secrets infrastructure, provider health/circuit breaking, usage accounting, token/cost telemetry, provider routing/fallback policies and production SaaS operational controls remain deferred.

See `docs/cap-020-production-model-adapter.md` and `docs/adr/ADR-0005-model-agnostic.md`.

------------------------------------------------------------------------

## Documentation audit — CAP-009 / CAP-019 / CAP-020

This audit closes the documentation gap identified after the CAP-020 baseline. The Project Master now records the material cumulative delta for the post-v1.0.3 preview, generation-loop/deployment and model-provider increments, including additions, changes, fixes, deliberate non-additions/removals, architectural rationale, verification and deferred work.

The capability documents remain the detailed local records; the Master Project Record is the cross-capability historical source of truth. Future capability packages must extend this audit trail rather than relying solely on a capability-specific changelog entry.

------------------------------------------------------------------------

## CAP-021 — Migration Hardening

**Status:** Implemented in the CAP-021 working package; pending owner local deployment/acceptance.

### Baseline

CAP-021 starts from the locally deployed CAP-020 Project Master-hardened baseline. `v1.0.3` remains frozen and is not modified or retagged.

### Objective

Replace implicit PostgreSQL schema creation with an explicit, reproducible migration lifecycle while preserving the existing in-memory test repository and MVP architecture.

### Added

- Alembic configuration at `apps/api/alembic.ini`.
- Alembic environment and migration template under `apps/api/alembic/`.
- Initial `0001_initial_schema` revision establishing the existing MVP SQLAlchemy schema.
- Alembic dependency pinned in `apps/api/requirements.txt`.
- Migration regression tests in `apps/api/tests/test_migrations.py`.
- ADR-0017 documenting migration authority.

### Changed

- `apps/api/app/store.py:init_database()` no longer invokes `Base.metadata.create_all()` during application startup.
- Startup now invokes `alembic upgrade head` through a worker thread, keeping synchronous migration work outside the FastAPI event loop.
- `docs/roadmap.md` marks migration hardening complete.
- `CHANGELOG.md` records CAP-021 as an unreleased working increment.

### Fixed / hardened

- Empty PostgreSQL initialization now has an explicit versioned schema path.
- Schema lifecycle is no longer silently coupled to SQLAlchemy metadata creation at every startup.
- Future schema changes now have a committed migration boundary that can be inspected, reviewed and tested.

### Removed / deliberately avoided

- Removed application-startup `Base.metadata.create_all()` behavior.
- No automatic generation of migration revisions.
- No destructive startup reset.
- No migration requirement for the in-memory repository used by tests without `DATABASE_URL`.
- No separate migration service or production orchestration layer was introduced.

### Architecture / rationale

Alembic is the authoritative PostgreSQL schema lifecycle. The initial revision deliberately establishes the current MVP schema using the existing metadata so this hardening step remains low-risk. Future changes must be represented by explicit new revisions rather than modifying the initial baseline.

See `docs/cap-021-migration-hardening.md` and `docs/adr/ADR-0017-migration-authority.md`.

### Verification

- API regression suite: **55 passed**.
- Migration configuration/revision regression tests: included in the 55 passing tests.
- Studio and Docker integration remain package acceptance checks after local deployment.

### Deferred

Online zero-downtime migration choreography, automated backup/restore validation, destructive-migration approval workflows and production migration orchestration remain deferred.


## CAP-022 + CAP-023 — Deployment Operations (current working increment)

### Baseline
Built from the accepted CAP-021 Migration Hardening baseline, including the CAP-009 preview fix, CAP-019 generation/build/validation/preview/deployment loop, CAP-020 production model adapter, and migration hardening.

### Added
- `POST /api/v1/website-performance/check` for deterministic generated-artifact performance budgets.
- `GET /api/v1/monitoring` for lightweight service/project/deployment health counts.
- Studio Deployment-stage controls for Performance check and Monitoring.
- `docs/cap-022-023-operations.md` and roadmap/changelog entries.
- Regression tests for operational endpoints.

### Changed
- M4 roadmap status now marks one-click deployment, performance checks, and monitoring as implemented at the MVP operational level.
- Deployment UI now exposes operational diagnostics alongside deployment history.

### Fixed
- No production defect was repaired in this increment; the work closes previously unimplemented M4 operational surfaces.

### Removed / deliberately not added
- No existing deployment provider or cloud integration was removed.
- Browser/Lighthouse performance scoring, real-user monitoring, external telemetry, alerting, and hosted workers remain deliberately deferred.

### Architecture decisions
- Performance checks operate on generated artifact source metadata rather than pretending to measure browser runtime performance from inside the API container.
- Monitoring remains provider-neutral and dependency-light; it does not introduce a mandatory observability vendor.

### Verification
- API regression suite: 58 passed.
- CAP-022/023 targeted tests: 3 passed.
- Studio lint/build require the locally installed pnpm workspace dependencies and remain part of the local package acceptance gate.

### Release status
Unreleased working increment. `v1.0.3` remains frozen and untouched.

------------------------------------------------------------------------

## CAP-024 — Hosted/Scalable Execution & Production Deployment Boundary

**Status:** Implemented as an unreleased working increment; local deterministic path preserved.

### Baseline
Built from the accepted CAP-022 + CAP-023 Deployment Operations baseline. `v1.0.3` remains frozen, and no release tag is moved or created.

### Objective
Separate execution concerns from capability orchestration so expensive website builds and deployment operations can be delegated to independently scalable infrastructure without coupling AWE to a specific cloud vendor.

### Added
- `BuildExecutionProvider` interface in `apps/api/app/services/execution.py`.
- `LocalDockerBuildExecutionProvider`, preserving the existing Docker-volume sandbox as the default execution implementation.
- `HostedBuildExecutionProvider`, an opt-in HTTP adapter for a separately deployed build worker/service.
- Environment-selected build execution using `AWE_BUILD_EXECUTION_PROVIDER`.
- Hosted build endpoint/token/timeout configuration through `AWE_BUILD_EXECUTION_URL`, `AWE_BUILD_EXECUTION_TOKEN`, and `AWE_BUILD_EXECUTION_TIMEOUT_SECONDS`.
- `HostedDeploymentProvider` and environment-selected deployment provider resolution.
- Hosted deployment endpoint/token/timeout configuration through `AWE_DEPLOYMENT_PROVIDER_URL`, `AWE_DEPLOYMENT_PROVIDER_TOKEN`, and `AWE_DEPLOYMENT_PROVIDER_TIMEOUT_SECONDS`.
- Explicit provider-selection and failure-path regression tests.
- CAP-024 capability documentation and ADR-0018.

### Changed
- `WebsiteBuildService.execute()` now resolves a provider rather than hard-coding the local execution mechanism.
- The existing local build implementation was retained behind the new provider boundary, minimizing behavioral change and preserving Docker isolation/network policy.
- `DeploymentService` now resolves the provider from `AWE_DEPLOYMENT_PROVIDER`, while defaulting to the existing local provider.
- The roadmap and changelog now distinguish the execution/deployment abstraction from actual hosted infrastructure.

### Fixed / hardened
- Future hosted execution no longer requires capability code to be rewritten around a particular worker implementation.
- Unsupported execution-provider values fail explicitly instead of silently selecting a fallback.
- Hosted execution/deployment failures are represented explicitly; the API does not silently fall back from hosted mode to local mode.
- Missing hosted configuration is surfaced as a deterministic configuration error.

### Removed / deliberately avoided
- No local Docker sandbox was removed.
- No cloud vendor SDK was introduced.
- No mandatory external queue, registry, Kubernetes cluster, cloud account, DNS/TLS service, or observability vendor was added.
- No production cloud provider is claimed merely because an HTTP adapter exists.
- No credentials are persisted in project state or committed to the repository.

### Architecture / rationale
The provider boundary is the stable contract. Local Docker remains the reproducible MVP implementation. Hosted adapters provide a narrow integration point for separately operated workers/deployment services, allowing scaling to evolve independently. The adapters deliberately do not own the security, queue durability, autoscaling, artifact retention, secrets management, or cloud lifecycle of the future hosted infrastructure.

### Configuration
Default local behavior requires no new configuration:

```text
AWE_BUILD_EXECUTION_PROVIDER=local-docker
AWE_DEPLOYMENT_PROVIDER=local
```

Hosted modes are explicit and opt-in:

```text
AWE_BUILD_EXECUTION_PROVIDER=hosted
AWE_BUILD_EXECUTION_URL=https://build.example.internal
AWE_BUILD_EXECUTION_TOKEN=...
AWE_BUILD_EXECUTION_TIMEOUT_SECONDS=600

AWE_DEPLOYMENT_PROVIDER=hosted
AWE_DEPLOYMENT_PROVIDER_URL=https://deploy.example.internal
AWE_DEPLOYMENT_PROVIDER_TOKEN=...
AWE_DEPLOYMENT_PROVIDER_TIMEOUT_SECONDS=600
```

### Verification
- Python compilation: passed.
- API regression suite after integration: **62 passed**.
- CAP-024 provider-selection/failure tests: **4 passed**.
- Existing build/deployment regression behavior remained green after the provider refactor.
- Studio source was not behaviorally changed in this increment; existing Studio lint/build remain part of the local package acceptance gate.

### Deferred
A durable asynchronous job queue, persistent worker fleet, artifact registry, cloud deployment implementation, autoscaling, workload cancellation/streaming, secrets management, deployment health reconciliation and zero-downtime production orchestration remain deferred. These are intentionally not represented as complete by CAP-024.

### Release status
Unreleased working increment. No tag or frozen release was modified.

See `docs/cap-024-hosted-execution.md` and `docs/adr/ADR-0018-execution-provider-boundary.md`.

## CAP-025 — Security & Access Boundary

### Baseline
CAP-024 hosted/scalable execution and production-deployment abstraction, with authentication/authorization still explicitly incomplete.

### Added
- Explicit authentication boundary with development and strict modes.
- Database-backed users, bearer sessions and API-key records.
- Password hashing using salted scrypt.
- Opaque `awe_` API keys with hashed-at-rest storage, one-time plaintext return, prefixes, scopes, last-used timestamp and revocation timestamp.
- Project ownership identity (`owner_id`) and server-side project authorization.
- Scope enforcement for programmatic API access.
- Auth endpoints for registration, login, current identity and API-key lifecycle.
- Security regression coverage, including unauthorized access and cross-owner denial.
- ADR-0018 documenting the security boundary.

### Changed
- Project creation now assigns the authenticated identity as owner.
- Project listing is owner-scoped.
- Project duplication preserves ownership and requires project authorization.
- Monitoring is owner-scoped rather than exposing aggregate data across tenants.
- Existing project resources are protected through the API middleware/resource boundary.
- Authentication is applied to API access while health and account-bootstrap endpoints remain intentionally public.

### Fixed / hardened
- Prevented authenticated users from accessing another owner's project by changing a project UUID.
- Prevented API keys from being treated as unrestricted credentials by adding explicit scopes.
- Prevented raw API-key secrets from being persisted.
- Added strict-mode rejection for unauthenticated API requests.

### Removed / deliberately not added
- No external identity/SSO vendor dependency.
- No plaintext credential storage.
- No cookie-only authentication requirement for API clients.
- No team/collaboration roles or billing model yet.
- No claim that development authentication is production-safe.

### Data/API/configuration impact
- Added `owner_id` to projects.
- Added `users`, `auth_sessions`, and `api_keys` persistence tables through migration `0002_auth_security`.
- Added `/api/v1/auth/register`, `/login`, `/me`, and API-key lifecycle endpoints.
- `AWE_AUTH_MODE=development|strict` controls the authentication boundary; development is the compatibility default for the local MVP stack.
- `AWE_SESSION_TTL_HOURS` controls session lifetime.

### Verification
- Full API regression suite: **69 passed**.
- Security-specific tests cover development identity, ownership assignment, cross-owner denial, password verification, secret hashing, API-key scope enforcement and strict-mode rejection.

### Known limitations / deferred work
- Production-grade email verification, password reset and account recovery are not yet implemented.
- OIDC/SAML/SSO, team roles, invitations and fine-grained tenant administration remain future work.
- API-key rotation UX is represented by revoke/create rather than a dedicated rotate endpoint.
- Existing production data requires ownership review before multi-user exposure.

### Release status
CAP-025 is an unreleased working increment. `v1.0.3` remains frozen and untouched.

---

# CAP-026 / CAP-027 / CAP-028 — Customer Mock Review Wave

Date: 2026-09-05
Status: **implemented in working increment; unreleased**
Baseline: CAP-025 verified security/access boundary; `v1.0.3` remains frozen.

## Decision

The next delivery wave groups three tightly coupled capabilities so the first customer-facing website experience arrives before executable build/deployment:

1. **CAP-026 — Customer Website Mock**: a first-class safe review stage derived from the validated generated artifact.
2. **CAP-027 — Visual Refinement / Feedback Loop**: persisted customer feedback plus immutable deterministic revisions.
3. **CAP-028 — Mock → Executable Preview**: explicit approval gate into the existing isolated build/validation/preview path.

## Implementation

The API adds `WebsiteMock`, version history and feedback persistence, with Alembic migrations `0003_website_mock` and `0004_website_mock_project_index`. CAP-025 security tables remain registered in Alembic metadata, while the mock project index is explicitly non-unique to support immutable revisions. The Studio pipeline now exposes a Customer Mock stage after generation and blocks Build until the mock is approved.

The deterministic refinement contract currently recognizes `headline: ...` and `cta: ...`. Unsupported feedback is retained instead of being converted into an invented change. Revised generation and mock versions are persisted independently, preserving the existing immutable-versioning direction.

The mock is rendered as safe HTML via Studio `iframe srcDoc`; generated application code is not executed inside the customer mock.

## Verification

- Focused customer-mock regression: **4 passed**.
- Full API regression after the wave: **71 passed**.
- Existing CAP-025 regression remains part of the full suite.
- Studio build/lint remains to be run on the development machine after dependency installation because the uploaded source snapshot does not include `node_modules`.

## Release posture

This is a working increment only. No release version is advanced. The frozen `v1.0.3` baseline remains unchanged.


## CAP-029 — Browser/Core Web Vitals Validation
Working implementation adds disposable Chromium validation against the active live preview, with browser-rendering checks and FCP/LCP/INP/CLS/TTFB metrics. External metrics/alerting remains deferred.

------------------------------------------------------------------------

## CAP-009 / CAP-029 — Disposable Runtime Lifecycle Correction

**Status:** Working corrective increment; release remains frozen at `v1.0.3`.

### Root cause confirmed

Live preview runtime networking was healthy: the API and Studio containers could both reach the active Next.js runtime directly on the shared Docker network and receive HTTP 200. The failure was runtime discovery: the preview proxy and browser validation depended on the API process-local `_sessions` registry. After an API restart, that registry could no longer describe already-running disposable containers, leaving orphaned runtimes and causing false `runtime unreachable` errors.

### Corrective changes

- Disposable runtime containers now carry explicit AWE labels for preview, project and generation version.
- Runtime lookup for the Studio proxy resolves the running container from Docker labels and its published port instead of relying on `_sessions`.
- Browser validation resolves the active runtime by project label and derives its current published port from Docker.
- Starting a preview removes previously labeled preview containers for the same project before creating a replacement.
- API startup removes orphaned AWE disposable preview containers left by an earlier API process.
- The existing private shared-network proxy architecture is retained; no direct generated-code execution is introduced.

### Verification target

After rebuilding the API and restarting Compose, the expected sequence is: orphan preview cleanup -> start one labeled runtime -> Studio iframe renders through the same-origin proxy -> browser validation resolves the same runtime -> stopping the preview removes the labeled runtime. CAP-029 should only be marked verified after this end-to-end sequence succeeds.


### CAP-009 / CAP-029 — Runtime lifecycle fix v4
- Hardened legacy runtime detection: the Docker ancestor filter identifies `node:22-alpine` candidates; cleanup no longer requires an exact `Config.Image` string, which may be normalized by Docker.
- Detection inspects the actual command and requires the npm start command plus port 3000.

## CAP-029 — Studio reporting + preview readiness correction

- Browser/Web Vitals results are rendered directly in the Preview & Validation stage, immediately below the live preview, instead of only in Deployment where the user cannot see them after running the browser check.
- Each Web Vital retains acronym, full name, plain-language meaning, measured value, and technical check details.
- Disposable preview startup now waits for the runtime to accept HTTP traffic before returning `started`, preventing the Studio iframe from racing Next.js startup and producing a transient proxy 502.
- Runtime lifecycle, private `awe-platform` network routing, labels, and disposable cleanup remain unchanged.


## CAP-031 working increment — Account Recovery & Email Verification
Implemented a strict-mode account recovery boundary with persisted verification/reset token hashes, explicit expiry and single-use semantics, email verification state, generic request responses, and a development-only token exposure switch for local testing. Transactional email delivery remains deferred.


## CAP-032 working increment — External SSO / OIDC

Implemented a provider-neutral external authentication boundary with an OIDC authorization-code adapter, one-time hashed state and nonce protection, persisted provider/subject identity linking, optional verified-email JIT provisioning (disabled by default), and deterministic mock IdP mode for local regression. Strict-mode SSO endpoints remain public only for the authorization initiation/callback boundary; API-key authentication and project authorization are unchanged. Migration: `0007_sso`. SAML remains explicitly deferred rather than represented as an unverified implementation.

---

# CAP-033 — Complete Website Creation Journey / Mock Fidelity Correction

Date: 2026-09-08
Status: frozen after regression correction; CAP-033 acceptance remains verified.

CAP-033 completes the intended Studio journey from generation through customer mock, build, validation, preview, deployment and live/completion handoff. During end-to-end acceptance testing, the Customer Website Mock was found to render a generic validation template while the executable preview rendered the business-specific generated site.

The correction introduces a canonical `awe-preview.html` artifact emitted during the same deterministic generation pass as the executable Next.js files. It carries the generated site's business content, navigation, layout and visual tokens into the safe customer-facing mock without executing generated application code. Validation and mock creation now prefer this artifact, while older generations retain a backward-compatible generic fallback.

Mock revisions also update the canonical preview artifact when supported headline/CTA feedback is applied, keeping the review representation aligned with the revised executable page.

Regression correction: industry alias matching now uses word/phrase boundaries to prevent category collisions (e.g. marketing→retail via 'market', fintech→technology via 'tech'), and generic 'help ...' goal phrasing is normalized. Canonical preview validation is asserted against the current `awe-preview.html` contract. The focused CAP-033 regression must be rerun in the Docker-enabled Python test harness before deployment freeze.


## Current capability status — CAP-034
The content/data management foundation now provides persistent project-scoped content, draft/published state, version history, and authenticated APIs. Runtime consumption and Studio editing remain the next implementation increment; CAP-033 remains frozen.


## CAP-035 — Studio Content Management + Live Preview Consumption

In progress: persistent CAP-034 website content is now exposed in Studio and synchronized into the disposable live preview on publish, without regenerating the website artifact. Focused and full regression evidence is pending.

## CAP-036 — End-to-End Customer Journey

Date: 2026-09-09
Status: **implementation increment — durable deployed-project resume correction added; end-to-end verification pending**

CAP-036 focuses on proving one complete customer journey rather than introducing another isolated subsystem:

`Create project → Discovery → Strategy → Design → Website Specification → Generate → Customer Mock → feedback/revision → approve → Build → Validate → Live Preview → edit content → publish → Deploy → Live → reopen project → continue editing`.

The first concrete gap found in the current Studio was the post-deployment resume path. A deployed project could be reopened, but Studio selected Build because it interpreted the durable Preview workspace state through transient mock/build execution artifacts. CAP-036 now treats the latest successful deployment as the durable completion boundary: the API marks Preview and Deployment complete, Studio resumes at Deployment, and the live summary still provides return-to-editing without regeneration.

This increment does not claim the whole customer journey is verified yet. The required acceptance evidence remains a fresh-project Studio run through deployment, live-site content verification, browser refresh/reopen, and continued editing/publishing without regeneration.

## Workflow state and stage-transition governance

The AWE Studio workflow is governed as a state machine rather than as a set of independently navigable pages. The authoritative rules are documented in `docs/workflow-state-machine.md`.

The platform must explicitly track current project, current stage, prerequisite state, represented website/content version, permitted transitions and downstream artifact validity. UI availability is not sufficient authorization for a transition; domain/API state must enforce the same rules.

Forward movement requires the applicable upstream state/artifacts. Backward movement is allowed only where the stage contract permits it and must not silently destroy immutable generated/deployment history. If an earlier-stage change affects downstream meaning, affected state must be marked stale and regeneration/revalidation must be required before that state can again be treated as current or deployable.

This governance is now a mandatory regression concern for every future capability that changes workflow stages: forward and backward transitions, blocked transitions, prerequisites, stale-state behavior, version identity, failure recovery and project restoration must all be covered.

## CAP-036 FIX-31 — Deployment-pinned live-preview navigation

Date: 2026-09-14
Status: **accepted and locally regression verified**

A CAP-036 historical-deployment defect was found during live deployment acceptance: V7 initially rendered its own snapshot content (`Coyote - Sylvester`) but could switch to V8 (`Coyote - Tweety`) after browser navigation. Direct runtime and initial stable-proxy checks proved the deployment snapshots were correct; the failure was loss of deployment identity across generated navigation.

FIX-31 makes deployment identity a first-class browser navigation boundary. The Studio exposes `/api/live-preview/deployment/<project-id>/<deployment-id>/...`, explicit `deployment_id` is authoritative in the API deployment proxy, and generated internal links/assets plus relevant Next.js navigation state are rewritten into the selected deployment namespace. Studio's current and historical deployment actions both pass the explicit deployment ID.

The correction preserves the FIX-30 runtime model: the latest deployment remains canonical, the immediately previous deployment remains restorable for comparison/testing, older versions remain snapshot-backed history, runtime ports remain disposable, and historical restore does not promote or tear down the current live deployment.

Acceptance evidence: direct V7/V8 render checks, deployment-scoped link inspection, focused API regression (`24 passed in 0.16s`), and browser navigation through the generated pages all passed. V7 remained V7 and V8 remained V8 throughout navigation.


## CAP-037 — Deployment lifecycle/current-previous policy

Implementation baseline: CAP-037 is implemented in the current package. It
formalizes durable deployment currentness (`current`, `previous`, `historical`),
snapshot observability, atomic promotion, local runtime reconciliation, and
non-promoting historical restore. CAP-036/FIX-31 deployment-pinned browser
navigation remains a required regression invariant.

## CAP-038.1 endpoint reconciliation

Repository-wide endpoint audit established two request planes. Studio deployment CRUD/history uses the canonical FastAPI `/api/v1/deployments...` contracts directly through `NEXT_PUBLIC_API_URL` and normal authentication/authorization. Generated live website traffic uses Studio `/api/live/...` routes, which privately proxy to `/api/v1/website-preview/live-proxy/...` with `X-AWE-Preview-Proxy`. New Studio live links no longer emit the FIX-31 `/api/live-preview/deployment/...` namespace; those routes remain compatibility aliases only. The full endpoint and interaction matrix is maintained in `docs/cap-038-endpoint-contract.md`.
