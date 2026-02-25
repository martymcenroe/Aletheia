# 10030 — Test Report Template

**Standard for:** All Aletheia test reports in `docs/reports/`
**Ref:** Issue #460

---

## Required Sections

### 1. Header

```markdown
# Test Report — Issue #NNN
**Feature:** [brief description]
**Date:** YYYY-MM-DD
```

### 2. Test Results

Summary of test execution: pass/fail counts, regression check.

### 3. Coverage Highlights

Table of what was tested and results.

### 4. What Was NOT Tested

**This section is mandatory.** List scenarios, edge cases, or components explicitly excluded from testing.

| Excluded Area | Reason |
|---------------|--------|
| [scenario] | [why it was excluded] |

If everything was tested, write: "No known exclusions — full coverage of the feature scope."

### 5. Lint and Type Check

ruff, mypy, ESLint results.

---

## Quality Grading

Reports are graded 0–4 by `/test-gaps`:

| Criteria | How Detected | Points |
|----------|-------------|--------|
| "What was tested" section | Heading with "tested" or "coverage" | +1 |
| "How tested" method specified | Contains "automated", "manual", "unit test", "e2e" | +1 |
| "What was NOT tested" section | Heading with "not tested" or "limitations" | +1 |
| Evidence provided | Logs, screenshots, test output | +1 |

**Target: 4/4 on all reports.**
