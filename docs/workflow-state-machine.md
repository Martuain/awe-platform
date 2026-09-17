# AWE Workflow State & Stage-Transition Rules

## Purpose

The AWE website-creation workflow is a state machine, not a collection of independently navigable Studio pages. Stage navigation must preserve project integrity, version identity, artifact provenance, and the user's ability to make deliberate changes without creating contradictory downstream state.

This document is a product/architecture invariant and applies across capabilities. A capability that changes a stage or transition must update this contract and its regression coverage.

## Core invariant

At every point in the workflow the platform must be able to determine:

1. the current project;
2. the current workflow stage;
3. which required upstream state/artifacts exist;
4. which website/content version the stage represents;
5. which forward and backward transitions are permitted; and
6. what downstream artifacts become stale, remain valid, or require regeneration after a transition.

A UI button is never, by itself, authorization to perform a workflow transition. The API/domain state must enforce the same rule.

## Canonical workflow

```text
Discovery
   ↓
Strategy
   ↓
Design
   ↓
Specification
   ↓
Build
   ↓
Validation
   ↓
Preview
   ↓
Deploy
```

This is the normal forward path. It is not a claim that every project must traverse the stages exactly once or that backward navigation is forbidden.

## Forward-transition rules

| From | To | Minimum condition |
|---|---|---|
| Discovery | Strategy | Required Discovery state exists and is usable |
| Strategy | Design | Required Strategy state exists and is usable |
| Design | Specification | Required Design state exists and is usable |
| Specification | Build | A valid, sufficiently complete specification exists |
| Build | Validation | A generated website artifact/version exists |
| Validation | Preview | A valid website version has passed the applicable validation gate |
| Preview | Deploy | The selected website version is deployable and satisfies deployment prerequisites |

A failed or incomplete prerequisite must block the transition rather than create partial downstream state.

## Backward-transition rules

Backward navigation is permitted where the product stage supports it, but it means **returning to an earlier state**, not silently deleting or rewriting downstream artifacts.

For example, moving from Preview to Design must not implicitly destroy deployment history, published content, immutable deployment snapshots, or other versioned artifacts.

When an earlier-stage state is changed, the platform must determine whether downstream artifacts are still semantically valid.

```text
Earlier-stage change
        ↓
Does it affect downstream meaning?
     ┌──┴──┐
    No     Yes
    ↓       ↓
 retain   mark affected state stale
             ↓
       require regeneration/
       revalidation where needed
```

### Required semantics

- **Preserve immutable history.** Existing generated/deployed versions and deployment history must not be rewritten merely because a user navigates backward.
- **Identify staleness explicitly.** If an earlier change invalidates a downstream artifact, mark that state/version as affected rather than pretending it remains current.
- **Do not silently promote stale state.** A stale build/validation/preview result must not become the current deployable version without the required work being repeated.
- **Keep version identity explicit.** Preview, validation and deployment must identify the exact website/content version they represent.
- **Separate inspection from mutation.** Navigating backward for review must not itself mutate downstream state.

## Stage-specific contract

### Discovery

- Entry requires a project identity.
- Discovery establishes the business context consumed by later stages.
- Returning to Discovery for additional information does not erase downstream history.
- Changes that materially affect later decisions may make dependent downstream state stale.

### Strategy

- Requires usable Discovery state.
- Strategy may be revised after returning from later stages.
- A material Strategy revision may invalidate dependent Design, Specification and generated artifacts.

### Design

- Requires usable Strategy state.
- Design revisions may invalidate the Specification and everything generated from it.
- Existing generated/deployed versions remain historical artifacts.

### Specification

- Requires usable Design state.
- Specification changes may require a new Build before Validation/Preview/Deploy can represent the new intent.

### Build

- Requires a valid Specification.
- A Build produces a versioned generated website artifact.
- A new Build must not overwrite the identity of an already validated/deployed version.

### Validation

- Operates on a specific generated website version.
- Validation status belongs to that version.
- Changing the source inputs after validation does not make the new source automatically validated.

### Preview

- Must render the intended published/validated Preview version, never an arbitrary stale runtime.
- Preview runtime identity and deployment runtime identity are separate concerns.
- Refresh, Validate and Publish operations must reconcile the runtime before presenting it as current.
- Navigation inside the iframe must remain within the preview website/runtime and must not accidentally route back to the Studio application.

### Deploy

- Deploys an explicitly eligible website version.
- Successful deployment creates immutable historical identity and, where applicable, persistent snapshot state.
- Historical deployment links must resolve to their selected deployment rather than silently substituting the latest deployment.
- Returning to earlier stages does not rewrite existing deployment history.

## Version/state integrity rules

The following are mandatory invariants:

1. **Current stage ≠ current version by implication.** The stage and represented version must both be explicit.
2. **Latest ≠ historical.** A historical deployment must never be resolved through a latest-deployment fallback.
3. **Published ≠ generated.** Publishing content updates the appropriate content state; it does not silently create a new generated website version unless the product explicitly says so.
4. **Validated ≠ merely generated.** Deployment cannot rely on generation alone when validation is a prerequisite.
5. **Preview ≠ deployment.** The Preview runtime must not accidentally serve a deployment snapshot, and deployment runtime state must not be used as Preview state merely because it is available.
6. **Navigation ≠ mutation.** Changing Studio stages must not silently mutate unrelated persistent artifacts.
7. **Failure ≠ success.** A failed transition must not leave a downstream stage appearing current or deployable.
8. **History is immutable.** Once a deployment/version is recorded, later edits do not rewrite its historical meaning.

## Transition matrix required for future CAPs

Every capability that changes workflow navigation must explicitly document:

- permitted forward transitions;
- permitted backward transitions;
- blocked transitions and the user-visible reason;
- prerequisites for each transition;
- artifacts affected by the transition;
- stale/invalidation behavior;
- version-selection behavior; and
- regression scenarios covering both directions.

## Regression gate

A workflow CAP is not complete until tests cover at least:

- a clean forward journey;
- forward navigation with missing prerequisites;
- backward navigation from later stages;
- backward edit followed by forward progression;
- stale downstream artifact handling;
- version identity across Preview and Deploy;
- failure recovery without falsely advancing the workflow; and
- restoration/reload of the project without losing the correct stage/version state.

## Relation to defect management

Workflow defects must be entered in `docs/defect-register.md` with their symptom, reproduction, root cause, fix, verification and troubleshooting path. Successful troubleshooting procedures belong in `docs/troubleshooting.md` so that future CAP work does not rediscover the same failure mode.

### Content-version authority across stages

CAP-036 regression establishes a strict distinction between **editable draft**, **published content**, and **immutable deployment snapshot**. A draft edit must not advance the website represented by Customer Website Mock or Preview. `Publish content → Live Preview` is the boundary that advances the published runtime content. `Deploy` creates the next immutable live deployment snapshot. Moving backward or forward between stages must not silently reinterpret a draft as published or mutate an existing deployment.
