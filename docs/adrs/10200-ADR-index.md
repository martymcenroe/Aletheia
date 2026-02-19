# 10200 - Architecture Decision Records Index

## Purpose
This document indexes all Architecture Decision Records (ADRs) for Aletheia. ADRs document significant architectural decisions with their context, alternatives, and rationale.

## Template
Use `AgentOS:templates/0104-adr-template` when creating new ADRs.

## Best Practice Reference
- [Michael Nygard's ADR article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub](https://adr.github.io/)

---

## ADR Index

| ID | Title | Status | Categories | Date |
|----|-------|--------|------------|------|
| [10201](10201-ADR-privacy-first-permissions.md) | Privacy-First Extension Permissions | Implemented | Security, Privacy, UX | 2025-12-21 |
| [10202](10202-ADR-shadow-dom-isolation.md) | Shadow DOM for Injected UI | Implemented | Security, UX | 2025-12-22 |
| [10203](10203-ADR-stateful-serverless.md) | Stateful Serverless Pattern | Implemented | Infrastructure, Data | 2025-12-15 |
| [10204](10204-ADR-defense-funnel.md) | Defense Funnel (Fail Fast) | Implemented | Security, Content Safety, Performance | 2025-12-15 |
| [10205](10205-ADR-langgraph-orchestration.md) | LangGraph for Agent Orchestration | Implemented | Infrastructure, Integration | 2025-12-15 |
| [10206](10206-ADR-streaming-sse.md) | Server-Sent Events for Streaming | Implemented | Infrastructure, UX, Performance | 2025-12-15 |
| [10207](10207-ADR-single-identity-orchestration.md) | Single-Identity Orchestration | Implemented | Process, Cost, Security | 2025-12-29 |
| [10208](10208-ADR-client-side-preference-storage.md) | Client-Side Preference Storage | Implemented | Privacy, UX, Data | 2025-12-29 |
| [10209](10209-ADR-static-compliance-hosting.md) | Static Compliance Hosting | Implemented | Compliance, Cost, Infra | 2025-12-29 |
| [10210](10210-ADR-git-worktree-isolation.md) | Git Worktree Isolation | Implemented | Process, Infra, UX | 2025-12-29 |
| [10211](10211-ADR-naked-python-architecture.md) | Naked Python Architecture | Implemented | Architecture, Performance | 2026-01-05 |
| [10212](10212-ADR-unified-v3-secure-dom.md) | Unified Manifest V3 & Secure DOM | Accepted | Security, Architecture | 2026-01-08 |
| [10213](10213-ADR-adversarial-audit-philosophy.md) | Adversarial Audit Philosophy | Proposed | Process, Security, Compliance | 2026-01-08 |
| [10214](10214-ADR-claude-staging-pattern.md) | Claude-Staging Pattern | Implemented | Process, Governance, Security | 2026-01-08 |
| [10215](10215-ADR-test-first-philosophy.md) | Test-First Philosophy | Accepted | Process, Testing, Quality | 2026-01-09 |
| [10216](10216-ADR-cloudflare-migration.md) | CloudFront+WAF to CloudFlare Migration | Implemented | Security, Infrastructure, Cost Optimization | 2026-02-16 |
| [10217](10217-ADR-jwt-authentication.md) | JWT Authentication Architecture | Implemented | Security, Authentication, Infrastructure | 2026-02-17 |
| [10218](10218-ADR-daily-token-cap.md) | Multi-Window Rate Limiting | Implemented | Infrastructure, Security, Cost Optimization | 2026-02-17 |
| [10219](10219-ADR-auth-middleware-pattern.md) | Decorator-Based Auth Middleware | Implemented | Architecture, Security, Patterns | 2026-02-17 |

---

## By Category

### Authentication
- [10217](10217-ADR-jwt-authentication.md)
- [10219](10219-ADR-auth-middleware-pattern.md)

### Cost Optimization
- [10207](10207-ADR-single-identity-orchestration.md)
- [10209](10209-ADR-static-compliance-hosting.md)
- [10216](10216-ADR-cloudflare-migration.md)
- [10218](10218-ADR-daily-token-cap.md)

### Process
- [10207](10207-ADR-single-identity-orchestration.md)
- [10210](10210-ADR-git-worktree-isolation.md)
- [10213](10213-ADR-adversarial-audit-philosophy.md)
- [10214](10214-ADR-claude-staging-pattern.md)
- [10215](10215-ADR-test-first-philosophy.md)

### Testing
- [10215](10215-ADR-test-first-philosophy.md)

### Quality
- [10215](10215-ADR-test-first-philosophy.md)

### Governance
- [10214](10214-ADR-claude-staging-pattern.md)

### Compliance
- [10209](10209-ADR-static-compliance-hosting.md)
- [10213](10213-ADR-adversarial-audit-philosophy.md)

### Security
- [10201](10201-ADR-privacy-first-permissions.md)
- [10202](10202-ADR-shadow-dom-isolation.md)
- [10204](10204-ADR-defense-funnel.md)
- [10207](10207-ADR-single-identity-orchestration.md)
- [10212](10212-ADR-unified-v3-secure-dom.md)
- [10213](10213-ADR-adversarial-audit-philosophy.md)
- [10214](10214-ADR-claude-staging-pattern.md)
- [10216](10216-ADR-cloudflare-migration.md)
- [10217](10217-ADR-jwt-authentication.md)
- [10218](10218-ADR-daily-token-cap.md)
- [10219](10219-ADR-auth-middleware-pattern.md)

### Privacy
- [10201](10201-ADR-privacy-first-permissions.md)
- [10208](10208-ADR-client-side-preference-storage.md)

### Content Safety
- [10204](10204-ADR-defense-funnel.md)

### Infrastructure
- [10203](10203-ADR-stateful-serverless.md)
- [10205](10205-ADR-langgraph-orchestration.md)
- [10206](10206-ADR-streaming-sse.md)
- [10209](10209-ADR-static-compliance-hosting.md)
- [10210](10210-ADR-git-worktree-isolation.md)
- [10216](10216-ADR-cloudflare-migration.md)
- [10217](10217-ADR-jwt-authentication.md)
- [10218](10218-ADR-daily-token-cap.md)

### Data
- [10203](10203-ADR-stateful-serverless.md)
- [10208](10208-ADR-client-side-preference-storage.md)

### Integration
- [10205](10205-ADR-langgraph-orchestration.md)

### Performance
- [10204](10204-ADR-defense-funnel.md)
- [10206](10206-ADR-streaming-sse.md)
- [10211](10211-ADR-naked-python-architecture.md)

### UX
- [10201](10201-ADR-privacy-first-permissions.md)
- [10202](10202-ADR-shadow-dom-isolation.md)
- [10206](10206-ADR-streaming-sse.md)
- [10208](10208-ADR-client-side-preference-storage.md)
- [10210](10210-ADR-git-worktree-isolation.md)

### Architecture
- [10211](10211-ADR-naked-python-architecture.md)
- [10212](10212-ADR-unified-v3-secure-dom.md)
- [10219](10219-ADR-auth-middleware-pattern.md)

### Patterns
- [10219](10219-ADR-auth-middleware-pattern.md)

---

## Superseded ADRs

None yet.

---

## Adding New ADRs

1. Copy `AgentOS:templates/0104-adr-template`
2. Use next available number (currently 10220)
3. Name format: `102xx-ADR-{short-topic}.md`
4. Fill in all sections (Security Risk Analysis is mandatory)
5. Update this index
6. Update `docs/standards/10003-file-inventory.md`
