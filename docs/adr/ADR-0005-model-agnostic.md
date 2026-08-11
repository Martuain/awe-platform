# ADR-0005 — Model Agnosticism

## Status
Accepted

## Decision
Capabilities use a provider-neutral ModelGateway. Provider-specific SDKs are isolated behind adapters.

## Consequence
Models can be swapped or self-hosted without rewriting capability logic.
