# 0003 - File Inventory & Map

## 00xx Core Architecture
| File | Role | Linked Issue | Description |
| :--- | :--- | :--- | :--- |
| `docs/0000-GUIDE.md` | **Guide** | - | The "Start Here" manual for AI agents. |
| `docs/0001-system-architecture.md` | **Master** | - | The high-level design, "Stateful Serverless" pattern, and performance budgets. |
| `docs/0002-coding-standards.md` | **Rules** | - | Style guides, linting rules, and naming conventions. |
| `docs/0003-file-inventory.md` | **Meta** | - | This file. The map of the repository. |
| `docs/0004-orchestration-protocol.md` | **Process** | #48 | The Single-User Orchestrator workflow and Emergency Recovery protocols. |

## 10xx Guardrails & Features (Series 1000)
| File | Role | Linked Issue | Description |
| :--- | :--- | :--- | :--- |
| `docs/1000-TEMPLATE-feature.md` | **Template** | - | Standard template for new feature documentation. |
| `docs/1005-graph-tests.md` | **Spec** | #5 | Unit tests for LangGraph node functions. |
| `docs/1006-rag-vector.md` | **Spec** | #6 | RAG Vector Store implementation. |
| `docs/1007-observability.md` | **Spec** | #7 | Observability and tracing for Lambda functions. |
| `docs/1010-semantic-guardrails.md` | **Spec** | #10 | Layer 3: Probabilistic Semantic Guardrail (Claude Haiku). |
| `docs/1011-local-guardrails.md` | **Spec** | #11 | Layer 1: Regex and pattern matching. |
| `docs/1014-compliance-engine.md` | **Spec** | #14 | Compliance checking engine for content validation. |
| `docs/1025-linkedin-auth-gate.md` | **Spec** | #25 | Strategy for LinkedIn authentication gating. |
| `docs/1041-security-audit.md` | **Audit** | #41 | Security posture and permission culling. |
| `docs/1042-whitelist-mode.md` | **Spec** | #42 | Strict whitelist enforcement protocols. |
| `docs/1043-privacy-compliance.md` | **Spec** | #43 | Privacy policy and store compliance. |
| `docs/1044-warning-ui.md` | **Spec** | #44 | Browser extension warning UI for guardrail triggers. |
| `docs/1045-deterministic-hate-filter.md` | **Spec** | #45 | Layer 2: Deterministic Hate Speech Filter (RSDB). |
| `docs/1051-store-compliance.md` | **Spec** | #51 | Chrome Web Store compliance requirements. |
| `docs/1053-store-assets.md` | **Spec** | #53 | Store asset generation for Chrome Web Store. |

## 90xx Knowledge Base
| File | Role | Linked Issue | Description |
| :--- | :--- | :--- | :--- |
| `docs/9000-lessons-learned.md` | **Log** | - | Cumulative corporate memory of mistakes and fixes. |
| `docs/9001-open-investigations.md` | **Spikes** | #49 | Centralized log for future work, automation ideas, and ongoing experiments. |

## Source Code (Key Files)
| File | Role | Linked Issue | Description |
| :--- | :--- | :--- | :--- |
| `src/guardrails/semantic.py` | **Logic** | #10 | The Semantic Guardrail implementation. |
| `src/guardrails/resources/taxonomy.json` | **Config** | #10 | Definitions and few-shot examples for Layer 3. |
| `verify_holistic.py` | **Test** | #13 | The standalone test harness for semantic guardrails. |

## Tools & Scripts
| File | Role | Linked Issue | Description |
| :--- | :--- | :--- | :--- |
| `tools/generate_store_assets.py` | **Utility** | #52 | Generates release zip and placeholder store assets. |
