# CAP-001 Business Discovery v1.1 — Validation

## Problem reproduced

The Studio could repeatedly display:

> AWE needs to know: What is the primary business goal for the website?

even after the user had supplied a natural-language goal.

The root cause was deterministic extraction in `apps/api/app/services/discovery.py`:
only a small fixed keyword list (`leads`, `enquiries`, `bookings`, `sales`,
`customers`, `visibility`) was recognized as a goal, and `open_questions`
was hard-coded to the same goal question whenever no keyword was found.

## Changes

- Natural-language goal patterns are now extracted from explicit goal/want/need/aim/website statements.
- Goal extraction removes presentation wording such as `help us` when appropriate.
- Knowledge is merged across messages instead of replacing the previous goal list.
- Audience and value proposition are captured when evidence is explicit.
- Open questions are derived from missing minimum fields.
- Industry + one goal remain the MVP approval gate.
- Audience and value proposition are retained as optional evidence and do not block approval.
- API modules using PEP 604 union annotations now use postponed annotation evaluation so the declared Python 3.9 local environment can import them; Docker remains Python 3.12.

## Automated validation

`python3 -m pytest apps/api/tests -q`

Result:

**18 passed**

The full `pnpm mvp:gate` could not be executed in the validation environment because
pnpm 10.0.0 is not installed locally and Corepack cannot download it without
network access. The repository's existing gate remains unchanged.
