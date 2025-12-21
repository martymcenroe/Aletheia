# 0003 - File Inventory & Status Map

## 1. Status Taxonomy
* 🟢 **Stable:** Verified, Documented, Production-Ready.
* 🟡 **Beta:** Functional but lacks comprehensive test coverage/docs.
* 🟠 **In-Progress:** Active development; expect instability.
* ⚪ **Placeholder:** Skeleton or empty file; do not run.
* ⚫ **Legacy:** Deprecated/Archived (Reference only).
* ❓ **Unknown:** Needs audit/verification.

## 2. Inventory

### 00xx Core Standards
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/0000-GUIDE.md` | **Guide** | 🟢 **Stable** | - | The "Start Here" manual and project philosophy. |
| `docs/0001-system-architecture.md` | **Spec** | 🟢 **Stable** | #1 | High-level system design and AWS topology. |
| `docs/0002-coding-standards.md` | **Standard** | 🟢 **Stable** | #36 | Python, Git, and Documentation standards. |
| `docs/0003-file-inventory.md` | **Register** | 🟢 **Stable** | #70 | This file. The map of the territory. |
| `docs/0004-orchestration-protocol.md` | **Protocol** | 🟢 **Stable** | #50 | Rules for AI-User collaboration and mini-sprints. |
| `docs/0005-testing-strategy-and-protocols.md` | **Protocol** | 🟢 **Stable** | #69 | Testing strategy and modular verification. |

### 01xx Templates & Style Guides
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/0100-TEMPLATE-GUIDE.md` | **Index** | 🟢 **Stable** | - | Index of all templates and their purposes. |
| `docs/0101-TEMPLATE-issue.md` | **Template** | 🟢 **Stable** | - | GitHub Issue template for features. |
| `docs/0102-TEMPLATE-feature-lld.md` | **Template** | 🟢 **Stable** | - | Low-Level Design doc template for features. |

### 10xx Feature Specifications
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/1005-graph-tests.md` | **Spec** | ❓ **Unknown** | #5 | Unit tests for LangGraph nodes. |
| `docs/1006-rag-vector.md` | **Spec** | ❓ **Unknown** | #6 | RAG Vector Store implementation. |
| `docs/1007-observability.md` | **Spec** | ❓ **Unknown** | #7 | Observability and tracing. |
| `docs/1010-semantic-guardrails.md` | **Spec** | ❓ **Unknown** | #10 | Layer 3 Semantic Guardrail. |
| `docs/1011-local-guardrails.md` | **Spec** | ❓ **Unknown** | #11 | Layer 1 Local Guardrails. |
| `docs/1014-compliance-engine.md` | **Spec** | ❓ **Unknown** | #14 | Compliance checking engine. |
| `docs/1025-linkedin-auth-gate.md` | **Spec** | ❓ **Unknown** | #25 | LinkedIn authentication gating. |
| `docs/1041-security-audit.md` | **Spec** | 🟢 **Stable** | #41 | Security audit and permission culling. |
| `docs/1042-whitelist-mode.md` | **Spec** | 🟢 **Stable** | #42 | Whitelist mode and safety filters. |
| `docs/1043-privacy-compliance.md` | **Spec** | 🟢 **Stable** | #43 | Privacy policy compliance. |
| `docs/1044-warning-ui.md` | **Spec** | ❓ **Unknown** | #44 | Browser extension warning UI. |
| `docs/1045-deterministic-hate-filter.md` | **Spec** | ❓ **Unknown** | #45 | Layer 2 Deterministic Hate Filter. |
| `docs/1051-store-compliance.md` | **Spec** | ❓ **Unknown** | #51 | Chrome Web Store compliance. |
| `docs/1053-store-assets.md` | **Spec** | ❓ **Unknown** | #53 | Store asset generation. |
| `docs/1069-log-inspector.md` | **Spec** | 🟢 **Stable** | #69 | CLI Inspector for DynamoDB telemetry. |

### 90xx Journals & Logs
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/9000-lessons-learned.md` | **Log** | 🟢 **Stable** | - | Pointer to Engineering Journal. |
| `docs/9001-open-investigations.md` | **Log** | ❓ **Unknown** | - | Future work and spikes. |
| `docs/ENGINEERING-JOURNAL.md` | **Log** | 🟢 **Stable** | - | Cross-project engineering lessons (synced). |

### Core Application (Python)
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `agent.py` | **Logic** | ❓ **Unknown** | - | Main LangGraph agent definitions. |
| `checkpointer.py` | **State** | ❓ **Unknown** | - | DynamoDB state management. |
| `compliance.py` | **Logic** | ❓ **Unknown** | #14 | Compliance checking logic. |
| `lambda_function.py` | **Entry** | ❓ **Unknown** | - | Main AWS Lambda handler. |
| `lambda_harvester_function.py` | **Entry** | ❓ **Unknown** | - | Secondary Lambda handler. |
| `src/guardrails/` | **Module** | ❓ **Unknown** | - | Guardrail implementations. |

### Chrome Extension
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `extension/manifest.json` | **Config** | ❓ **Unknown** | - | Chrome Extension manifest. |
| `extension/service-worker.js` | **Logic** | ❓ **Unknown** | - | Background script. |
| `index.html` | **Asset** | ❓ **Unknown** | - | Landing page. |

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
| `harvest_test_data.py` | **Utility** | 🟡 **Beta** | #72 | Log puller. Pending move to tools/. |
| `tools/generate_store_assets.py` | **Utility** | ❓ **Unknown** | - | Store asset generator. |
| `tools/log_viewer.py` | **Utility** | 🟢 **Stable** | #69 | DynamoDB Inspector. |

### Testing & Verification
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `run_guardrails.py` | **Test** | ⚪ **Placeholder** | - | Guardrail runner. |
| `test_ground_truth.json` | **Data** | 🟢 **Stable** | - | Gold standard test dataset. |
| `test_holistic_data.json` | **Data** | 🟡 **Beta** | - | Raw harvested test data. |
| `tests/test_guardrails.py` | **Test** | ❓ **Unknown** | - | Unit tests for guardrails. |
| `tests/test_semantic.py` | **Test** | ❓ **Unknown** | - | Unit tests for semantic layer. |
| `verify_bedrock.py` | **Test** | ⚪ **Placeholder** | - | Bedrock connectivity test. |
| `verify_holistic.py` | **Test** | 🟡 **Beta** | - | LLM-based holistic judge. |

### Legacy & Abandoned
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `build/` | **Artifact** | ⚫ **Legacy** | - | Abandoned build directory. |
| `legacy/` | **Archive** | ⚫ **Legacy** | - | Old guardrails and tests. |
| `prompts/` | **Archive** | ⚫ **Legacy** | - | Old text prompts. |
