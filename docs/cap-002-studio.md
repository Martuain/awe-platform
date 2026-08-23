# CAP-002 — Website Strategy Studio Experience

## Purpose

Expose the approved Business Discovery → Website Strategy transition as a real AWE Studio workflow.

## Product flow

```text
Project
  ↓
Business Discovery
  ↓
Human approval
  ↓
Website Strategy generation
  ↓
Evaluation
  ↓
Revision (optional)
  ↓
Human approval
  ↓
CAP-003 Design
```

## Studio responsibilities

- Create a project and start Discovery.
- Display captured business knowledge and Discovery completeness.
- Submit Discovery messages to the API.
- Require explicit Discovery approval before Strategy generation.
- Generate Strategy from the approved Discovery context.
- Display sitemap, positioning, messages, tone and design principles.
- Display the four deterministic Strategy evaluation dimensions.
- Allow user feedback/revision before approval.
- Prevent navigation to CAP-003 until Strategy is approved.

## API contract used

- `POST /api/v1/projects`
- `POST /api/v1/business-discovery/start`
- `GET /api/v1/business-discovery/context/{project_id}`
- `POST /api/v1/business-discovery/message`
- `POST /api/v1/business-discovery/approve/{project_id}`
- `POST /api/v1/website-strategy/generate`
- `GET /api/v1/website-strategy/{project_id}`
- `POST /api/v1/website-strategy/{project_id}/revise`
- `POST /api/v1/website-strategy/{project_id}/approve`

## Boundary

CAP-002 remains provider-independent. Studio consumes the capability contract and does not know whether the strategy was produced by the deterministic gateway or a future model gateway.
