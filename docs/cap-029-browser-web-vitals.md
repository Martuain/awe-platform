# CAP-029 — Browser/Core Web Vitals Validation

## Status
Implemented in working increment; automated verification pending local Docker browser image pull.

## Goal
Add a real browser-level quality check after an approved generation has been built and a disposable live preview is running.

## Scope
- Launch Chromium in a disposable Docker container.
- Navigate to the active disposable preview.
- Verify HTTP response and browser-rendered page.
- Collect First Contentful Paint (FCP), Largest Contentful Paint (LCP), Interaction to Next Paint (INP), Cumulative Layout Shift (CLS), Time to First Byte (TTFB), DOMContentLoaded and load timing where available.
- Apply advisory budgets: FCP 1800 ms, LCP 2500 ms, INP 200 ms, CLS 0.1, TTFB 800 ms.
- Surface results in Studio.
- No external metrics/alerting backend.

## Boundary
The browser audit is separate from deterministic artifact validation and does not replace it. It requires an active validated disposable preview and runs in its own disposable browser container.

## Operational note
The first run may pull `mcr.microsoft.com/playwright:v1.55.0-noble`; subsequent runs reuse the local image.
