---
description: Full 08xx audit suite (1-2 hours)
---

# Full Audit Suite (0800)

Execute all 08xx audits in sequence per @docs/0800-common-audits.md

This is **explicit approval** to execute all audits autonomously.

## Rules
- Use absolute paths and `git -C` patterns (no cd && chaining)
- Use `--repo martymcenroe/Aletheia` for all gh commands
- **Evidence over inference:** Grep code/config, don't trust doc claims
- **Do NOT auto-fix issues** - report findings for orchestrator triage
- Report findings with severity: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`
- Skip audits that require external access (e.g., 0815 web search) unless explicitly enabled

## Audit Sequence

### 0801 - Open Issues Currency
**Purpose:** Identify issues that are actually complete, deprecated, or stale.
```bash
gh issue list --state open --repo martymcenroe/Aletheia --limit 100
```
**Check:** For each open issue, verify it's truly in progress. Flag:
- Issues with no activity in 30+ days
- Issues that appear complete based on merged PRs
- Issues superseded by other work

### 0802 - Reports Completeness
**Purpose:** Ensure all closed issues have required reports.
```bash
gh issue list --state closed --repo martymcenroe/Aletheia --limit 50 --json number,title,closedAt
```
**Check:** For each closed issue, verify `docs/reports/{IssueID}/` exists with:
- `implementation-report.md`
- `test-report.md`

### 0803 - LLD-to-Code Alignment
**Purpose:** Verify implementation matches LLD.
**Check:** For each `docs/1xxx-*.md` with status 🟢 Stable:
1. Read the LLD requirements
2. Grep codebase for implementation
3. Flag deviations not documented in implementation report

### 0804 - File Inventory Drift
**Purpose:** Detect files not in inventory, or inventory entries for deleted files.
**Check:**
1. Glob `src/**/*.py`, `tools/**/*.py`, `extensions/**/*.js`
2. Compare against `docs/0003-file-inventory.md`
3. Flag missing entries or orphaned inventory lines

### 0805 - Terminology Consistency
**Purpose:** Ensure consistent naming across docs and code.
**Check:** Grep for deprecated terms:
```bash
grep -rn "L1\|L2\|L3" docs/ src/
grep -rn "whitelist" docs/ src/ extensions/
grep -rn "blacklist" docs/ src/ extensions/
```
Should find: `allowlist`, `denylist`, `Selection Check`, `Denylist`, `Semantic`

### 0806 - Architecture Audit
**Purpose:** Detect drift between docs/0001-system-architecture.md and actual codebase.
**Check:**
1. Verify each component in 0001 exists in code
2. Verify code components are documented in 0001
3. Check ADRs are still accurate

### 0807 - AgentOS Health Check
**Purpose:** Verify the documentation system itself is healthy.
**Check:**
1. All docs/0xxx files have correct formatting
2. Cross-references resolve (grep for broken `docs/0xxx` refs)
3. Templates match current practice

### 0808 - Permission Permissiveness
**Purpose:** Ensure agent permissions are maximally permissive within safety bounds.
**Check:** Read `.claude/settings.local.json`:
1. Verify deny list contains only truly dangerous commands
2. Identify patterns that cause frequent approval prompts

### 0809 - Security Audit
**Purpose:** Comprehensive security audit.
**Prerequisite:** 0816 (Dependabot PRs) must run first.
**Check per** `docs/0809-audit-security.md`:
1. OWASP Top 10 (2021)
2. OWASP LLM Top 10 (2025)
3. OWASP Agentic Security (2026)
4. Extension-specific (Manifest V3, CSP)

### 0810 - Privacy Audit
**Purpose:** Verify data protection compliance.
**Check per** `docs/0810-audit-privacy.md`:
1. Data collection inventory
2. Storage duration
3. User consent mechanisms
4. Data deletion capability

### 0811 - Accessibility Audit
**Purpose:** WCAG 2.1 compliance for browser extension.
**Check per** `docs/0811-audit-accessibility.md`:
1. Keyboard navigation
2. Screen reader compatibility
3. Color contrast
4. Focus indicators

### 0812 - Performance Audit
**Purpose:** Ensure acceptable performance.
**Check per** `docs/0812-audit-performance.md`:
1. Extension load time
2. Lambda cold start
3. Memory usage
4. Cost per request

### 0813 - Code Quality Audit
**Purpose:** Manual quality checks beyond linting.
**Check per** `docs/0813-audit-code-quality.md`:
1. SOLID principles
2. Cyclomatic complexity
3. Test coverage gaps
4. Documentation completeness

### 0814 - License Compliance
**Purpose:** Ensure MIT-compatible licenses.
**Check:**
```bash
poetry show --tree
npm ls --all
```
Verify all dependencies use: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, 0BSD, Unlicense

### 0815 - Claude Capabilities (SKIP unless enabled)
**Purpose:** Track new Claude Code features.
**Note:** Requires web search. Skip unless user explicitly requests.

### 0816 - Dependabot PR Audit
**Purpose:** Review and merge pending Dependabot PRs.
**MUST run before 0809.**
```bash
gh pr list --state open --repo martymcenroe/Aletheia --author "app/dependabot"
```
**Check per** `docs/0816-audit-dependabot-prs.md`

### 0817 - Wiki Alignment
**Purpose:** Ensure GitHub Wiki reflects current state.
**Check per** `docs/0817-audit-wiki-alignment.md`:
1. Privacy page matches actual data handling
2. Features list is current
3. Installation instructions work

### 0899 - Meta-Audit
**Purpose:** Audit the audit suite itself.
**Check:**
1. All 08xx procedures are indexed in 0800
2. No stale audit procedures
3. Audit triggers are appropriate

## Output Format

After all audits complete, produce a summary table:

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
