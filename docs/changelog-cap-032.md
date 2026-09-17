# CAP-032 — External SSO / OIDC

## Working increment

- Added a provider-neutral external authentication boundary with OIDC as the first concrete adapter.
- Added one-time hashed SSO state with nonce and expiry to protect authorization callbacks against CSRF/replay.
- Added persisted provider/subject identity linking to existing AWE accounts.
- Added optional verified-email JIT provisioning, disabled by default.
- Added deterministic local mock OIDC mode for regression without an external identity provider.
- Added strict-mode public SSO start/callback endpoints without weakening API-key authentication or project authorization.
- Added persisted SSO identity/state migration `0007_sso`.
- SAML remains an adapter boundary for a subsequent increment; no fake SAML implementation is claimed.
