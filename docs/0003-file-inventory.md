# 0003 - File Inventory & Status Map

## 1. Status Taxonomy
* 🟢 **Stable:** Verified, Documented, Production-Ready.
* 🟡 **Beta:** Functional but lacks comprehensive test coverage/docs.
* 🟠 **In-Progress:** Active development; expect instability.
* ⚪ **Placeholder:** Skeleton or empty file; do not run.
* ⚫ **Legacy:** Deprecated/Archived (Reference only).
* ❓ **Unknown:** Needs audit/verification.

## 2. Inventory

### 00xx Core Architecture (Documentation)
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/0000-GUIDE.md` | **Guide** | 🟢 **Stable** | - | The "Start Here" manual and project philosophy. |
| `docs/0001-system-architecture.md` | **Spec** | 🟢 **Stable** | #1 | High-level system design and AWS topology. |
| `docs/0002-coding-standards.md` | **Standard** | 🟢 **Stable** | #36 | Python, Git, and Documentation standards. |
| `docs/0003-file-inventory.md` | **Register** | 🟢 **Stable** | #70 | This file. The map of the territory. |
| `docs/0004-orchestration-protocol.md` | **Protocol** | 🟢 **Stable** | #50 | Rules for AI-User collaboration. |
| `docs/0005-testing-strategy-and-protocols.md` | **Protocol** | 🟢 **Stable** | #69 | Testing strategy and modular verification. |

### 10xx Feature Specifications
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/1000-TEMPLATE-feature.md` | **Template** | 🟢 **Stable** | - | Standard template for feature docs. |
| `docs/1005-graph-tests.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1006-rag-vector.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1007-observability.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1010-semantic-guardrails.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1011-local-guardrails.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1014-compliance-engine.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1025-linkedin-auth-gate.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1041-security-audit.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1042-whitelist-mode.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1043-privacy-compliance.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1044-warning-ui.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1045-deterministic-hate-filter.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1051-store-compliance.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1053-store-assets.md` | **Spec** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/1069-log-inspector.md` | **Spec** | 🟢 **Stable** | #69 | CLI Inspector for DynamoDB telemetry. |

### Journals & Logs
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/9000-lessons-learned.md` | **Log** | 🟢 **Stable** | - | Repository of hard-won knowledge. |
| `docs/9001-open-investigations.md` | **Log** | ❓ **Unknown** | - | *Status Unknown.* |
| `docs/ENGINEERING-JOURNAL.md` | **Log** | 🟢 **Stable** | - | Chronological work log. |

### Core Application (Python)
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `agent.py` | **Logic** | ❓ **Unknown** | - | Main LangGraph agent definitions. |
| `checkpointer.py` | **State** | ❓ **Unknown** | - | DynamoDB state management. |
| `compliance.py` | **Logic** | ❓ **Unknown** | #14 | Compliance checking logic. |
| `lambda_function.py` | **Entry** | ❓ **Unknown** | - | Main AWS Lambda handler. |
| `lambda_harvester_function.py` | **Entry** | ❓ **Unknown** | - | Secondary Lambda handler. |
| `src/guardrails/` | **Module** | ❓ **Unknown** | - | Specific guardrail implementations. |

### Chrome Extension
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `extension/manifest.json` | **Config** | ❓ **Unknown** | - | Chrome Extension capability manifest. |
| `extension/service-worker.js` | **Logic** | ❓ **Unknown** | - | Background script. |
| `index.html` | **Asset** | ❓ **Unknown** | - | *Status Unknown.* |

### Infrastructure & Deployment
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `deploy.sh` | **Script** | ❓ **Unknown** | - | Deployment automation. |
| `poetry.lock` | **Lock** | 🟢 **Stable** | - | Exact dependency tree. |
| `provision.sh` | **Script** | ❓ **Unknown** | - | Infrastructure provisioning. |
| `pyproject.toml` | **Config** | 🟢 **Stable** | - | Python dependencies. |

### Tools & Utilities
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `harvest_test_data.py` | **Utility** | 🟡 **Beta** | #72 | Log puller. *Pending move to tools/.* |
| `tools/generate_store_assets.py` | **Utility** | ❓ **Unknown** | - | *Status Unknown.* |
| `tools/log_viewer.py` | **Utility** | 🟢 **Stable** | #69 | DynamoDB Inspector. |

### Testing & Verification
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `run_guardrails.py` | **Test** | ⚪ **Placeholder** | - | *Status Unknown.* |
| `test_ground_truth.json` | **Data** | 🟢 **Stable** | - | "Gold Standard" dataset. |
| `test_holistic_data.json` | **Data** | 🟡 **Beta** | - | Raw harvested data. |
| `tests/test_guardrails.py` | **Test** | ❓ **Unknown** | - | Unit tests. |
| `tests/test_semantic.py` | **Test** | ❓ **Unknown** | - | Unit tests. |
| `verify_bedrock.py` | **Test** | ⚪ **Placeholder** | - | Connectivity test. |
| `verify_holistic.py` | **Test** | 🟡 **Beta** | - | LLM-based judge. |

### Legacy, Temporary & Abandoned
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `build/` | **Artifact** | ⚫ **Legacy** | - | Abandoned print artifact directory. |
| `legacy/` | **Archive** | ⚫ **Legacy** | - | Old guardrails and tests. |
| `prompts/` | **Archive** | ⚫ **Legacy** | - | Old text prompts. |