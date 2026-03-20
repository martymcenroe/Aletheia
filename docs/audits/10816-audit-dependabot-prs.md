# 0816 - Audit: Dependabot PRs

## 1. Purpose

Automated process to safely merge pending Dependabot PRs with regression verification. This audit ensures dependency updates don't break the build while minimizing manual intervention.

**Key Principle:** Dependency updates are merged automatically when safe, with automatic rollback and issue creation when problems occur.

---

## 2. Trigger Conditions

| Trigger | Context |
|---------|---------|
| **Pre-Security Audit** | MUST run before 0809 Security Audit |
| **Weekly** | Part of regular maintenance (Mondays) |
| **On Demand** | When Dependabot PRs accumulate or security concern arises |

---

## 2a. Force Run Protocol (On-Demand)

Relying on the weekly schedule is insufficient for high-velocity development or when you suspect a security issue *now*. Use these methods to trigger Dependabot immediately:

### Method 1: GitHub UI (Quickest)

1. Navigate to repository on GitHub
2. Go to **Insights** → **Dependency graph** → **Dependabot**
3. Click **"Check for updates"** to force an immediate scan

For security alerts specifically:
- Go to **Security** tab → **Dependabot**
- Security alerts trigger automatically on manifest changes

### Method 2: Config Bump (Most Reliable)

Dependabot *always* runs when its configuration file changes. Add a timestamp comment and push:

```bash
# Add trigger comment to dependabot.yml
echo "# Triggering scan: $(date +%Y-%m-%d)" >> .github/dependabot.yml
git add .github/dependabot.yml
git commit -m "chore: trigger Dependabot scan"
git push
```

This forces a re-evaluation of the entire dependency tree immediately.

### Method 3: PR-Time Scanning (Automated)

The CI workflow includes `dependency-review-action` which scans every PR automatically. This catches vulnerable packages *before* merge, providing callable feedback on every push.

---

## 3. Procedure

### Phase 1: Baseline

```bash
# 1.1 Ensure clean working directory
cd /c/Users/mcwiz/Projects/Aletheia
git checkout main
git pull origin main
git status  # Must be clean

# 1.2 Run full regression test (baseline)
poetry run pytest --tb=short 2>&1 | tee /tmp/baseline-test.log
BASELINE_EXIT=$?

# 1.3 Record baseline metrics
BASELINE_PASSED=$(grep -oP '\d+(?= passed)' /tmp/baseline-test.log | head -1)
BASELINE_FAILED=$(grep -oP '\d+(?= failed)' /tmp/baseline-test.log | head -1 || echo "0")
BASELINE_ERRORS=$(grep -oP '\d+(?= error)' /tmp/baseline-test.log | head -1 || echo "0")

echo "Baseline: $BASELINE_PASSED passed, $BASELINE_FAILED failed, $BASELINE_ERRORS errors"
```

**Stop Condition:** If baseline tests fail, abort audit and fix existing issues first.

### Phase 1a: CI Consistency Check (CRITICAL)

**Verify that CI commands use project-local versions**, not hardcoded versions that might mask upgrade breaks:

```bash
# Check for hardcoded version numbers in CI commands
🤖 grep -rn "@[0-9]" .github/workflows/*.yml

# Bad: npx eslint@8 (hardcoded version)
# Good: npx eslint (uses project-local version from package.json)
```

| Pattern | Risk | Fix |
|---------|------|-----|
| `npx <tool>@<version>` | False green on upgrades | Use `npx <tool>` after `npm ci` |
| `pip install <pkg>==<version>` | Bypasses poetry.lock | Use `poetry run` |

**If hardcoded versions found:** Create issue to fix CI before merging dependency upgrades.

### Phase 2: Identify Dependabot PRs

```bash
# 2.1 List all open Dependabot PRs
gh pr list --repo martymcenroe/Aletheia --author "app/dependabot" --json number,title,headRefName --jq '.[] | "\(.number) | \(.title) | \(.headRefName)"'

# 2.2 Store PR numbers for processing
DEPENDABOT_PRS=$(gh pr list --repo martymcenroe/Aletheia --author "app/dependabot" --json number --jq '.[].number' | tr '\n' ' ')
echo "Dependabot PRs to process: $DEPENDABOT_PRS"
```

**Stop Condition:** If no Dependabot PRs, audit passes immediately (no action needed).

### Phase 3: Batch Merge Attempt

```bash
# 3.1 Merge all Dependabot PRs
for PR in $DEPENDABOT_PRS; do
    echo "Merging PR #$PR..."
    gh pr merge $PR --repo martymcenroe/Aletheia --merge --auto
done

# 3.2 Wait for merges to complete
sleep 10
git pull origin main

# 3.3 Run full regression test (post-merge)
poetry run pytest --tb=short 2>&1 | tee /tmp/postmerge-test.log
POSTMERGE_EXIT=$?

# 3.4 Record post-merge metrics
POSTMERGE_PASSED=$(grep -oP '\d+(?= passed)' /tmp/postmerge-test.log | head -1)
POSTMERGE_FAILED=$(grep -oP '\d+(?= failed)' /tmp/postmerge-test.log | head -1 || echo "0")
POSTMERGE_ERRORS=$(grep -oP '\d+(?= error)' /tmp/postmerge-test.log | head -1 || echo "0")

echo "Post-merge: $POSTMERGE_PASSED passed, $POSTMERGE_FAILED failed, $POSTMERGE_ERRORS errors"
```

### Phase 4: Compare Results

```bash
# 4.1 Compare baseline vs post-merge
if [ "$BASELINE_PASSED" = "$POSTMERGE_PASSED" ] && \
   [ "$BASELINE_FAILED" = "$POSTMERGE_FAILED" ] && \
   [ "$BASELINE_ERRORS" = "$POSTMERGE_ERRORS" ]; then
    echo "✅ PASS: All Dependabot PRs merged successfully. Test results identical."
    # Audit complete - exit successfully
else
    echo "❌ REGRESSION DETECTED: Test results differ. Initiating rollback..."
    # Proceed to Phase 5
fi
```

### Phase 5: Rollback and Isolate (If Regression Detected)

```bash
# 5.1 Revert all Dependabot merges
# Get the commit before the first Dependabot merge
REVERT_TO=$(git log --oneline | grep -v "dependabot\|Bump" | head -1 | cut -d' ' -f1)
git revert --no-commit HEAD...$REVERT_TO
git commit -m "chore: revert Dependabot batch merge due to regression"
git push origin main

# 5.2 Re-verify baseline
poetry run pytest --tb=short
```

### Phase 6: One-by-One Merge (Isolation Mode)

For each Dependabot PR:

```bash
for PR in $DEPENDABOT_PRS; do
    echo "=== Testing PR #$PR in isolation ==="

    # 6.1 Merge single PR
    gh pr merge $PR --repo martymcenroe/Aletheia --merge
    git pull origin main

    # 6.2 Run regression test
    poetry run pytest --tb=short 2>&1 | tee /tmp/pr-$PR-test.log
    PR_EXIT=$?

    PR_PASSED=$(grep -oP '\d+(?= passed)' /tmp/pr-$PR-test.log | head -1)
    PR_FAILED=$(grep -oP '\d+(?= failed)' /tmp/pr-$PR-test.log | head -1 || echo "0")

    # 6.3 Check for regression
    if [ "$BASELINE_PASSED" != "$PR_PASSED" ] || [ "$BASELINE_FAILED" != "$PR_FAILED" ]; then
        echo "❌ PR #$PR caused regression. Reverting..."

        # 6.4 Revert this specific merge
        git revert HEAD --no-edit
        git push origin main

        # 6.5 Comment on the PR
        gh pr comment $PR --repo martymcenroe/Aletheia --body "## ⚠️ Automated Regression Detected

This dependency update caused test failures when merged.

**Baseline:** $BASELINE_PASSED passed, $BASELINE_FAILED failed
**After merge:** $PR_PASSED passed, $PR_FAILED failed

The merge has been automatically reverted. Please review the dependency update for breaking changes.

---
*Automated by 0816-audit-dependabot-prs*"

        # 6.6 Create issue for review
        gh issue create --repo martymcenroe/Aletheia \
            --title "Dependabot PR #$PR causes regression" \
            --body "## Summary

Dependabot PR #$PR was automatically reverted due to test regression.

## Details

- **PR:** #$PR
- **Baseline tests:** $BASELINE_PASSED passed
- **After merge:** $PR_PASSED passed
- **Test log:** See attached or run locally

## Action Required

1. Review the dependency changelog for breaking changes
2. Update code to accommodate the new version
3. Re-run tests locally
4. Close this issue when resolved

## References

- Audit: docs/0816-audit-dependabot-prs.md
- PR: #$PR

---
*Automated by 0816-audit-dependabot-prs*" \
            --label "dependencies,regression,automated"

        echo "Issue created for PR #$PR"
    else
        echo "✅ PR #$PR merged successfully"
        # Update baseline for next iteration
        BASELINE_PASSED=$PR_PASSED
    fi
done
```

---

## 4. Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│                    Run Baseline Tests                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Baseline passes?  │
                    └─────────┬─────────┘
                         No ──┼── Yes
                              │
              ┌───────────────┘
              ▼
    ┌─────────────────┐
    │ ABORT: Fix      │
    │ existing issues │
    └─────────────────┘

                              │ (Yes path)
                    ┌─────────▼─────────┐
                    │ Any Dependabot    │
                    │ PRs pending?      │
                    └─────────┬─────────┘
                         No ──┼── Yes
                              │
              ┌───────────────┘
              ▼
    ┌─────────────────┐
    │ PASS: No action │
    │ needed          │
    └─────────────────┘

                              │ (Yes path)
                    ┌─────────▼─────────┐
                    │ Merge ALL PRs     │
                    │ Run tests again   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Results identical │
                    │ to baseline?      │
                    └─────────┬─────────┘
                       Yes ───┼─── No
                              │
              ┌───────────────┘
              ▼
    ┌─────────────────┐              ┌─────────────────────────────┐
    │ PASS: All PRs   │              │ Revert all, then merge      │
    │ merged          │              │ one-by-one with tests       │
    └─────────────────┘              └──────────────┬──────────────┘
                                                    │
                                          ┌─────────▼─────────┐
                                          │ Each PR:          │
                                          │ Merge → Test      │
                                          └─────────┬─────────┘
                                                    │
                                          ┌─────────▼─────────┐
                                          │ Regression?       │
                                          └─────────┬─────────┘
                                             No ────┼──── Yes
                                                    │
                              ┌─────────────────────┘
                              ▼
                    ┌─────────────────────────────────────────┐
                    │ Revert PR                               │
                    │ Comment on PR                           │
                    │ Create issue                            │
                    └─────────────────────────────────────────┘
```

---

## 5. Automation Notes

### GitHub CLI Requirements

This audit requires `gh` CLI with appropriate permissions:
- `repo` scope for PR operations
- `issues:write` for issue creation

### Test Command Configuration

Default: `poetry run pytest --tb=short`

For projects with different test commands, set:
```bash
export ALETHEIA_TEST_CMD="poetry run pytest --tb=short"
```

### Parallel Execution

PRs are merged sequentially in isolation mode to pinpoint the exact PR causing regression.

---

## 6. Integration with Security Audit

This audit is a **prerequisite** for the Security Audit (0809).

```markdown
## Security Audit Procedure (0809)

### Step 0: Run Dependabot PR Audit (REQUIRED)

Before beginning security audit, run 0816-audit-dependabot-prs to ensure:
1. All safe dependency updates are merged
2. Known-problematic updates are documented
3. Dependency baseline is clean for vulnerability analysis
```

---

## 7. Audit Record

| Date | Auditor | PRs Processed | Result | Issues Created |
|------|---------|---------------|--------|----------------|
| 2026-01-04 | Claude Opus 4.5 | 4 (#142, #143, #144, #146) | ✅ PASS | None |
| 2026-02-18 | Claude Opus 4.6 (reviewed: martymcenroe) | 4 alerts (lodash, lodash-es, jsonpath x2) | ✅ PASS | None (4 mod ajv accepted risk) |
| 2026-02-23 | Claude Opus 4.6 | 5 (#421–#425): 2 merged (#421 npm-minor, #424 python-minor), 3 conflicting (#422 @eslint/js 10, #423 eslint-plugin-security 4, #425 stripe 14) — rebase requested | ✅ PARTIAL | None |
| 2026-02-24 | Claude Opus 4.6 | 2 (#423 eslint-plugin-security 3→4, #425 stripe 7→14): #423 merged directly, #425 superseded by #435 (migration PR with regression testing) | ✅ PASS | None |
| 2026-02-27 | Claude Opus 4.6 | 1 alert (#19): basic-ftp 5.1.0→5.2.0 (critical path traversal GHSA-5rq4-664w-9x2c), lockfile-only fix via `npm audit fix` | ✅ PASS | #482 |
| 2026-03-15 | Claude Opus 4.6 | 3 (#567 python-minor, #566 npm-minor, #484 upload-artifact v6→v7): all merged. Pre-req: fixed integration test regression #568. Discovered pr-sentinel-mm + auto-reviewer didn't handle dependabot PRs (fixed in AssemblyZero). Baseline 1027 passed → post-merge 1027 passed, identical. | ✅ PASS | #564, #568 |
| *Template* | *Agent* | *Count* | *PASS/FAIL* | *Issue links* |

---

## 8. History

| Date | Change |
|------|--------|
| 2026-01-04 | Created. Automated Dependabot PR merge with regression detection. |
| 2026-01-05 | Added §2a Force Run Protocol. Added `dependency-review-action` to CI. |
