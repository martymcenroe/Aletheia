# Implementation Report: #499 Fix AUTH_ENABLED in provision.sh

## Changes
- `provision.sh` lines 446 and 465: `AUTH_ENABLED=false` → `AUTH_ENABLED=true`

## Context
AUTH_ENABLED was already set to `true` in production via manual `aws lambda update-function-configuration`, but provision.sh still had `false`. Next provision run would have reverted it.

## Runtime Fix (Manual)
CLOUDFLARE_ORIGIN_SECRET must be set via AWS CLI (contains secret, cannot be in code/transcript). Command provided to user separately.
