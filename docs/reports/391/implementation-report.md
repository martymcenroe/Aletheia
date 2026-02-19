# Implementation Report — Issue #391

**Title:** feat: observability overhaul — error handling, alerting, diagnostics, coaching
**Date:** 2026-02-19
**Status:** Complete

## Summary

Comprehensive observability overhaul across 6 phases to prevent silent production failures like the #389 P0 outage.

## Changes by Phase

### Phase 1: Backend Health Check
| File | Change |
|------|--------|
| `src/lambda_function.py` | Added `GET /health` route before auth gate, returns `{"status":"ok","version":"1.0"}` |
| `src/lambda_function.py` | Added `_metrics_handler()` function for Phase 6 |

### Phase 2: Extension Error Handling
| File | Change |
|------|--------|
| `extensions/chrome/service-worker.js` | Added `AbortController` with 30s timeout on fetch |
| `extensions/chrome/service-worker.js` | Added `mapHttpStatusToMessage()` — maps 401, 429, 500 to user-friendly text |
| `extensions/chrome/service-worker.js` | Added `storeDiagnostics()` — writes to `chrome.storage.session` |
| `extensions/chrome/service-worker.js` | Added response schema validation (check for `signal`/`gem`) |
| `extensions/chrome/service-worker.js` | Added `chrome.notifications` fallback when CSP blocks overlay |
| `extensions/chrome/manifest.json` | Added `notifications` permission |

### Phase 3: Overlay Error Rendering
| File | Change |
|------|--------|
| `extensions/chrome/overlay.js` | Fixed `isHardBlock()` — 401 returns false (not a hard block) |

### Phase 4: Popup Diagnostics & Version
| File | Change |
|------|--------|
| `extensions/chrome/popup.html` | Added diagnostics panel section and version footer `v1.0` |
| `extensions/chrome/popup.js` | Added `loadDiagnostics()` — reads from `chrome.storage.session` |

### Phase 5: CloudWatch Alerting
| File | Change |
|------|--------|
| `docs/runbooks/provision-cloudwatch.sh` | Added 4 new alarms: LambdaErrors, 4xxRate, 5xxRate, LambdaThrottles |

### Phase 6: Admin Metrics Endpoint
| File | Change |
|------|--------|
| `src/lambda_function.py` | Added `GET /metrics` route with auth support |
| `src/lambda_function.py` | Added `_metrics_handler()` — queries DynamoDB for user/tier/usage data |

## Test Files
| File | Change |
|------|--------|
| `tests/unit/test_lambda_handler.py` | Added `TestHealthCheck` (4 tests) and `TestMetricsEndpoint` (2 tests) |
| `tests/unit/chrome/service-worker.test.js` | Added error handling tests (11 tests) |
| `tests/unit/chrome/overlay.test.js` | New file — 6 tests for isHardBlock and error rendering |
| `tests/unit/chrome/popup.test.js` | Added version footer and diagnostics tests (4 tests) |
| `tests/mocks/chrome-api.mock.js` | Added `chrome.notifications.create` mock |

## LLD
| File | Change |
|------|--------|
| `docs/lld/active/LLD-391.md` | New LLD for observability overhaul |
