# Test Report: Issue #306 - Chrome E2E CI Gate

**Issue:** #306 - Add Chrome E2E Tests to CI as Blocking Gate
**Date:** 2026-01-11
**Test Method:** Manual verification + CI validation

## Test Scenarios from LLD Section 11.1

| ID | Scenario | Status | Verification Method |
|----|----------|--------|---------------------|
| 010 | Job runs on PR | Pending | Will verify on PR creation |
| 020 | All specs pass | Pending | CI will run tests |
| 030 | Failure blocks PR | Pending | No `continue-on-error` set |
| 040 | Artifact uploaded on failure | Pending | `if: failure()` configured |
| 050 | Job respects timeout | Pending | `timeout-minutes: 15` set |

## Pre-PR Verification

### 1. YAML Syntax Validation
```bash
# Command: yamllint .github/workflows/ci.yml
# Status: No syntax errors
```

### 2. Job Structure Verification
```bash
# Verified e2e-chrome job exists
grep -n "e2e-chrome:" .github/workflows/ci.yml
# Result: Line 267

# Verified needs: policy-check
grep -A2 "e2e-chrome:" .github/workflows/ci.yml | grep "needs:"
# Result: needs: policy-check

# Verified timeout-minutes
grep -A4 "e2e-chrome:" .github/workflows/ci.yml | grep "timeout-minutes:"
# Result: timeout-minutes: 15

# Verified no continue-on-error
grep -A10 "e2e-chrome:" .github/workflows/ci.yml | grep "continue-on-error" || echo "Not found (correct)"
# Result: Not found (correct)
```

### 3. Local E2E Test Run
```bash
# Command: npx playwright test --project=chromium
# Status: [PENDING - to be run before commit]
```

## CI Validation Plan

After PR is created, the following will be validated:

1. **Job Appears in Actions Tab** - e2e-chrome job should appear in workflow
2. **Dependencies Correct** - Job waits for policy-check
3. **Tests Execute** - Playwright runs successfully
4. **Artifact Upload** - If tests fail, playwright-report/ is uploaded

## Definition of Done Checklist

### Code (from LLD Section 12)
- [x] `e2e-chrome` job added to `.github/workflows/ci.yml`
- [x] Job uses `needs: policy-check`
- [x] Job uses `xvfb-run` for headed mode
- [x] Job does NOT use `continue-on-error`
- [x] Artifact upload on `failure()` condition
- [x] `timeout-minutes: 15` set

### Tests
- [ ] All E2E specs pass in CI (pending CI run)
- [ ] Verify artifact is uploaded on intentional failure (manual test)
- [ ] Verify PR is blocked on failure (automatic via no continue-on-error)

### Documentation
- [x] N/A (CI workflow is self-documenting)

### Reports
- [x] `docs/reports/306/implementation-report.md` created
- [x] `docs/reports/306/test-report.md` created

### Review
- [x] LLD reviewed by Gemini (APPROVED after 2 rounds)
- [ ] Code review completed (pending)
- [ ] Implementation review by Gemini (pending)
