# Test Report: #381 DynamoDB TTL on Coupon Expiry

## Verification
- `bash -n provision.sh` — syntax check PASSED
- Manual diff review — TTL block follows token-cap pattern exactly
- No unit tests required (infrastructure-only change)
