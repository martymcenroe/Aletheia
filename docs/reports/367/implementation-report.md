# Implementation Report: Issue #367 — Manual Subscriptions with Coupons

## Summary

Implemented coupon-based manual subscription upgrades including admin CLI for coupon management, authenticated redemption API endpoint, atomic DynamoDB conditional writes for race-condition prevention, and Chrome extension UI for coupon entry.

## Files Created

| File | Purpose |
|------|---------|
| `tools/admin_coupons.py` | CLI: generate/list/revoke coupon codes |
| `src/auth/coupon_handler.py` | POST /redeem-coupon handler with JWT auth |
| `tests/unit/test_coupon_handler.py` | 34 tests for redemption logic |
| `tests/unit/test_admin_coupons.py` | 19 tests for CLI operations |
| `tests/fixtures/coupon_records.json` | DynamoDB fixture data |

## Files Modified

| File | Changes |
|------|---------|
| `src/lambda_auth_function.py` | Added `/redeem-coupon` POST route |
| `provision.sh` | Added `aletheia-coupons` DynamoDB table, IAM permissions, env vars |
| `extensions/chrome/popup.html` | Added coupon redemption UI section |
| `extensions/chrome/popup.js` | Added coupon toggle, input validation, submit handler |
| `extensions/chrome/popup.css` | Added coupon section styles |

## Key Design Decisions

- **16-char uppercase alphanumeric codes** via `secrets.choice` (cryptographic randomness)
- **Atomic redemption** via DynamoDB ConditionExpression preventing race conditions
- **Case-insensitive input** — codes uppercased on both CLI and API
- **Revoked codes return same error as non-existent** — prevents enumeration attacks
- **Code prefix logging only** (`ABCD****`) — never log full coupon codes
- **Optional email collection** stored in users table on redemption
- **Lazy DynamoDB client** with `DYNAMODB_ENDPOINT` support for local testing

## Verification

- 53 unit tests pass (34 handler + 19 CLI)
- 939 full regression tests pass (2 skipped)
- mypy: 0 errors
- ruff: 0 errors (in new files)
- ESLint: 0 errors
