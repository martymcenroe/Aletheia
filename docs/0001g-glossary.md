# 0001g - Glossary

Key terms and concepts used throughout Aletheia documentation.

## Architecture Terms

| Term | Definition | Deep Dive |
|------|------------|-----------|
| **Defense Funnel** | 4-layer fail-fast pipeline: Selection Check → Denylist → Semantic → Transform. Each layer can block requests before reaching expensive LLM calls. | [ADR-0204](0204-ADR-defense-funnel.md) |
| **Digital Etymologist** | AI persona that returns structured etymological context as `{signal, gem, context}` JSON. Neutral, scholarly tone like a museum placard. | [LLD-1124](lld/done/1124-digital-etymologist.md) |
| **Hydration/Dehydration** | Pattern for Lambda state persistence. Hydrate = load state from DynamoDB at request start. Dehydrate = save state back at request end. | [ADR-0203](0203-ADR-stateful-serverless.md) |
| **Museum Label** | The overlay UI that displays etymological context. Named for its concise, informative style like museum exhibit labels. | [LLD-1125](lld/done/1125-museum-label-ui.md) |
| **Naked Python** | Architecture pattern using direct boto3 calls instead of frameworks like LangChain. Minimizes cold start and dependencies. | [ADR-0211](0211-ADR-naked-python-architecture.md) |
| **Stateful Serverless** | Pattern combining AWS Lambda (stateless) with DynamoDB (persistent state) to maintain conversation context across requests. | [ADR-0203](0203-ADR-stateful-serverless.md) |

## Response Structure

| Term | Definition | Example |
|------|------------|---------|
| **Signal** | 2-4 word classification of the term | "Archaic Pejorative", "Regional Slang" |
| **Gem** | Single sentence summary, max 25 words | "Once clinical, now outdated and considered offensive." |
| **Context** | 3 sentences of historical detail, max 100 words | Full etymological background |

## Process Terms

| Term | Definition | Deep Dive |
|------|------------|-----------|
| **AgentOS** | The documentation system that treats AI agents as team members requiring onboarding and SOPs. Docs are executable instructions, not just reference. | [0000-GUIDE](0000-GUIDE.md) |
| **Claude-Staging Pattern** | Workflow where Claude stages changes for human approval before committing. Never auto-commits. | [ADR-0214](0214-ADR-claude-staging-pattern.md) |
| **Dual-AI Review** | Review process using both Claude Code and Gemini CLI. Gemini reviews LLDs and implementations before merge. | [CLAUDE.md](../CLAUDE.md) |
| **Pre-Merge Gate** | Mandatory checkpoint requiring implementation report, test report, and review approval before any merge. | [0004-orchestration-protocol](0004-orchestration-protocol.md) |
| **Worktree Isolation** | Each feature gets its own git worktree. Code never committed directly to main. | [ADR-0210](0210-ADR-git-worktree-isolation.md) |

## Security Terms

| Term | Definition | Deep Dive |
|------|------------|-----------|
| **Denylist** | 803 terms from Wikipedia's "List of ethnic slurs" used for deterministic blocking. Only hash stored, never the term itself. | [LLD-1121](lld/done/1121-wikipedia-denylist.md) |
| **Shadow DOM** | Browser API for DOM encapsulation. All Aletheia UI uses closed Shadow DOM to prevent style bleed and XSS. | [ADR-0202](0202-ADR-shadow-dom-isolation.md) |
| **activeTab Permission** | Chrome extension permission granting temporary access only when user interacts. Safer than `<all_urls>`. | [ADR-0201](0201-ADR-privacy-first-permissions.md) |

## Infrastructure Terms

| Term | Definition |
|------|------------|
| **Cold Start** | First Lambda invocation after idle period. Includes runtime init (~200ms) and handler init (~600ms). |
| **SSE (Server-Sent Events)** | One-way streaming from server to client. Used for progressive response delivery. |
| **TTL (Time-To-Live)** | DynamoDB feature that auto-deletes items after expiration. Set to 24h for privacy. |
| **WAF (Web Application Firewall)** | AWS service providing rate limiting and request filtering. Protects API Gateway. |

## Document Types

| Term | Definition | Location |
|------|------------|----------|
| **ADR** | Architecture Decision Record. Documents significant decisions with context and rationale. | `docs/02xx-ADR-*.md` |
| **LLD** | Low-Level Design. Detailed feature specification before implementation. | `docs/lld/` |
| **Audit** | Verification procedure checking specific compliance area. | `docs/08xx-audit-*.md` |

---

[← Deployment View](0001f-deployment-view.md) | [Back to Architecture](0001-architecture.md)
