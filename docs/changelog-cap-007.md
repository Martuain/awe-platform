# CAP-007 Changelog

## v0.7.0

### Added
- Website build planning contract.
- Sandbox-required execution boundary.
- Allowlisted Next.js build/runtime commands.
- Network-disabled-by-default policy.
- Deterministic diagnostics.
- API regression test.

### Security
Generated code is not executed by CAP-007. Dependency installation and
runtime execution are deferred until a real isolated execution adapter is
available.
