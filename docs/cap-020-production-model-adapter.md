# CAP-020 — Production Model Adapter

## Objective

Introduce a real provider boundary without coupling AWE capabilities to a vendor SDK, while preserving deterministic local development and tests.

## Scope

- Keep the existing `ModelGateway` contract capability-facing.
- Add an OpenAI-compatible HTTP adapter using the Python standard library.
- Select the provider through environment configuration.
- Keep the deterministic mock as the default when no provider is configured.
- Fail explicitly on missing credentials, unsupported providers, provider errors, timeouts, and malformed responses.

## Configuration

```text
AWE_MODEL_PROVIDER=mock                  # default
AWE_MODEL_PROVIDER=openai-compatible
AWE_MODEL_API_KEY=...
AWE_MODEL_BASE_URL=https://api.openai.com/v1
AWE_MODEL_NAME=gpt-4o-mini
AWE_MODEL_TIMEOUT_SECONDS=60
```

`AWE_MODEL_BASE_URL` makes the adapter compatible with providers exposing the same chat-completions contract. Credentials are read only from environment variables and are never persisted in capability state.

## Safety / product boundary

CAP-020 does not claim production SaaS readiness. The deterministic mock remains the default, provider calls are opt-in, and the existing Discovery structured-output contract remains unchanged. Provider response validation is intentionally strict so malformed model output cannot silently corrupt Discovery state.

## Acceptance criteria

- [x] Provider-neutral gateway boundary remains intact.
- [x] Production HTTP adapter is opt-in.
- [x] Default local/test behavior remains deterministic.
- [x] Provider configuration is environment-driven.
- [x] Provider failures become explicit gateway errors.
- [x] Regression tests cover provider selection and request handling.
