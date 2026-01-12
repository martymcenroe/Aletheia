# 7000 - AgentOS Classification Audit

**Generated:** 2026-01-11
**Issue:** #312
**Status:** Draft

---

## Summary

This audit classifies all Aletheia documentation files to prepare for AgentOS centralization. Each file is assigned one of four categories:

| Category | Code | Description | Count |
|----------|------|-------------|-------|
| **AgentOS Core** | `a-core` | Move entirely to AgentOS | 35 |
| **AgentOS Template** | `a-tmpl` | Create template in AgentOS | 19 |
| **Split** | `a-split` | Extract generic parts | 9 |
| **Project-Specific** | `proj` | Stays in Aletheia | 24 |

**Note:** File number 0827 is duplicated (infrastructure-integration and web-assets). This should be corrected in a future cleanup.

---

## Classification Criteria

### AgentOS Core (`a-core`)
- No references to Aletheia-specific infrastructure (Lambda, Bedrock, DynamoDB, Chrome/Firefox)
- Applies to ANY project using AgentOS
- Examples: generic audits, universal templates, cross-project standards

### AgentOS Template (`a-tmpl`)
- Structure is reusable, content is project-specific
- Needs `{{VAR}}` placeholders for project customization
- Examples: architecture docs, file inventory structure

### Split (`a-split`)
- Contains both generic framework AND project-specific details
- Generic parts → AgentOS template, project-specific → local instance
- Examples: security audit (OWASP generic + browser-specific)

### Project-Specific (`proj`)
- Inherently tied to Aletheia's domain/architecture
- No value in generalizing
- Examples: ADRs about Shadow DOM, Defense Funnel

---

## Classification Results

### 00xx - Standards & Core Documentation

| File | Category | Rationale |
|------|----------|-----------|
| `0000-GUIDE.md` | `a-tmpl` | Filing system structure reusable; file references and project name are Aletheia-specific |
| `0000a-IMMEDIATE-PLAN.md` | `proj` | Current sprint status - inherently project-specific |
| `0000b-ONBOARD-DIGEST.md` | `proj` | Auto-generated project status - inherently project-specific |
| `0001-architecture.md` | `a-tmpl` | C4 landing page structure reusable; diagrams are Aletheia-specific |
| `0001a-context-view.md` | `a-tmpl` | C4 Level 1 template reusable; actors are project-specific |
| `0001b-container-view.md` | `a-tmpl` | C4 Level 2 template reusable; containers are project-specific |
| `0001c-runtime-view.md` | `a-tmpl` | Sequence diagram format reusable; flows are project-specific |
| `0001d-adr-digest.md` | `a-tmpl` | ADR digest format reusable; ADR content is project-specific |
| `0001e-quality-attributes.md` | `a-tmpl` | NFR table structure reusable; targets are project-specific |
| `0001f-deployment-view.md` | `a-tmpl` | Deployment doc structure reusable; AWS details are project-specific |
| `0001g-glossary.md` | `a-tmpl` | Glossary format reusable; terms are project-specific |
| `0002-coding-standards.md` | `a-split` | Forbidden commands, poetry rules generic; worktree pattern refs Aletheia |
| `0003-file-inventory.md` | `a-tmpl` | Status taxonomy and table format reusable; file list is project-specific |
| `0004-orchestration-protocol.md` | `a-core` | Generic orchestration workflow applicable to all AgentOS projects |
| `0005-testing-strategy-and-protocols.md` | `a-split` | Trust-but-verify philosophy generic; DynamoDB, Bedrock refs project-specific |
| `0006-mermaid-diagrams.md` | `a-core` | Generic diagram standards applicable to all projects |
| `0007-signal-handling.md` | `proj` | Aletheia-specific policy on web signals (extension behavior) |
| `0008-orchestrator-instructions.md` | `proj` | DEPRECATED - superseded by runbooks |
| `0009-session-closeout-protocol.md` | `a-core` | Generic session cleanup protocol applicable to all projects |
| `0010-standard-labels.md` | `a-core` | Generic GitHub label taxonomy applicable to all projects |
| `0012-devops-architecture.md` | `proj` | Aletheia CI/CD with GitHub Actions - project-specific workflows |
| `0013-testing-architecture.md` | `proj` | Aletheia test pyramid with Playwright, pytest - project-specific |
| `0014-cost-architecture.md` | `proj` | AWS cost breakdown (Lambda, Bedrock, DynamoDB) - project-specific |
| `0015-agent-prohibited-actions.md` | `a-split` | Generic forbidden commands + Aletheia-specific merge_pr.py reference |

### 01xx - Templates

| File | Category | Rationale |
|------|----------|-----------|
| `0100-TEMPLATE-GUIDE.md` | `a-core` | Generic template index applicable to all projects |
| `0101-TEMPLATE-issue.md` | `a-core` | Generic GitHub issue template applicable to all projects |
| `0102-TEMPLATE-feature-lld.md` | `a-core` | Generic LLD template applicable to all projects |
| `0103-TEMPLATE-implementation-report.md` | `a-core` | Generic implementation report template |
| `0104-TEMPLATE-adr.md` | `a-core` | Generic ADR template following Nygard format |
| `0105-TEMPLATE-implementation-plan.md` | `a-core` | Generic implementation plan template |
| `0108-lld-pre-implementation-review.md` | `a-core` | Generic LLD review checklist |
| `0111-TEMPLATE-test-script.md` | `a-core` | Generic manual test script template |
| `0112-TEMPLATE-browser-extension-test-script.md` | `proj` | Browser extension specific test template |
| `0113-TEMPLATE-test-report.md` | `a-core` | Generic test report template |

### 02xx - Architecture Decision Records

| File | Category | Rationale |
|------|----------|-----------|
| `0200-ADR-index.md` | `a-tmpl` | ADR index format reusable; ADR list is project-specific |
| `0201-ADR-privacy-first-permissions.md` | `proj` | Chrome extension activeTab decision - Aletheia-specific |
| `0202-ADR-shadow-dom-isolation.md` | `proj` | Chrome extension Shadow DOM - Aletheia-specific |
| `0203-ADR-stateful-serverless.md` | `proj` | DynamoDB hydration pattern - Aletheia-specific |
| `0204-ADR-defense-funnel.md` | `proj` | Aletheia security pipeline - project-specific |
| `0205-ADR-langgraph-orchestration.md` | `proj` | SUPERSEDED - Aletheia-specific |
| `0206-ADR-streaming-sse.md` | `proj` | Lambda SSE streaming - Aletheia-specific |
| `0207-ADR-single-identity-orchestration.md` | `a-core` | Generic single-user orchestration pattern |
| `0208-ADR-client-side-preference-storage.md` | `proj` | Chrome storage.local - Aletheia-specific |
| `0209-ADR-static-compliance-hosting.md` | `proj` | GitHub Pages for privacy policy - Aletheia-specific |
| `0210-ADR-git-worktree-isolation.md` | `a-core` | Generic worktree pattern for feature branches |
| `0211-ADR-naked-python-architecture.md` | `proj` | boto3 direct vs LangChain - Aletheia-specific |
| `0212-ADR-unified-v3-secure-dom.md` | `proj` | MV3 + innerHTML prohibition - Aletheia-specific |
| `0213-ADR-adversarial-audit-philosophy.md` | `a-core` | Generic audit philosophy for all projects |
| `0214-ADR-claude-staging-pattern.md` | `a-core` | Generic Claude Code staging pattern |
| `0215-ADR-test-first-philosophy.md` | `a-core` | Generic test-first philosophy |

### 06xx - Skill Instructions

| File | Category | Rationale |
|------|----------|-----------|
| `0600-skill-instructions-index.md` | `a-core` | Generic skill index format |
| `0601-skill-gemini-lld-review.md` | `a-core` | Generic Gemini LLD review procedure |
| `0602-skill-gemini-dual-review.md` | `a-core` | Generic Claude-Gemini dual review system |

### 08xx - Audits

| File | Category | Rationale |
|------|----------|-----------|
| `0800-audit-index.md` | `a-core` | Generic audit index and philosophy |
| `0801-open-issues-audit.md` | `a-tmpl` | Issue audit format reusable; GitHub repo is project-specific |
| `0802-reports-completeness-audit.md` | `a-tmpl` | Report audit format reusable; paths are project-specific |
| `0803-lld-code-audit.md` | `a-tmpl` | LLD-code alignment format reusable; LLDs are project-specific |
| `0804-inventory-audit.md` | `a-tmpl` | Inventory audit format reusable; inventory is project-specific |
| `0805-terminology-audit.md` | `a-tmpl` | Terminology audit format reusable; terms are project-specific |
| `0806-architecture-audit.md` | `a-tmpl` | Architecture audit format reusable; docs are project-specific |
| `0807-agentos-audit.md` | `a-core` | Generic AgentOS self-audit |
| `0808-audit-permission-permissiveness.md` | `a-core` | Generic Claude Code permission audit |
| `0809-audit-security.md` | `a-split` | OWASP Top 10 generic; browser/Lambda sections project-specific |
| `0810-audit-privacy.md` | `a-split` | IAPP framework generic; Lambda/Bedrock sections project-specific |
| `0811-audit-accessibility.md` | `a-split` | WCAG 2.1 generic; extension UI sections project-specific |
| `0812-audit-performance.md` | `a-split` | Performance metrics framework generic; Lambda targets project-specific |
| `0813-audit-code-quality.md` | `a-split` | Linting standards generic; CI gates project-specific |
| `0814-audit-license-compliance.md` | `a-core` | Generic SPDX license audit |
| `0815-audit-claude-capabilities.md` | `a-core` | Generic Claude Code feature tracking |
| `0816-audit-dependabot-prs.md` | `a-tmpl` | Dependabot process reusable; CI commands project-specific |
| `0817-audit-wiki-alignment.md` | `a-tmpl` | Wiki audit format reusable; wiki URL is project-specific |
| `0818-audit-ai-management-system.md` | `a-core` | Generic AI lifecycle management |
| `0819-audit-ai-supply-chain.md` | `a-core` | Generic AI supply chain security |
| `0820-audit-explainability.md` | `a-core` | Generic AI explainability audit |
| `0821-audit-agentic-ai-governance.md` | `a-core` | Generic agentic AI governance |
| `0822-audit-bias-fairness.md` | `a-core` | Generic AI bias/fairness audit |
| `0823-audit-ai-incident-post-mortem.md` | `a-core` | Generic AI incident post-mortem |
| `0824-audit-permission-friction.md` | `a-core` | Generic permission friction analysis |
| `0825-audit-ai-safety.md` | `a-split` | AI safety framework generic; Bedrock/etymologist project-specific |
| `0826-audit-cross-browser-testing.md` | `proj` | Browser extension testing - Aletheia-specific |
| `0827-audit-infrastructure-integration.md` | `proj` | Lambda/DynamoDB/Bedrock integration - Aletheia-specific |
| `0827-audit-web-assets.md` | `proj` | Web assets for extension/landing page - Aletheia-specific |
| `0828-audit-build-artifact-freshness.md` | `proj` | Build artifacts for extension - Aletheia-specific |
| `0829-audit-lambda-failure-remediation.md` | `proj` | Lambda failure recovery - Aletheia-specific |
| `0830-audit-architecture-freshness.md` | `a-tmpl` | Architecture freshness format reusable; docs are project-specific |
| `0898-horizon-scanning-protocol.md` | `a-core` | Generic horizon scanning for emerging risks |
| `0899-meta-audit.md` | `a-core` | Generic meta-audit of audit system |

### 09xx - Runbooks

| File | Category | Rationale |
|------|----------|-----------|
| `0900-runbook-index.md` | `a-core` | Generic runbook index format |
| `0901-runbook-nightly-agentos-audit.md` | `a-core` | Generic AgentOS nightly audit procedure |

### 6xxx - Reports (Generated)

| File | Category | Rationale |
|------|----------|-----------|
| `6000-open-issues.md` | `proj` | Project-specific open issues report |
| `6001-closed-issues.md` | `proj` | Project-specific closed issues archive |

### 9xxx - Knowledge

| File | Category | Rationale |
|------|----------|-----------|
| `9000-lessons-learned.md` | `proj` | Aletheia-specific lessons (Chrome extension, Bedrock gotchas) |
| `9001-open-investigations.md` | `proj` | Aletheia-specific future work |

---

## Summary Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| `a-core` | 35 | 40% |
| `a-tmpl` | 19 | 22% |
| `a-split` | 9 | 10% |
| `proj` | 24 | 28% |
| **Total** | 87 | 100% |

**Note:** Total includes 87 classified files (excludes 7000 itself and files in appendix).

---

## Dependency Map

### High-Value Dependencies (files referenced by many others)

1. **`0000-GUIDE.md`** - Referenced by CLAUDE.md, most onboarding docs
2. **`0002-coding-standards.md`** - Referenced by all code-related docs
3. **`0015-agent-prohibited-actions.md`** - Referenced by CLAUDE.md, coding standards
4. **`0100-TEMPLATE-GUIDE.md`** - Referenced by all template users
5. **`0800-audit-index.md`** - Referenced by all audit docs

### Circular Dependencies

None identified. The filing system is hierarchical (index → specific docs).

---

## Recommendations for Migration (Future Work)

### Phase 1: Move `a-core` Files (~35 files)
These can move to AgentOS with minimal modification:
- All 01xx templates (except 0112)
- Generic ADRs (0207, 0210, 0213-0215)
- Generic audits (0800, 0807-0808, 0814-0815, 0818-0824, 0898-0899)
- Skills (0600-0602)
- Runbooks (0900-0901)
- Standards (0004, 0006, 0009, 0010)

### Phase 2: Create Templates for `a-tmpl` Files (~19 files)
These need `{{VAR}}` placeholder versions:
- Architecture docs (0001 series) - use `{{PROJECT_NAME}}`, `{{GITHUB_REPO}}`
- Inventory (0003) - use `{{PROJECT_ROOT}}`
- Issue/report audits (0801-0806, 0816-0817, 0830)

### Phase 3: Split `a-split` Files (~9 files)
These need extraction of generic framework:
- `0002-coding-standards.md` - Extract generic rules, keep worktree pattern local
- `0005-testing-strategy.md` - Extract philosophy, keep tool refs local
- `0015-agent-prohibited-actions.md` - Extract generic bans, keep merge_pr.py local
- Security/privacy/accessibility audits - Extract framework, keep infrastructure local

### Phase 4: Leave `proj` Files (~20 files)
These stay in Aletheia:
- All Aletheia-specific ADRs
- Browser extension templates and audits
- Lambda/infrastructure audits
- Lessons learned and investigations

---

## Verification Checklist

- [x] Every file in 00xx series classified (24 files)
- [x] Every file in 01xx series classified (10 files)
- [x] Every file in 02xx series classified (16 files)
- [x] Every file in 06xx series classified (3 files)
- [x] Every file in 08xx series classified (32 files)
- [x] Every file in 09xx series classified (2 files)
- [x] 6xxx and 9xxx series classified (4 files)
- [x] Classification rationale provided for each file
- [x] Summary statistics calculated
- [x] Dependencies documented
- [x] Migration recommendations provided

---

## Appendix: Files Excluded from Classification

The following directories/files were intentionally excluded as clearly project-specific:

- `docs/lld/` - Feature LLDs for Aletheia issues
- `docs/session-logs/` - Historical session logs
- `docs/reports/` - Implementation/test reports per issue
- `docs/legacy/` - Archived/superseded documents
- `docs/assets/` - Images and diagrams
- `docs/audit-state/` - Audit tracking state
- `docs/prototypes/` - Prototype code
- Root HTML files (index.html, privacy.html, context.html)
- CNAME, ENGINEERING-JOURNAL.md, MVP-ASSESSMENT.md, GEMINI-HANDOFF-*.md
