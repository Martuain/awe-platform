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
- [ ] Production model adapter
- [ ] Migration hardening

### M3 Website Generation
- [x] Single supported framework baseline (Next.js App Router)
- [x] Responsive UI generation baseline
- [x] SEO/accessibility validation baseline
- [x] Preview
- [x] Build → validate → preview executable flow

### M4 Deployment
- [ ] One-click deployment
- [ ] Performance checks
- [ ] Monitoring

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
- [ ] Authentication and authorization
- [ ] Multi-tenancy and collaboration


- **CAP-014:** Project duplication / fresh workspace templates — implemented.


## CAP-015 — Executable Website Build & MVP Runtime Gate
- [x] Studio Build stage
- [x] Build-plan visibility
- [x] Existing isolated Docker execution surfaced in Studio
- [x] Successful build gate before preview/deployment
- [x] Build diagnostics
- [ ] Hosted/scalable build workers


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
