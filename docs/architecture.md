# AWE Architecture — Genesis

## Architectural stance

AWE is API-first, capability-driven, knowledge-first and model-agnostic.

```mermaid
flowchart TD
    U[SMB Owner] --> S[AWE Studio]
    S --> API[API Layer]
    API --> C[Capability Runtime]
    C --> CTX[Context Engine]
    CTX --> K[Knowledge Engine]
    C --> E[Evaluation]
    C --> M[Model Gateway]
    M --> L[LiteLLM / Provider Adapter]
    K --> DB[(PostgreSQL)]
    API --> R[(Redis)]
```

## MVP simplification

Genesis intentionally avoids:
- a graph database
- a distributed workflow engine
- autonomous multi-agent swarms
- multi-framework website output
- deployment automation

Those may be introduced only when implementation evidence justifies them.

## AI loop

```mermaid
flowchart LR
    D[Discover] --> P[Prepare]
    P --> PL[Plan]
    PL --> X[Execute]
    X --> E[Evaluate]
    E --> R[Reflect]
    R --> I[Improve]
    I --> A{Approval}
    A -->|Approved| F[Freeze]
    A -->|Needs work| D
```
