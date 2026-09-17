# AWE Roadmap

## MVP — Website Engineering

### M0 Genesis
- [x] Repository bootstrap
- [x] API skeleton
- [x] Studio skeleton
- [x] Capability/context/knowledge interfaces
- [x] CAP-001 specification

### M1 Business Discovery
- [x] PostgreSQL persistence
- [x] Provider-neutral model gateway boundary with deterministic mock
- [x] Conversational discovery loop
- [x] Structured context extraction
- [x] Minimum completeness evaluation
- [x] Human approval lifecycle
- [x] Natural-language extraction and multi-turn accumulation hardening
- [x] Discovery session initialization lifecycle hardening

### M2 Website Strategy
- [x] Information architecture baseline
- [x] Sitemap baseline
- [x] Content strategy baseline
- [x] Design direction baseline
- [x] Strategy evaluation
- [x] Strategy revision workflow
- [x] Studio strategy review UI
- [x] Production model adapter
- [x] Migration hardening

### M3 Website Generation
- [x] Single supported framework baseline (Next.js App Router)
- [x] Responsive UI generation baseline
- [x] SEO/accessibility validation baseline
- [x] Preview
- [x] Build → validate → preview executable flow

### M4 Deployment
- [x] One-click deployment
- [x] Performance checks (CAP-022)
- [x] Monitoring (CAP-023)

## Post-MVP

- Collaborative intervention between stages
- Additional frameworks
- Plugins/marketplace
- Team features
- Billing
- Continuous optimization
- Additional digital-experience outputs

### M3 Website Generation — CAP-005 progress
- [x] Deterministic Website Generation artifact
- [x] Approved Website Specification gate
- [x] Next.js App Router file generation baseline
- [x] Generation validation contract
- [x] Deterministic artifact validation
- [x] Safe browser preview



### M3 Website Generation — CAP-007 progress
- [x] Build lifecycle contract
- [x] Explicit sandbox boundary
- [x] Ephemeral workspace strategy
- [x] Allowlisted build/runtime commands
- [x] Network-disabled-by-default policy
- [x] Deterministic build-plan diagnostics
- [x] Real isolated execution adapter
- [x] Disposable build workspace
- [ ] Long-lived disposable runtime
- [x] Live preview endpoint
- [x] Disposable live runtime


## CAP-010 — Deployment Abstraction
Provider-neutral deployment lifecycle with a deterministic local provider; permanent cloud selection deferred.


## CAP-011 — Deployment UX & Lifecycle
First-class deployment state, history, live URL and stop/redeploy lifecycle using the provider-neutral API.


## CAP-012 — Project Persistence & Workspace Model
- [x] Project listing API
- [x] Persistent workspace summary
- [x] Capability version visibility
- [x] Deployment history included in workspace state
- [x] Studio project switching
- [x] Repository abstraction preserved


## CAP-013 — Project Lifecycle & Workspace UX
- [x] Project lifecycle status (active/archived)
- [x] Reversible archive/restore API
- [x] Derived workspace progress
- [x] Next-capability visibility
- [x] Last activity visibility
- [x] Studio workspace summary
- [x] Lifecycle/workspace test coverage
- [x] Authentication and authorization (CAP-025)
- [x] Multi-tenancy and collaboration (CAP-030 team roles/invitations/project access)


- **CAP-014:** Project duplication / fresh workspace templates — implemented.


## CAP-015 — Executable Website Build & MVP Runtime Gate
- [x] Studio Build stage
- [x] Build-plan visibility
- [x] Existing isolated Docker execution surfaced in Studio
- [x] Successful build gate before preview/deployment
- [x] Build diagnostics
- [ ] Hosted/scalable build workers


## CAP-019 — Studio Generation Loop
- [x] Explicit Studio Build stage
- [x] Build-plan visibility and refresh
- [x] Isolated build execution with diagnostics
- [x] Explicit validation gate
- [x] Preview as the post-validation stage
- [x] Deployment as an explicit pipeline stage
- [x] Deployment history restored on project load
- [x] Versioned deployment lifecycle and supersession semantics
- [x] Deployment requires validated generation
- [x] Studio uses canonical deployment API routes

## CAP-016 + CAP-017 — MVP acceleration
- [x] End-to-end Build → Validate → Preview Studio flow
- [x] Strategy/design traceability in generated output
- [x] Responsive generated-site baseline
- [x] SEO metadata baseline
- [x] Improved generated-site presentation
- [ ] Hosted/scalable execution
- [ ] Production cloud deployment provider

## CAP-018 + MVP v1.0 — Release Gate
- [x] Canonical repository MVP gate
- [x] Local executable stack command
- [x] MVP release criteria documented
- [x] Technology decisions and post-MVP deferrals documented
- [x] MVP release ADR
- [x] Fresh-project end-to-end verification through a running local deployment
- [x] Live HTTP smoke check against the generated website

### MVP v1.0 status
- Release candidate: **ready for owner validation**
- Production SaaS readiness: **not claimed**


## CAP-020 — Production Model Adapter
- [x] Provider-neutral OpenAI-compatible HTTP adapter
- [x] Environment-driven provider selection
- [x] Deterministic mock remains default
- [x] Explicit provider error handling
- [x] Regression coverage


## CAP-022 + CAP-023 — Deployment Operations
- [x] Generated-artifact performance budget checks
- [x] Studio performance-check surface
- [x] API monitoring summary
- [x] Studio monitoring surface
- [x] Regression coverage
- [ ] Browser/Core Web Vitals measurement
- [ ] External metrics/alerting backend

## CAP-024 — Hosted/Scalable Execution & Production Deployment Boundary
- [x] Provider-neutral build execution interface
- [x] Local Docker execution retained as default
- [x] Opt-in hosted HTTP build adapter
- [x] Provider-neutral deployment selection
- [x] Opt-in hosted HTTP deployment adapter
- [x] Explicit provider failure handling
- [ ] Production worker fleet / durable queue
- [ ] Artifact registry
- [ ] Production cloud provider integration
- [ ] Autoscaling and zero-downtime orchestration


## CAP-025 — Security & Access Boundary
- [x] Explicit development/strict authentication modes
- [x] Database-backed user and session model
- [x] API-key authentication and lifecycle
- [x] API-key scopes
- [x] Project ownership and server-side authorization
- [x] Cross-owner negative regression coverage
- [x] Security ADR and Project Master record
- [x] External SSO/OIDC boundary (CAP-032); SAML adapter deferred
- [x] Team roles, invitations and collaboration
- [x] Account recovery/email verification

## CAP-026 — Customer Website Mock

**Status: Implemented in working increment**

Introduce a first-class, safe customer-facing website mock between generation and executable build. The mock is persisted by generation version and requires explicit customer approval before build.

## CAP-027 — Visual Refinement / Feedback Loop

**Status: Implemented in working increment**

Capture review feedback and produce immutable mock/generation revisions. The first deterministic refinement contract supports explicit `headline:` and `cta:` instructions; richer model-driven visual editing remains deferred until the provider/model boundary is expanded.

## CAP-028 — Mock → Executable Preview

**Status: Implemented in working increment**

Make approved mock acceptance the gate into the existing isolated build, validation and preview path. Reuse the established execution boundary rather than introducing a second runtime.


## CAP-029 — Browser/Core Web Vitals Validation
- [x] Disposable Chromium browser validation boundary
- [x] Browser HTTP/rendering check
- [x] FCP/LCP/INP/CLS/TTFB measurement
- [x] Advisory performance budgets
- [x] Studio browser/Web Vitals surface
- [x] No external observability dependency


### CAP-030 — Team Roles, Invitations & Collaboration
- [x] Tenant-scoped team membership
- [x] Admin/member roles
- [x] Invitation creation with hashed one-time token
- [x] Invitation expiry and email binding
- [x] Team membership access to projects
- [x] Server-side tenant-aware project authorization
- [x] API-key restriction for team administration
- [ ] External SSO/OIDC/SAML
- [ ] Rich role/permission matrix
- [ ] Invitation email delivery
- [ ] Cross-tenant switching UX


### CAP-031 — Account Recovery & Email Verification
- [x] Email verification state on accounts
- [x] Single-use, hashed verification tokens with expiry
- [x] Password-reset request/confirmation flow
- [x] Single-use, hashed reset tokens with short expiry
- [x] Generic request responses to avoid account enumeration
- [x] No plaintext token persistence
- [x] Development-only token exposure for local verification
- [ ] Transactional email provider / delivery


### CAP-032 — External SSO / OIDC
- [x] Provider-neutral SSO boundary
- [x] OIDC authorization-code flow
- [x] One-time hashed state + nonce + expiry
- [x] ID-token signature, issuer, audience, expiry and nonce validation
- [x] Existing-account identity linking
- [x] Optional verified-email JIT provisioning (disabled by default)
- [x] Deterministic mock IdP mode for local regression
- [ ] SAML adapter

### CAP-033 — Complete Website Creation Journey
- [x] Coherent Studio stages through deployment
- [x] Durable artifact hydration avoids probing future stages
- [x] Customer mock approval gates executable build
- [x] Canonical safe preview artifact shared by generation/validation/mock
- [x] Mock revision keeps canonical preview synchronized for supported feedback
- [x] Durable persisted build/validation/preview execution state across reloads
- [ ] Production deployment infrastructure (tracked separately under CAP-024)


## CAP-034 — Website Content & Data Management Foundation
- Status: implementation increment complete; local regression/deployment pending.
- Persistent project-scoped content, draft/published lifecycle, and version history established.
- Generated-site consumption and Studio editor are the next increment.

## CAP-036 — End-to-End Customer Journey
- [ ] Fresh-project customer journey verified from creation through live deployment
- [x] Post-deployment completion state exposes live deployment and return-to-editing path
- [x] Deployed projects can reopen Website Content editing without regeneration
- [ ] Full Studio/browser journey regression frozen with evidence
- [x] Customer Website Mock iframe navigation isolation hardened and regression-covered

### CAP-036 Customer Mock correction — fix-24
- [x] Preserve Mock iframe isolation from AWE Studio
- [x] Render Mock from latest persisted website content rather than canonical generation-only HTML
- [x] Preserve supported internal Mock navigation inside the iframe
- [x] Add focused API and Studio regression coverage
- [ ] Browser regression: verify latest modified content + Home/About/Services/Contact navigation in local Docker deployment
