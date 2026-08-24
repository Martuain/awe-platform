# CAP-006 — Preview & Validation

CAP-006 closes the gap between a generated website artifact and an observable result. It validates the CAP-005 artifact using deterministic structural checks and provides a safe browser preview rendered from validation metadata.

## Scope

- Validate the latest Website Generation artifact.
- Check required Next.js project files and page coverage.
- Produce diagnostics when structural checks fail.
- Produce a browser-safe HTML preview without executing generated application code inside Studio.
- Add a dedicated **06 Preview** stage to AWE Studio.

## API

`POST /api/v1/website-validation/validate?project_id={id}`

The response contains:

- validation status (`passed` / `failed`)
- generation version
- named boolean checks
- diagnostics
- preview metadata and HTML

## Validation boundary

CAP-006 deliberately does **not** execute arbitrary generated code inside the Studio process. The current validator is a deterministic structural gate. A later capability can introduce isolated sandbox builds and runtime previews once the execution boundary, resource limits and cleanup strategy are established.

## Checks

The initial checks verify:

1. A generation artifact exists.
2. `package.json` exists.
3. `app/layout.tsx` exists.
4. `app/globals.css` exists.
5. At least one page was generated.
6. Generated page files match the generation page list.
7. Generated page files expose a default `Page` export.

## Studio experience

The pipeline is now:

`01 Discovery → 02 Strategy → 03 Design → 04 Website Spec → 05 Generate → 06 Preview`

The Preview stage shows validation results and an iframe-based browser preview generated from the validated artifact metadata.

## Architectural rationale

CAP-005 proves that AWE can turn approved decisions into concrete project files. CAP-006 makes the result observable while keeping code execution outside the Studio trust boundary. This gives the project a safer foundation for a future isolated build/preview runner.
