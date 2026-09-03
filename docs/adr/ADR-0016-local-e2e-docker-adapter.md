# ADR-0016 — Local End-to-End Docker Adapter for MVP Verification

**Status:** Accepted  
**Date:** 2026-09-02

## Context

The AWE MVP already defines a disposable Docker execution adapter for generated websites, but the API Compose service did not expose the Docker CLI/socket required to invoke that adapter. As a result, repository-level tests could pass while a real fresh-project flow stopped before a running website.

The MVP needs a deterministic way to verify the actual product loop without introducing hosted workers or another orchestration system.

## Decision

For the **local MVP only**, the API container receives the Docker CLI and a read/write bind mount of the host Docker Unix socket. The existing build and preview services continue to launch disposable `node:22-alpine` containers with their existing CPU, memory, PID, filesystem and network restrictions.

The canonical executable verification command is:

```text
pnpm e2e:mvp
```

It creates a fresh project, drives all approval gates, executes the build, deploys the generated site and performs an HTTP request against the returned live URL.

## Why

- It closes the gap between unit/API tests and the actual local product loop.
- It reuses the existing Docker execution adapter instead of introducing a new worker architecture.
- It keeps the generated application outside the FastAPI process.
- It is easy to replace later with a hosted/scalable worker boundary.

## Security boundary

The Docker socket is effectively a high-privilege local control interface. This is therefore an **explicit local-development/MVP trade-off**, not a production isolation model. The API service must not be exposed as an untrusted multi-tenant workload using this configuration.

The generated build/preview containers remain separately constrained, but the host Docker daemon itself is trusted by this local configuration.

## Consequences

- `docker compose up --build` can execute the local build/preview adapter from the API container.
- `pnpm mvp:gate` remains fast and package-focused.
- `pnpm e2e:mvp` becomes the runtime verification command for a complete fresh-project iteration.
- Hosted/scalable build workers and stronger isolation remain deferred until post-MVP architecture work.
