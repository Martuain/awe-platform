# CI Notes

The canonical CI workflow lives at `.github/workflows/ci.yml`.

It provisions Node.js 22 and Python 3.12, installs the locked pnpm dependency
graph plus API requirements, then runs lint, production build, tests and the
same `pnpm mvp:gate` used for local release validation.

The Studio ESLint configuration uses `@next/eslint-plugin-next` directly to
avoid the `nextVitals is not iterable` incompatibility observed with the
Next.js 15.5.21 dependency line.

Dependency lockfile updates should be made deliberately and reviewed as part
of release changes.
