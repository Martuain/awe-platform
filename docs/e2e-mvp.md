# Local MVP end-to-end verification

## Purpose

`pnpm e2e:mvp` verifies the complete local product loop against the running Docker Compose stack. It creates a **new project** for every run and drives the API through the same capability boundaries exposed by Studio:

`Discovery → Strategy → Design → Website Specification → Generation → Build → Validation → Deployment → live HTTP response`

The script intentionally does not reuse Studio localStorage or an existing project, so a successful run proves that a brand-new project can reach a running generated website.

## Prerequisites

Install the repository dependencies first:

```bash
pnpm install
python3 -m pip install -r apps/api/requirements.txt
```

Then start the executable stack:

```bash
pnpm mvp:up
```

The API container must be rebuilt after Docker-adapter changes:

```bash
docker compose up --build -d
```

## Run

From the repository root:

```bash
pnpm e2e:mvp
```

The verification performs these checks:

1. Creates a fresh project.
2. Confirms the API still rejects an uninitialized Discovery message.
3. Starts Discovery and completes a minimal business interview.
4. Approves Business Discovery.
5. Generates and approves Website Strategy.
6. Generates and approves Brand & Design Direction.
7. Generates and approves Website Specification.
8. Generates the deterministic Next.js website artifact.
9. Plans and executes the isolated Docker build.
10. Validates the generated artifact.
11. Deploys the site through the local deployment provider.
12. Performs an HTTP request against the returned live URL and verifies the workspace records the deployment.

The final deployment is intentionally left running so the URL can be opened in a browser for owner validation.

Build execution uses separate phase budgets: dependency installation defaults to 300 seconds and the offline production build defaults to 180 seconds. The E2E runner allows up to 480 seconds for the API request that encompasses the build operation.

## Docker boundary

The local API container uses the Docker CLI and the host Docker socket to invoke disposable `node:22-alpine` containers for build and preview execution. The generated application is **not** executed inside the FastAPI process.

This socket mount is a deliberate local-MVP convenience and is **not** a production SaaS isolation model. Hosted/scalable build workers and a stronger execution boundary remain deferred.

## Troubleshooting

If the script reports that Docker is unavailable, rebuild the API image and confirm the socket is mounted:

```bash
docker compose up --build -d api

docker compose exec api docker version
```

If a previous test left deployments running, inspect them with:

```bash
docker ps
```

and stop the relevant disposable containers before rerunning the verification.
