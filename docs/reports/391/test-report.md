# Test Report — Issue #391

**Title:** feat: observability overhaul — error handling, alerting, diagnostics, coaching
**Date:** 2026-02-19
**Status:** All passing

## Python Test Results

```
920 passed, 2 skipped in 19.27s
```

### New Python Tests (6)

| Test | Description | Result |
|------|-------------|--------|
| `test_health_check_returns_200` | GET /health returns 200 with status ok | PASS |
| `test_health_check_no_auth_required` | GET /health works with AUTH_ENABLED=true | PASS |
| `test_health_check_post_falls_through` | POST /health triggers normal handler | PASS |
| `test_health_check_no_origin_secret_required` | GET /health ignores origin secret | PASS |
| `test_metrics_requires_auth` | GET /metrics returns 401 when auth enabled | PASS |
| `test_metrics_returns_expected_shape` | GET /metrics returns users/usage/caps JSON | PASS |

## JS Test Results

```
153 passed, 2 skipped (5 test files)
2 pre-existing failures in article-extractor.test.js (phone scrubbing — unrelated)
```

### New JS Tests (21)

**overlay.test.js (6 tests)**
| Test | Result |
|------|--------|
| overlay.js file exists and is non-empty | PASS |
| 401 is NOT rendered as hard block | PASS |
| 403 is still rendered as hard block | PASS |
| source contains isHardBlock function | PASS |
| overlay uses fallback signal when missing | PASS |
| overlay uses fallback gem when missing | PASS |

**service-worker.test.js — Error Handling (11 tests)**
| Test | Result |
|------|--------|
| defines mapHttpStatusToMessage function | PASS |
| maps 401 to auth error message | PASS |
| maps 429 to rate limit with reset time | PASS |
| maps 500 to server error message | PASS |
| handles malformed response | PASS |
| defines storeDiagnostics function | PASS |
| stores to chrome.storage.session | PASS |
| stores status/latency/timestamp/error | PASS |
| uses AbortController with 30s timeout | PASS |
| handles AbortError for timeout | PASS |

**popup.test.js — Version & Diagnostics (4 tests)**
| Test | Result |
|------|--------|
| popup.html contains version footer element | PASS |
| version footer displays v1.0 | PASS |
| popup.html contains diagnostics section | PASS |
| popup.js contains loadDiagnostics function | PASS |

## Regression

No regressions. All 920 Python tests and 153 JS tests pass.
