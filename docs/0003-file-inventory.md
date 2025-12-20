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
| `docs/1010-semantic-guardrails.md` | **Spec** | #10 | Layer 3: Probabilistic Semantic Guardrail (Claude Haiku). |
| `docs/1011-local-guardrails.md` | **Spec** | #11 | Layer 1: Regex and pattern matching. |
| `docs/1012-deterministic-hate-filter.md` | **Spec** | #45 | Layer 2: Deterministic Hate Speech Filter (RSDB). |
| `docs/1025-linkedin-auth-gate.md` | **Spec** | #25 | Strategy for LinkedIn authentication gating. |
| `docs/1014-security-audit.md` | **Audit** | - | Security posture and audit logs. |
| `docs/1015-whitelist-mode.md` | **Spec** | - | Strict whitelist enforcement protocols. |
| `docs/1016-privacy-compliance.md` | **Spec** | #14 | GDPR/CCPA compliance engine architecture. |

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
