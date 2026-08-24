# CI Notes

## Genesis 0.1.1

The original GitHub failure was caused by `next build` detecting TypeScript while the
Studio package did not declare TypeScript or the required React/Node type packages.

Fixed by adding:
- `typescript`
- `@types/node`
- `@types/react`
- `@types/react-dom`
- explicit `tsconfig.json`
- `next-env.d.ts`

The workflow also uses `actions/checkout@v5` and `actions/setup-node@v5`.

The Node 20 messages in the previous run were action-runtime deprecation warnings,
not the cause of the failed build.
