# Test Report: Security Audit Remediations

**Issues:** #436, #438, #439, #440
**Branch:** `security-hardening-audit-remediations`
**Date:** 2026-02-24

## Test Results

```
poetry run pytest
1002 passed, 2 skipped, 0 failures (28.79s)
```

Full regression suite — zero failures, zero regressions.

## Verification Checks

| Check | Command | Expected | Result |
|-------|---------|----------|--------|
| No jose imports | `grep -r "jose" src/` | No matches | PASS |
| No CDN references | `grep "jsdelivr" static/admin/metrics.html` | No matches | PASS |
| CORS restricted | `grep "AllowOrigins" provision.sh` | `api.aletheia.study` | PASS |
| DynamoDB scoped | `grep "arn:aws:dynamodb" provision.sh` | `us-east-1:383687041805` | PASS |
| Bedrock scoped | `grep "arn:aws:bedrock" provision.sh` | 2 specific model ARNs | PASS |
| No wildcard IAM resources | `grep '"Resource": "*"' provision.sh` | Only CloudWatch (condition-scoped) | PASS |

## Notes

- The 2 skipped tests are pre-existing (unrelated to this change)
- The 13 warnings are pre-existing PyJWT InsecureKeyLengthWarning from test fixtures using short keys
- Chart.js vendored file is 205 KB (chart.umd.min.js v4.4.0)
