# AWE Platform --- Environment, Tooling & Configuration Baseline

**Repository:** AWE Platform Genesis — v0.1.1 baseline\
**Status:** GREEN baseline\
**Purpose:** Document the environment/configuration issues encountered
during initial stabilization, the fixes applied, the role of the main
tooling, and the remaining improvements before returning to
product/application development.

## 1. Executive summary

The repository is now in a stable development state.

Final validation:

``` bash
pnpm lint && pnpm build && pnpm test
```

Result:

-   **Lint:** PASS
-   **Production build:** PASS
-   **Tests:** PASS --- 3/3 API tests
-   **ESLint:** 9.39.5
-   **Next.js:** 15.5.21
-   **Python:** 3.12.14
-   **pytest:** 8.4.2
-   **pnpm:** 10.0.0
-   **Turbo:** 2.10.11
-   **Git:** known-good checkpoint committed

This should now be treated as the **known-good baseline**.

------------------------------------------------------------------------

## 2. Tooling: what it is and why AWE uses it

### ESLint

ESLint is a static-analysis and code-quality tool for JavaScript and
TypeScript. It detects coding errors, problematic patterns,
unused/invalid code, and framework-specific issues.

AWE uses it because Studio is built with Next.js, React and TypeScript,
and the platform is expected to grow beyond a prototype. Linting
provides an automated quality gate before code reaches production.

Current relevant versions:

``` text
eslint              9.39.5
eslint-config-next   15.5.21
next                 15.5.21
```

The project uses ESLint's modern flat-config system.

### pnpm

pnpm is the Node.js package manager used by AWE.

It manages dependencies, development dependencies, workspace packages,
lockfiles and executable binaries.

AWE is a monorepo containing multiple applications and packages, so pnpm
is appropriate because it provides:

-   workspace-aware dependency management
-   efficient shared storage
-   deterministic dependency resolution
-   package-level dependency isolation
-   workspace filtering

The repository declares:

``` json
"packageManager": "pnpm@10.0.0"
```

and:

``` yaml
packages:
  - "apps/*"
  - "packages/*"
```

### Turborepo

Turborepo is the monorepo task orchestrator/build system.

It coordinates:

-   lint
-   build
-   test
-   dev

across packages, with dependency-aware execution and caching.

AWE uses Turbo because the platform has multiple apps/packages. Instead
of manually running commands in each package, the root provides:

``` bash
pnpm dev
pnpm lint
pnpm build
pnpm test
```

Turbo then determines which workspace tasks need to run.

Current version:

``` text
2.10.11
```

------------------------------------------------------------------------

## 3. Repository tooling model

Root `package.json`:

``` json
{
  "packageManager": "pnpm@10.0.0",
  "scripts": {
    "dev": "turbo dev",
    "build": "turbo build",
    "lint": "turbo lint",
    "test": "turbo test",
    "format": "prettier --write ."
  }
}
```

Conceptually:

``` text
pnpm
 └── Turbo
      ├── lint
      ├── build
      ├── test
      └── dev
```

------------------------------------------------------------------------

## 4. ESLint problems encountered

### 4.1 Next.js configuration could not be resolved

Initial error:

``` text
Error [ERR_MODULE_NOT_FOUND]:
Cannot find module .../eslint-config-next/core-web-vitals
```

The resolver suggested:

``` text
eslint-config-next/core-web-vitals.js
```

The configuration was updated to explicitly reference the `.js` module.

### 4.2 `nextVitals is not iterable`

The next failure was:

``` text
TypeError: nextVitals is not iterable
```

The imported Next configuration was inspected directly:

``` bash
node -e "import('eslint-config-next/core-web-vitals.js').then(m => console.log(m.default))"
```

The result showed an object containing:

``` text
extends: [
  ".../eslint-config-next/index.js",
  "plugin:@next/next/core-web-vitals"
]
```

Therefore the import was not a flat-config array that could simply be
spread.

### 4.3 `Plugin "" not found`

A subsequent configuration attempt produced:

``` text
TypeError: Plugin "" not found.
```

This confirmed that the configuration was still being interpreted
incorrectly by ESLint's flat-config processing.

### 4.4 `extends` not supported directly in flat config

The next diagnostic was:

``` text
A config object is using the "extends" key,
which is not supported in flat config system.
```

This identified the actual compatibility layer involved: a legacy-style
`extends` configuration was reaching ESLint's flat-config system in the
wrong form.

The Studio ESLint configuration was subsequently corrected and now
passes.

**Do not modify the working ESLint configuration again without a
concrete reason.**

------------------------------------------------------------------------

## 5. pnpm / node_modules installation problem

At one point:

``` bash
pnpm lint
```

failed with:

``` text
sh: eslint: command not found
```

and:

``` bash
pnpm exec eslint -v
```

returned:

``` text
Command "eslint" not found
```

Although `apps/studio/package.json` correctly declared:

``` json
"eslint": "^9.39.5"
```

the local installation state was inconsistent.

The important lesson is:

> A dependency can be declared correctly in `package.json` while its
> installed executable is missing or its workspace symlinks are broken.

The Studio package eventually showed a correct symlink:

``` text
apps/studio/node_modules/eslint
  -> ../../../node_modules/.pnpm/eslint@9.39.5/node_modules/eslint
```

and:

``` text
apps/studio/node_modules/.bin/eslint
```

was present.

Verification:

``` bash
cd apps/studio
pnpm exec eslint -v
```

returned:

``` text
v9.39.5
```

------------------------------------------------------------------------

## 6. Clean pnpm dependency recovery

The successful recovery was:

``` bash
rm -rf node_modules
rm -rf apps/studio/node_modules
rm -rf pnpm-lock.yaml
pnpm install
```

This regenerated a healthy dependency tree.

### Important caution

Deleting `pnpm-lock.yaml` was a recovery action for this inconsistent
local state. It should **not** be normal maintenance.

Normally:

``` bash
pnpm install --frozen-lockfile
```

should be used for reproducible CI/deployment installations.

------------------------------------------------------------------------

## 7. Python version problem

The API tests initially failed at:

``` python
value: str | None = None
```

with:

``` text
TypeError: unsupported operand type(s)
for |: 'type' and 'NoneType'
```

The machine was initially using:

``` text
Python 3.9.6
/usr/bin/python3
```

The `str | None` syntax requires Python 3.10+.

Python 3.12 was already installed through Homebrew:

``` text
/usr/local/opt/python@3.12
Python 3.12.14
```

A project virtual environment was then used.

Final runtime:

``` text
.venv/bin/python
Python 3.12.14
```

------------------------------------------------------------------------

## 8. Python virtual environment

The final API environment uses:

``` text
.venv/bin/python
Python 3.12.14
```

and:

``` text
.venv/bin/pytest
pytest 8.4.2
```

The API dependency stack includes:

``` text
fastapi==0.116.1
uvicorn==0.35.0
pydantic==2.11.7
sqlalchemy==2.0.43
asyncpg==0.30.0
redis==6.4.0
httpx==0.28.1
pytest==8.4.2
```

The successful installation command was:

``` bash
python -m pip install -r requirements.txt
```

------------------------------------------------------------------------

## 9. API tests

Final direct API execution:

``` text
Python 3.12.14
pytest 8.4.2

collected 3 items

tests/test_design.py .
tests/test_discovery.py .
tests/test_strategy.py .

3 passed
```

The repository-level Turbo test also passes.

------------------------------------------------------------------------

## 10. Turbo test output warning

Turbo initially reported:

``` text
WARNING no output files found for task @awe/api#test.
Please check your `outputs` key in `turbo.json`
```

The original configuration declared:

``` json
"test": {
  "dependsOn": ["^test"],
  "outputs": ["coverage/**"]
}
```

But the API test command is:

``` json
"test": "python3 -m pytest"
```

and does not currently generate a `coverage/` directory.

Therefore `coverage/**` was an incorrect Turbo output declaration.

It was removed.

Current conceptual test task:

``` json
"test": {
  "dependsOn": ["^test"]
}
```

This is correct for the current test setup.

Coverage can be added later when the project deliberately introduces
coverage tooling.

------------------------------------------------------------------------

## 11. Current Turbo task model

Current intended behavior:

``` text
build
  ├── depends on dependency-package builds
  └── caches .next/** and dist/**

dev
  ├── cache disabled
  └── persistent

lint
  └── dependency-aware

test
  └── dependency-aware
```

This gives the monorepo a scalable task model as more packages gain
implementations and tests.

------------------------------------------------------------------------

## 12. Final production build

Studio production build succeeds with:

``` text
Next.js 15.5.21

✓ Compiled successfully
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages (4/4)
✓ Collecting build traces
✓ Finalizing page optimization
```

Current generated routes include:

``` text
/
 /_not-found
```

------------------------------------------------------------------------

## 13. Final green gate

The final command:

``` bash
pnpm lint && pnpm build && pnpm test
```

completed successfully.

Result:

``` text
LINT  → PASS
BUILD → PASS
TEST  → PASS
```

API:

``` text
3 passed
```

No Turbo output warning remains.

This is the official **known-good baseline**.

------------------------------------------------------------------------

## 14. What should remain stable

Avoid unnecessary changes to:

-   ESLint major version
-   eslint-config-next
-   Next.js version
-   pnpm version
-   pnpm workspace structure
-   Python runtime
-   `.venv` approach
-   Turbo task architecture
-   current test `outputs` configuration
-   working Studio ESLint configuration

Tooling changes should be driven by a real requirement.

------------------------------------------------------------------------

# 15. Remaining environment/configuration improvements

These are improvements, not blockers.

### 15.1 Explicitly document Node.js version

The repository pins pnpm but does not yet explicitly pin/document the
supported Node.js version.

Recommended:

-   `.nvmrc`
-   `.node-version`
-   or equivalent documentation

CI should use the same Node version.

### 15.2 Explicitly document Python version

Recommended:

-   `.python-version`
-   `pyproject.toml`
-   setup documentation
-   CI runtime pin

The goal is to prevent macOS system Python 3.9 from being selected
accidentally.

### 15.3 Verify `.venv/` is ignored

The virtual environment should never be committed.

`.gitignore` should contain:

``` text
.venv/
```

### 15.4 Consider modernizing Python dependency management

`requirements.txt` works today.

As the backend grows, consider a more centralized Python project
configuration for:

-   runtime dependencies
-   development dependencies
-   pytest configuration
-   formatting/linting
-   Python version constraints

This is not urgent.

### 15.5 Add test coverage later

The current suite contains only three API tests.

When coverage becomes meaningful, add coverage tooling deliberately,
then restore a Turbo output such as:

``` json
"outputs": ["coverage/**"]
```

Do not add coverage merely to satisfy Turbo.

### 15.6 Add Studio/frontend tests

The Studio currently has a successful build but no meaningful frontend
test suite reported by Turbo.

Future tests should cover:

-   components
-   forms
-   state transitions
-   API interactions
-   important user journeys
-   accessibility-critical interactions

### 15.7 Add CI

A future CI pipeline should run:

``` bash
pnpm install --frozen-lockfile
pnpm lint
pnpm build
pnpm test
```

The CI environment should explicitly pin:

-   Node.js
-   pnpm
-   Python

### 15.8 Review pnpm build-script policy

The installation process reported build scripts for:

``` text
sharp
unrs-resolver
```

being handled through the workspace's allowed build dependency
configuration.

This should be reviewed when dependencies change, but it is not
currently a blocker.

------------------------------------------------------------------------

# 16. Product/application work can now resume

Infrastructure stabilization is complete.

The next phase should focus on the AWE product.

Recommended sequence:

### Phase A --- Product baseline

1.  Inspect the current Studio UI.
2.  Inspect the current API surface.
3.  Map package responsibilities.
4.  Identify placeholders versus implemented functionality.
5.  Define the first complete AWE workflow.

### Phase B --- First end-to-end workflow

The existing API tests suggest a natural domain sequence:

``` text
User
 ↓
Studio
 ↓
Project
 ↓
Discovery
 ↓
Strategy
 ↓
Design
 ↓
Generated output
```

### Phase C --- Studio/API integration

The next meaningful milestone is functional integration:

``` text
Studio UI
    ↓
API
    ↓
Domain logic
    ↓
Persistence / services
```

### Phase D --- Domain expansion

Then progressively implement:

-   project lifecycle
-   discovery
-   strategy
-   design
-   knowledge/context
-   capability execution
-   evaluation
-   plugins
-   persistence
-   authentication/authorization
-   observability

------------------------------------------------------------------------

# 17. Engineering contract going forward

The baseline should be protected by:

``` bash
pnpm lint
pnpm build
pnpm test
```

or:

``` bash
pnpm lint && pnpm build && pnpm test
```

A product change that breaks one of these gates should be treated as a
regression until understood.

The engineering rule is:

> **If lint, build and tests pass, the repository is technically healthy
> enough to continue product development.**

------------------------------------------------------------------------

# 18. Baseline snapshot

``` text
AWE Platform Genesis
────────────────────────────────────

Repository
  awe-platform-genesis-v0.1.0

Package management
  pnpm              10.0.0
  workspace         pnpm workspaces

Build system
  Turbo             2.10.11

Studio
  Next.js           15.5.21
  React             19.1.9
  ESLint            9.39.5
  TypeScript        5.9.3

API
  Python            3.12.14
  FastAPI           0.116.1
  Pydantic          2.11.7
  SQLAlchemy        2.0.43
  pytest            8.4.2

Validation
  Lint              PASS
  Build             PASS
  Tests             PASS
  API tests         3/3 PASS

Git
  Baseline commit   CREATED
  Working state     GREEN
```

------------------------------------------------------------------------

# 19. Final engineering principle

The stabilization work demonstrates an important rule:

> **Do not solve environment problems by changing application code.**

The failures came from different layers:

-   package-manager installation state
-   ESLint flat-config semantics
-   Next.js configuration format
-   Python runtime version
-   Turbo task output declarations

Each was isolated and fixed at the correct layer.

The preferred workflow going forward is:

``` text
Observe
  ↓
Isolate
  ↓
Identify the layer
  ↓
Fix the layer
  ↓
Run lint/build/test
  ↓
Commit the known-good state
  ↓
Continue product development
```

The AWE repository is now at that final step: **the tooling baseline is
green and product development can resume.**
