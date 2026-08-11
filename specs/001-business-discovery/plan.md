# Implementation Plan: Business Discovery

## Technical approach

Implement CAP-001 as an API-backed capability with a thin Studio client.

### Phase 1 — Contract
- Define OpenAPI endpoints.
- Define request/response schemas.
- Define lifecycle states.

### Phase 2 — Persistence
- Replace the Genesis in-memory store with PostgreSQL repositories.
- Version Business Knowledge Contexts.
- Persist source messages.

### Phase 3 — AI boundary
- Add a provider-neutral ModelGateway.
- Add a prompt template registry.
- Add structured-output validation.
- Add confidence/evidence fields.

### Phase 4 — AI loop
- Detect missing critical information.
- Generate one or more targeted questions.
- Re-evaluate after each answer.
- Stop when minimum completeness is reached or the user explicitly chooses to proceed.

### Phase 5 — Human approval
- Present a context review screen.
- Require explicit approval.
- Persist immutable approved version.

### Phase 6 — Evaluation
- Add completeness evaluator.
- Add consistency evaluator.
- Add unsupported-claim evaluator.
- Add test fixtures.

## Deferred

- Knowledge graph database
- Temporal
- Multi-agent parallel execution
- Competitor crawling
- Website generation
- Deployment
