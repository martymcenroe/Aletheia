# 0802 - Reports Completeness Audit

## Purpose

Verify all closed issues have required reports (implementation-report.md, test-report.md). Catches process violations where issues were closed without documentation.

## Trigger

- Weekly (as part of session closeout)
- Before any major milestone
- After discovering a missing report

## Procedure

### Step 1: List Recently Closed Issues

```bash
# Get issues closed in last 30 days
gh issue list --state closed --limit 100 --json number,title,closedAt \
  --jq '.[] | select(.closedAt > (now - 2592000 | todate)) | "\(.number): \(.title)"'
```

### Step 2: Check for Reports

```bash
# For each closed issue, check if reports exist
for issue in $(gh issue list --state closed --limit 50 --json number -q '.[].number'); do
  if [ ! -d "docs/reports/$issue" ]; then
    echo "MISSING: #$issue - No reports directory"
  elif [ ! -f "docs/reports/$issue/implementation-report.md" ]; then
    echo "MISSING: #$issue - No implementation report"
  elif [ ! -f "docs/reports/$issue/test-report.md" ]; then
    echo "MISSING: #$issue - No test report"
  else
    echo "OK: #$issue"
  fi
done
```

### Step 3: Check Exceptions (CRITICAL)

**Before flagging any issue, verify it's not exempt:**

```bash
# For each closed issue, check exception criteria:
gh issue view {ID} --json labels,title,body

# Check for exemptions:
# 1. Labels contain "chore" or "documentation" → EXEMPT
# 2. Title starts with "chore:" or "docs:" → EXEMPT
# 3. Implementation plan exists → EXEMPT
ls docs/lld/done/1{ID}-implementation-plan.md 2>/dev/null && echo "EXEMPT: has implementation plan"

# 4. No code changes (docs-only PR) → EXEMPT
gh pr view {PR} --json changedFiles --jq '.changedFiles | map(select(endswith(".md"))) | length == .changedFiles | length'
```

### Step 4: Auto-Fix (Default Behavior)

**This audit auto-creates missing reports rather than just flagging them.**

For each non-exempt issue missing reports:

1. Get PR context: `gh pr view {PR_NUMBER} --json body,files,additions,deletions`
2. Generate minimal implementation-report.md:
   - Summary from PR body
   - Files changed table from PR
   - Mark as "retroactive report"
3. Generate minimal test-report.md:
   - Extract test plan from PR body if present
   - Mark as "retroactive report"
4. Create `docs/reports/{ID}/` directory and files
5. Log auto-fix action to audit output

### Step 5: Manual Remediation (Fallback)

Only use manual remediation if auto-fix cannot determine:
- PR context unavailable (deleted/private)
- Complex multi-PR implementation
- LLD required but missing

Manual steps:
1. Read the LLD (`docs/lld/done/1{ISSUE_ID}-*.md`)
2. Read session logs for implementation context
3. Create reports using templates:
   - `docs/0103-TEMPLATE-implementation-report.md`
   - `docs/0113-TEMPLATE-test-report.md`
4. Commit with message: `docs: add missing reports for Issue #{ID}`

## Exceptions

| Issue Type | Reports Required? | Notes |
|------------|-------------------|-------|
| Feature implementation | Yes | Both reports required |
| Bug fix | Yes | Both reports required |
| Implementation plan (process/config) | No | Plan is self-contained (see `0105-TEMPLATE-implementation-plan.md`) |
| Documentation only | No | No code = no test report |
| Chore (deps, formatting) | No | Minor changes exempt |
| Superseded/Deprecated | No | Closed without implementation |

## Output Format

```markdown
## Reports Completeness Audit - {DATE}

### Summary
- Issues checked: {N}
- Complete: {N}
- Missing reports: {N}

### Missing Reports
| Issue | Title | Missing |
|-------|-------|---------|
| #121 | Wikipedia Denylist | Both |

### Actions Taken
- Created docs/reports/121/implementation-report.md
- Created docs/reports/121/test-report.md
```

## Integration

Referenced by:
- `docs/0004-orchestration-protocol.md` §8.6
- `docs/0009-session-closeout-protocol.md`
