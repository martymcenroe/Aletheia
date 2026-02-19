# Implementation Report: #381 DynamoDB TTL on Coupon Expiry

## Summary
Added TTL enablement block for `aletheia-coupons` table in `provision.sh`, using the `expiry` attribute (unix timestamp already present on coupon items).

## Changes
| File | Change |
|------|--------|
| `provision.sh` | Added TTL block after coupons table creation (pattern from token-cap TTL) |
| `provision.sh` | Updated summary output to show `(TTL enabled)` for coupons table |

## Design Notes
- Coupons with `expiry = 0` are unaffected (DynamoDB ignores epoch-0 TTL values)
- Follows exact pattern of token-cap TTL block (lines 175-192 of original)
- Idempotent: checks `TimeToLiveStatus` before enabling
