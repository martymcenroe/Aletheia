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
| `.claude/commands/closeout.md` | **Skill** | 🟢 **Stable** | - | Session closeout skill (5-10 min). |
| `.claude/commands/full-cleanup.md` | **Skill** | 🟢 **Stable** | - | Full cleanup skill (20-30 min). |
| `.claude/commands/audit.md` | **Skill** | 🟢 **Stable** | - | Full 08xx audit suite skill (1-2 hrs). |
| `.claude/commands/onboard.md` | **Skill** | 🟢 **Stable** | - | Agent onboarding skill (quick/full mode). |
| `.gitignore` | **Config** | 🟢 **Stable** | - | Git ignore rules. |
| `.print-history.json` | **Log** | 🚫 **Gitignored** | - | Print tracking for markdown files (mtime + timestamp). |
| `.session-log.md` | **Log** | 🚫 **Gitignored** | - | AI session continuity log. |
| `CHATGPT.md` | **Config** | 🟢 **Stable** | - | ChatGPT agent onboarding. |
| `CLAUDE.md` | **Config** | 🟢 **Stable** | - | Claude Code agent onboarding. |
| `GEMINI.md` | **Config** | 🟢 **Stable** | - | Gemini agent onboarding. |
| `LICENSE` | **Legal** | 🟢 **Stable** | - | MIT License. |
| `NOTICE` | **Legal** | 🟢 **Stable** | - | Apache-2.0 third-party attributions (boto3, requests, etc.). |
| `SECURITY.md` | **Policy** | 🟢 **Stable** | #151 | Security policy (vulnerability reporting, supported versions). |
| `README.md` | **Doc** | 🟢 **Stable** | - | Project overview. |
| `IMMEDIATE-PLAN.md` | **Log** | 🟢 **Stable** | - | Current session focus and context handoff. |
| `poetry.lock` | **Lock** | 🟢 **Stable** | - | Exact dependency tree. |
| `pyproject.toml` | **Config** | 🟢 **Stable** | - | Python dependencies. |
| `package.json` | **Config** | 🟢 **Stable** | #95 | Node.js dependencies (Playwright E2E). |
| `playwright.config.js` | **Config** | 🟢 **Stable** | #95 | Playwright test configuration. |
| `eslint.config.mjs` | **Config** | 🟢 **Stable** | #157 | ESLint flat config for browser extensions. |

### 00xx Core Standards
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/0000-GUIDE.md` | **Guide** | 🟢 **Stable** | - | The "Start Here" manual and project philosophy. |
| `docs/0000a-IMMEDIATE-PLAN.md` | **Plan** | 🟢 **Stable** | - | Current sprint focus and handoff context. |
| `docs/0000b-ONBOARD-DIGEST.md` | **Report** | 🟢 **Stable** | - | Auto-generated onboard digest (regenerate with `tools/generate_onboard_digest.py`). |
| `docs/0001-system-architecture.md` | **Spec** | 🟢 **Stable** | #1 | High-level system design and AWS topology. |
| `docs/0002-coding-standards.md` | **Standard** | 🟢 **Stable** | #36 | Python, Git, and Documentation standards. |
| `docs/0003-file-inventory.md` | **Register** | 🟡 **Beta** | #70 | This file. Requires regular audit (0009 Full Mode §F9). |
| `docs/0004-orchestration-protocol.md` | **Protocol** | 🟢 **Stable** | #50 | Rules for AI-User collaboration and mini-sprints. |
| `docs/0005-testing-strategy-and-protocols.md` | **Protocol** | 🟢 **Stable** | #69 | Testing strategy and modular verification. |
| `docs/0006-mermaid-diagrams.md` | **Standard** | 🟢 **Stable** | - | Mermaid JS diagramming standards and patterns. |
| `docs/0007-signal-handling.md` | **Standard** | 🟢 **Stable** | #112 | Signal handling strategy (noai, noarchive, robots.txt). |
| `docs/0008-orchestrator-instructions.md` | **Guide** | 🟢 **Stable** | - | Rules for human orchestrator managing AI sessions. |
| `docs/0009-session-closeout-protocol.md` | **Protocol** | 🟢 **Stable** | - | Checklist for ending sessions (Session Mode + Full Mode). |
| `docs/0010-standard-labels.md` | **Standard** | 🟢 **Stable** | - | Label taxonomy for Issues and PRs. |
| `docs/0012-devops-architecture.md` | **Standard** | 🟢 **Stable** | - | CI/CD pipeline, GitHub Actions, deployment, quality gates. |
| `docs/0013-testing-architecture.md` | **Standard** | 🟢 **Stable** | #105 | Test pyramid, Playwright, coverage strategy. |
| `docs/0014-cost-architecture.md` | **Standard** | 🟢 **Stable** | #137 | AWS cost model, budgets, optimization, abuse prevention. |
| `docs/0015-agent-prohibited-actions.md` | **Policy** | 🟢 **Stable** | - | Agent prohibited actions and permission philosophy. |

### 01xx Templates & Style Guides
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/0100-TEMPLATE-GUIDE.md` | **Index** | 🟢 **Stable** | - | Index of all templates and their purposes. |
| `docs/0101-TEMPLATE-issue.md` | **Template** | 🟢 **Stable** | - | GitHub Issue template for features. |
| `docs/0102-TEMPLATE-feature-lld.md` | **Template** | 🟢 **Stable** | - | Low-Level Design doc template for features. |
| `docs/0103-TEMPLATE-implementation-report.md` | **Template** | 🟢 **Stable** | #77 | Implementation report template for completed features. |
| `docs/0104-TEMPLATE-adr.md` | **Template** | 🟢 **Stable** | #111 | Architecture Decision Record template. |
| `docs/0108-lld-pre-implementation-review.md` | **Protocol** | 🟢 **Stable** | - | LLD pre-implementation review checklist. |
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
| `docs/0212-ADR-unified-v3-secure-dom.md` | **ADR** | 🟢 **Stable** | #193, #194 | Decision: Manifest V3 + DOM methods for security. |

### 06xx Skill Instructions
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/0600-skill-instructions-index.md` | **Index** | 🟢 **Stable** | - | Index of all skill instructions. |
| `docs/0601-skill-gemini-lld-review.md` | **Skill** | 🟢 **Stable** | - | Gemini LLD review procedure with priority tiers. |

### 08xx Audit Procedures (Numbered by Execution Order)
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/0800-common-audits.md` | **Index** | 🟢 **Stable** | - | Master index of all audit procedures. |
| `docs/0801-open-issues-audit.md` | **Protocol** | 🟢 **Stable** | - | Check for complete/deprecated/stale issues. |
| `docs/0802-reports-completeness-audit.md` | **Protocol** | 🟢 **Stable** | - | Verify closed issues have reports. |
| `docs/0803-lld-code-audit.md` | **Protocol** | 🟢 **Stable** | - | Verify implementation matches LLD. |
| `docs/0804-inventory-audit.md` | **Protocol** | 🟢 **Stable** | - | Detect file inventory drift. |
| `docs/0805-terminology-audit.md` | **Protocol** | 🟢 **Stable** | - | Detect stale terminology after renaming. |
| `docs/0806-architecture-audit.md` | **Protocol** | 🟢 **Stable** | - | Architecture drift detection (strategic). |
| `docs/0807-agentos-audit.md` | **Protocol** | 🟢 **Stable** | - | AgentOS health check (system self-audit). |
| `docs/0808-audit-permission-permissiveness.md` | **Protocol** | 🟢 **Stable** | - | Agent permission maximization audit. |
| `docs/0809-audit-security.md` | **Protocol** | 🟢 **Stable** | - | Security audit (OWASP, LLM, Agentic, Extension). |
| `docs/0810-audit-privacy.md` | **Protocol** | 🟢 **Stable** | - | Privacy audit (IAPP, IEEE, NIST). |
| `docs/0811-audit-accessibility.md` | **Protocol** | 🟢 **Stable** | - | Accessibility audit (WCAG 2.1). |
| `docs/0812-audit-performance.md` | **Protocol** | 🟢 **Stable** | - | Performance audit (latency, memory, cost). |
| `docs/0813-audit-code-quality.md` | **Protocol** | 🟢 **Stable** | - | Code quality audit (SOLID, complexity). |
| `docs/0814-audit-license-compliance.md` | **Protocol** | 🟢 **Stable** | - | License compliance audit (SPDX). |
| `docs/0815-audit-claude-capabilities.md` | **Protocol** | 🟢 **Stable** | - | Claude Code capabilities audit (weekly). |
| `docs/0816-audit-dependabot-prs.md` | **Protocol** | 🟢 **Stable** | - | Dependabot PR audit with regression detection. Prerequisite for 0809. |
| `docs/0817-audit-wiki-alignment.md` | **Protocol** | 🟢 **Stable** | - | Wiki alignment audit. Part of 0009 Full Mode. |
| `docs/0899-meta-audit.md` | **Protocol** | 🟢 **Stable** | - | Meta-audit (audit of audits). |

### 10xx Feature Specifications
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/1005-graph-tests.md` | **Spec** | ⚫ **Legacy** | #5 | Obsolete (LangGraph removed per ADR 0211). |
| `docs/1006-rag-vector.md` | **Spec** | ⚪ **Placeholder** | #6 | RAG Vector Store implementation. |
| `docs/1007-observability.md` | **Spec** | ⚪ **Placeholder** | #7 | Observability and tracing. |
| `docs/1010-semantic-guardrails.md` | **Spec** | 🟡 **Beta** | #10 | Semantic Guardrail (LLM-based). |
| `docs/1011-local-guardrails.md` | **Spec** | 🟡 **Beta** | #11 | Selection Check (local validation). |
| `docs/1014-compliance-engine.md` | **Spec** | 🟡 **Beta** | #14 | Compliance checking engine. |
| `docs/legacy/1025-linkedin-auth-gate.md` | **Spec** | ⚫ **Legacy** | #25 | LinkedIn auth (cookie heuristic). Superseded by #116 (OAuth). |
| `docs/1041-security-audit.md` | **Spec** | 🟢 **Stable** | #41 | Security audit and permission culling. |
| `docs/1042-whitelist-mode.md` | **Spec** | 🟢 **Stable** | #42 | Whitelist mode and safety filters. |
| `docs/1043-privacy-compliance.md` | **Spec** | 🟢 **Stable** | #43 | Privacy policy compliance. |
| `docs/1045-deterministic-hate-filter.md` | **Spec** | 🟢 **Stable** | #45 | Denylist (deterministic hate filter). |
| `docs/1051-store-compliance.md` | **Spec** | 🟡 **Beta** | #51 | Chrome Web Store compliance. |
| `docs/1053-store-assets.md` | **Spec** | ⚪ **Placeholder** | #53 | Store asset generation. |
| `docs/1069-log-inspector.md` | **Spec** | 🟢 **Stable** | #69 | CLI Inspector for DynamoDB telemetry. |
| `docs/1076-allowlist-popup.md` | **Spec** | 🟢 **Stable** | #76 | Domain allowlist popup LLD. |
| `docs/1077-action-feedback.md` | **Spec** | 🟢 **Stable** | #77 | User action feedback overlay LLD. |
| `docs/legacy/1080-wire-agent-logic-langgraph.md` | **Spec** | ⚫ **Legacy** | #80 | Wiring agent.py (LangGraph). Superseded by #113. |
| `docs/1104-age-restricted-blocking.md` | **Spec** | 🟢 **Stable** | #104 | Age-restricted site blocking via RTA/adult rating detection. |
| `docs/1105-test-site-infrastructure.md` | **Spec** | 🟢 **Stable** | #105 | Scriptable test site infrastructure (GitHub Pages + Playwright). |
| `docs/1113-naked-python-architecture.md` | **Spec** | 🟢 **Stable** | #113 | Naked Python sequential pipeline (replaces LangGraph). |
| `docs/1116-linkedin-oauth.md` | **Spec** | 🟢 **Stable** | #116 | LinkedIn OAuth authentication for user gating. |
| `docs/legacy/1119-rsdb-download-utility.md` | **Spec** | ⚫ **Legacy** | #119 | RSDB download utility (superseded by #121). |
| `docs/1121-wikipedia-denylist.md` | **Spec** | 🟢 **Stable** | #121 | Wikipedia denylist integration (replaces RSDB Gist source). |
| `docs/1124-digital-etymologist.md` | **Spec** | 🟢 **Stable** | #124 | Digital Etymologist persona with structured JSON response. |
| `docs/1125-museum-label-ui.md` | **Spec** | 🟢 **Stable** | #125 | Museum Label progressive disclosure UI. |
| `docs/1095-security-hardening.md` | **Spec** | 🟢 **Stable** | #95 | Security hardening via CloudFront + WAF (rate limiting, header validation). |
| `docs/1126-hard-soft-blocking.md` | **Spec** | 🟠 **In-Progress** | #126 | Hard vs. Soft blocking logic differentiation. |
| `docs/1084-signal-inspector.md` | **Spec** | 🟢 **Stable** | #84 | Signal Inspector CLI for compliance auditing. |
| `docs/1100-firefox-compatibility.md` | **Spec** | 🟢 **Stable** | #100 | Firefox MV2 compatibility. |
| `docs/1102-repo-reorganization.md` | **Spec** | 🟠 **In-Progress** | #102 | Repository structure reorganization. |
| `docs/1132-support-email-infrastructure.md` | **Spec** | 🟠 **In-Progress** | #132 | Cloudflare email routing setup. |
| `docs/1137-lambda-latency-investigation.md` | **Spec** | 🟢 **Stable** | #137 | Lambda 5-second latency investigation. |
| `docs/1145-dynamodb-ttl.md` | **Spec** | 🟢 **Stable** | #145 | DynamoDB TTL for automatic data expiry. |
| `docs/1147-gdpr-data-erasure.md` | **Spec** | 🟢 **Stable** | #147 | GDPR Article 17 data erasure process. |
| `docs/1148-bedrock-no-training.md` | **Spec** | 🟢 **Stable** | #148 | Bedrock no-training compliance verification (compliance-as-code). |
| `docs/1150-dynamodb-data-hygiene.md` | **Spec** | 🟠 **In-Progress** | #150 | AI-powered DynamoDB data cleanup tool. |
| `docs/1153-smoke-test-fixture-fix.md` | **Spec** | 🟠 **In-Progress** | #153 | Fix pytest fixture errors in smoke_test.py. |
| `docs/1154-aria-accessibility.md` | **Spec** | 🟠 **In-Progress** | #154 | ARIA attributes for screen reader accessibility. |
| `docs/1155-noarchive-skip-persistence.md` | **Spec** | 🟠 **In-Progress** | #155 | Skip DynamoDB persistence for noarchive signal. |
| `docs/1156-extension-latency-optimization.md` | **Spec** | 🟠 **In-Progress** | #156 | Extension click-to-glass latency optimization. |
| `docs/1157-eslint-flat-config.md` | **Spec** | 🟠 **In-Progress** | #157 | ESLint flat config migration. |
| `docs/1160-ci-accessibility-checks.md` | **Spec** | 🟠 **In-Progress** | #160 | Automated accessibility checks in CI. |
| `docs/1161-ci-performance-benchmarks.md` | **Spec** | 🟠 **In-Progress** | #161 | Automated performance benchmarks in CI. |
| `docs/1162-noarchive-transform-layer.md` | **Spec** | 🟢 **Stable** | #162 | Transform layer (summarization) for noarchive. |

### Prototypes & Design Artifacts
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/prototypes/popup-prototype.jsx` | **Prototype** | 🟢 **Stable** | #76 | React prototype for allowlist popup UI. |

### Implementation Reports (Nested by Issue)
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/reports/45/implementation-report.md` | **Report** | 🟢 **Stable** | #45 | Implementation report for denylist feature. |
| `docs/reports/45/test-report.md` | **Report** | 🟢 **Stable** | #45 | Test report for denylist feature. |
| `docs/reports/69/implementation-report.md` | **Report** | 🟢 **Stable** | #69 | Implementation report for log inspector tool. |
| `docs/reports/69/test-report.md` | **Report** | 🟢 **Stable** | #69 | Test report for log inspector tool. |
| `docs/reports/76/implementation-report.md` | **Report** | 🟢 **Stable** | #76 | Implementation report for allowlist popup. |
| `docs/reports/76/test-report.md` | **Report** | 🟢 **Stable** | #76 | Test report for allowlist popup. |
| `docs/reports/77/implementation-report.md` | **Report** | 🟢 **Stable** | #77 | Implementation report for action feedback feature. |
| `docs/reports/77/test-report.md` | **Report** | 🟢 **Stable** | #77 | Test report for action feedback feature. |
| `docs/reports/80/implementation-report.md` | **Report** | 🟢 **Stable** | #80 | Retroactive report for abandoned LangGraph implementation. |
| `docs/reports/82/implementation-report.md` | **Report** | 🟢 **Stable** | #82 | Implementation report for icon assets. |
| `docs/reports/82/test-report.md` | **Report** | 🟢 **Stable** | #82 | Test report for icon assets. |
| `docs/reports/113/implementation-report.md` | **Report** | 🟢 **Stable** | #113 | Implementation report for Naked Python architecture. |
| `docs/reports/113/test-report.md` | **Report** | 🟢 **Stable** | #113 | Test report for Naked Python architecture. |
| `docs/reports/114/implementation-report.md` | **Report** | 🟢 **Stable** | #114 | Implementation report for overlay restore (also closes #98). |
| `docs/reports/114/test-report.md` | **Report** | 🟢 **Stable** | #114 | Test report for overlay restore. |
| `docs/reports/121/implementation-report.md` | **Report** | 🟢 **Stable** | #121 | Implementation report for Wikipedia denylist integration. |
| `docs/reports/121/test-report.md` | **Report** | 🟢 **Stable** | #121 | Test report for Wikipedia denylist integration. |
| `docs/reports/84/implementation-report.md` | **Report** | 🟢 **Stable** | #84 | Implementation report for Signal Inspector CLI. |
| `docs/reports/84/test-report.md` | **Report** | 🟢 **Stable** | #84 | Test report for Signal Inspector CLI. |
| `docs/reports/95/implementation-report.md` | **Report** | 🟢 **Stable** | #95 | Implementation report for security hardening via CloudFront + WAF. |
| `docs/reports/95/test-report.md` | **Report** | 🟢 **Stable** | #95 | Test report for security hardening via CloudFront + WAF. |
| `docs/reports/100/implementation-report.md` | **Report** | 🟢 **Stable** | #100 | Implementation report for Firefox compatibility. |
| `docs/reports/100/test-report.md` | **Report** | 🟢 **Stable** | #100 | Test report for Firefox compatibility. |
| `docs/reports/104/implementation-report.md` | **Report** | 🟢 **Stable** | #104 | Implementation report for age-restricted site blocking. |
| `docs/reports/104/test-report.md` | **Report** | 🟢 **Stable** | #104 | Test report for age-restricted site blocking. |
| `docs/reports/105/implementation-report.md` | **Report** | 🟢 **Stable** | #105 | Implementation report for test site infrastructure. |
| `docs/reports/105/test-report.md` | **Report** | 🟢 **Stable** | #105 | Test report for test site infrastructure. |
| `docs/reports/124/implementation-report.md` | **Report** | 🟢 **Stable** | #124 | Implementation report for Digital Etymologist. |
| `docs/reports/124/test-report.md` | **Report** | 🟢 **Stable** | #124 | Test report for Digital Etymologist. |
| `docs/reports/162/implementation-report.md` | **Report** | 🟢 **Stable** | #162 | Implementation report for NoArchive Transform layer. |
| `docs/reports/162/test-report.md` | **Report** | 🟢 **Stable** | #162 | Test report for NoArchive Transform layer. |

### 90xx Journals & Logs
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/6000-open-issues.md` | **Report** | 🟢 **Stable** | - | Current open GitHub issues (regenerate with `poetry run python tools/print/print_most_recent_open_issues.py`). |
| `docs/6001-closed-issues.md` | **Report** | 🟢 **Stable** | - | All closed GitHub issues (historical reference). |
| `docs/9000-lessons-learned.md` | **Log** | 🟢 **Stable** | - | Aletheia-specific lessons (project-scoped). |
| `docs/9001-open-investigations.md` | **Log** | 🟡 **Beta** | - | Future work and spikes. |
| `docs/ENGINEERING-JOURNAL.md` | **Log** | 🟢 **Stable** | - | Cross-project engineering lessons (synced). |

### Core Application (Python)
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `src/lambda_function.py` | **Entry** | 🟢 **Stable** | #113, #124 | Main AWS Lambda handler (Naked Python orchestrator, Digital Etymologist). |
| `src/etymologist.py` | **Logic** | 🟢 **Stable** | #124 | Digital Etymologist persona with structured JSON output. |
| `src/observability.py` | **Logic** | 🟢 **Stable** | #7 | X-Ray tracing and CloudWatch metrics (STRICT BAN on PII). |
| `src/__init__.py` | **Module** | 🟢 **Stable** | - | Package init. |
| `src/guardrails/__init__.py` | **Module** | 🟢 **Stable** | - | Guardrails package init. |
| `src/guardrails/denylist.py` | **Logic** | 🟢 **Stable** | #45 | Denylist guardrail (hash-based term blocking). |
| `src/guardrails/engine.py` | **Logic** | 🟡 **Beta** | #113 | Guardrails engine (Selection Check + Denylist stub). |
| `src/guardrails/validators.py` | **Logic** | 🟡 **Beta** | #11 | Validator functions. |
| `src/guardrails/semantic.py` | **Logic** | 🟡 **Beta** | #10 | Semantic guardrail (LLM-based). |
| `src/guardrails/resources/denylist.json` | **Data** | 🟢 **Stable** | #121 | Denylist terms (803 terms from Wikipedia). |
| `src/guardrails/resources/taxonomy.json` | **Data** | 🟢 **Stable** | #10 | Taxonomy and few-shot examples. |
| `src/signal_inspector/__init__.py` | **Module** | 🟢 **Stable** | #84 | Signal Inspector package init. |
| `src/signal_inspector/fetcher.py` | **Logic** | 🟢 **Stable** | #84 | URL fetching with User-Agent handling. |
| `src/signal_inspector/models.py` | **Logic** | 🟢 **Stable** | #84 | Data models (SignalResult, FetchStatus, etc.). |
| `src/signal_inspector/parser.py` | **Logic** | 🟢 **Stable** | #84 | Signal extraction (meta, headers, robots.txt). |
| `src/signal_inspector/reporter.py` | **Logic** | 🟢 **Stable** | #84 | Console and JSONL output reporting. |

### Browser Extensions
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `extensions/chrome/manifest.json` | **Config** | 🟢 **Stable** | #100 | Chrome Manifest V3 (Privacy-First). |
| `extensions/chrome/overlay.js` | **Logic** | 🟢 **Stable** | #100 | Chrome overlay UI with stateful timer management. |
| `extensions/chrome/service-worker.js` | **Logic** | 🟢 **Stable** | #100 | Chrome background script with allowlist gate and WAF header. |
| `extensions/chrome/popup.html` | **UI** | 🟡 **Beta** | #76 | Popup UI structure (three views). |
| `extensions/chrome/popup.css` | **Style** | 🟡 **Beta** | #76 | Popup styling with design tokens. |
| `extensions/chrome/popup.js` | **Logic** | 🟡 **Beta** | #76 | Popup logic and storage interaction. |
| `extensions/chrome/content-safety.js` | **Logic** | 🟢 **Stable** | #104 | Content script for age-gate detection (RTA meta tags). |
| `extensions/chrome/content-check.js` | **Logic** | 🟢 **Stable** | #104 | Content script for adult site detection (multiple signals). |
| `extensions/chrome/icons/*` | **Asset** | 🟢 **Stable** | #82 | Chrome extension icons (16/32/48/128px). |
| `extensions/firefox/manifest.json` | **Config** | 🟢 **Stable** | #100 | Firefox Manifest V2 (browser_specific_settings). |
| `extensions/firefox/overlay.js` | **Logic** | 🟢 **Stable** | #100 | Firefox overlay UI with stateful timer management. |
| `extensions/firefox/service-worker.js` | **Logic** | 🟢 **Stable** | #100 | Firefox background script (browser.* API). |
| `extensions/firefox/popup.html` | **UI** | 🟡 **Beta** | #100 | Popup UI structure (three views). |
| `extensions/firefox/popup.css` | **Style** | 🟡 **Beta** | #100 | Popup styling with design tokens. |
| `extensions/firefox/popup.js` | **Logic** | 🟡 **Beta** | #100 | Popup logic and storage interaction. |
| `extensions/firefox/icons/*` | **Asset** | 🟢 **Stable** | #82 | Firefox extension icons (16/32/48/128px). |
| `index.html` | **Asset** | ⚫ **Legacy** | #81 | Landing page (cyberpunk). To be redesigned. |

### Infrastructure & Deployment
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `aws-cleanup-old-resources.sh` | **Script** | 🟡 **Beta** | - | Cleanup old AWS resources. |
| `aws-inventory-check.sh` | **Script** | 🟡 **Beta** | - | AWS resource inventory audit. |
| `batch-pdf.sh` | **Script** | 🟡 **Beta** | - | Batch PDF generation script. |
| `deploy.sh` | **Script** | 🟢 **Stable** | #113 | Lambda deployment automation. |
| `print-all-pdfs.sh` | **Script** | 🟡 **Beta** | - | Print all markdown files to PDF. |
| `print-docs.sh` | **Script** | 🟡 **Beta** | - | Print documentation to PDF. |
| `provision.sh` | **Script** | 🟢 **Stable** | #113 | AWS infrastructure provisioning. |
| `scripts/aws/.gitkeep` | **Placeholder** | 🟢 **Stable** | - | AWS scripts directory placeholder. |
| `dist/` | **Output** | 🚫 **Gitignored** | - | Build artifacts (empty). |
| `temp-pdfs/` | **Output** | 🚫 **Gitignored** | - | Temporary PDF storage (auto-deleted after successful print). |

### Tools & Utilities
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `format-issues.py` | **Utility** | 🟡 **Beta** | - | GitHub issues formatter. |
| `harvest_test_data.py` | **Utility** | 🟡 **Beta** | #72 | Log puller. Pending move to tools/. |
| `tools/fetch_denylist.py` | **Utility** | 🟢 **Stable** | #121 | Wikipedia denylist fetcher (multi-pass wikitext parser). |
| `tools/generate_store_assets.py` | **Utility** | ⚪ **Placeholder** | #53 | Store asset generator. |
| `tools/log_viewer.py` | **Utility** | 🟢 **Stable** | #69 | DynamoDB Inspector. |
| `tools/generate_icons.py` | **Utility** | 🟢 **Stable** | #82 | Icon factory (Pillow). Supports `--transparent` and `--threshold N` CLI options. |
| `tools/master_lambda.png` | **Asset** | 🟢 **Stable** | #82 | Master source for branding. |
| `tools/smoke_test.py` | **Utility** | 🟢 **Stable** | #113 | Lambda smoke test (3 scenarios). |
| `tools/build_release.py` | **Utility** | 🟢 **Stable** | #100 | Build release ZIPs for Chrome and Firefox extensions. |
| `tools/inspect_signals.py` | **Utility** | 🟢 **Stable** | #84 | Signal Inspector CLI (robots.txt, meta, headers, rating). |
| `tools/print/print_markdown.py` | **Utility** | 🟢 **Stable** | - | Batch markdown→PDF printer with spooler monitoring and print tracking. |
| `tools/print/print_most_recent_open_issues.py` | **Utility** | 🟢 **Stable** | - | GitHub issues fetcher/printer (saves to docs/6000-*.md). |
| `tools/print/audit_long_lines.py` | **Utility** | 🟢 **Stable** | #103 | Audits markdown files for print overflow (>100 char lines). |
| `tools/print/pandoc-header.tex` | **Asset** | 🟢 **Stable** | - | LaTeX header template for PDF generation (fancy headers). |
| `tools/append_session_log.py` | **Utility** | 🟢 **Stable** | - | Append session log entries without reading entire file (avoids token limits). |
| `tools/generate_onboard_digest.py` | **Utility** | 🟢 **Stable** | - | Generate compact onboard digest from live repo state (~92% token reduction). |
| `tools/aws/lambda-status.sh` | **Utility** | 🟢 **Stable** | - | Show Lambda concurrency status (ON/OFF). |
| `tools/aws/lambda-on.sh` | **Utility** | 🟢 **Stable** | - | Enable Lambda (remove concurrency limit). |
| `tools/aws/lambda-off.sh` | **Utility** | 🟢 **Stable** | - | Disable Lambda (set concurrency=0). |
| `tools/aws/waf-setup.sh` | **Utility** | 🟢 **Stable** | #95 | CloudFront + WAF setup with rate limiting (--env dev/prod). |
| `tools/policy_check.sh` | **Utility** | 🟢 **Stable** | - | Pre-commit/CI policy compliance check (ADR 0201, CLAUDE.md directives). |
| `tools/deploy_test_sites.sh` | **Utility** | 🟢 **Stable** | #105 | Deploy test site fixtures to GitHub Pages. |

### Testing & Verification
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `run_guardrails.py` | **Test** | ⚪ **Placeholder** | - | Guardrail runner. |
| `test_ground_truth.json` | **Data** | 🟢 **Stable** | - | Gold standard test dataset. |
| `test_holistic_data.json` | **Data** | 🟡 **Beta** | - | Raw harvested test data. |
| `tests/__init__.py` | **Test** | 🟢 **Stable** | - | Test package init. |
| `tests/test_denylist.py` | **Test** | 🟢 **Stable** | #45 | Unit tests for denylist guardrail. |
| `tests/test_fetch_denylist.py` | **Test** | 🟢 **Stable** | #121 | Unit tests for Wikipedia denylist fetcher (26 tests). |
| `tests/test_guardrails.py` | **Test** | 🟡 **Beta** | #11 | Unit tests for guardrails. |
| `tests/test_lambda_handler.py` | **Test** | 🟢 **Stable** | #113, #124 | Unit tests for Lambda handler. |
| `tests/test_etymologist.py` | **Test** | 🟢 **Stable** | #124 | Unit tests for Digital Etymologist (51 tests). |
| `tests/test_noarchive.py` | **Test** | 🟢 **Stable** | #162 | Unit tests for NoArchive Transform layer (25 tests). |
| `tests/test_signal_inspector.py` | **Test** | 🟢 **Stable** | #84 | Unit + live tests for Signal Inspector (31 tests). |
| `tests/fixtures/signal_inspector/` | **Data** | 🟢 **Stable** | #84 | HTML/txt test fixtures for signal parsing. |
| `tests/test_semantic.py` | **Test** | 🟡 **Beta** | #10 | Unit tests for semantic layer. |
| `tests/manual_overlay_math.html` | **Test** | 🟢 **Stable** | #98 | Manual viewport positioning test page. |
| `tests/data/.gitkeep` | **Placeholder** | 🟢 **Stable** | - | Test data directory placeholder. |
| `tests/data/etymology_golden_set.json` | **Data** | 🟢 **Stable** | #124 | Golden set for Digital Etymologist (20 terms, 8 extraction tests, 6 validation tests). |
| `tests/infra/verify_waf.sh` | **Test** | 🟢 **Stable** | #95 | Automated WAF verification (no vibes testing). |
| `tests/e2e/waf-integration.spec.js` | **Test** | 🟢 **Stable** | #95 | Playwright E2E tests for WAF integration. |
| `tests/e2e/age-gate.spec.js` | **Test** | 🟢 **Stable** | #104 | Playwright E2E tests for age-restricted site blocking. |
| `tests/e2e/xss-protection.spec.js` | **Test** | 🟢 **Stable** | #95 | Playwright E2E tests for XSS protection. |
| `tests/fixtures/html/test-waf.html` | **Fixture** | 🟢 **Stable** | #95 | Test page for WAF E2E tests. |
| `tests/fixtures/html/test-adult.html` | **Fixture** | 🟢 **Stable** | #104 | Test page with adult rating meta tag. |
| `tests/fixtures/html/test-rta.html` | **Fixture** | 🟢 **Stable** | #104 | Test page with RTA label pattern. |
| `tests/fixtures/html/test-mature.html` | **Fixture** | 🟢 **Stable** | #104 | Test page with mature rating (allowed). |
| `tests/fixtures/html/test-clean.html` | **Fixture** | 🟢 **Stable** | #104 | Test page with no rating meta. |
| `tests/fixtures/html/test-xss-*.html` | **Fixture** | 🟢 **Stable** | #95 | XSS attack vector test pages (script, img, event). |
| `verify_bedrock.py` | **Test** | ⚪ **Placeholder** | - | Bedrock connectivity test. |
| `verify_holistic.py` | **Test** | 🟡 **Beta** | - | LLM-based holistic judge. |
| `docs/security/vulnerability-test.md` | **Test** | 🟢 **Stable** | #95 | Manual vulnerability reproduction scripts. |

### Session Logs

**Format change (2026-01-07):** New session logs use daily format `YYYY-MM-DD.md`. Legacy weekly files remain for historical reference.

| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `docs/session-logs/YYYY-MM-DD.md` | **Log** | 🟠 **In-Progress** | #191 | Daily session logs (new format). |
| `docs/session-logs/Week-starting-2025-12-15.md` | **Log** | 🟢 **Stable** | - | (Legacy) Session log week of Dec 15-21. |
| `docs/session-logs/Week-starting-2025-12-22.md` | **Log** | 🟢 **Stable** | - | (Legacy) Session log week of Dec 22-28. |
| `docs/session-logs/Week-starting-2025-12-29.md` | **Log** | 🟢 **Stable** | - | (Legacy) Session log week of Dec 29 - Jan 4 (part 1). |
| `docs/session-logs/Week-starting-2025-12-29-part2.md` | **Log** | 🟢 **Stable** | - | (Legacy) Session log week of Dec 29 - Jan 4 (part 2). |
| `docs/session-logs/Week-starting-2026-01-05.md` | **Log** | 🟢 **Stable** | - | (Legacy) Last weekly log before format change. |

### Legacy & Abandoned
| File | Role | Status | Linked Issue | Description |
| :--- | :--- | :--- | :--- | :--- |
| `prompts/` | **Archive** | ⚫ **Legacy** | - | Old text prompts. To be cleaned. |
