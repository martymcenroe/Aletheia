# Test Report — Issue #400: Hermes Admin Dashboard

## Test Results

```
tests/unit/test_status_handler.py  — 20 passed
tests/unit/test_hermes_poller.py   — 17 passed
Full suite                         — 957 passed, 2 skipped, 0 failed (22s)
```

## New Test Coverage

### test_status_handler.py (20 tests)

| Test Class | Tests | Coverage |
|-----------|-------|----------|
| TestAuth | 4 | No token, secret unavailable, invalid token, non-admin tier |
| TestDenyPolicy | 3 | Attached, not attached, API error fallback |
| TestKillSwitch | 3 | Active (concurrency=0), not active, no setting |
| TestAlarmStates | 1 | Mixed alarm states + NOT_FOUND for missing alarms |
| TestBudget | 1 | Budget limit/actual/forecast/percent calculation |
| TestOverallStatus | 5 | Healthy, down (deny), down (kill switch), degraded (alarm), degraded (budget) |
| TestCaching | 1 | Cache hit returns cached=true, fetch called only once |
| TestBuildResponse | 2 | CORS header, JSON body formatting |

### test_hermes_poller.py (17 tests)

| Test Class | Tests | Coverage |
|-----------|-------|----------|
| TestDiffStates | 9 | No changes, deny policy, kill switch, auth, budget threshold (single, multi, down), empty previous, None skip |
| TestFetchCurrentState | 1 | All-healthy state from mocked AWS APIs |
| TestLoadPreviousState | 2 | Existing state, missing state |
| TestSaveState | 1 | DynamoDB put_item with correct key |
| TestPublishAlert | 2 | Critical severity (deny policy), info severity (auth) |
| TestLambdaHandler | 2 | No changes (no publish), with changes (publish called) |

## Regression

Full test suite (957 tests) passes with no regressions.

## Manual Verification

- Dashboard renders correctly in mock mode (?mock=true)
- Protection state cards show correct indicators
- Alarm grid renders all 6 alarms with OK status
- Budget gauge shows correct percentage and color
- Auth gate appears when no JWT is stored
- Unauthenticated API request → 401 (auth enabled)
- Health endpoint → 200 (no auth required)
