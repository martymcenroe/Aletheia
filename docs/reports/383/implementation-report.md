# Implementation Report: #383 Lambda Layer Rebuild for Stripe SDK

## Summary
Added `stripe` to the Lambda dependency layer and fixed IAM permissions for Stripe secrets access.

## Changes
| File | Change |
|------|--------|
| `provision.sh` | Added `stripe` to pip install and layer description |
| `provision.sh` | Added `STRIPE_SECRET_NAME`, `STRIPE_WEBHOOK_SECRET_NAME` variables |
| `provision.sh` | Added `STRIPE_PRICE_ID` env var (defaults empty, set after #366) |
| `provision.sh` | Added Stripe secret ARNs to Secrets Manager IAM permissions |
| `provision.sh` | Added Stripe env vars to Auth Lambda create + update config |

## IAM Bug Fix
Without the Secrets Manager permissions for `aletheia/stripe-secret-key-test` and `aletheia/stripe-webhook-secret-test`, the Stripe endpoints would return 500 at runtime when `stripe_handler.py` calls `get_secret_value()`.
