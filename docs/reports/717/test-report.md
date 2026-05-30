# Test Report — Issue #717

## What this PR changes

Pure documentation. Five small text changes in one file: header version line, three reference removals in §3b.4 / §10a / §18, one new change-log entry. No code, no config, no tests.

## Verification

### Pre-commit hooks

Same gates as #714: trailing whitespace, end-of-file, project-policy compliance, pre-merge-gate reports-required check. Language-specific linters (ESLint, ruff, mypy) skip when no JS/Python files are in the diff.

### Manual

```bash
cd /c/Users/mcwiz/Projects/Aletheia
grep -E "^> \*\*Version:" docs/runbooks/10907-runbook-amo-publish.md
# Expected: > **Version:** 1.0.8

# Operational text (everything before the change log) carries zero 10920 references:
sed -n '1,/^## 20\. Change log/p' docs/runbooks/10907-runbook-amo-publish.md | grep -c "10920"
# Expected: 0

# Change log honestly records what was removed:
grep "^| 1.0.8" docs/runbooks/10907-runbook-amo-publish.md
# Expected: the new entry
```

## Regression scope

None possible. Documentation-only patch to a runbook that is read, not executed.

## What this report does NOT claim

- Does not claim `docs/10920-cws-listing-corrections-2026-05-27.md` is also being deleted. It is not. Its lifecycle is operator-owned and out of scope for this PR.
- Does not assert anything about CWS, the CWS runbook, or any cross-runbook concerns. This is the AMO runbook.
