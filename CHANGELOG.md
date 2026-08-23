## Unreleased

### Added
- CAP-003 Studio integration for Brand & Design Direction review and approval.
- Studio persistence/reload of CAP-003 state.
- Visual direction presentation covering palette, typography, imagery, components, accessibility and rationale.

# Changelog

## CAP-003 v0.1.1 — Deployment Hardening

- Upgrade Next.js from 15.4.6 to 15.5.21.
- Upgrade React and React DOM from 19.1.1 to 19.1.9.
- Upgrade eslint-config-next to 15.5.21.
- Fix the ESM import for `eslint-config-next/core-web-vitals.js`.
- Explicitly allow `sharp` and `unrs-resolver` build scripts via pnpm `onlyBuiltDependencies`.
- Add deployment-hardening documentation and release-gate rules.
- Preserve `docs/project-master.md` as the living project record.
- Lockfile regeneration is intentionally deferred to the repository owner because this environment cannot access the pnpm registry.
\n\n## CAP-003 v0.1.2 — local validation hardening\n\n- Moved pnpm `onlyBuiltDependencies` from deprecated `package.json#pnpm` to `pnpm-workspace.yaml`.\n- Reworked Next.js ESLint configuration to use `@next/eslint-plugin-next` directly, avoiding the `nextVitals is not iterable` incompatibility observed with `eslint-config-next@15.5.21`.\n- Added `@next/eslint-plugin-next@15.5.21` as an explicit Studio dev dependency.\n- Made the Python API test command explicit as `python3 -m pytest`.\n- Updated GitHub CI to provision Python 3.12, install API requirements, and run the test suite.\n\nThese changes address the local `pnpm lint` and `pnpm test` failures reported after the CAP-003 deployment-hardening patch.\n