# Tasks: Business Discovery

## T001 — Contract
- [ ] Define OpenAPI contract for project/discovery endpoints.
- [ ] Add schema validation tests.

## T002 — Database
- [ ] Add PostgreSQL repository layer.
- [ ] Add migrations.
- [ ] Add project table.
- [ ] Add discovery_session table.
- [ ] Add context_version table.
- [ ] Add source_message table.

## T003 — Model Gateway
- [ ] Define provider-neutral gateway interface.
- [ ] Add LiteLLM adapter behind the interface.
- [ ] Add mock adapter for tests.
- [ ] Ensure UI cannot access provider credentials.

## T004 — Context
- [ ] Define Business Knowledge schema.
- [ ] Add confidence and evidence metadata.
- [ ] Add unknown-value representation.
- [ ] Implement context versioning.

## T005 — AI Loop
- [ ] Implement discover step.
- [ ] Implement structure step.
- [ ] Implement completeness evaluation.
- [ ] Implement targeted follow-up question generation.
- [ ] Implement iteration limits.

## T006 — Approval
- [ ] Add awaiting_approval state.
- [ ] Add approval endpoint.
- [ ] Persist approved version.
- [ ] Prevent silent mutation of approved context.

## T007 — Studio
- [ ] Create project UI.
- [ ] Create interview UI.
- [ ] Create context review UI.
- [ ] Add explicit approval action.
- [ ] Display evidence/confidence.

## T008 — Quality
- [ ] Unit tests for schemas.
- [ ] Integration tests for discovery lifecycle.
- [ ] Golden fixtures for representative SMB projects.
- [ ] Add unsupported-claim evaluation.
- [ ] Add CI checks.

## Definition of Done

- [ ] API contract implemented.
- [ ] Persistence implemented.
- [ ] AI boundary implemented.
- [ ] Human approval implemented.
- [ ] Automated tests pass.
- [ ] Local Docker environment works.
- [ ] Documentation updated.
