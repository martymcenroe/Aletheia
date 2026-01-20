# Implementation Report: #249 + #253 - Audit Record Pre-commit Hooks

## Summary

Added pre-commit hook to enforce audit record compliance policies from 0800-audit-index.md Section 8:
- **#249**: Auditor identity requirements (no empty/TBD/generic entries)
- **#253**: FAIL findings must have GitHub issue references

## Changes

### Files Created

| File | Purpose |
|------|---------|
| `tools/audit_record_check.py` | Python script to parse and validate audit records |

### Files Modified

| File | Change |
|------|--------|
| `.pre-commit-config.yaml` | Added `audit-record-check` hook |

## Implementation Details

### Audit Record Parser

The script parses markdown tables in the "Audit Record" section of 08xx audit files:

```python
def parse_audit_record_table(content: str) -> list[dict]:
    """Extract entries from: | Date | Auditor | Findings | Issues |"""
```

### Validation Rules

**Section 8.1 - Auditor Identity:**
```python
FORBIDDEN_AUDITORS = {"", "tbd", "todo", "agent", "-", "n/a"}
```

**Section 8.3 - FAIL → Issue:**
- If findings contain "FAIL", issues column must contain "#NNN" reference
- Forbidden: "none", "-", "", "n/a" when FAIL present

### Pre-commit Hook

```yaml
- id: audit-record-check
  name: Audit Record Compliance
  entry: python tools/audit_record_check.py
  files: ^docs/08.*-audit-.*\.md$
```

Only runs when audit files are modified (performance optimization).

## Policy Cross-Reference

| Requirement | Source | Enforced |
|-------------|--------|----------|
| No empty auditor | 0800 §8.1 | Yes |
| No "TBD" auditor | 0800 §8.2 | Yes |
| No "Agent" (generic) | 0800 §8.2 | Yes |
| FAIL needs issue | 0800 §8.3 | Yes |
