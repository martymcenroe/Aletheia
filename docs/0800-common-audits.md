# 0800 - Common Audits Index

## Purpose

This document indexes all audit procedures used to maintain system health, detect drift, and ensure process compliance. Audits are proactive verification activities that catch problems before they become incidents.

## Audit Philosophy

> "Don't trust metadata—verify reality."

Audits exist because:
1. **Docs drift from code** - Architecture changes, docs don't update
2. **Issues drift from reality** - Issues marked open are actually complete (or vice versa)
3. **Process steps get skipped** - Reports not created, inventory not updated
4. **Terminology evolves** - Old names persist in forgotten corners
5. **The system itself decays** - Cross-references break, templates diverge

## How to Run All Audits

Prompt: **"Run all audits"** or **"Execute 08xx audit suite"**

Audits are numbered in recommended execution order. Run sequentially for best results.

## Audit Taxonomy (Execution Order)

| Code | Name | Frequency | Trigger |
|------|------|-----------|---------|
| **0801** | Open Issues Currency | Bi-weekly | Before sprint planning |
| **0802** | Reports Completeness | Weekly / On close | After any issue closure |
| **0803** | LLD-to-Code Alignment | Per feature | Before closing implementation issues |
| **0804** | File Inventory Drift | Weekly | Part of 0009 Full Mode cleanup |
| **0805** | Terminology Consistency | After renaming | When layer/component names change |
| **0806** | Architecture Audit | Monthly / Major changes | After significant refactoring |
| **0807** | AgentOS Health Check | Monthly | System maintenance, onboarding new agents |
| **0808** | Permission Permissiveness | On friction | When agents ask for too many approvals |
| **0809** | Security Audit | Quarterly | Before releases, after security incidents |
| **0810** | Privacy Audit | Quarterly | Before releases, regulatory changes |

## Audit Procedures

### 0801 - Open Issues Currency Audit
**File:** `docs/0801-open-issues-audit.md`
**Purpose:** Identify issues that are actually complete, deprecated, or stale.
**Trigger:** Bi-weekly, or before sprint planning.
**Output:** Issues to close, deprecate, or update.
**Run First:** Establishes ground truth of what's actually done.

### 0802 - Reports Completeness Audit
**File:** `docs/0802-reports-completeness-audit.md`
**Purpose:** Ensure all closed issues have required reports.
**Trigger:** Weekly, or before session closeout.
**Output:** List of issues missing reports.

### 0803 - LLD-to-Code Alignment Audit
**File:** `docs/0803-lld-code-audit.md`
**Purpose:** Verify implementation matches LLD, or deviations are documented.
**Trigger:** Before closing any implementation issue.
**Output:** LLD updates or Implementation Report deviations.

### 0804 - File Inventory Drift Audit
**File:** `docs/0804-inventory-audit.md`
**Purpose:** Detect files not in inventory, or inventory entries for deleted files.
**Trigger:** Weekly (part of 0009 Full Mode §F9).
**Output:** Inventory corrections.

### 0805 - Terminology Consistency Audit
**File:** `docs/0805-terminology-audit.md`
**Purpose:** Ensure consistent naming across all docs and code after terminology changes.
**Trigger:** After any layer/component renaming (e.g., L1/L2/L3 → Selection/Denylist/Semantic).
**Output:** Files with stale terminology.

### 0806 - Architecture Audit ("Drift Detector")
**File:** `docs/0806-architecture-audit.md`
**Purpose:** Detect drift between documentation (0001, ADRs) and actual codebase.
**Trigger:** Monthly, or after major refactoring (new layers, removed components).
**Output:** List of discrepancies with remediation actions.

### 0807 - AgentOS Health Check
**File:** `docs/0807-agentos-audit.md`
**Purpose:** Verify the documentation system itself is healthy and internally consistent.
**Trigger:** Monthly, or when onboarding new agents, or after major doc reorganization.
**Output:** Broken references, template drift, protocol inconsistencies.

### 0808 - Permission Permissiveness Audit
**File:** `docs/0808-audit-permission-permissiveness.md`
**Purpose:** Ensure agent permissions are maximally permissive within safety bounds.
**Trigger:** When agents frequently ask for permission, or after permission friction reports.
**Output:** Updated `.claude/settings.local.json` with expanded allow list.
**Philosophy:** If it's not destructive, the agent shouldn't need to ask.

### 0809 - Security Audit
**File:** `docs/0809-audit-security.md`
**Purpose:** Comprehensive security audit covering OWASP, LLM, Agentic, and extension security.
**Trigger:** Quarterly, before major releases, or after security incidents.
**Output:** Security findings with severity ratings and remediation actions.
**Frameworks:** OWASP Top 10 (2021, LLM 2025, Agentic 2026), NIST AI RMF, Manifest V3.

### 0810 - Privacy Audit
**File:** `docs/0810-audit-privacy.md`
**Purpose:** Comprehensive privacy audit covering data protection and AI privacy concerns.
**Trigger:** Quarterly, before major releases, or when regulatory landscape changes.
**Output:** Privacy findings with remediation recommendations.
**Frameworks:** IAPP Privacy Framework, IEEE 7000 Series, NIST Privacy Framework 1.1.

## Integration Points

| Protocol | Audits Referenced |
|----------|-------------------|
| **0004 §8.6** | 0802 (Reports Completeness) |
| **0009 Session** | 0802 (Quick Closeout) |
| **0009 Full** | 0802, 0804 (Comprehensive Cleanup) |

## Quick Reference Commands

```bash
# 0801: Find issues that might be done
gh issue list --state open --limit 50

# 0802: Find closed issues missing reports
for issue in $(gh issue list --state closed --limit 50 --json number -q '.[].number'); do
  if [ ! -d "docs/reports/$issue" ]; then
    echo "Missing reports: #$issue"
  fi
done

# 0804: Find files not in inventory
find src tests tools -name "*.py" | while read f; do
  grep -q "$f" docs/0003-file-inventory.md || echo "Not in inventory: $f"
done

# 0807: Find broken internal references
grep -r "docs/0[0-9]" docs/*.md | grep -v "0800-common-audits"
```

## History

| Date | Change |
|------|--------|
| 2026-01-04 | Added 0808 Permission Permissiveness, 0809 Security Audit, 0810 Privacy Audit. |
| 2026-01-04 | Renumbered by execution order. Added 0807 AgentOS Health Check. |
| 2026-01-01 | Created. Moved 0110 → 0801. Added 0802-0806. |
