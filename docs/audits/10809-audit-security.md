# 0809 - Audit: Application Security

**Split per ADR 0213 - Adversarial Audit Philosophy**
AI-specific security moved to 0825-audit-ai-safety.md

## 1. Purpose

Application security audit covering web application, browser extension, and AWS infrastructure security. Based on industry frameworks including OWASP, NIST, and ISC2 best practices.

**Scope:** Infrastructure and application security (NOT AI safety - see 0825)

**Aletheia Context:**
- Browser extension (Chrome MV3 / Firefox MV3)
- AWS Lambda backend (Python)
- CloudFlare Free (proxy + rate limiting + DDoS) — replaced CloudFront+WAF per ADR 10216
- CloudFlare Worker (`aletheia-api`) proxies to Lambda Function URL
- Shared secret header locks Lambda to CloudFlare-only access (Issue #351)
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
| **A01: Broken Access Control** | Lambda API endpoints | CloudFlare proxy + shared secret header + Lambda header check (ADR 10216). Rate limiting at edge. Kill switch at >100 inv/5min. | ✅ Pass |
| **A02: Security Misconfiguration** | AWS, extension | Minimal permissions, no debug endpoints | ✅ Pass |
| **A03: Software Supply Chain Failures** | Dependencies + models | npm audit: 10 dev-only vulns (ajv, minimatch — not shipped), poetry.lock pinned, Bedrock managed. **Admin dashboard loads Chart.js from CDN (C-1)** | ⚠️ Warning |
| **A04: Cryptographic Failures** | Data in transit | HTTPS only via CloudFlare (SSL Full mode) | ✅ Pass |
| **A05: Injection** | User input to Lambda | Input validation (20k limit), no eval() | ✅ Pass |
| **A06: Insecure Design** | Architecture | ADRs document security decisions | ✅ Pass |
| **A07: Auth Failures** | LinkedIn + GitHub OAuth | CSRF protection (HMAC-signed state tokens). Admin JWT in localStorage (H-1). AUTH_ENABLED=false in production (H-5) | ⚠️ Warning |
| **A08: Data Integrity Failures** | Extension updates | No remote code in extension JS. **Admin dashboard CDN script (C-1)** | ⚠️ Warning |
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
| No CDN dependencies | Extension: all local. **Admin dashboard: Chart.js from jsdelivr CDN (C-1)** | ⚠️ Warning |
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

> **AI Safety:** LLM and Agentic security moved to [AgentOS:audits/0808-ai-safety-audit](AgentOS:audits/0808-ai-safety-audit)

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
| Dependencies audited | npm audit: 10 dev-only vulns (ajv ReDoS, minimatch ReDoS — not in shipped code) | ⚠️ Note |
| Lock files committed | package-lock.json, poetry.lock | ✅ Pass |
| No CDN dependencies | Extension code: all local. Admin dashboard: CDN (C-1) | ⚠️ Warning |
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
| IAM least privilege | DynamoDB, Bedrock, CloudWatch, Secrets Manager. **Bedrock Resource: "*" (H-3), DynamoDB wildcard region (H-4)** | ⚠️ Warning |
| No hardcoded secrets | Environment variables, policy_check.sh verified | ✅ Pass |
| VPC isolation | N/A (public Lambda via CloudFront) | ✅ N/A |
| Concurrency limits | Configurable via lambda-on/off scripts | ✅ Pass |
| Function URL auth | CloudFlare Worker + origin secret (replaced CloudFront+WAF). **CORS AllowOrigins=['*'] (H-2)** | ⚠️ Warning |

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

> **NIST AI RMF:** See [AgentOS:audits/0808-ai-safety-audit](AgentOS:audits/0808-ai-safety-audit) for AI governance alignment

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
| 2026-02-24 | Claude Opus 4.6 (Security Reviewer) | **WARNING** — 1 Critical (CDN supply chain), 5 High (localStorage JWT, CORS wildcard, IAM over-permission, auth disabled), 8 Medium, 7 Low. No active exploitation. Extension code secure. | Remediation tracked below |

### 2026-02-24 Audit Details

**Auditor:** Claude Opus 4.6 (Security Reviewer Agent, ADR 0213 Adversarial Audit Philosophy)
**Scope:** Full application — browser extensions, Lambda backend, infrastructure, OAuth flows, admin dashboard, dependencies, agent permissions
**Prerequisite:** 10816 Dependabot audit completed (2 PRs: #423 merged, #425 migrated via #435)

**Tools Used:**
- `tools/policy_check.sh` — All 6 policies passed
- `npm audit` — 10 dev-only vulnerabilities (ajv, minimatch in eslint/serve/pa11y-ci — not in shipped code)
- Dependabot alerts — 0 open
- Manual code review of all auth, extension, infrastructure, and worker code

**Findings (1 Critical, 5 High, 8 Medium, 7 Low, 4 Informational):**

| ID | Severity | Category | Finding | File(s) | Remediation |
|----|----------|----------|---------|---------|-------------|
| C-1 | 🔴 Critical | A08 Supply Chain | Admin dashboard loads Chart.js from jsdelivr CDN — supply chain risk | `static/admin/metrics.html:8` | Vendor Chart.js locally + add SRI hash |
| H-1 | 🟠 High | A07 Auth | Admin JWT stored in localStorage (vulnerable to XSS, amplified by C-1) | `static/admin/metrics.js:25,36` | Use HttpOnly cookie or sessionStorage |
| H-2 | 🟠 High | A01 Access Control | Lambda Function URLs have CORS AllowOrigins=['*'] | `provision.sh:533-558` | Restrict to known origins |
| H-3 | 🟠 High | AWS Least Privilege | Bedrock IAM uses Resource: "*" — can invoke any model | `provision.sh:322-325` | Scope to specific model ARNs |
| H-4 | 🟠 High | AWS Least Privilege | DynamoDB IAM uses wildcard region/account | `provision.sh:308-314` | Pin to `us-east-1:383687041805` |
| H-5 | 🟠 High | A07 Auth | AUTH_ENABLED=false in production — JWT auth bypassed | `provision.sh:441`, `lambda_function.py:736` | Enable when auth is stable |
| M-1 | 🟡 Medium | Attack Surface | python-jose installed in Lambda layer but unused (has CVEs) | `provision.sh:384` | Remove python-jose from pip install |
| M-2 | 🟡 Medium | A03 Injection | OAuth callback HTML attribute injection (mitigated by html.escape) | `lambda_auth_function.py:720` | Add code comment noting html.escape(quote=True) is required |
| M-3 | 🟡 Medium | Info Disclosure | Direct Lambda Function URLs exposed in extension source | `extensions/*/auth.js` | Route Auth through CloudFlare Worker |
| M-4 | 🟡 Medium | DoS/Cost | DynamoDB scan operations in metrics handler — expensive at scale | `metrics_handler.py:171,199,246,289` | Add GSIs for common queries |
| M-6 | 🟡 Medium | Side-Channel | Coupon code timing: different errors for expired vs exhausted reveals existence | `coupon_handler.py:162-189` | Normalize error messages |
| M-7 | 🟡 Medium | A02 Misconfig | No CSP header on Lambda HTML responses | `lambda_auth_function.py:763` | Add CSP: default-src 'none'; style-src 'unsafe-inline' |
| M-8 | 🟡 Medium | A09 Logging | LinkedIn API responses logged without sanitization (log injection risk) | `lambda_auth_function.py:131,165` | Sanitize before logging |
| L-1 | 🔵 Low | Permissions | Chrome "notifications" permission — not needed for core function | `extensions/chrome/manifest.json:14` | Document justification |
| L-4 | 🔵 Low | Config | Stripe price ID hardcoded in provision.sh | `provision.sh:35` | Move to SSM Parameter Store |
| L-5 | 🔵 Low | DoS | No input length validation on full_article content | `lambda_function.py:471-476` | Add length check in validate_input() |
| L-6 | 🔵 Low | Info Disclosure | ALETHEIA_ENV=dev in production — debug timings in responses | `provision.sh:441` | Change to prod |
| L-7 | 🔵 Low | DoS | No rate limiting on GDPR data erasure endpoint | `lambda_auth_function.py:772` | Add CloudFlare rate rule |

**Agent Permissions Audit:**

| Check | Status |
|-------|--------|
| `eval:` in deny list | ✅ Pass |
| `format:` in deny list | ✅ Pass |
| `git push --force`, `git reset --hard`, `git clean -fd` in deny | ✅ Pass |
| `pip install:` in deny list | ✅ Pass |
| `exec:` in deny list | ❌ Missing |
| `env:` in deny list | ❌ Missing |
| `printenv:` in deny list | ❌ Missing |
| `python:` NOT in allow list | ❌ In allow list (should use `poetry run python` only) |

**Positive Findings (no action needed):**
- Extension Shadow DOM uses closed mode correctly — DOM clobbering protection present
- JWT dual-secret rotation well-implemented in jwt_service.py
- Stripe webhook signature verification correct with idempotency
- Chrome/Firefox service workers validate sender.id on all messages
- GitHub OAuth: HMAC-signed CSRF state tokens, collaborator+push check, html.escape on error pages

**Prioritized Remediation (top 5):**
1. C-1: Vendor Chart.js locally (Low effort, eliminates supply chain risk)
2. H-5: Enable AUTH_ENABLED=true (Config change, activates JWT auth)
3. M-1: Remove python-jose from Lambda layer (Low effort, removes CVE exposure)
4. H-2: Restrict CORS AllowOrigins (Low effort, limits cross-origin abuse)
5. H-3/H-4: Scope Bedrock/DynamoDB IAM (Low effort, tightens least privilege)

---

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

> **AI Security:** See [0825-audit-ai-safety.md](AgentOS:audits/0808-ai-safety-audit) for LLM and Agentic OWASP Top 10

### Browser Extension
- [Chrome Extension Security](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security)
- [Manifest V3 CSP](https://developer.chrome.com/docs/extensions/reference/manifest/content-security-policy)

### Internal
- [0825-audit-ai-safety.md](AgentOS:audits/0808-ai-safety-audit) - AI Safety audit (LLM, Agentic, NIST AI RMF)
- ADR 0201 - Privacy-First Extension Permissions
- ADR 0204 - Defense Funnel
- ADR 0213 - Adversarial Audit Philosophy
- docs/0012-devops-architecture.md §2.4 - Policy Compliance
