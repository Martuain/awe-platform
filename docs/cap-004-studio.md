# CAP-004 — Website Specification

## Purpose

CAP-004 converts the approved Website Strategy and approved Brand & Design Direction into an implementation-ready **Website Specification**.

It is the bridge between product/design reasoning and code generation.

## Product boundary

CAP-004 does **not** generate a website. It defines what the future generation capability must build.

```text
Approved Discovery
        ↓
Approved Strategy
        ↓
Approved Design Direction
        ↓
CAP-004 Website Specification
        ↓
CAP-005 Website Generation
```

## Why this capability matters

Generating code directly from a conversational prompt makes the resulting implementation difficult to evaluate and reproduce. AWE instead creates progressively more concrete artifacts.

The Website Specification is the first artifact that should be sufficiently deterministic for a generation capability to consume without reopening upstream business decisions.

## Specification contents

### Page-level

Each approved sitemap page receives:

- path;
- name;
- objective;
- primary CTA;
- required sections;
- content requirements;
- component requirements.

### Global

The artifact also defines:

- shared components;
- content requirements;
- SEO requirements;
- accessibility requirements;
- responsive requirements;
- technical requirements;
- acceptance criteria;
- generation rationale.

## Traceability

The artifact records:

- `source_strategy_version`
- `source_design_version`

This makes the dependency explicit and prevents a specification from silently being based on an unapproved upstream artifact.

## Approval gate

A specification is generated as `ready_for_review` and becomes authoritative only after human approval:

```text
READY_FOR_REVIEW
      ↓
Human review
      ↓
APPROVED
```

The API rejects generation when Strategy or Design has not been approved.

## API

```text
POST /api/v1/website-specification/generate?project_id={id}
GET  /api/v1/website-specification/{id}
POST /api/v1/website-specification/{id}/approve
```

## Studio

The Studio now exposes a fourth pipeline stage:

```text
01 Discovery → 02 Strategy → 03 Design → 04 Website Spec
```

The specification view provides page-level implementation intent, global requirements and acceptance criteria, while retaining links back to the upstream Strategy and Design versions.

## Architectural decision

The Website Specification is an **artifact contract**, not a prompt transcript. Future generators should consume the structured artifact and produce code against its acceptance criteria.

This separation allows AWE to evaluate the specification independently from the implementation and later compare generated output against the approved contract.

## Next step

CAP-005 should consume only approved Website Specifications and generate the first real Next.js website artifact plus a previewable result.
