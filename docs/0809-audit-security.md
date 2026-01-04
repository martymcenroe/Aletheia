# 0809 - Audit: Security

## 1. Purpose

Comprehensive security audit covering web application, LLM, agentic AI, and browser extension security concerns. Based on industry frameworks including OWASP, NIST, and ISC2 best practices.

**Aletheia Context:**
- Browser extension (Chrome MV3 / Firefox MV2)
- AWS Lambda backend (Python)
- AWS Bedrock Claude LLM integration
- Processes user-selected text from web pages

---

## 2. OWASP Top 10 (2021) - Web Application Security

### Checklist

| Risk | Aletheia Applicability | Check | Status |
|------|------------------------|-------|--------|
| **A01: Broken Access Control** | Lambda API endpoints | API Gateway auth, CORS headers properly configured | |
| **A02: Cryptographic Failures** | Data in transit | HTTPS only, TLS 1.2+, no sensitive data in localStorage | |
| **A03: Injection** | User input to Lambda | Input validation, parameterized queries, no eval() | |
| **A04: Insecure Design** | Architecture | Threat modeling done, security requirements documented | |
| **A05: Security Misconfiguration** | AWS, extension | Least privilege IAM, CSP headers, no debug in prod | |
| **A06: Vulnerable Components** | Dependencies | poetry.lock pinned, npm audit clean, Dependabot enabled | |
| **A07: Auth Failures** | N/A (no user accounts) | Not applicable - stateless design | |
| **A08: Data Integrity Failures** | Extension updates | Chrome Web Store signed, no remote code execution | |
| **A09: Logging Failures** | Lambda | CloudWatch logging enabled, no PII in logs | |
| **A10: SSRF** | Lambda fetch operations | URL validation, no user-controlled URLs passed to fetch | |

### Aletheia-Specific Checks

| Check | Requirement | Status |
|-------|-------------|--------|
| No `<all_urls>` permission | ADR 0201 - Privacy First | |
| CSP in manifest.json | script-src 'self' only | |
| No remote code execution | All code bundled in extension | |
| No eval() or new Function() | MV3 requirement | |
| Service worker event-driven | No persistent background | |

---

## 3. OWASP Top 10 for LLM Applications (2025)

### Checklist

| Risk | Aletheia Applicability | Mitigation | Status |
|------|------------------------|------------|--------|
| **LLM01: Prompt Injection** | User-selected text sent to Claude | System prompt isolation, output validation | |
| **LLM02: Sensitive Info Disclosure** | Claude responses | No PII in prompts, response filtering | |
| **LLM03: Supply Chain** | Bedrock/Claude dependency | AWS-managed, version pinning | |
| **LLM04: Data Poisoning** | N/A (no fine-tuning) | Not applicable | |
| **LLM05: Improper Output Handling** | Rendering Claude output | XSS prevention, HTML sanitization | |
| **LLM06: Excessive Agency** | Claude actions | Read-only (analysis only), no tool use | |
| **LLM07: System Prompt Leakage** | System prompt exposure | Prompt hardening, no reflection | |
| **LLM08: Vector/Embedding Weaknesses** | N/A (no RAG) | Not applicable | |
| **LLM09: Misinformation** | Claude accuracy | Bias warnings in UI, user education | |
| **LLM10: Unbounded Consumption** | Bedrock costs | Request throttling, cost monitoring | |

### Aletheia-Specific Checks

| Check | Requirement | Status |
|-------|-------------|--------|
| System prompt not user-modifiable | Hardcoded in Lambda | |
| Output sanitized before display | HTML entities escaped | |
| Rate limiting implemented | DynamoDB-based throttle | |
| Cost guardrails | Lambda concurrency limits | |

---

## 4. OWASP Top 10 for Agentic Applications (2026)

### Checklist

| Risk | Aletheia Applicability | Mitigation | Status |
|------|------------------------|------------|--------|
| **AA01: Agent Goal Hijacking** | Low risk (single-purpose) | Fixed purpose, no goal modification | |
| **AA02: Rogue Agents** | N/A (no agent persistence) | Stateless Lambda | |
| **AA03: Memory Poisoning** | N/A (no memory) | No conversation history | |
| **AA04: Insecure Inter-Agent Comms** | N/A (single agent) | Not applicable | |
| **AA05: Tool Misuse** | N/A (no tools) | Read-only analysis | |
| **AA06: Excessive Autonomy** | Low (user-initiated) | Requires user context menu click | |
| **AA07: Trust Boundary Violations** | Extension ↔ Lambda | Signed requests, API key | |
| **AA08: Cascading Hallucinations** | N/A (single step) | Not applicable | |
| **AA09: Agent Impersonation** | N/A (no multi-agent) | Not applicable | |
| **AA10: Persistence Mechanisms** | N/A (stateless) | Lambda + DynamoDB TTL | |

### Least Agency Principle

| Check | Requirement | Status |
|-------|-------------|--------|
| User initiates all actions | Context menu click required | |
| No proactive monitoring | On-demand only (ADR 0201) | |
| No autonomous decisions | Analysis only, no actions | |
| Bounded output | Character limits on response | |

---

## 5. Browser Extension Security (Manifest V3)

### Chrome Extension Checks

| Check | Requirement | Status |
|-------|-------------|--------|
| Minimal permissions | Only activeTab, contextMenus, storage | |
| No host_permissions | Empty array (ADR 0201) | |
| No `<all_urls>` | PROHIBITED by ADR 0201 | |
| CSP enforced | script-src 'self' only | |
| No remote code | All JS bundled | |
| No eval() | MV3 prohibited | |
| Service worker scoped | event-driven, not persistent | |
| web_accessible_resources limited | Only what's needed | |

### Firefox Extension Checks

| Check | Requirement | Status |
|-------|-------------|--------|
| Same permission minimalism | Match Chrome restrictions | |
| MV2 → MV3 migration path | Documented | |
| No browser_specific_settings abuse | Minimal gecko config | |

### Supply Chain

| Check | Requirement | Status |
|-------|-------------|--------|
| Dependencies audited | npm audit, Snyk | |
| Lock files committed | package-lock.json | |
| No CDN dependencies | All local | |
| Quarterly dependency review | Calendar reminder | |

---

## 6. AWS Security

### Lambda Security

| Check | Requirement | Status |
|-------|-------------|--------|
| IAM least privilege | Only DynamoDB + Bedrock | |
| No hardcoded secrets | Environment variables only | |
| VPC isolation | N/A (public Lambda) | |
| Concurrency limits | Cost control | |
| Function URL auth | AWS_IAM or API Gateway | |

### Bedrock Security

| Check | Requirement | Status |
|-------|-------------|--------|
| Model access scoped | Only claude-3-haiku | |
| Guardrails enabled | Content filtering | |
| No PII in prompts | User-selected text only | |
| Response logging | CloudWatch (no PII) | |

### DynamoDB Security

| Check | Requirement | Status |
|-------|-------------|--------|
| Encryption at rest | AWS default | |
| No PII stored | Only state/rate data | |
| TTL enabled | Auto-cleanup | |
| IAM scoped | Lambda role only | |

---

## 7. NIST AI RMF Alignment

### MAP Function (Context)

| Requirement | Aletheia Implementation | Status |
|-------------|------------------------|--------|
| AI system documented | Architecture docs | |
| Intended use defined | Bias/slur detection | |
| Stakeholders identified | End users, web publishers | |

### MEASURE Function (Assessment)

| Requirement | Aletheia Implementation | Status |
|-------------|------------------------|--------|
| Accuracy measured | Test suite for known biases | |
| Bias evaluated | Denylist coverage | |
| Security tested | Penetration testing | |

### MANAGE Function (Controls)

| Requirement | Aletheia Implementation | Status |
|-------------|------------------------|--------|
| Incident response plan | Documented | |
| Monitoring active | CloudWatch | |
| Human oversight | User reviews output | |

### GOVERN Function (Oversight)

| Requirement | Aletheia Implementation | Status |
|-------------|------------------------|--------|
| Policies documented | ADRs, this audit | |
| Roles defined | Orchestrator protocol | |
| Continuous improvement | Lessons learned log | |

---

## 8. Audit Procedure

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
| | | | |

---

## 10. References

### OWASP
- [OWASP Top 10:2021](https://owasp.org/Top10/2021/)
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

### Internal
- ADR 0201 - Privacy-First Extension Permissions
- ADR 0204 - Defense Funnel
- docs/0012-devops-architecture.md §2.4 - Policy Compliance
