# ADR-0001 — Capability-Driven Architecture

## Status
Accepted

## Decision
Capabilities are the stable business-facing execution boundary. Agents, prompts and models are internal implementation mechanisms.

## Rationale
AI models and orchestration techniques evolve faster than business capabilities. Stable capability contracts reduce vendor and implementation coupling.

## Consequence
The platform SDK and API expose capabilities, not individual agents.
