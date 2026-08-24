# CAP-005 — Website Generation

CAP-005 introduces the first concrete generation capability in AWE: an approved Website Specification can be consumed by a deterministic generator and turned into a runnable Next.js App Router project artifact.

## Product principle

AWE does not reopen upstream business decisions during generation. The generator consumes only an **approved Website Specification** and preserves the specification version as traceability metadata.

## Generation artifact

`WebsiteGeneration` records:

- generation ID and version;
- source specification version;
- generated framework;
- generated files;
- generated page paths;
- validation results;
- generation rationale.

## Deterministic generator

The first implementation is deliberately template-driven. This makes generation reproducible and testable before introducing LLM-driven code generation.

The generated artifact includes:

- `package.json`;
- App Router layout;
- global CSS;
- one page file for every approved sitemap page.

## Validation

Generation validates:

- specification is approved;
- every sitemap page is represented;
- every page has required sections;
- output targets Next.js App Router.

A successful generation is marked `validated`.

## API

```text
POST /api/v1/website-generation/generate?project_id={id}
GET  /api/v1/website-generation/{id}
```

Generation is rejected with `409` unless the Website Specification is approved.

## Architectural decision

CAP-005 separates **generation intent** from **generated implementation**. The current deterministic generator is a controlled baseline. Future LLM generation can replace the renderer while retaining the same input artifact and validation contract.

## Next step

CAP-006 should turn the generated artifact into a previewable/runnable website and introduce build validation of the generated project.
