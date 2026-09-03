# Tasks: Business Discovery

## T001 — Contract
- [x] Define API contract for project/discovery endpoints through FastAPI/OpenAPI.
- [x] Add API lifecycle/schema validation coverage.

## T002 — Database
- [x] Add PostgreSQL repository layer.
- [ ] Add Alembic migrations (next hardening step).
- [x] Add project table.
- [x] Add discovery_session table.
- [x] Add context_version table.
- [x] Add source_message table.

## T003 — Model Gateway
- [x] Define/use provider-neutral ModelGateway boundary.
- [ ] Add LiteLLM adapter behind the interface.
- [x] Add deterministic mock adapter for tests.
- [ ] Ensure UI cannot access provider credentials.

## T004 — Context
- [x] Define Business Knowledge schema.
- [x] Add confidence and evidence metadata.
- [x] Add null/empty unknown-value representation.
- [x] Implement context versioning.

## T005 — AI Loop
- [x] Implement initial discovery extraction step.
- [x] Implement structured context update.
- [x] Implement minimum completeness evaluation.
- [x] Implement initial targeted open-question generation.
- [ ] Implement iteration limits.

## T006 — Approval
- [x] Add awaiting_approval state.
- [x] Add approval endpoint.
- [x] Persist approved version.
- [x] Approval is an explicit state transition; post-approval mutation remains a hardening test.

## T007 — Studio
- [x] Create project UI.
- [x] Create interview UI.
- [x] Create context review UI.
- [x] Add explicit approval action.
- [ ] Display evidence/confidence.
- [x] Initialize Discovery on create/restore/switch when the context is missing.
- [x] Keep the Discovery composer hidden until a context exists.

## T008 — Quality
- [x] Add lifecycle test coverage.
- [x] Add discovery lifecycle integration test.
- [x] Add duplicate-project Discovery initialization regression coverage.
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
