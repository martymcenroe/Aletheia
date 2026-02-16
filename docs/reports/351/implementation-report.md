# Implementation Report: Issue #351 — Shared Secret Header

**Date:** 2026-02-16
**Author:** Claude Opus 4.6
**Branch:** `351-shared-secret-header`

## Summary

Lock the Lambda Function URL to CloudFlare-only access using a shared secret header. The secret exists only in SSM Parameter Store and CloudFlare Worker encrypted env var — never in source code.

## Changes

### 1. Lambda Handler (`src/lambda_function.py`)

Added origin secret check before the existing client version check:

- Reads `CLOUDFLARE_ORIGIN_SECRET` from environment variable
- Compares against `x-origin-secret` request header
- Returns 403 "Forbidden" on mismatch (generic error — doesn't leak info)
- Gracefully skips when env var is not set (tests, dev, rollback)

### 2. Provisioning Script (`provision.sh`)

- Reads secret from SSM Parameter Store: `/aletheia/cloudflare-origin-secret`
- Passes as `CLOUDFLARE_ORIGIN_SECRET` env var to Lambda on create and update
- Gracefully handles missing parameter (empty string → check disabled)

### 3. CloudFlare Worker (dashboard, not in code)

- `ORIGIN_SECRET` encrypted env var added
- Worker injects `X-Origin-Secret` header into every proxied request
- Secret never transmitted to or from the browser

### 4. SSM Parameter Store

- Parameter: `/aletheia/cloudflare-origin-secret`
- Type: SecureString (encrypted at rest with AWS-managed KMS key)
- Cost: $0 (Standard tier, free)

## Security Properties

| Property | Status |
|----------|--------|
| Secret in git? | No |
| Secret in extension code? | No |
| Secret in browser requests? | No |
| Secret at rest encrypted? | Yes (SSM SecureString + CloudFlare encrypted var) |
| Rotation requires downtime? | No (update SSM + CloudFlare env var) |
| Graceful degradation? | Yes (missing env var → check disabled) |

## Testing

- 37/37 Lambda handler unit tests pass
- Secret check skipped in tests (no env var set) — correct behavior
- CloudFlare route returns 200 (Worker injects secret)
- Direct Lambda returns 200 (pre-deploy, check not yet active)
- Post-deploy: direct access will return 403
