# Implementation Report — Issue #364: Tiered Rate Limiting with Multi-Window Caps

**Date:** 2026-02-18
**Branch:** `364-tiered-rate-limiting`
**Commit:** `65c0a27`

---

## Summary

Added per-request rate limiting with three time windows (hourly/daily/monthly) and three user tiers (free/subscriber/admin), enforced at request time in the `require_auth` middleware. Uses DynamoDB transactions for atomic 3-counter increments. Implements hybrid fail mode: free tier fail-closed (503), subscriber/admin fail-open on DynamoDB errors.

## Files Changed (14 files, +2287 lines)

### New Files (7)

| File | Lines | Purpose |
|------|-------|---------|
| `src/auth/models/__init__.py` | 24 | Re-exports all model types |
| `src/auth/models/rate_limit.py` | 66 | Core types: UserTier, WindowType, TierConfig, RateLimitResult |
| `src/auth/models/user.py` | 17 | UserRecord TypedDict |
| `src/auth/tier_config_service.py` | 197 | TierConfigService with 5-min TTL cache + DynamoDB persistence |
| `tests/unit/test_multi_window_counter.py` | 669 | 47 tests for MultiWindowCounter (T010-T160) |
| `tests/unit/test_tier_config_service.py` | 333 | 21 tests for TierConfigService (T130, T150, T170, T180) |
| `tests/fixtures/rate_limit_429_response.json` | 7 | Sample 429 response fixture |

### Modified Files (7)

| File | Delta | Changes |
|------|-------|---------|
| `src/auth/token_cap_service.py` | +418 | Added MultiWindowCounter class (existing daily cap code untouched) |
| `src/auth/auth_middleware.py` | +131 | Rate limiting in require_auth, extract_tier_from_jwt, check_rate_limit |
| `src/auth/jwt_service.py` | +19 | tier/billing_anchor_day in JWT, claims field in AuthResult |
| `src/lambda_auth_function.py` | +37 | get_user_tier(), tier embedding in token exchange |
| `src/auth/__init__.py` | +29 | New exports |
| `tests/unit/test_auth_middleware.py` | +284 | 20 new tests (T070, T120, T140) + autouse rate limit mock |
| `tests/unit/test_jwt_service.py` | +66 | 8 new tests (T220: tier claims) |

## Key Design Decisions

1. **Hybrid fail mode:** Free tier fail-closed protects against abuse during outages; subscriber/admin fail-open avoids blocking paying users on infra blips
2. **Module-level singletons:** `_tier_config_service` and `_multi_window_counter` in `auth_middleware.py` for connection reuse across Lambda invocations
3. **DynamoDB transactions:** `transact_write_items` ensures all 3 counters increment atomically (no partial writes)
4. **Monthly billing anchor:** Supports per-user billing cycle via `billing_anchor_day` with clamping for short months
5. **Existing code untouched:** All existing daily cap code in `token_cap_service.py` is preserved; MultiWindowCounter is added alongside

## DynamoDB Key Design (same `aletheia-token-cap` table)

| PK | SK | TTL |
|----|-----|-----|
| `USER#{user_id}` | `RATE#HOURLY#{window}` | 2h |
| `USER#{user_id}` | `RATE#DAILY#{window}` | 2d |
| `USER#{user_id}` | `RATE#MONTHLY#{window}` | 35d |
| `CONFIG` | `TIER#{tier}` | none |

## Tier Caps (Defaults)

| Tier | Hourly | Daily | Monthly |
|------|--------|-------|---------|
| Free | 5 | 15 | 100 |
| Subscriber | 20 | 200 | 2000 |
| Admin | 50 | 500 | 10000 |
