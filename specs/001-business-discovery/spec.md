# Specification: Business Discovery

**ID:** CAP-001  
**Status:** Draft for implementation  
**Version:** 0.1.0

## Problem

SMB owners often know their business but cannot efficiently translate fragmented business information into the structured context required to build a differentiated website.

## Goal

Transform conversational and supplied business information into a structured, reviewable Business Knowledge Context.

## User

Primary MVP user: SMB owner.

## Inputs

- User conversation
- Optional existing website
- Optional business documents
- Optional competitor references
- Optional brand assets

## Outputs

The capability must produce a versioned context containing, where available:

- business identity
- industry
- goals
- target audiences
- products/services
- value proposition
- brand/tone information
- website objectives
- source messages/references
- confidence and completeness metadata

Unknown information must be represented as unknown rather than invented.

## AI loop

1. Discover
2. Structure
3. Infer only where evidence permits
4. Evaluate completeness and consistency
5. Ask targeted follow-up questions when required
6. Present the resulting context to the user
7. Wait for explicit approval
8. Freeze an approved version

## Human checkpoints

The MVP must require approval before the Business Knowledge Context is considered frozen.

## Non-functional requirements

- API-first
- model-agnostic
- observable
- deterministic persistence for approved contexts
- open-source-first implementation
- no direct model-provider calls from UI components

## Acceptance criteria

1. A project can be created through the API.
2. A Business Discovery session can be started.
3. User messages can be captured.
4. A structured context can be retrieved.
5. The context distinguishes known information from unknown information.
6. The UI can consume the API without direct AI-provider access.
7. Approval is represented as an explicit state transition.
