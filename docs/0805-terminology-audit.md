# 0805 - Terminology Consistency Audit

## Purpose

Ensure consistent naming across all documentation and code after terminology changes. Stale terminology causes confusion and indicates docs-code drift.

## Trigger

- After any layer/component renaming
- After architectural pivots
- When onboarding reveals confusion

## Known Terminology Changes

| Old Term | New Term | Changed | Reason |
|----------|----------|---------|--------|
| L1, L2, L3, L4 | Selection Check, Denylist, Semantic, Transform | 2025-12-30 | Functional names over numbers |
| Compliance Layer | Transform Layer | 2025-12-30 | Better describes function |
| LangGraph | Naked Python | 2025-12-31 | ADR 0211 |
| LangChain | boto3 | 2025-12-31 | Direct AWS SDK |
| RSDB | Wikipedia | 2026-01-01 | Issue #121 |
| `lambda_function.py` | `src/lambda_function.py` | 2026-01-01 | Repo restructure |

## Procedure

### Step 1: Define Search Patterns

For each old term, create a grep pattern:

```bash
# Layer naming
OLD_LAYERS="L1|L2|L3|L4|layer 1|layer 2|layer 3|layer 4"

# Architecture
OLD_ARCH="LangGraph|LangChain|LangSmith"

# Data sources
OLD_DATA="RSDB|rsdb|Racial Slur"

# File paths
OLD_PATHS="lambda_function\.py[^/]"  # Not followed by slash (old root location)
```

### Step 2: Search Documentation

```bash
# Search docs for old terminology
grep -rni "L1\|L2\|L3\|L4" docs/ --include="*.md" | grep -v "legacy/"
grep -rni "LangGraph\|LangChain" docs/ --include="*.md" | grep -v "legacy/" | grep -v "0205"
grep -rni "RSDB" docs/ --include="*.md" | grep -v "legacy/"
```

### Step 3: Search Code

```bash
# Search code for old terminology (in comments/strings)
grep -rni "L1\|L2\|L3\|L4" src/ tests/ tools/ --include="*.py"
grep -rni "RSDB" src/ tests/ tools/ --include="*.py"
```

### Step 4: Search GitHub Issues

```bash
# Export issues and search locally
gh issue list --state all --limit 200 --json number,title,body > temp-all-issues.json
grep -i "RSDB\|LangGraph\|L1\|L2\|L3\|L4" temp-all-issues.json
```

### Step 5: Remediation

| Location | Action |
|----------|--------|
| Active docs | Edit directly, commit |
| Legacy docs | Leave as-is (historical) |
| Code comments | Update if touched, note if not |
| GitHub issues (open) | `gh issue edit --body` |
| GitHub issues (closed) | Leave as-is (historical) |

## Exclusions

Files that should retain old terminology:
- `docs/legacy/*.md` - Historical record
- `docs/02xx-ADR-*.md` - ADRs document decisions AT TIME MADE
- Session logs - Historical record
- Closed issues - Historical record

## Output Format

```markdown
## Terminology Consistency Audit - {DATE}

### Search Terms
- Old layers: L1, L2, L3, L4
- Old arch: LangGraph, LangChain
- Old data: RSDB

### Findings

#### Documentation (Non-Legacy)
| File | Line | Content | Action |
|------|------|---------|--------|
| docs/1045.md | 23 | "L2 filter" | Updated to "Denylist" |

#### Code
| File | Line | Content | Action |
|------|------|---------|--------|
| (none) | - | - | - |

#### Open Issues
| Issue | Content | Action |
|-------|---------|--------|
| #126 | "denylist.json" | Added "Wikipedia-sourced" |
```

## Integration

- Run after Issue #109 type changes (layer renaming)
- Run after any ADR that deprecates prior approach
