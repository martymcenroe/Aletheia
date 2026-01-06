# 0809 - Audit: Security

## 1. Purpose

Comprehensive security audit covering web application, LLM, agentic AI, and browser extension security concerns. Based on industry frameworks including OWASP, NIST, and ISC2 best practices.

**Aletheia Context:**
- Browser extension (Chrome MV3 / Firefox MV2)
- AWS Lambda backend (Python)
- AWS Bedrock Claude LLM integration
- Processes user-selected text from web pages

---

## 2. OWASP Top 10 (2025) - Web Application Security

> **Updated 2026-01-06:** Migrated from OWASP 2021 to 2025 framework per Issue #180.

### Key Changes from 2021 → 2025

| 2021 Position | 2025 Position | Category | Change |
|---------------|---------------|----------|--------|
| A02 | A04 | Cryptographic Failures | Fell from #2 to #4 |
| A05 | A02 | Security Misconfiguration | Rose from #5 to #2 |
| A06 | A03 | Vulnerable Components → **Software Supply Chain Failures** | Expanded scope |
| - | A10 | **Mishandling of Exceptional Conditions** | NEW (24 CWEs) |
| A10 | Merged | SSRF | Absorbed into Broken Access Control |

### Checklist

| Risk | Aletheia Applicability | Check | Status |
|------|------------------------|-------|--------|
| **A01: Broken Access Control** | Lambda API endpoints | CloudFront + WAF protected, SSRF controls | ✅ Pass |
| **A02: Security Misconfiguration** | AWS, extension | Minimal permissions, no debug endpoints | ✅ Pass |
| **A03: Software Supply Chain Failures** | Dependencies + models | npm audit: 0 vulns, poetry.lock pinned, Bedrock managed | ✅ Pass |
| **A04: Cryptographic Failures** | Data in transit | HTTPS only via CloudFront | ✅ Pass |
| **A05: Injection** | User input to Lambda | Input validation (20k limit), no eval() | ✅ Pass |
| **A06: Insecure Design** | Architecture | ADRs document security decisions | ✅ Pass |
| **A07: Auth Failures** | LinkedIn OAuth | CSRF protection, secure token storage | ✅ Pass |
| **A08: Data Integrity Failures** | Extension updates | No remote code, all JS bundled | ✅ Pass |
| **A09: Logging & Monitoring Failures** | Lambda | CloudWatch enabled, generic error messages | ✅ Pass |
| **A10: Mishandling of Exceptional Conditions** | Error handling | Fail-closed guardrails, generic errors to client | ✅ Pass |

### A03: Software Supply Chain Failures (Expanded)

The 2025 framework expands A06 "Vulnerable Components" into broader supply chain concerns:

| Check | Requirement | Status |
|-------|-------------|--------|
| Dependency pinning | poetry.lock, package-lock.json committed | ✅ Pass |
| Dependency scanning | Dependabot configured, 0 open alerts | ✅ Pass |
| AI model provenance | Bedrock Claude (AWS-managed, Anthropic source) | ✅ Pass |
| No CDN dependencies | All assets bundled locally | ✅ Pass |
| Build integrity | No untrusted build plugins | ✅ Pass |
| Denylist source | Wikipedia via trusted GitHub Gist (#121) | ✅ Pass |

Cross-reference: See 0819 AI Supply Chain Audit for AIBOM details.

### A10: Mishandling of Exceptional Conditions (NEW)

This new category covers 24 CWEs related to error handling, edge cases, and unexpected conditions:

| Check | Requirement | Status |
|-------|-------------|--------|
| Fail-closed design | Guardrails block on error | ✅ Pass |
| Generic error messages | No stack traces to client | ✅ Pass |
| Rate limit handling | Graceful 429 response | ✅ Pass |
| Timeout handling | Lambda timeout = 30s, CloudFront = 30s | ✅ Pass |
| Empty input handling | Returns error, doesn't crash | ✅ Pass |
| Large input handling | Truncated at 20k chars | ✅ Pass |

### Aletheia-Specific Checks

| Check | Requirement | Status |
|-------|-------------|--------|
| No `<all_urls>` permission | ADR 0201 - Privacy First | ✅ Pass (policy_check.sh) |
| CSP in manifest.json | script-src 'self' only | ✅ Pass (MV3 default) |
| No remote code execution | All code bundled in extension | ✅ Pass (grep verified) |
| No eval() or new Function() | MV3 requirement | ✅ Pass (grep verified) |
| Service worker event-driven | No persistent background | ✅ Pass |

---

## 3. OWASP Top 10 for LLM Applications (2025)

### Checklist

| Risk | Aletheia Applicability | Mitigation | Status |
|------|------------------------|------------|--------|
| **LLM01: Prompt Injection** | User-selected text sent to Claude | XML-wrapped in etymologist.py, prompt injection instruction | ✅ Pass |
| **LLM02: Sensitive Info Disclosure** | Claude responses | No PII stored, in-memory only | ✅ Pass |
| **LLM03: Supply Chain** | Bedrock/Claude dependency | AWS-managed, no custom models | ✅ Pass |
| **LLM04: Data Poisoning** | N/A (no fine-tuning) | Not applicable | ✅ N/A |
| **LLM05: Improper Output Handling** | Rendering Claude output | textContent used (not innerHTML) | ✅ Pass |
| **LLM06: Excessive Agency** | Claude actions | Read-only analysis, no tool use | ✅ Pass |
| **LLM07: System Prompt Leakage** | System prompt exposure | Hardcoded, "Prompt Injection Attempt" response | ✅ Pass |
| **LLM08: Vector/Embedding Weaknesses** | N/A (no RAG) | Not applicable | ✅ N/A |
| **LLM09: Misinformation** | Claude accuracy | Etymologist persona, neutral tone | ✅ Pass |
| **LLM10: Unbounded Consumption** | Bedrock costs | 20k char limit, 500 token max | ✅ Pass |

### Aletheia-Specific Checks

| Check | Requirement | Status |
|-------|-------------|--------|
| System prompt not user-modifiable | Hardcoded in Lambda | ✅ Pass |
| Output sanitized before display | textContent (not innerHTML) | ✅ Pass |
| Rate limiting implemented | Input length limits | ✅ Pass |
| Cost guardrails | Max tokens = 500 | ✅ Pass |

### Finding: Semantic Guardrail Input Handling

| Severity | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| ⚠️ Low | Semantic guardrail sends user text directly without XML wrapping | `src/guardrails/semantic.py:60` | Consider XML-wrapping like etymologist.py for consistency |

**Note:** This is low severity because (1) the guardrail fails-closed on errors, (2) deterministic policy enforcement overrides LLM classification, and (3) even if bypassed, the etymologist has its own prompt injection defenses.

---

## 4. OWASP Top 10 for Agentic Applications (2026)

### Checklist

| Risk | Aletheia Applicability | Mitigation | Status |
|------|------------------------|------------|--------|
| **AA01: Agent Goal Hijacking** | Low risk (single-purpose) | Fixed purpose, no goal modification | ✅ Pass |
| **AA02: Rogue Agents** | N/A (no agent persistence) | Stateless Lambda | ✅ N/A |
| **AA03: Memory Poisoning** | N/A (no memory) | No conversation history | ✅ N/A |
| **AA04: Insecure Inter-Agent Comms** | N/A (single agent) | Not applicable | ✅ N/A |
| **AA05: Tool Misuse** | N/A (no tools) | Read-only analysis | ✅ N/A |
| **AA06: Excessive Autonomy** | Low (user-initiated) | Requires user context menu click | ✅ Pass |
| **AA07: Trust Boundary Violations** | Extension ↔ Lambda | WAF header validation | ✅ Pass |
| **AA08: Cascading Hallucinations** | N/A (single step) | Not applicable | ✅ N/A |
| **AA09: Agent Impersonation** | N/A (no multi-agent) | Not applicable | ✅ N/A |
| **AA10: Persistence Mechanisms** | N/A (stateless) | In-memory only, no state | ✅ N/A |

### Least Agency Principle

| Check | Requirement | Status |
|-------|-------------|--------|
| User initiates all actions | Context menu click required | ✅ Pass |
| No proactive monitoring | On-demand only (ADR 0201) | ✅ Pass |
| No autonomous decisions | Analysis only, no actions | ✅ Pass |
| Bounded output | 500 token limit | ✅ Pass |

---

## 5. Browser Extension Security (Manifest V3)

### Chrome Extension Checks

| Check | Requirement | Status |
|-------|-------------|--------|
| Minimal permissions | activeTab, tabs, scripting, contextMenus, storage | ✅ Pass |
| No host_permissions | Empty array `[]` | ✅ Pass |
| No `<all_urls>` | PROHIBITED by ADR 0201 | ✅ Pass |
| CSP enforced | MV3 default (script-src 'self') | ✅ Pass |
| No remote code | All JS bundled | ✅ Pass |
| No eval() | MV3 prohibited, grep verified | ✅ Pass |
| Service worker scoped | event-driven | ✅ Pass |
| web_accessible_resources | Not declared (none needed) | ✅ Pass |

### Firefox Extension Checks

| Check | Requirement | Status |
|-------|-------------|--------|
| Same permission minimalism | activeTab, tabs, contextMenus, storage | ✅ Pass |
| MV2 → MV3 migration path | Documented in ADRs | ✅ Pass |
| No browser_specific_settings abuse | Minimal gecko config (id + version) | ✅ Pass |

### Supply Chain

| Check | Requirement | Status |
|-------|-------------|--------|
| Dependencies audited | npm audit: 0 vulnerabilities | ✅ Pass |
| Lock files committed | package-lock.json, poetry.lock | ✅ Pass |
| No CDN dependencies | All local | ✅ Pass |
| Dependabot alerts | 0 open (3 fixed historically) | ✅ Pass |
| Dependabot configured | `.github/dependabot.yml` | ✅ Pass |
| Quarterly dependency review | Some outdated (boto3, certifi) - not critical | ⚠️ Note |

### Dependabot Alert Check

**Command:** `gh api repos/martymcenroe/Aletheia/dependabot/alerts --jq '.[] | select(.state == "open")'`

| Alert State | Count | Action Required |
|-------------|-------|-----------------|
| Open | 0 | None |
| Fixed | 3 | None (resolved) |

**Note:** All open Dependabot alerts MUST be resolved before audit passes.

---

## 6. AWS Security

### Lambda Security

| Check | Requirement | Status |
|-------|-------------|--------|
| IAM least privilege | Only DynamoDB + Bedrock | ✅ Pass |
| No hardcoded secrets | Environment variables, policy_check.sh verified | ✅ Pass |
| VPC isolation | N/A (public Lambda via CloudFront) | ✅ N/A |
| Concurrency limits | Configurable via lambda-on/off scripts | ✅ Pass |
| Function URL auth | CloudFront + WAF (X-Aletheia-Client-Version) | ✅ Pass |

### Bedrock Security

| Check | Requirement | Status |
|-------|-------------|--------|
| Model access scoped | claude-3-haiku-20240307-v1:0 | ✅ Pass |
| Guardrails enabled | Denylist + Semantic + fail-closed | ✅ Pass |
| No PII in prompts | User-selected text, in-memory only | ✅ Pass |
| Response logging | CloudWatch, generic errors only | ✅ Pass |

### DynamoDB Security

| Check | Requirement | Status |
|-------|-------------|--------|
| Encryption at rest | AWS default | ✅ Pass |
| No PII stored | Only thread_id, input hash, scores | ✅ Pass |
| TTL enabled | Via DynamoDB config | ✅ Pass |
| IAM scoped | Lambda role only | ✅ Pass |

---

## 7. NIST AI RMF Alignment

### MAP Function (Context)

| Requirement | Aletheia Implementation | Status |
|-------------|------------------------|--------|
| AI system documented | Architecture docs (0001, ADRs) | ✅ Pass |
| Intended use defined | Etymology analysis, bias detection | ✅ Pass |
| Stakeholders identified | End users, web publishers | ✅ Pass |

### MEASURE Function (Assessment)

| Requirement | Aletheia Implementation | Status |
|-------------|------------------------|--------|
| Accuracy measured | pytest test suite | ✅ Pass |
| Bias evaluated | Denylist + semantic guardrail | ✅ Pass |
| Security tested | This audit | ✅ Pass |

### MANAGE Function (Controls)

| Requirement | Aletheia Implementation | Status |
|-------------|------------------------|--------|
| Incident response plan | AWS CloudWatch alerts | ✅ Pass |
| Monitoring active | CloudWatch Logs | ✅ Pass |
| Human oversight | User initiates, reviews output | ✅ Pass |

### GOVERN Function (Oversight)

| Requirement | Aletheia Implementation | Status |
|-------------|------------------------|--------|
| Policies documented | ADRs, CLAUDE.md, audit docs | ✅ Pass |
| Roles defined | Orchestrator protocol (0004) | ✅ Pass |
| Continuous improvement | 9000-lessons-learned.md | ✅ Pass |

---

## 7a. Claude Code Agent Permissions (CRITICAL)

**The agent's permission model is a security boundary.** Overly permissive settings can bypass all other controls.

### Forbidden Substrings Check

Grep `.claude/settings.local.json` for these forbidden patterns. If found in the `allow` list, **FAIL the audit immediately**:

```bash
🤖 grep -E "eval:|env:|printenv:|exec:" .claude/settings.local.json
```

| Pattern | Risk | Must Be In |
|---------|------|------------|
| `eval:` | Arbitrary command execution bypass | `deny` list |
| `exec:` | Process replacement | `deny` list |
| `env:` | Secret exposure via env dump | `deny` list |
| `printenv:` | Secret exposure via env dump | `deny` list |
| `python:` | Write+execute arbitrary code | `deny` list (use `poetry run`) |

### Verification

```bash
# These should return matches (in deny list)
🤖 grep -A50 '"deny"' .claude/settings.local.json | grep -E "eval|env|exec|python"

# This should return NO matches (not in allow list)
🤖 grep -B100 '"deny"' .claude/settings.local.json | grep -E '"Bash\(eval|"Bash\(env:|"Bash\(exec:|"Bash\(python:'
```

---

## 8. Audit Procedure

### Step 0: Prerequisites (MANDATORY)

**Run Dependabot PR Audit (0816) BEFORE proceeding.**

This ensures:
- All safe dependency updates are merged
- Known-problematic updates are documented with issues
- Dependency baseline is clean for vulnerability analysis

```bash
# Execute 0816-audit-dependabot-prs.md procedure
# STOP if 0816 fails - resolve dependency issues first
```

### Steps 1-6: Security Audit Execution

1. Run `tools/policy_check.sh` - automated checks
2. Review each section above systematically
3. Mark status: ✅ Pass, ⚠️ Warning, ❌ Fail
4. Document findings in audit record
5. Create issues for any failures
6. Re-audit after remediation

---

## 9. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|
| 2026-01-04 | Claude Opus 4.5 | **PASS** - All sections passed. 1 low-severity finding (semantic.py input handling). Some outdated dependencies (non-critical). | None (findings below threshold) |

### 2026-01-04 Audit Details

**Tools Used:**
- `tools/policy_check.sh` - All 6 policies passed
- `npm audit` - 0 vulnerabilities
- `poetry show --outdated` - boto3, certifi, pillow, pytest outdated (no CVEs)
- `grep` for eval(), innerHTML, remote code patterns

**Findings:**

| ID | Severity | Category | Finding | Status |
|----|----------|----------|---------|--------|
| F1 | ⚠️ Low | LLM01 | `semantic.py:60` sends user text without XML wrapping | ✅ FIXED |
| F2 | ℹ️ Info | Supply Chain | boto3 1.41.2 → 1.42.21 available | Open |
| F3 | ℹ️ Info | Supply Chain | certifi 2025.11.12 → 2026.1.4 available | Open |

**Notes:**
- F1 FIXED (2026-01-04): Added `<user_text>` XML wrapping in `semantic.py:60`
- F2/F3: No action required (no CVEs, patch releases only)

---

## 10. References

### OWASP
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/) (Updated Jan 2026)
- [OWASP Top 10:2021](https://owasp.org/Top10/2021/) (Historical reference)
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)

### Browser Extension
- [Chrome Extension Security](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security)
- [Manifest V3 CSP](https://developer.chrome.com/docs/extensions/reference/manifest/content-security-policy)

### NIST
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST Cyber AI Profile (Draft)](https://csrc.nist.gov/News/2025/nist-releases-prelim-draft-cyber-ai-profile)

### ISC2
- [CISSP-Inspired AI Security](https://www.isc2.org/Insights/2025/12/A-CISSP-Inspired-AI-Security-Approach)

### IEEE
- [IEEE 7001-2021 Transparency of Autonomous Systems](https://standards.ieee.org/ieee/7001/6929/)
- [IEEE 7007-2021 Ontological Standard for Ethically Driven Robotics and Automation Systems](https://standards.ieee.org/ieee/7007/6926/)

### Internal
- ADR 0201 - Privacy-First Extension Permissions
- ADR 0204 - Defense Funnel
- docs/0012-devops-architecture.md §2.4 - Policy Compliance
