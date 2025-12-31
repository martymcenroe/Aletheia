# Immediate Plan: Chrome Web Store Submission

**Updated:** 2025-12-31
**Goal:** Submit Aletheia to Chrome Web Store

---

## Critical Path Status

| # | Issue | Status |
|---|-------|--------|
| 1 | ~~#45 (Denylist)~~ | ✅ COMPLETE (PR #122) |
| 2 | ~~#113 (Naked Python)~~ | ✅ COMPLETE (PR #122) |
| 3 | **#51/#53 (Store)** | ← YOU ARE HERE |
| 4 | #100 (Firefox) | Pending |

---

## Next: Chrome Web Store (#51, #53)

### #51 - Chrome Web Store Compliance
- Manifest review
- Privacy Policy
- Store Listing copy

### #53 - Generate Store Assets
- Extension zip script
- Placeholder images (icons, screenshots)

---

## What's Working Now

The core pipeline is deployed and tested:
- ✅ Lambda function deployed (`lambda_function.py`)
- ✅ Denylist filter (`src/guardrails/denylist.py`) with 2,584 terms
- ✅ Smoke test passing (`tools/smoke_test.py`)
- ✅ Deploy script fixed (`deploy.sh`)

---

## Open Issues (23 remaining)

Run `gh issue list --state open` for current list.
See `docs/6000-open-issues.md` for formatted view.
