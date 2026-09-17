# 009 — Complete Website Creation Journey

## Status
Working increment — CAP-033.

## Goal
Provide one coherent Studio journey from approved discovery through generation, customer review, executable build, validation, live preview and deployment completion.

## Acceptance criteria
- The customer mock is created from the same canonical generated website representation used by validation.
- The mock contains business-specific content, navigation and visual tokens rather than a generic placeholder page.
- The mock never executes generated application code.
- Mock revisions update the canonical preview representation together with the executable generated files.
- Reloading Studio does not probe future artifacts that do not yet exist.
- Approved mock remains the explicit gate into build.
- Build, validation, preview and deployment continue to use the existing isolated execution boundary.
- Deployment success provides a clear completion/live handoff.
- The generated runtime imports its generated global stylesheet so Mock, Browser Preview and Open in New Tab preserve the same visual design tokens and layout.

## Canonical preview representation
Each generation now emits `awe-preview.html` alongside the Next.js application files. It is generated in the same deterministic pass from the same strategy, design, specification and business context used to produce the executable pages. Validation and the Customer Website Mock consume this artifact for their safe HTML preview.

This is a safe representation: generated application code is not executed inside the mock iframe.
