# 0001d - ADR Digest

One-liner summaries of all Architecture Decision Records. Click through for full context, alternatives considered, and security analysis.

## Active ADRs

| ID | Title | One-Liner | Status |
|----|-------|-----------|--------|
| [0201](0201-ADR-privacy-first-permissions.md) | Privacy-First Extension Permissions | Never request `<all_urls>`; use `activeTab` only | Final |
| [0202](0202-ADR-shadow-dom-isolation.md) | Shadow DOM for Injected UI | All injected UI uses closed Shadow DOM for style isolation | Final |
| [0203](0203-ADR-stateful-serverless.md) | Stateful Serverless Pattern | DynamoDB hydration/dehydration for Lambda state persistence | Final |
| [0204](0204-ADR-defense-funnel.md) | Defense Funnel (Fail Fast) | 4-layer ordered pipeline: Selection → Denylist → Semantic → Transform | Final |
| [0205](0205-ADR-langgraph-orchestration.md) | LangGraph for Agent Orchestration | *Superseded by ADR-0211* | Superseded |
| [0206](0206-ADR-streaming-sse.md) | Server-Sent Events for Streaming | SSE via Lambda streaming for <500ms TTFB | Final |
| [0207](0207-ADR-single-identity-orchestration.md) | Single-Identity Orchestration | One orchestrator (human) coordinates all AI agents | Final |
| [0208](0208-ADR-client-side-preference-storage.md) | Client-Side Preference Storage | User preferences stored in browser, never sent to backend | Final |
| [0209](0209-ADR-static-compliance-hosting.md) | Static Compliance Hosting | Privacy policy/ToS on static S3/CloudFront, not in extension | Final |
| [0210](0210-ADR-git-worktree-isolation.md) | Git Worktree Isolation | Each feature gets isolated worktree, never commit to main | Final |
| [0211](0211-ADR-naked-python-architecture.md) | Naked Python Architecture | Replace LangChain with direct boto3 for minimal cold start | Final |
| [0212](0212-ADR-unified-v3-secure-dom.md) | Unified Manifest V3 & Secure DOM | Single codebase for Chrome MV3 and Firefox MV2 | Accepted |
| [0213](0213-ADR-adversarial-audit-philosophy.md) | Adversarial Audit Philosophy | Audits assume attacker mindset; verify, don't trust | Proposed |
| [0214](0214-ADR-claude-staging-pattern.md) | Claude-Staging Pattern | Stage changes, get approval, then commit (never auto-commit) | Final |
| [0215](0215-ADR-test-first-philosophy.md) | Test-First Philosophy | Tests specify behavior before implementation | Accepted |

## By Category

### Security & Privacy
- [0201](0201-ADR-privacy-first-permissions.md) - Minimal extension permissions
- [0202](0202-ADR-shadow-dom-isolation.md) - DOM isolation
- [0208](0208-ADR-client-side-preference-storage.md) - No server-side user data
- [0213](0213-ADR-adversarial-audit-philosophy.md) - Security-first audits

### Architecture & Performance
- [0203](0203-ADR-stateful-serverless.md) - State management
- [0204](0204-ADR-defense-funnel.md) - Request pipeline
- [0206](0206-ADR-streaming-sse.md) - Response streaming
- [0211](0211-ADR-naked-python-architecture.md) - Minimal dependencies
- [0212](0212-ADR-unified-v3-secure-dom.md) - Cross-browser architecture

### Process & Governance
- [0207](0207-ADR-single-identity-orchestration.md) - AI agent coordination
- [0210](0210-ADR-git-worktree-isolation.md) - Git workflow
- [0214](0214-ADR-claude-staging-pattern.md) - Change management
- [0215](0215-ADR-test-first-philosophy.md) - Testing approach

### Infrastructure
- [0209](0209-ADR-static-compliance-hosting.md) - Static hosting

## Superseded ADRs

| ID | Title | Superseded By | Reason |
|----|-------|---------------|--------|
| [0205](0205-ADR-langgraph-orchestration.md) | LangGraph Orchestration | [0211](0211-ADR-naked-python-architecture.md) | Framework overhead exceeded benefit for linear pipeline |

---

[← Runtime View](0001c-runtime-view.md) | [Back to Architecture](0001-architecture.md) | [Quality Attributes →](0001e-quality-attributes.md)
