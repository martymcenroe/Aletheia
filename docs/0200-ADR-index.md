# 0200 - Architecture Decision Records Index

## Purpose
This document indexes all Architecture Decision Records (ADRs) for Aletheia. ADRs document significant architectural decisions with their context, alternatives, and rationale.

## Template
Use `docs/0104-TEMPLATE-adr.md` when creating new ADRs.

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

---

## By Category

### Security
- [0201](0201-ADR-privacy-first-permissions.md) - Privacy-First Extension Permissions
- [0202](0202-ADR-shadow-dom-isolation.md) - Shadow DOM for Injected UI
- [0204](0204-ADR-defense-funnel.md) - Defense Funnel (Fail Fast)

### Privacy
- [0201](0201-ADR-privacy-first-permissions.md) - Privacy-First Extension Permissions

### Content Safety
- [0204](0204-ADR-defense-funnel.md) - Defense Funnel (Fail Fast)

### Infrastructure
- [0203](0203-ADR-stateful-serverless.md) - Stateful Serverless Pattern
- [0205](0205-ADR-langgraph-orchestration.md) - LangGraph for Agent Orchestration
- [0206](0206-ADR-streaming-sse.md) - Server-Sent Events for Streaming

### Data
- [0203](0203-ADR-stateful-serverless.md) - Stateful Serverless Pattern

### Integration
- [0205](0205-ADR-langgraph-orchestration.md) - LangGraph for Agent Orchestration

### Performance
- [0204](0204-ADR-defense-funnel.md) - Defense Funnel (Fail Fast)
- [0206](0206-ADR-streaming-sse.md) - Server-Sent Events for Streaming

### UX
- [0201](0201-ADR-privacy-first-permissions.md) - Privacy-First Extension Permissions
- [0202](0202-ADR-shadow-dom-isolation.md) - Shadow DOM for Injected UI
- [0206](0206-ADR-streaming-sse.md) - Server-Sent Events for Streaming

---

## Superseded ADRs

None yet.

---

## Adding New ADRs

1. Copy `docs/0104-TEMPLATE-adr.md`
2. Use next available number (currently 0207)
3. Name format: `0207-ADR-{short-topic}.md`
4. Fill in all sections (Security Risk Analysis is mandatory)
5. Update this index
6. Update `docs/0003-file-inventory.md`
