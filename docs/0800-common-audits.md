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

## Audit Taxonomy

| Code | Name | Frequency | Trigger |
|------|------|-----------|---------|
| **0801** | Architecture Audit | Monthly / Major changes | After significant refactoring |
| **0802** | Reports Completeness | Weekly / On close | After any issue closure |
| **0803** | Open Issues Currency | Bi-weekly | Before sprint planning |
| **0804** | Terminology Consistency | After renaming | When layer/component names change |
| **0805** | File Inventory Drift | Weekly | Part of 0011 cleanup |
| **0806** | LLD-to-Code Alignment | Per feature | Before closing implementation issues |

## Audit Procedures

### 0801 - Architecture Audit ("Drift Detector")
**File:** `docs/0801-architecture-audit.md`
**Purpose:** Detect drift between documentation (0001, ADRs) and actual codebase.
**Trigger:** Monthly, or after major refactoring (new layers, removed components).
**Output:** List of discrepancies with remediation actions.

### 0802 - Reports Completeness Audit
**File:** `docs/0802-reports-completeness-audit.md`
**Purpose:** Ensure all closed issues have required reports.
**Trigger:** Weekly, or before session closeout.
**Output:** List of issues missing reports.

### 0803 - Open Issues Currency Audit
**File:** `docs/0803-open-issues-audit.md`
**Purpose:** Identify issues that are actually complete, deprecated, or stale.
**Trigger:** Bi-weekly, or before sprint planning.
**Output:** Issues to close, deprecate, or update.

### 0804 - Terminology Consistency Audit
**File:** `docs/0804-terminology-audit.md`
**Purpose:** Ensure consistent naming across all docs and code after terminology changes.
**Trigger:** After any layer/component renaming (e.g., L1/L2/L3 → Selection/Denylist/Semantic).
**Output:** Files with stale terminology.

### 0805 - File Inventory Drift Audit
**File:** `docs/0805-inventory-audit.md`
**Purpose:** Detect files not in inventory, or inventory entries for deleted files.
**Trigger:** Weekly (part of 0011 §5.2).
**Output:** Inventory corrections.

### 0806 - LLD-to-Code Alignment Audit
**File:** `docs/0806-lld-code-audit.md`
**Purpose:** Verify implementation matches LLD, or deviations are documented.
**Trigger:** Before closing any implementation issue.
**Output:** LLD updates or Implementation Report deviations.

## Integration Points

| Protocol | Audits Referenced |
|----------|-------------------|
| **0004 §8.6** | 0802 (Reports Completeness) |
| **0009** | 0802, 0805 (Session Closeout) |
| **0011 §5.2** | 0805 (Inventory) |
| **0110** | Superseded by 0801 |

## Audit Execution

Audits can be run by:
- **Agents:** As part of session work when triggered
- **Orchestrator:** Periodic scheduled runs
- **Gemini (Architect):** Strategic audits before major milestones

## Quick Reference Commands

```bash
# 0802: Find closed issues missing reports
for issue in $(gh issue list --state closed --limit 50 --json number -q '.[].number'); do
  if [ ! -d "docs/reports/$issue" ]; then
    echo "Missing reports: #$issue"
  fi
done

# 0805: Find files not in inventory
find src tests tools -name "*.py" | while read f; do
  grep -q "$f" docs/0003-file-inventory.md || echo "Not in inventory: $f"
done
```

## History

| Date | Change |
|------|--------|
| 2026-01-01 | Created. Moved 0110 → 0801. Added 0802-0806. |
