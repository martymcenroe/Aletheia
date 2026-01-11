---
description: Full 08xx audit suite (1-2 hours)
argument-hint: "[--help] [--deep] [NNNN] [NNNN] ..."
---

# Full Audit Suite (0800)

**If `$ARGUMENTS` contains `--help`:** Display the Help section below and STOP. Do not execute any audits.

---

## Help

Usage: `/audit [--help] [--deep] [NNNN] [NNNN] ...`

| Argument | Description |
|----------|-------------|
| `--help` | Show this help message and exit |
| `--deep` | Enable web search for external research (CVEs, GDPR, etc.) |
| `NNNN` | Run specific audit(s) by number (e.g., `0809`, `0810`) |
| (none) | Run ALL audits in sequence (internal analysis only) |

**Examples:**
- `/audit --help` - show this help
- `/audit` - run full suite (standard mode, 1-2 hours)
- `/audit --deep` - run full suite with web research
- `/audit 0809` - run just security audit
- `/audit 0809 0810 0811` - run security, privacy, accessibility
- `/audit --deep 0809` - run security audit with CVE lookups

**Time estimates:**
- Single audit: 5-15 minutes
- Full suite (standard): 1-2 hours
- Full suite (deep): 2-3 hours

**Output:** Results saved to `docs/audit-results/YYYY-MM-DD.md`

---

## Execution

Execute all 08xx audits in sequence per @docs/0800-audit-index.md

This is **explicit approval** to execute all audits autonomously.

## Arguments

| Arg | Effect |
|-----|--------|
| (none) | Run ALL audits - internal analysis only |
| `--deep` | Run ALL audits with web search for external research |
| `NNNN` | Run SINGLE audit by number (e.g., `0817`, `0821`) |
| `NNNN NNNN ...` | Run MULTIPLE audits by number (space-separated) |
| `--deep NNNN ...` | Run specified audit(s) with web search |

**Examples:**
- `/audit` - run full suite (standard mode)
- `/audit --deep` - run full suite with web research
- `/audit 0809` - run just security audit
- `/audit 0809 0810 0811` - run security, privacy, and accessibility audits
- `/audit --deep 0821` - run agentic governance with web search
- `/audit --deep 0809 0819` - run security and AI supply chain with web search
- `ultrathink: /audit 0899` - run meta-audit with extended thinking

## Deep Mode

**Deep mode enables WebSearch/WebFetch for:**
- 0809 Security: OWASP updates, CVEs, extension vulnerabilities
- 0810 Privacy: GDPR/CCPA guidance, Chrome Web Store requirements
- 0814 License: Package license lookups, SPDX compatibility
- 0815 Claude Capabilities: Anthropic changelog, Claude Code releases
- 0818 AI Management: ISO/IEC 42001 updates
- 0819 AI Supply Chain: CVE searches, dependency vulnerabilities
- 0820 Explainability: EU AI Act updates, XAI frameworks
- 0821 Agentic Governance: OWASP Agentic Top 10 updates
- 0898 Horizon Scanning: **REQUIRES deep** - framework discovery
- 0899 Meta-Audit: Industry audit best practices

## Rules
- Use absolute paths and `git -C` patterns (no cd && chaining)
- Use `--repo martymcenroe/Aletheia` for all gh commands
- **Evidence over inference:** Grep code/config, don't trust doc claims
- **Do NOT auto-fix issues** - report findings for orchestrator triage
  - **Exception:** 0829 Lambda Failure Remediation is a remediation audit - it MAY fix issues on worktrees
- Report findings with severity: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`
- In standard mode: Skip audits that require external access
- In deep mode: Use WebSearch tool for external research

---

## Audit Sequence

### 0801 - Open Issues Currency
**Purpose:** Identify issues that are actually complete, deprecated, or stale.
**Ref:** `docs/0801-open-issues-audit.md`
```bash
gh issue list --state open --repo martymcenroe/Aletheia --limit 100
```
**Check:** For each open issue, verify it's truly in progress. Flag:
- Issues with no activity in 30+ days
- Issues that appear complete based on merged PRs
- Issues superseded by other work

### 0802 - Reports Completeness
**Purpose:** Ensure all closed issues have required reports.
**Ref:** `docs/0802-reports-completeness-audit.md`
```bash
gh issue list --state closed --repo martymcenroe/Aletheia --limit 50 --json number,title,closedAt
```
**Check:** For each closed issue, verify `docs/reports/{IssueID}/` exists with:
- `implementation-report.md`
- `test-report.md`

### 0803 - LLD-to-Code Alignment
**Purpose:** Verify implementation matches LLD.
**Ref:** `docs/0803-lld-code-audit.md`
**Check:** For each `docs/1xxx-*.md` with status 🟢 Stable:
1. Read the LLD requirements
2. Grep codebase for implementation
3. Flag deviations not documented in implementation report

### 0804 - File Inventory Drift
**Purpose:** Detect files not in inventory, or inventory entries for deleted files.
**Ref:** `docs/0804-inventory-audit.md`
**Check:**
1. Glob `src/**/*.py`, `tools/**/*.py`, `extensions/**/*.js`
2. Compare against `docs/0003-file-inventory.md`
3. Flag missing entries or orphaned inventory lines

### 0805 - Terminology Consistency
**Purpose:** Ensure consistent naming across docs and code.
**Ref:** `docs/0805-terminology-audit.md`
**Check:** Grep for deprecated terms:
```bash
grep -rn "L1\|L2\|L3" docs/ src/
grep -rn "whitelist" docs/ src/ extensions/
grep -rn "blacklist" docs/ src/ extensions/
```
Should find: `allowlist`, `denylist`, `Selection Check`, `Denylist`, `Semantic`

### 0806 - Architecture Audit
**Purpose:** Detect drift between docs/0001-system-architecture.md and actual codebase.
**Ref:** `docs/0806-architecture-audit.md`
**Check:**
1. Verify each component in 0001 exists in code
2. Verify code components are documented in 0001
3. Check ADRs are still accurate

### 0807 - AgentOS Health Check
**Purpose:** Verify the documentation system itself is healthy.
**Ref:** `docs/0807-agentos-audit.md`
**Check:**
1. All docs/0xxx files have correct formatting
2. Cross-references resolve (grep for broken `docs/0xxx` refs)
3. Templates match current practice

### 0808 - Permission Permissiveness
**Purpose:** Ensure agent permissions are maximally permissive within safety bounds.
**Ref:** `docs/0808-audit-permission-permissiveness.md`
**Check:** Read `.claude/settings.local.json`:
1. Verify deny list contains only truly dangerous commands
2. Identify patterns that cause frequent approval prompts

### 0809 - Security Audit
**Purpose:** Comprehensive security audit.
**Ref:** `docs/0809-audit-security.md`
**Prerequisite:** 0816 (Dependabot PRs) must run first.
**Check:**
1. OWASP Top 10 (2021)
2. OWASP LLM Top 10 (2025)
3. OWASP Agentic Security (2026)
4. Extension-specific (Manifest V3, CSP)

**Deep mode:**
- WebSearch: "OWASP Top 10 2025 updates"
- WebSearch: "Chrome extension security vulnerabilities 2026"
- WebSearch: "AWS Lambda security best practices 2026"
- WebSearch: "LLM prompt injection CVEs recent"

### 0810 - Privacy Audit
**Purpose:** Verify data protection compliance.
**Ref:** `docs/0810-audit-privacy.md`
**Check:**
1. Data collection inventory
2. Storage duration
3. User consent mechanisms
4. Data deletion capability

**Deep mode:**
- WebSearch: "GDPR browser extension requirements 2026"
- WebSearch: "CCPA compliance updates 2026"
- WebSearch: "Chrome Web Store privacy policy requirements"

### 0811 - Accessibility Audit
**Purpose:** WCAG 2.1 compliance for browser extension.
**Ref:** `docs/0811-audit-accessibility.md`
**Check:**
1. Keyboard navigation
2. Screen reader compatibility
3. Color contrast
4. Focus indicators

### 0812 - Performance Audit
**Purpose:** Ensure acceptable performance.
**Ref:** `docs/0812-audit-performance.md`
**Check:**
1. Extension load time
2. Lambda cold start
3. Memory usage
4. Cost per request

### 0813 - Code Quality Audit
**Purpose:** Manual quality checks beyond linting.
**Ref:** `docs/0813-audit-code-quality.md`
**Check:**
1. SOLID principles
2. Cyclomatic complexity
3. Test coverage gaps
4. Documentation completeness

### 0814 - License Compliance
**Purpose:** Ensure MIT-compatible licenses.
**Ref:** `docs/0814-audit-license-compliance.md`
**Check:**
```bash
poetry show --tree
npm ls --all
```
Verify all dependencies use: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, 0BSD, Unlicense

**Deep mode:**
- WebSearch: "[package-name] license" for any unclear licenses
- WebSearch: "SPDX license compatibility MIT"

### 0815 - Claude Capabilities
**Purpose:** Track new Claude Code features.
**Ref:** `docs/0815-audit-claude-capabilities.md`
**Standard mode:** SKIP (requires web search)
**Deep mode:** ENABLED

**Deep mode:**
- WebSearch: "Claude Code changelog 2026"
- WebSearch: "Anthropic Claude Code new features"
- WebSearch: "Claude Code MCP servers"
- Compare against current CLAUDE.md and .claude/ config

### 0816 - Dependabot PR Audit
**Purpose:** Review and merge pending Dependabot PRs.
**Ref:** `docs/0816-audit-dependabot-prs.md`
**MUST run before 0809.**
```bash
gh pr list --state open --repo martymcenroe/Aletheia --author "app/dependabot"
```

### 0817 - Wiki Alignment
**Purpose:** Ensure GitHub Wiki reflects current state.
**Ref:** `docs/0817-audit-wiki-alignment.md`
**Check:**
1. Privacy page matches actual data handling
2. Features list is current
3. Installation instructions work

### 0818 - AI Management System (ISO/IEC 42001)
**Purpose:** AI governance per ISO/IEC 42001:2023.
**Ref:** `docs/0818-audit-ai-management-system.md`
**Check:**
1. AI system inventory (Bedrock, Claude Code, Denylist)
2. Risk classification
3. Development lifecycle documentation
4. Data management practices

**Deep mode:**
- WebSearch: "ISO 42001 updates 2026"
- WebSearch: "AI management system best practices"

### 0819 - AI Supply Chain
**Purpose:** Model provenance, dependency security, AIBOM.
**Ref:** `docs/0819-audit-ai-supply-chain.md`
**Check:**
1. Model source verification (Bedrock/Anthropic)
2. Model version pinning
3. Dependency vulnerability scan
4. Wikipedia denylist source integrity

**Deep mode:**
- WebSearch: "AWS Bedrock vulnerabilities"
- WebSearch: "Anthropic Claude security advisories"
- WebSearch: "AIBOM AI Bill of Materials standards"

### 0820 - Explainability (XAI)
**Purpose:** Ensure AI outputs are understandable and traceable.
**Ref:** `docs/0820-audit-explainability.md`
**Check:**
1. AI disclosure to users
2. Etymology output includes reasoning
3. Guardrail decisions traceable
4. Uncertainty markers present

**Deep mode:**
- WebSearch: "EU AI Act Article 13 transparency requirements"
- WebSearch: "Explainable AI XAI frameworks 2026"

### 0821 - Agentic AI Governance
**Purpose:** OWASP Agentic Top 10 compliance for Claude Code/AgentOS.
**Ref:** `docs/0821-audit-agentic-ai-governance.md`
**Check:**
1. AA01 Agent Goal Hijacking - CLAUDE.md boundaries
2. AA05 Tool Misuse - settings.local.json deny list
3. AA06 Excessive Autonomy - human approval gates
4. AA07 Trust Boundary Violations - worktree isolation

**Deep mode:**
- WebSearch: "OWASP Agentic Top 10 2026 updates"
- WebSearch: "agentic AI governance frameworks"

### 0822 - Bias & Fairness
**Purpose:** Ensure fair, unbiased AI outputs.
**Ref:** `docs/0822-audit-bias-fairness.md`
**Check:**
1. Cultural bias in etymology interpretation
2. Linguistic fairness across language origins
3. Denylist selection bias (Wikipedia sources)
4. Output consistency testing

### 0823 - AI Incident Post-Mortem
**Purpose:** Structured process for AI failure analysis.
**Ref:** `docs/0823-audit-ai-incident-post-mortem.md`
**Check:**
1. Review any open/recent AI-related issues
2. Verify incident classification process exists
3. Check lessons learned captured in 9000
4. Review response time SLAs

### 0829 - Lambda Failure Remediation
**Purpose:** Proactively detect and fix Lambda failures from CloudWatch logs.
**Ref:** `docs/0829-audit-lambda-failure-remediation.md`
**Special:** This is a REMEDIATION audit - it MAY fix issues on worktrees.

**Check:**
1. Get Lambda deployment timestamp from AWS
2. Query CloudWatch for all errors since deployment
3. Categorize and deduplicate by root cause
4. For each error:
   - If fixable: Create worktree, implement fix, create PR (don't merge)
   - If not fixable: Draft issue to `tmp/pending-issues/`
5. Generate report showing: errors found, PRs created, issues drafted

**Output:**
- Report: `tmp/audit-reports/0829-lambda-failures-{date}.md`
- Pending issues: `tmp/pending-issues/lambda-failure-*.md`
- PRs: Listed in report (require orchestrator merge)

**AWS commands require:** `MSYS_NO_PATHCONV=1` prefix on Windows.

### 0898 - Horizon Scanning
**Purpose:** Discover emerging AI governance frameworks and threats.
**Ref:** `docs/0898-horizon-scanning-protocol.md`
**Standard mode:** SKIP (requires web search)
**Deep mode:** ENABLED - **This is the primary discovery audit**

**Deep mode:**
- WebSearch: "OWASP LLM Top 10" site:owasp.org
- WebSearch: "OWASP Agentic" site:genai.owasp.org
- WebSearch: "ISO 42001 updates" site:iso.org
- WebSearch: "NIST AI RMF updates" site:nist.gov
- WebSearch: "EU AI Act implementation guidance"
- Compare findings against 0800-audit-index.md
- Flag new frameworks that need audit procedures

### 0899 - Meta-Audit
**Purpose:** Audit the audit suite itself.
**Ref:** `docs/0899-meta-audit.md`
**Check:**
1. All 08xx procedures are indexed in 0800-audit-index.md
2. No stale audit procedures
3. Audit triggers are appropriate
4. Coverage gaps identified by 0898 addressed

**Deep mode:**
- WebSearch: "software audit best practices 2026"
- WebSearch: "AI system audit frameworks"
- WebSearch: "browser extension compliance audit checklist"

---

## Output Format

After audit(s) complete, produce a summary table:

```markdown
## Audit Results - YYYY-MM-DD

| Audit | Status | Findings |
|-------|--------|----------|
| 0801 Open Issues | PASS/FAIL | N issues need attention |
| 0802 Reports | PASS/FAIL | N missing reports |
| ... | ... | ... |

### Critical Findings
1. [CRITICAL] Description...

### High Priority Findings
1. [HIGH] Description...

### Recommendations
1. ...
```

Save findings to `docs/audit-results/YYYY-MM-DD.md` (create directory if needed).
