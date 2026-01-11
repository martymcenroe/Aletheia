# 272 - Implementation Report: Apply Shadow DOM Patch to Chrome E2E Tests

## 1. Metadata

| Field | Value |
|-------|-------|
| **Issue** | #272 |
| **LLD** | N/A - Tech debt fix, no LLD required |
| **Test Report** | `docs/reports/272/test-report.md` |
| **Implementer** | Claude Opus 4.5 via Claude Code |
| **Date** | 2026-01-10 |
| **PR** | TBD |

## 2. Summary

Applied the existing Shadow DOM `attachShadow` patch (already working in Firefox tests) to Chrome tests. The patch forces `mode: 'open'` for Shadow DOM attachment, which allows test code to access `host.shadowRoot` - a property that returns `null` for closed shadow roots.

Before this fix, Chrome E2E tests were failing because they couldn't query elements inside the closed Shadow DOM. Firefox tests already had this patch applied (added in #265), but Chrome tests were using a local copy of the helper functions without the patch.

**Result:** Chrome museum-label tests improved from 4/16 passing to 15/16 passing.

## 3. Files Created

| File | Description |
|------|-------------|
| `docs/reports/272/implementation-report.md` | This report |
| `docs/reports/272/test-report.md` | Test results documentation |

## 4. Files Modified

| File | Changes | Description |
|------|---------|-------------|
| `tests/e2e/helpers/overlay-helpers.js` | +2/-4 lines | Removed Firefox-only condition so patch applies to both browsers |
| `tests/e2e/museum-label.spec.js` | +9/-97 lines | Removed duplicate local helpers, now imports from shared module |

## 5. Deviations from LLD

None - no LLD for this tech debt fix. Implementation followed the straightforward approach:
1. Make the existing patch apply unconditionally (was Firefox-only)
2. Update Chrome tests to use the shared helpers

## 6. Test Harness

No new test infrastructure created. Existing helpers were consolidated:

- **Test file:** `tests/e2e/museum-label.spec.js`
- **Fixtures:** Uses `TEST_DATA` from `overlay-helpers.js`
- **Shared helpers:** `injectOverlay`, `shadowQuery`, `shadowClick`, `shadowHover`, etc.

## 7. Test Coverage

| Area | Coverage | Notes |
|------|----------|-------|
| Neutral badge display | Covered | Test 010 |
| Warning badge display | Covered | Test 020 |
| Block badge display | Covered | Test 030 |
| Gem hover reveal | Covered | Tests 040, 050 |
| Context expand/collapse | Covered | Tests 060, 070, 080 |
| Typewriter animation | Covered | Test 090 |
| Close behavior | Covered | Tests 100, 110, 120 |
| Accessibility - focus | Covered | Test 130 |
| Accessibility - ARIA | **Failing** | Test 140 - pre-existing bug |
| Loading state | Covered | Test 150 |
| XSS prevention | Covered | Test 160 |

**Willison Protocol Compliance:**
- [x] Automated tests written (existing)
- [x] Tests fail on revert (verified - 4/16 before, 15/16 after)
- [x] Proof captured in Test Report

## 8. Lessons Learned

- The Shadow DOM patch is required for **both** Chrome and Firefox. The original implementation incorrectly assumed Chrome exposed closed shadow roots to test code.
- Duplicate helper functions across test files lead to inconsistencies. The shared helpers pattern (overlay-helpers.js) is the right approach.
- The one remaining test failure (ARIA attributes) is a separate bug in overlay.js, not a Shadow DOM access issue.

## 9. Open Issues

| Issue | Type | Description |
|-------|------|-------------|
| TBD | Bug | `overlay.js` doesn't set `aria-expanded` attribute on `.aletheia-context` element |

## 10. Orchestrator Review Notes

**Reviewer:** TBD
**Date:** TBD

### In-Scope Observations
{Pending review}

### New-Scope Observations
{Pending review}

### Meta Observations
{Pending review}

### Approval
- [ ] Code reviewed
- [ ] Manual tests passed (see Test Report)
- [ ] Ready for merge
