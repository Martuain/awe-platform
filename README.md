# AWE Platform

**Genesis v0.1.0**

AWE (AI-native Website Engineering) is an API-first, model-agnostic platform for turning structured business knowledge into production-ready digital experiences.

> AWE Studio is the commercial product. AWE Framework/Core are platform concepts. They must not be confused with the AWE framework as a methodology.

## Genesis scope

This release is intentionally a walking skeleton:

1. Start the local platform.
2. Open the Studio.
3. Call the API.
4. Create a project.
5. Start Business Discovery.
6. Persist a first Business Knowledge context.

Website generation is deliberately deferred until the foundation and discovery loop work end-to-end.

## Stack

- Next.js + React + TypeScript
- FastAPI + Pydantic
- PostgreSQL
- Redis
- pnpm + Turborepo
- OpenAPI-first API contract
- Provider-agnostic AI boundary

Open-source-first is an architectural requirement, not a promise that every dependency is permissively licensed. Dependency licenses must be reviewed before commercial distribution.

## Run

```bash
corepack enable
pnpm install
docker compose up --build
```

Studio: http://localhost:3000  
API: http://localhost:8000  
API docs: http://localhost:8000/docs

## Repository status

This is an implementation baseline, not a finished SaaS product.
