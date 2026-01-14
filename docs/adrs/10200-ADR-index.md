# 0200 - Architecture Decision Records Index

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
| [0201](0201-ADR-privacy-first-permissions.md) | Privacy-First Extension Permissions | Implemented | Security, Privacy, UX | 2025-12-21 |
| [0202](0202-ADR-shadow-dom-isolation.md) | Shadow DOM for Injected UI | Implemented | Security, UX | 2025-12-22 |
| [0203](0203-ADR-stateful-serverless.md) | Stateful Serverless Pattern | Implemented | Infrastructure, Data | 2025-12-15 |
| [0204](0204-ADR-defense-funnel.md) | Defense Funnel (Fail Fast) | Implemented | Security, Content Safety, Performance | 2025-12-15 |
| [0205](0205-ADR-langgraph-orchestration.md) | LangGraph for Agent Orchestration | Implemented | Infrastructure, Integration | 2025-12-15 |
| [0206](0206-ADR-streaming-sse.md) | Server-Sent Events for Streaming | Implemented | Infrastructure, UX, Performance | 2025-12-15 |
| [0207](AgentOS:adrs/0201-single-identity-orchestration) | Single-Identity Orchestration | Implemented | Process, Cost, Security | 2025-12-29 |
| [0208](0208-ADR-client-side-preference-storage.md) | Client-Side Preference Storage | Implemented | Privacy, UX, Data | 2025-12-29 |
| [0209](0209-ADR-static-compliance-hosting.md) | Static Compliance Hosting | Implemented | Compliance, Cost, Infra | 2025-12-29 |
| [0210](AgentOS:adrs/0202-git-worktree-isolation) | Git Worktree Isolation | Implemented | Process, Infra, UX | 2025-12-29 |
| [0211](0211-ADR-naked-python-architecture.md) | Naked Python Architecture | Implemented | Architecture, Performance | 2026-01-05 |
| [0212](0212-ADR-unified-v3-secure-dom.md) | Unified Manifest V3 & Secure DOM | Accepted | Security, Architecture | 2026-01-08 |
| [0213](AgentOS:adrs/0203-adversarial-audit-philosophy) | Adversarial Audit Philosophy | Proposed | Process, Security, Compliance | 2026-01-08 |
| [0214](AgentOS:adrs/0204-claude-staging-pattern) | Claude-Staging Pattern | Implemented | Process, Governance, Security | 2026-01-08 |
| [0215](AgentOS:adrs/0205-test-first-philosophy) | Test-First Philosophy | Accepted | Process, Testing, Quality | 2026-01-09 |

---

## By Category

### Cost Optimization
- [0207](AgentOS:adrs/0201-single-identity-orchestration)
- [0209](0209-ADR-static-compliance-hosting.md)

### Process
- [0207](AgentOS:adrs/0201-single-identity-orchestration)
- [0210](AgentOS:adrs/0202-git-worktree-isolation)
- [0213](AgentOS:adrs/0203-adversarial-audit-philosophy)
- [0214](AgentOS:adrs/0204-claude-staging-pattern)
- [0215](AgentOS:adrs/0205-test-first-philosophy)

### Testing
- [0215](AgentOS:adrs/0205-test-first-philosophy)

### Quality
- [0215](AgentOS:adrs/0205-test-first-philosophy)

### Governance
- [0214](AgentOS:adrs/0204-claude-staging-pattern)

### Compliance
- [0209](0209-ADR-static-compliance-hosting.md)
- [0213](AgentOS:adrs/0203-adversarial-audit-philosophy)

### Security
- [0201](0201-ADR-privacy-first-permissions.md)
- [0202](0202-ADR-shadow-dom-isolation.md)
- [0204](0204-ADR-defense-funnel.md)
- [0207](AgentOS:adrs/0201-single-identity-orchestration)
- [0212](0212-ADR-unified-v3-secure-dom.md)
- [0213](AgentOS:adrs/0203-adversarial-audit-philosophy)
- [0214](AgentOS:adrs/0204-claude-staging-pattern)

### Privacy
- [0201](0201-ADR-privacy-first-permissions.md)
- [0208](0208-ADR-client-side-preference-storage.md)

### Content Safety
- [0204](0204-ADR-defense-funnel.md)

### Infrastructure
- [0203](0203-ADR-stateful-serverless.md)
- [0205](0205-ADR-langgraph-orchestration.md)
- [0206](0206-ADR-streaming-sse.md)
- [0209](0209-ADR-static-compliance-hosting.md)
- [0210](AgentOS:adrs/0202-git-worktree-isolation)

### Data
- [0203](0203-ADR-stateful-serverless.md)
- [0208](0208-ADR-client-side-preference-storage.md)

### Integration
- [0205](0205-ADR-langgraph-orchestration.md)

### Performance
- [0204](0204-ADR-defense-funnel.md)
- [0206](0206-ADR-streaming-sse.md)
- [0211](0211-ADR-naked-python-architecture.md)

### UX
- [0201](0201-ADR-privacy-first-permissions.md)
- [0202](0202-ADR-shadow-dom-isolation.md)
- [0206](0206-ADR-streaming-sse.md)
- [0208](0208-ADR-client-side-preference-storage.md)
- [0210](AgentOS:adrs/0202-git-worktree-isolation)

### Architecture
- [0211](0211-ADR-naked-python-architecture.md)
- [0212](0212-ADR-unified-v3-secure-dom.md)

---

## Superseded ADRs

None yet.

---

## Adding New ADRs

1. Copy `AgentOS:templates/0104-adr-template`
2. Use next available number (currently 0216)
3. Name format: `02xx-ADR-{short-topic}.md`
4. Fill in all sections (Security Risk Analysis is mandatory)
5. Update this index
6. Update `docs/0003-file-inventory.md`
