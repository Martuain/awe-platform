# AWE Platform

**Genesis v1.0.2 — Executable MVP end-to-end verification**

AWE (AI-native Website Engineering) is an API-first, model-agnostic platform for turning structured business knowledge into engineered digital experiences.

> AWE Studio is the commercial product. AWE Framework/Core are platform concepts. They must not be confused with AWE framework as a methodology.

## MVP scope

This repository is a local executable MVP/release candidate covering the core website-engineering flow:

1. Create or restore a project workspace.
2. Initialize and conduct Business Discovery.
3. Review and approve the structured business context.
4. Generate and approve Website Strategy.
5. Generate and approve Brand & Design Direction.
6. Generate and approve Website Specification.
7. Generate a deterministic Next.js website artifact.
8. Build and validate the generated artifact through the isolated local execution boundary.
9. Preview the resulting site safely.
10. Exercise the provider-neutral local deployment lifecycle.

The platform remains deliberately provider-agnostic. Hosted/scalable workers, production cloud deployment, authentication, multi-tenancy and collaboration remain post-MVP work.

## Stack

- Next.js + React + TypeScript
- FastAPI + Pydantic
- SQLAlchemy + PostgreSQL
- Redis
- pnpm + Turborepo
- Docker Compose
- OpenAPI-first API contract
- Provider-agnostic AI boundary

Open-source-first is an architectural requirement; dependency licenses still require review before commercial distribution.

## Repository layout

```text
apps/
  api/                 FastAPI application, services, persistence and tests
  studio/              Next.js Studio
packages/              Shared capability/context/knowledge/runtime interfaces
docs/                  Architecture, ADRs, capability notes and project record
specs/                 Capability specifications, plans and task tracking
```

Generated dependencies, build output, caches and macOS metadata are intentionally excluded from source control and release archives.

## Local development

### Prerequisites

- Node.js 22+
- pnpm 10
- Python 3.12+
- Docker / Docker Compose

Install JavaScript dependencies and Python API dependencies:

```bash
corepack enable
pnpm install
python3 -m pip install -r apps/api/requirements.txt
```

### Validate

```bash
pnpm lint
pnpm build
pnpm test
pnpm mvp:gate
```

The release gate runs lint, production build and the complete test suite. For a brand-new project to live-website verification, run `pnpm e2e:mvp` against the running Compose stack.

### Run the executable stack

```bash
pnpm mvp:up
```

Studio: http://localhost:3000  
API: http://localhost:8000  
API docs: http://localhost:8000/docs

Stop the stack:

```bash
pnpm mvp:down
```

## End-to-end MVP verification

The repository includes a fresh-project smoke test that exercises Discovery through deployment and then performs a real HTTP request against the returned running website:

```bash
pnpm mvp:up
pnpm e2e:mvp
```

See `docs/e2e-mvp.md` for the verification contract and the local Docker execution boundary.

## Discovery lifecycle invariant

Business Discovery is strict at the API boundary: `/business-discovery/message` never creates a missing session implicitly.

Studio uses an idempotent `ensureDiscovery(projectId)` boundary when:

- creating a project,
- restoring the saved project,
- switching projects.

A duplicated project receives a new identity and a clean workspace. Its Discovery context is **not** copied from the source project; Studio initializes a new independent Discovery session before messaging it.

This closes the lifecycle hole where a valid project could reach the Discovery composer without a persisted Discovery session.

## Current release status

**MVP v1.0.2 release candidate — ready for owner validation.**

Production SaaS readiness is not claimed.
