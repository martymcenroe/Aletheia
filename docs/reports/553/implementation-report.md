# Implementation Report — Issue #553

**Issue:** fix: GDPR erasure endpoint — delete from all tables, not just analysis
**Audit Reference:** `docs/audits/10817-audit-privacy-policy-compliance.md` — CRITICAL-03
**Date:** 2026-03-13

## Changes

### `src/lambda_auth_function.py`

Refactored `delete_user_data()` from a single-table function into a complete GDPR Article 17 erasure:

1. **`_delete_analysis_records()`** — unchanged logic, extracted to helper
2. **`_cancel_stripe_subscription()`** — new: cancels active Stripe subscription before profile deletion
3. **`_delete_user_profile()`** — new: deletes user record from `aletheia-users`
4. **`_remove_from_coupon_redeemed_by()`** — new: scans `aletheia-coupons`, removes user_id from `redeemed_by` String Sets
5. **`_delete_rate_limit_records()`** — new: deletes `USER#{user_id}` entries from `aletheia-token-cap`

`delete_user_data()` now returns a summary dict (was: int count). `handle_delete_my_data()` updated to include summary in response.

Execution order is deliberate: Stripe cancellation happens before profile deletion (need Stripe IDs from user record).

### `tests/unit/test_lambda_auth.py`

- Added `aletheia-coupons` table to moto fixture
- Expanded from 1 GDPR test to 7 (analysis, profile, coupons, rate limits, summary, handler, unauthorized)
- All tests use real DynamoDB operations via moto (no mocks)

## Blast Radius

- Users calling `DELETE /my-data` will now lose their profile, subscription, and all associated data
- This is the correct GDPR behavior — "right to erasure" means everything
- Users must re-authenticate after erasure (expected)

## Test Results

- 978 unit tests passed, 0 failed
- 34 auth-specific tests passed (was 23, +11 new)
