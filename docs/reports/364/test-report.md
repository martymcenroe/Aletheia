# Test Report — Issue #364: Tiered Rate Limiting with Multi-Window Caps

**Date:** 2026-02-18
**Branch:** `364-tiered-rate-limiting`

---

## Test Results

### Targeted Tests (195 total)

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_multi_window_counter.py` | 47 | All passed |
| `test_tier_config_service.py` | 21 | All passed |
| `test_auth_middleware.py` | 80 (20 new) | All passed |
| `test_jwt_service.py` | 47 (8 new) | All passed |

### Full Regression

```
834 passed, 2 skipped, 7 warnings in 25.36s
```

- **0 failures** — no regressions
- **2 skipped** — pre-existing (LinkedIn OAuth tests requiring live credentials)
- **7 warnings** — pre-existing PyJWT InsecureKeyLengthWarning from test fixtures using short HMAC keys

## LLD Test Matrix Coverage

| ID | Scenario | Test | Status |
|----|----------|------|--------|
| T010 | Request under all limits → allowed | `TestUnderAllLimits::test_allowed_when_under_caps` | Pass |
| T020 | Hourly limit exceeded → 429 | `TestHourlyLimitExceeded::test_hourly_exceeded_returns_denied` | Pass |
| T030 | Daily limit exceeded → 429 | `TestDailyLimitExceeded::test_daily_exceeded_returns_denied` | Pass |
| T040 | Monthly limit exceeded → 429 | `TestMonthlyLimitExceeded::test_monthly_exceeded_returns_denied` | Pass |
| T050 | Free tier boundary (5th OK, 6th fails) | `TestFreeTierBoundary::test_5th_request_allowed` / `test_6th_request_denied` | Pass |
| T060 | Subscriber tier boundary (20th OK, 21st fails) | `TestSubscriberTierBoundary::test_20th_request_allowed` / `test_21st_request_denied` | Pass |
| T070 | JWT contains tier → correct limits | `TestMiddlewareRateLimitWithTier::test_free_tier_rate_limited` | Pass |
| T080a | DynamoDB timeout + free → fail-closed | `TestFailClosedFree::test_timeout_free_tier_denied` | Pass |
| T080b | DynamoDB timeout + subscriber → fail-open | `TestFailOpenSubscriber::test_timeout_subscriber_allowed` | Pass |
| T090 | Atomic transaction (single call) | `TestAtomicTransaction::test_single_transact_write_call` | Pass |
| T100 | Monthly anniversary reset | `TestMonthlyAnchor::test_before_anchor_uses_previous_month` | Pass |
| T110 | TTL verification (2h/2d/35d) | `TestTTLValues::test_hourly_ttl_is_2_hours` etc. | Pass |
| T120 | 429 includes resets_at and resets_in_seconds | `TestRateLimitResponse::test_429_response_has_resets_at` | Pass |
| T130 | Cache hit (no second DynamoDB call) | `TestCacheHit::test_cache_hit_no_second_dynamo_call` | Pass |
| T140 | Missing tier → free limits | `TestMissingTierDefaultsFree::test_extract_tier_missing_defaults_free` | Pass |
| T150 | Config loaded from DynamoDB | `TestLoadFromDynamoDB::test_dynamo_config_overrides_defaults` | Pass |
| T160 | Multiple windows exceeded → hourly priority | `TestMultipleWindowsExceeded::test_hourly_and_daily_exceeded_returns_hourly` | Pass |
| T170 | Tier config values match stored | `TestTierConfigValues::test_subscriber_config_from_dynamo` | Pass |
| T180 | Admin tier 50/500/10000 | `TestAdminTier::test_admin_defaults_in_module` | Pass |
| T220 | Tier embedded in JWT | `TestJwtTierClaims::test_create_jwt_contains_tier` | Pass |

## Existing Test Compatibility

Four existing tests (`TestMiddlewareValidToken`, `TestMiddlewareDualSecret`) required an `autouse` fixture to mock `check_rate_limit` — the new rate limiting code in `require_auth` tries to instantiate real DynamoDB clients. Fix: `@pytest.fixture(autouse=True)` with `patch("auth.auth_middleware.check_rate_limit", return_value=(True, None))`.
