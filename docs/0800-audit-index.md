# 0800 - Audit Index

## 1. Purpose

Master index of all AgentOS audits. Provides navigation, categorization, and quick reference for the audit suite.

---

## 2. Audit Philosophy

> "Don't trust metadata—verify reality."

Audits exist because:
1. **Docs drift from code** - Architecture changes, docs don't update
2. **Issues drift from reality** - Issues marked open are actually complete (or vice versa)
3. **Process steps get skipped** - Reports not created, inventory not updated
4. **Terminology evolves** - Old names persist in forgotten corners
5. **The system itself decays** - Cross-references break, templates diverge

### 2.1 Evidence over Inference (CRITICAL)

**Do not assume compliance based on file names or documentation claims. Grep the code/config for the specific setting.**

| Bad Practice | Good Practice |
|--------------|---------------|
| "0810 says in-memory only" | `grep put_item src/lambda_function.py` |
| "CLAUDE.md says eval is forbidden" | `grep eval .claude/settings.local.json` |
| "Package says MIT license" | Compare LICENSE, package.json, pyproject.toml |

**The code is the truth. The docs are a claim about the truth.**

---

## 3. Audit Suite Overview

### 3.1 At a Glance

| Category | Count | Focus |
|----------|-------|-------|
| Core Development | 11 | Code quality, security, privacy, accessibility |
| AI Governance | 6 | AI-specific controls and compliance |
| Meta | 2 | Audit system governance |
| **Total** | **19** | |

### 3.2 Quick Reference

| Audit | One-Line Description |
|-------|----------------------|
| 0808 | Agent permission policy (deny dangerous commands) |
| 0824 | Permission friction analysis (find missing allows) |
| 0809 | Security (OWASP, ASVS, prompt injection) |
| 0810 | Privacy (GDPR-aware, data handling) |
| 0811 | Accessibility |
| 0812 | Performance |
| 0813 | Code Quality |
| 0814 | License Compliance |
| 0817 | Wiki Alignment |
| 0815 | Claude Code workflow compliance |
| 0816 | Dependabot PR management |
| 0818 | AI Management System (ISO 42001) |
| 0819 | AI Supply Chain (OWASP LLM03, AIBOM) |
| 0820 | Explainability (XAI) |
| 0821 | Agentic AI Governance (OWASP Agentic) |
| 0822 | Bias & Fairness |
| 0823 | AI Incident Post-Mortem |
| 0898 | Horizon Scanning Protocol |
| 0899 | Meta-Audit (validation & execution) |

---

## 4. Audit Categories

### 4.1 Core Development Audits

Audits for code quality, security, and development practices.

| Number | Name | Frequency | Automation |
|--------|------|-----------|------------|
| 0808 | Permission Permissiveness | On friction | Manual |
| 0824 | Permission Friction | On friction | Manual (/friction) |
| 0809 | Security | Quarterly | Manual |
| 0810 | Privacy | Quarterly | Manual |
| 0811 | Accessibility | As needed | Manual |
| 0812 | Performance | Quarterly | Manual |
| 0813 | Code Quality | Per PR | CI |
| 0814 | License Compliance | Quarterly | Manual |
| 0817 | Wiki Alignment | On user-facing changes | Manual |
| 0815 | Claude Code Workflow | Monthly | Manual |
| 0816 | Dependabot PRs | Weekly | Semi-auto |

### 4.2 AI Governance Audits

Audits specific to AI system governance, compliance, and responsible AI.

| Number | Name | Frequency | Framework |
|--------|------|-----------|-----------|
| 0818 | AI Management System | Quarterly | ISO/IEC 42001:2023 |
| 0819 | AI Supply Chain | Quarterly | OWASP LLM03:2025, SPDX 3.0 |
| 0820 | Explainability | Quarterly | XAI, EU AI Act Art. 13 |
| 0821 | Agentic AI Governance | Monthly | OWASP Agentic 2026 |
| 0822 | Bias & Fairness | Quarterly | ISO 24027, NIST |
| 0823 | AI Incident Post-Mortem | On incident | NIST AI RMF |

### 4.3 Meta Audits

Audits that govern the audit system itself.

| Number | Name | Frequency | Purpose |
|--------|------|-----------|---------|
| 0898 | Horizon Scanning Protocol | Quarterly | Discover missing audits |
| 0899 | Meta-Audit | Quarterly | Validate audit execution |

---

## 5. Frequency Matrix

### 5.1 By Frequency

| Frequency | Audits |
|-----------|--------|
| **Per PR** | 0813 |
| **As needed** | 0811, 0817 |
| **Weekly** | 0816 |
| **Monthly** | 0815, 0821 |
| **Quarterly** | 0809, 0810, 0812, 0814, 0818, 0819, 0820, 0822, 0898, 0899 |
| **On Event** | 0808 (policy), 0824 (friction analysis), 0823 (incident) |

### 5.2 Calendar View

| Month | Week 1 | Week 2 | Week 3 | Week 4 |
|-------|--------|--------|--------|--------|
| **Jan** | 0816, 0815 | 0816 | 0816, 0809, 0810 | 0816, 0898, 0899 |
| **Feb** | 0816, 0815, 0821 | 0816 | 0816 | 0816 |
| **Mar** | 0816, 0815 | 0816, 0821 | 0816 | 0816, 0818, 0819, 0820, 0822 |
| **Apr** | 0816, 0815 | 0816 | 0816, 0821, 0809, 0810 | 0816, 0898, 0899 |
| ... | | | | |

---

## 6. Standards Coverage Map

### 6.1 By Standard

| Standard | Primary Audit | Supporting Audits |
|----------|---------------|-------------------|
| **OWASP LLM Top 10 (2025)** | 0809 | 0819, 0821 |
| **OWASP Agentic Top 10 (2026)** | 0821 | 0808, 0815 |
| **ISO/IEC 42001:2023** | 0818 | 0809, 0810, 0822 |
| **EU AI Act** | 0820 | 0809, 0810, 0818 |
| **NIST AI RMF** | 0818 | 0823 |
| **ASVS 4.0.3** | 0809 §4 | |
| **CWE Top 25** | 0809 §2 | |
| **SPDX 3.0 AI Profile** | 0819 | |

### 6.2 Coverage Gaps

See **0898 Horizon Scanning Protocol** for ongoing gap discovery.

---

## 7. Audit Dependencies

### 7.1 Dependency Graph

```
0899 Meta-Audit
  └── validates all 08xx audits

0898 Horizon Scanning
  └── discovers gaps for all 08xx

0821 Agentic AI Governance
  ├── depends on: 0808, 0815
  └── informs: 0823

0819 AI Supply Chain
  └── depends on: 0816

0809 Security
  └── informs: 0821, 0823

0823 AI Incident Post-Mortem
  └── triggers: 0809, 0821, 0822 (as needed)
```

### 7.2 Run Order (when running multiple)

1. Code quality audit first (0813)
2. Dependency audit (0816)
3. Security/Privacy (0809, 0810)
4. AI Governance (0818-0822)
5. Agent audits (0808, 0815, 0821)
6. Meta audits last (0898, 0899)

---

## 8. Audit Ownership

### 8.1 By Role

| Role | Audits Owned |
|------|--------------|
| **Developer** | All (solo project) |
| **CI/CD** | 0813 |
| **Dependabot** | 0816 (triggers) |

### 8.2 Accountability

| Audit | Accountable | Responsible | Consulted |
|-------|-------------|-------------|-----------|
| 0809 Security | Developer | Developer | - |
| 0821 Agentic | Developer | Claude Code | Developer |
| 0823 Incident | Developer | Developer | - |

---

## 9. Quick Links

### 9.1 By Number

- [0808 - Permission Permissiveness](0808-audit-permission-permissiveness.md)
- [0824 - Permission Friction](0824-audit-permission-friction.md)
- [0809 - Security](0809-audit-security.md)
- [0810 - Privacy](0810-audit-privacy.md)
- [0811 - Accessibility](0811-audit-accessibility.md)
- [0812 - Performance](0812-audit-performance.md)
- [0813 - Code Quality](0813-audit-code-quality.md)
- [0814 - License Compliance](0814-audit-license-compliance.md)
- [0817 - Wiki Alignment](0817-audit-wiki-alignment.md)
- [0815 - Claude Code Capabilities](0815-audit-claude-capabilities.md)
- [0816 - Dependabot PRs](0816-audit-dependabot-prs.md)
- [0818 - AI Management System](0818-audit-ai-management-system.md)
- [0819 - AI Supply Chain](0819-audit-ai-supply-chain.md)
- [0820 - Explainability](0820-audit-explainability.md)
- [0821 - Agentic AI Governance](0821-audit-agentic-ai-governance.md)
- [0822 - Bias & Fairness](0822-audit-bias-fairness.md)
- [0823 - AI Incident Post-Mortem](0823-audit-ai-incident-post-mortem.md)
- [0898 - Horizon Scanning Protocol](0898-horizon-scanning-protocol.md)
- [0899 - Meta-Audit](0899-meta-audit.md)

### 9.2 By Topic

| Topic | Relevant Audits |
|-------|-----------------|
| Agent behavior | 0808, 0824, 0815, 0821 |
| AI safety | 0809, 0818, 0821, 0822 |
| Accessibility | 0811 |
| Code quality | 0813 |
| Performance | 0812 |
| License | 0814 |
| Wiki/Docs | 0817 |
| Compliance | 0818, 0820, 0898 |
| Dependencies | 0816, 0819 |
| Incidents | 0823 |
| Privacy | 0810 |
| Security | 0809, 0819 |

---

## 10. Getting Started

### 10.1 For New Contributors

1. Read this index to understand the audit landscape
2. Review 0815 for Claude Code workflow rules
3. Code quality audit (0813) runs automatically on PRs
4. Security (0809) and Privacy (0810) are the most comprehensive

### 10.2 For Audit Execution

1. Check 0899 for audit schedule and status
2. Run audit per its documented procedure
3. Record findings in audit's Audit Record section
4. Create GitHub issues for failures
5. Update 0899 with execution date

### 10.3 For Gap Discovery

1. Review 0898 Horizon Scanning Protocol
2. Check Framework Registry for updates
3. Triage new frameworks per 0898 §4
4. Propose new audits if gaps found

---

## 11. History

| Date | Change |
|------|--------|
| 2026-01-08 | Index consistency audit. Fixed broken links (0811-0814, 0815, 0817). Corrected audit names/descriptions to match actual files. Added 0817 Wiki Alignment. Total audits: 19. |
| 2026-01-06 | Major update. Added AI Governance audits (0818-0823), split meta-audit into 0898 (horizon scanning) and 0899 (validation). Merged 0800-common-audits.md into this file (preserved Audit Philosophy section). Total audits: 17. |
