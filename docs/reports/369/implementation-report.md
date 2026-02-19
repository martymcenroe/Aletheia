# Implementation Report — Issue #369: CloudWatch Usage Dashboard

## Summary

Implemented EMF structured logging for 6 CloudWatch metrics, user anonymization, dashboard/alarm provisioning configs, and Contributor Insights rule.

## Files Created

| File | Purpose |
|------|---------|
| `src/auth/anonymize.py` | SHA-256 truncated to 12 hex chars for privacy-preserving user logging |
| `docs/runbooks/cloudwatch-dashboard.json` | Dashboard definition with 6 widgets |
| `docs/runbooks/sns-alarm.json` | SNS topic + CapDenialSpike alarm config |
| `docs/runbooks/contributor-insights-top-talkers.json` | Abuse detection rule |
| `docs/runbooks/logs-insights-active-users.sql` | Unique user count query |
| `docs/runbooks/provision-cloudwatch.sh` | Dashboard, SNS, alarm provisioning |
| `tests/unit/test_anonymize.py` | 6 anonymization tests |
| `tests/unit/test_metrics_emf.py` | 17 EMF metric tests |

## Files Modified

| File | Changes |
|------|---------|
| `src/observability.py` | Added 7 EMF emission functions + `_build_emf_payload` helper |
| `src/auth/__init__.py` | Exported `anonymize_user_id` |
| `src/auth/auth_middleware.py` | Added RequestCount, anonymized user logging, and CapDenied emission in `require_auth` |
| `src/lambda_function.py` | Added Latency, BedrockCostEstimate, and ErrorRate emission in response/error paths |

## Key Design Decisions

- **EMF via stdout** (not PutMetricData) — zero latency overhead
- **Namespace:** `Aletheia/API`
- **All emission wrapped in try/except** — fail-open, never blocks requests
- **Anonymized user ID in logs only** — NOT as metric dimension (avoids high-cardinality cost)
- **Infrastructure files in `docs/runbooks/`** — matches existing project structure

## Deviations from LLD

None. Implementation matches the approved LLD-369.
