# 0003 - File Inventory & Status Map

## 1. Status Taxonomy
* 🟢 **Stable:** Verified, Documented, Production-Ready.
* 🟡 **Beta:** Functional but lacks full test coverage (all LLD scenarios) or documentation.
* 🟠 **In-Progress:** Active development; expect instability.
* ⚪ **Placeholder:** Skeleton or empty file; do not run.
* ⚫ **Legacy:** Deprecated/Archived (Reference only).
* ❓ **Unknown:** Needs audit/verification.
* 🚫 **Gitignored:** Not tracked; listed for completeness.

## 2. Inventory

### Root Configuration
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `.claude/settings.local.json` | **Config** | 🟢 **Stable** | - | Claude Code permissions (commit to main when updated). |
| `.gitignore` | **Config** | 🟢 **Stable** | - | Git ignore rules. |
| `.print-history.json` | **Log** | 🚫 **Gitignored** | - | Print tracking for markdown files (mtime + timestamp). |
| `.session-log.md` | **Log** | 🚫 **Gitignored** | - | AI session continuity log. |
| `CHATGPT.md` | **Config** | 🟢 **Stable** | - | ChatGPT agent onboarding. |
| `CLAUDE.md` | **Config** | 🟢 **Stable** | - | Claude Code agent onboarding. |
| `GEMINI.md` | **Config** | 🟢 **Stable** | - | Gemini agent onboarding. |
| `LICENSE` | **Legal** | 🟢 **Stable** | - | MIT License. |
| `README.md` | **Doc** | 🟢 **Stable** | - | Project overview. |
| `IMMEDIATE-PLAN.md` | **Log** | 🟢 **Stable** | - | Current session focus and context handoff. |
| `poetry.lock` | **Lock** | 🟢 **Stable** | - | Exact dependency tree. |
| `pyproject.toml` | **Config** | 🟢 **Stable** | - | Python dependencies. |

### 00xx Core Standards
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/0000-GUIDE.md` | **Guide** | 🟢 **Stable** | - | The "Start Here" manual and project philosophy. |
| `docs/0001-system-architecture.md` | **Spec** | 🟢 **Stable** | #1 | High-level system design and AWS topology. |
| `docs/0002-coding-standards.md` | **Standard** | 🟢 **Stable** | #36 | Python, Git, and Documentation standards. |
| `docs/0003-file-inventory.md` | **Register** | 🟢 **Stable** | #70 | This file. The map of the territory. |
| `docs/0004-orchestration-protocol.md` | **Protocol** | 🟢 **Stable** | #50 | Rules for AI-User collaboration and mini-sprints. |
| `docs/0005-testing-strategy-and-protocols.md` | **Protocol** | 🟢 **Stable** | #69 | Testing strategy and modular verification. |
| `docs/0006-mermaid-diagrams.md` | **Standard** | 🟢 **Stable** | - | Mermaid JS diagramming standards and patterns. |
| `docs/0007-signal-handling.md` | **Standard** | 🟢 **Stable** | #112 | Signal handling strategy (noai, noarchive, robots.txt). |
| `docs/0008-orchestrator-instructions.md` | **Guide** | 🟢 **Stable** | - | Rules for human orchestrator managing AI sessions. |
| `docs/0009-session-closeout-protocol.md` | **Protocol** | 🟢 **Stable** | - | Checklist for ending sessions cleanly. |
| `docs/0010-standard-labels.md` | **Standard** | 🟢 **Stable** | - | Label taxonomy for Issues and PRs. |
| `docs/0011-environment-cleanup-checklist.md` | **Protocol** | 🟢 **Stable** | - | Comprehensive cleanup checklist for dev environment. |

### 01xx Templates & Style Guides
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/0100-TEMPLATE-GUIDE.md` | **Index** | 🟢 **Stable** | - | Index of all templates and their purposes. |
| `docs/0101-TEMPLATE-issue.md` | **Template** | 🟢 **Stable** | - | GitHub Issue template for features. |
| `docs/0102-TEMPLATE-feature-lld.md` | **Template** | 🟢 **Stable** | - | Low-Level Design doc template for features. |
| `docs/0103-TEMPLATE-implementation-report.md` | **Template** | 🟢 **Stable** | #77 | Implementation report template for completed features. |
| `docs/0104-TEMPLATE-adr.md` | **Template** | 🟢 **Stable** | #111 | Architecture Decision Record template. |
| `docs/0111-TEMPLATE-test-script.md` | **Template** | 🟢 **Stable** | - | Manual test script template (generic). |
| `docs/0112-TEMPLATE-browser-extension-test-script.md` | **Template** | 🟢 **Stable** | #77 | Browser extension test script template for non-technical users. |
| `docs/0113-TEMPLATE-test-report.md` | **Template** | 🟢 **Stable** | - | Test report template for recording test execution results. |

### 02xx Architecture Decision Records
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/0200-ADR-index.md` | **Index** | 🟢 **Stable** | #111 | Master index of all ADRs with category cross-reference. |
| `docs/0201-ADR-privacy-first-permissions.md` | **ADR** | 🟢 **Stable** | #111 | Decision: Never request `<all_urls>` permission. |
| `docs/0202-ADR-shadow-dom-isolation.md` | **ADR** | 🟢 **Stable** | #111 | Decision: Closed Shadow DOM for injected UI. |
| `docs/0203-ADR-stateful-serverless.md` | **ADR** | 🟢 **Stable** | #111 | Decision: DynamoDB hydration/dehydration pattern. |
| `docs/0204-ADR-defense-funnel.md` | **ADR** | 🟢 **Stable** | #111 | Decision: Ordered defense layers (fail fast). |
| `docs/0205-ADR-langgraph-orchestration.md` | **ADR** | ⚫ **Legacy** | #111 | Decision: LangGraph for agent orchestration. Superseded by 0211. |
| `docs/0206-ADR-streaming-sse.md` | **ADR** | 🟢 **Stable** | #111 | Decision: SSE for streaming responses. |
| `docs/0207-ADR-single-identity-orchestration.md` | **ADR** | 🟢 **Stable** | - | Decision: Single human committer identity. |
| `docs/0208-ADR-client-side-preference-storage.md` | **ADR** | 🟢 **Stable** | - | Decision: chrome.storage.local for persistence. |
| `docs/0209-ADR-static-compliance-hosting.md` | **ADR** | 🟢 **Stable** | - | Decision: GitHub Pages for legal docs. |
| `docs/0210-ADR-git-worktree-isolation.md` | **ADR** | 🟢 **Stable** | - | Decision: Worktrees for feature isolation. |
| `docs/0211-ADR-naked-python-architecture.md` | **ADR** | 🟢 **Stable** | #113 | Decision: Remove LangGraph, use boto3 directly. |

### 10xx Feature Specifications
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/1005-graph-tests.md` | **Spec** | ⚪ **Placeholder** | #5 | Unit tests for LangGraph nodes. |
| `docs/1006-rag-vector.md` | **Spec** | ⚪ **Placeholder** | #6 | RAG Vector Store implementation. |
| `docs/1007-observability.md` | **Spec** | ⚪ **Placeholder** | #7 | Observability and tracing. |
| `docs/1010-semantic-guardrails.md` | **Spec** | 🟡 **Beta** | #10 | Semantic Guardrail (LLM-based). |
| `docs/1011-local-guardrails.md` | **Spec** | 🟡 **Beta** | #11 | Selection Check (local validation). |
| `docs/1014-compliance-engine.md` | **Spec** | 🟡 **Beta** | #14 | Compliance checking engine. |
| `docs/legacy/1025-linkedin-auth-gate.md` | **Spec** | ⚫ **Legacy** | #25 | LinkedIn auth (cookie heuristic). Superseded by #116 (OAuth). |
| `docs/1041-security-audit.md` | **Spec** | 🟢 **Stable** | #41 | Security audit and permission culling. |
| `docs/1042-whitelist-mode.md` | **Spec** | 🟢 **Stable** | #42 | Whitelist mode and safety filters. |
| `docs/1043-privacy-compliance.md` | **Spec** | 🟢 **Stable** | #43 | Privacy policy compliance. |
| `docs/1044-warning-ui.md` | **Spec** | ⚪ **Placeholder** | #44 | Browser extension warning UI. |
| `docs/1045-deterministic-hate-filter.md` | **Spec** | ⚪ **Placeholder** | #45 | Denylist (deterministic hate filter). |
| `docs/1051-store-compliance.md` | **Spec** | 🟡 **Beta** | #51 | Chrome Web Store compliance. |
| `docs/1053-store-assets.md` | **Spec** | ⚪ **Placeholder** | #53 | Store asset generation. |
| `docs/1069-log-inspector.md` | **Spec** | 🟢 **Stable** | #69 | CLI Inspector for DynamoDB telemetry. |
| `docs/1076-allowlist-popup.md` | **Spec** | 🟢 **Stable** | #76 | Domain allowlist popup LLD. |
| `docs/1077-action-feedback.md` | **Spec** | 🟢 **Stable** | #77 | User action feedback overlay LLD. |
| `docs/legacy/1080-wire-agent-logic-langgraph.md` | **Spec** | ⚫ **Legacy** | #80 | Wiring agent.py (LangGraph). Superseded by #113. |
| `docs/1113-naked-python-architecture.md` | **Spec** | 🟠 **In-Progress** | #113 | Naked Python sequential pipeline (replaces LangGraph). |

### Prototypes & Design Artifacts
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/prototypes/popup-prototype.jsx` | **Prototype** | 🟢 **Stable** | #76 | React prototype for allowlist popup UI. |

### Implementation Reports (Nested by Issue)
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/reports/77/implementation-report.md` | **Report** | 🟢 **Stable** | #77 | Implementation report for action feedback feature. |
| `docs/reports/80/implementation-report.md` | **Report** | 🟢 **Stable** | #80 | Retroactive report for abandoned LangGraph implementation. |

### 90xx Journals & Logs
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/6000-open-issues.md` | **Report** | 🟢 **Stable** | - | Current open GitHub issues (regenerate with `poetry run python tools/print/print_most_recent_open_issues.py`). |
| `docs/9000-lessons-learned.md` | **Log** | 🟢 **Stable** | - | Aletheia-specific lessons (project-scoped). |
| `docs/9001-open-investigations.md` | **Log** | 🟡 **Beta** | - | Future work and spikes. |
| `docs/ENGINEERING-JOURNAL.md` | **Log** | 🟢 **Stable** | - | Cross-project engineering lessons (synced). |

### Core Application (Python)
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `lambda_function.py` | **Entry** | 🟠 **In-Progress** | #113 | Main AWS Lambda handler (Naked Python orchestrator). |
| `lambda_harvester_function.py` | **Entry** | 🟢 **Stable** | - | Data harvester Lambda handler. |
| `src/__init__.py` | **Module** | 🟢 **Stable** | - | Package init. |
| `src/guardrails/__init__.py` | **Module** | 🟢 **Stable** | - | Guardrails package init. |
| `src/guardrails/engine.py` | **Logic** | 🟡 **Beta** | #113 | Guardrails engine (Selection Check + Denylist stub). |
| `src/guardrails/validators.py` | **Logic** | 🟡 **Beta** | #11 | Validator functions. |
| `src/guardrails/semantic.py` | **Logic** | 🟡 **Beta** | #10 | Semantic guardrail (LLM-based). |
| `src/guardrails/resources/taxonomy.json` | **Data** | 🟢 **Stable** | #10 | Taxonomy and few-shot examples. |

### Chrome Extension
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `extension/manifest.json` | **Config** | 🟢 **Stable** | #82 | V3 Manifest (Privacy-First). |
| `extension/overlay.js` | **Logic** | 🟢 **Stable** | #114 | Injected overlay UI (Shadow DOM isolated). |
| `extension/service-worker.js` | **Logic** | 🟢 **Stable** | #76 | Background script with allowlist gate. |
| `extension/popup.html` | **UI** | 🟡 **Beta** | #76 | Popup UI structure (three views). |
| `extension/popup.css` | **Style** | 🟡 **Beta** | #76 | Popup styling with design tokens. |
| `extension/popup.js` | **Logic** | 🟡 **Beta** | #76 | Popup logic and storage interaction. |
| `extension/icons/icon16.png` | **Asset** | 🟢 **Stable** | #82 | Toolbar icon (Lambda). |
| `extension/icons/icon32.png` | **Asset** | 🟢 **Stable** | #82 | Small icon (Lambda). |
| `extension/icons/icon48.png` | **Asset** | 🟢 **Stable** | #82 | Medium icon (Lambda). |
| `extension/icons/icon128.png` | **Asset** | 🟢 **Stable** | #82 | Large icon (Lambda). |
| `index.html` | **Asset** | ⚫ **Legacy** | #81 | Landing page (cyberpunk). To be redesigned. |

### Infrastructure & Deployment
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `aws-cleanup-old-resources.sh` | **Script** | 🟡 **Beta** | - | Cleanup old AWS resources. |
| `aws-inventory-check.sh` | **Script** | 🟡 **Beta** | - | AWS resource inventory audit. |
| `deploy.sh` | **Script** | 🟡 **Beta** | - | Lambda deployment automation. |
| `provision.sh` | **Script** | 🟡 **Beta** | - | AWS infrastructure provisioning. |
| `scripts/aws/.gitkeep` | **Placeholder** | 🟢 **Stable** | - | AWS scripts directory placeholder. |
| `dist/` | **Output** | 🚫 **Gitignored** | - | Build artifacts (empty). |
| `temp-pdfs/` | **Output** | 🚫 **Gitignored** | - | Temporary PDF storage (auto-deleted after successful print). |

### Tools & Utilities
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `harvest_test_data.py` | **Utility** | 🟡 **Beta** | #72 | Log puller. Pending move to tools/. |
| `tools/generate_store_assets.py` | **Utility** | ⚪ **Placeholder** | #53 | Store asset generator. |
| `tools/log_viewer.py` | **Utility** | 🟢 **Stable** | #69 | DynamoDB Inspector. |
| `tools/generate_icons.py` | **Utility** | 🟢 **Stable** | #82 | Icon factory (Pillow). Supports `--transparent` and `--threshold N` CLI options. |
| `tools/master_lambda.png` | **Asset** | 🟢 **Stable** | #82 | Master source for branding. |
| `tools/print/print_markdown.py` | **Utility** | 🟢 **Stable** | - | Batch markdown→PDF printer with spooler monitoring and print tracking. |
| `tools/print/print_most_recent_open_issues.py` | **Utility** | 🟢 **Stable** | - | GitHub issues fetcher/printer (saves to docs/6000-*.md). |
| `tools/print/audit_long_lines.py` | **Utility** | 🟢 **Stable** | #103 | Audits markdown files for print overflow (>100 char lines). |
| `tools/print/pandoc-header.tex` | **Asset** | 🟢 **Stable** | - | LaTeX header template for PDF generation (fancy headers). |
| `tools/aws/lambda-status.sh` | **Utility** | 🟢 **Stable** | - | Show Lambda concurrency status (ON/OFF). |
| `tools/aws/lambda-on.sh` | **Utility** | 🟢 **Stable** | - | Enable Lambda (remove concurrency limit). |
| `tools/aws/lambda-off.sh` | **Utility** | 🟢 **Stable** | - | Disable Lambda (set concurrency=0). |

### Testing & Verification
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `run_guardrails.py` | **Test** | ⚪ **Placeholder** | - | Guardrail runner. |
| `test_ground_truth.json` | **Data** | 🟢 **Stable** | - | Gold standard test dataset. |
| `test_holistic_data.json` | **Data** | 🟡 **Beta** | - | Raw harvested test data. |
| `tests/__init__.py` | **Test** | 🟢 **Stable** | - | Test package init. |
| `tests/test_guardrails.py` | **Test** | 🟡 **Beta** | #11 | Unit tests for guardrails. |
| `tests/test_semantic.py` | **Test** | 🟡 **Beta** | #10 | Unit tests for semantic layer. |
| `tests/manual_overlay_math.html` | **Test** | 🟢 **Stable** | #98 | Manual viewport positioning test page. |
| `tests/data/.gitkeep` | **Placeholder** | 🟢 **Stable** | - | Test data directory placeholder. |
| `verify_bedrock.py` | **Test** | ⚪ **Placeholder** | - | Bedrock connectivity test. |
| `verify_holistic.py` | **Test** | 🟡 **Beta** | - | LLM-based holistic judge. |
| `docs/security/vulnerability-test.md` | **Test** | 🟢 **Stable** | #95 | Manual vulnerability reproduction scripts. |

### Session Logs
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/session-logs/Week-starting-2025-12-15.md` | **Log** | 🟢 **Stable** | - | Session log week of Dec 15-21. |
| `docs/session-logs/Week-starting-2025-12-22.md` | **Log** | 🟢 **Stable** | - | Session log week of Dec 22-28. |
| `docs/session-logs/Week-starting-2025-12-29.md` | **Log** | 🟠 **In-Progress** | - | Session log week of Dec 29+. |

### Legacy & Abandoned
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `prompts/` | **Archive** | ⚫ **Legacy** | - | Old text prompts. To be cleaned. |
