# CAP-011 Changelog — Deployment UX & Lifecycle

## Added

- Deployment lifecycle model and API.
- Local deployment provider abstraction.
- Deployment history in the repository contract.
- Studio-ready deployment state/URL contract.
- API tests for successful, failed and stopped deployments.
- Master-document and ADR updates.

## Security

- Studio does not execute generated code.
- Deployment provider remains behind an API/service boundary.
- CAP-009 isolation is reused rather than introducing a second execution path.

## Deferred

- Permanent cloud provider selection.
- Custom domains, DNS/TLS and production secrets.
