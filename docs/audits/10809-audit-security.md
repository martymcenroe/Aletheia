# 0809 - Audit: Application Security

**Split per ADR 0213 - Adversarial Audit Philosophy**
AI-specific security moved to 0825-audit-ai-safety.md

## 1. Purpose

Application security audit covering web application, browser extension, and AWS infrastructure security. Based on industry frameworks including OWASP, NIST, and ISC2 best practices.

**Scope:** Infrastructure and application security (NOT AI safety - see 0825)

**Aletheia Context:**
- Browser extension (Chrome MV3 / Firefox MV3)
- AWS Lambda backend (Python)
- AWS CloudFront + WAF
- DynamoDB persistence

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

The 2025 framework expands A06 "Vulnerable Components" into broader supply chain concerns.

> **Executive Order 14028 (May 2021):** "Improving the Nation's Cybersecurity" requires SBOM (Software Bill of Materials) for federal software supply chain transparency. While Aletheia is not federal software, we adopt these practices proactively.

#### Dependency Scanning

| Ecosystem | Command | Frequency | Current Status |
|-----------|---------|-----------|----------------|
| npm | `npm audit` | Every audit | 0 vulnerabilities |
| Python | `pip-audit` or manual review | Quarterly | poetry.lock pinned |
| Dependabot | GitHub alerts | Continuous | 0 open alerts |

#### Supply Chain Checklist

| Check | Requirement | Status |
|-------|-------------|--------|
| **npm audit** | 0 high/critical vulnerabilities | ✅ Pass |
| Dependency pinning | poetry.lock, package-lock.json committed | ✅ Pass |
| Dependency scanning | Dependabot configured, 0 open alerts | ✅ Pass |
| AI model provenance | Bedrock Claude (AWS-managed, Anthropic source) | ✅ Pass |
| No CDN dependencies | All assets bundled locally | ✅ Pass |
| Build integrity | No untrusted build plugins | ✅ Pass |
| Denylist source | Wikipedia via trusted GitHub Gist (#121) | ✅ Pass |

Cross-reference: See 0819 AI Supply Chain Audit for AIBOM (AI Bill of Materials) details.

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

## 3. Browser Extension Security (Manifest V3)

> **AI Safety:** LLM and Agentic security moved to [0825-audit-ai-safety.md](0825-audit-ai-safety.md)

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

## 4. AWS Security

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

## 5. Claude Code Agent Permissions (CRITICAL)

> **NIST AI RMF:** See [0825-audit-ai-safety.md](0825-audit-ai-safety.md) for AI governance alignment

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

## 6. Audit Procedure

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

## 7. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|
| 2026-01-04 | Claude Opus 4.5 | **PASS** - All sections passed. 1 low-severity finding (semantic.py input handling). Some outdated dependencies (non-critical). | None (findings below threshold) |
| 2026-01-06 | Claude Opus 4.5 | **PASS** - Tier 1 Store Compliance audit. All policy checks pass. 0 npm vulnerabilities. 0 Dependabot alerts. Forbidden patterns in deny list. innerHTML safe (static templates only). | None |

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

## 8. References

### OWASP
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/) (Updated Jan 2026)
- [OWASP Top 10:2021](https://owasp.org/Top10/2021/) (Historical reference)

> **AI Security:** See [0825-audit-ai-safety.md](0825-audit-ai-safety.md) for LLM and Agentic OWASP Top 10

### Browser Extension
- [Chrome Extension Security](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security)
- [Manifest V3 CSP](https://developer.chrome.com/docs/extensions/reference/manifest/content-security-policy)

### Internal
- [0825-audit-ai-safety.md](0825-audit-ai-safety.md) - AI Safety audit (LLM, Agentic, NIST AI RMF)
- ADR 0201 - Privacy-First Extension Permissions
- ADR 0204 - Defense Funnel
- ADR 0213 - Adversarial Audit Philosophy
- docs/0012-devops-architecture.md §2.4 - Policy Compliance
