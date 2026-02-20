# Implementation Report — Issue #400: Hermes Admin Dashboard

## Summary

Built the Hermes admin dashboard for visibility into Aletheia's protection state, plus state change alerting via SNS email. Also enabled auth on AletheiaAgent (Issue #399).

## Files Created

| File | Purpose |
|------|---------|
| `src/auth/status_handler.py` | GET /admin/status endpoint — aggregates protection state from 4 AWS APIs |
| `src/hermes_poller.py` | EventBridge Lambda — diffs protection state every 5 min, SNS alerts on change |
| `hermes/index.html` | Dashboard shell with auth gate, protection cards, alarm grid, chart containers |
| `hermes/hermes.css` | Dark theme, card layout, responsive grid, status indicators |
| `hermes/hermes.js` | Fetch /admin/status + /metrics, render protection state + business charts |
| `hermes/mock-status.json` | Mock data for local dev (?mock=true) |
| `tests/unit/test_status_handler.py` | 20 tests for status endpoint (auth, deny policy, kill switch, alarms, budget, caching) |
| `tests/unit/test_hermes_poller.py` | 17 tests for poller (diff logic, fetch, save, publish, handler integration) |
| `docs/reports/400/implementation-report.md` | This file |
| `docs/reports/400/test-report.md` | Test results |

## Files Modified

| File | Change |
|------|--------|
| `src/lambda_auth_function.py` | Added `/admin/status` route (3 lines) |
| `provision.sh` | Added IAM permissions (iam:ListAttachedRolePolicies, lambda:GetFunctionConcurrency, lambda:GetFunctionConfiguration, cloudwatch:DescribeAlarms, budgets:DescribeBudget, sns:Publish), Hermes poller Lambda deployment, EventBridge schedule, AUTH_ENABLED=true |

## Architecture

```
Browser (admin)
    |  HTTPS
    v
CloudFlare Pages (hermes.aletheia.study)
    |  fetch() with Bearer JWT
    v
AletheiaAuth Lambda
    |-- GET /admin/status (NEW)
    |-- GET /metrics (EXISTING)
    v
AWS APIs (IAM, Lambda, CloudWatch, Budgets) — read-only

Alerting:
EventBridge (5 min) → AletheiaHermesPoller Lambda
    → diff state in DynamoDB → SNS email if changed
```

## Operational Changes (Issue #399)

- Flipped `AUTH_ENABLED=true` on AletheiaAgent Lambda
- Verified: unauthenticated requests return 401
- Verified: /health endpoint still returns 200 (no auth)
- Updated provision.sh to persist AUTH_ENABLED=true

## Design Decisions

1. **60-second cache on /admin/status** (vs 5-min for /metrics) — status is more urgent
2. **Fail-open for read-only checks** — if IAM API fails, report false rather than crash
3. **Poller stores state in existing AletheiaAgentState table** — no new table needed
4. **Budget threshold alerting** — alerts on crossing 40%, 80%, 95% in either direction
5. **SNS severity levels** — CRITICAL for deny policy/kill switch, WARNING for budget 80%, INFO for auth changes
6. **No innerHTML** — all DOM manipulation uses textContent and createElement (XSS-safe)
