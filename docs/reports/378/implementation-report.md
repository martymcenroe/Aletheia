# Implementation Report: #378 DynamoDB GSI on Tier for Users Table

## Summary
Added `tier-index` GSI to `aletheia-users` table and fixed IAM permissions for index queries.

## Changes
| File | Change |
|------|--------|
| `provision.sh` | Added tier-index GSI creation block (pattern from user_id-index) |
| `provision.sh` | Added `/index/*` suffix to users table IAM resource ARN |
| `provision.sh` | Updated summary to show `(tier-index GSI)` |

## IAM Bug Fix
Without the `/index/*` resource suffix on the users table ARN, any DynamoDB `Query` operation against the GSI would fail with `AccessDeniedException`. The agent state table already had this suffix; the users table was missing it.

## Design Notes
- `KEYS_ONLY` projection minimizes GSI storage cost
- `PAY_PER_REQUEST` billing inherited from table
- `metrics_handler.py` update deferred (Scan with 5-min cache is fine at current scale)
