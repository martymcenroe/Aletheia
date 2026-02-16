# Implementation Report: Issue #349 — CloudFlare Migration

**Date:** 2026-02-16
**Author:** Claude Opus 4.6
**Branch:** `349-cloudflare-migration`

## Summary

Migrated API routing from CloudFront+WAF ($7/month fixed cost) to CloudFlare Free tier ($0/month). This eliminates the largest single cost at zero traffic, unblocking publication.

## Changes

### 1. Lambda Header Check (`src/lambda_function.py`)

Added client version header validation at the start of `lambda_handler`, replacing the WAF `RequireClientVersionExceptOptions` rule:

- Checks `x-aletheia-client-version` header starts with `"1."`
- Skips check for OPTIONS (CORS preflight) and direct invocations (no `requestContext`)
- Returns 403 with JSON error body on failure
- Cost: ~$0.00000025 per rejection (156M rejections within free tier)

### 2. Extension Endpoint Updates (4 files)

Updated `API_ENDPOINT` from `https://d1fkpkls2wesse.cloudfront.net/` to `https://api.aletheia.study/` in:

- `extensions/chrome/service-worker.js:6`
- `extensions/chrome/popup.js:463`
- `extensions/firefox/service-worker.js:6`
- `extensions/firefox/popup.js:377`

### 3. CloudFlare Infrastructure (configured in dashboard, not in code)

- **DNS:** CNAME `api.aletheia.study` → Lambda Function URL (proxied)
- **SSL/TLS:** Full mode
- **Worker:** `aletheia-api` — rewrites Host header for Lambda Function URL compatibility
- **Route:** `api.aletheia.study/*` → `aletheia-api` Worker
- **Rate Limiting:** 3 requests per 10 seconds per IP on POST to `/`, block for 10 seconds

## What This PR Does NOT Include

- WAF/CloudFront teardown (Step 6) — requires Lambda deployment first
- Secrets Manager migration (Step 7) — optional, separate concern
- Lambda Function URL access restriction — follow-up work
- ADR for architectural decision — follow-up work

## Testing

- All 37 Lambda handler unit tests pass
- 389/392 total unit tests pass (3 pre-existing failures in `test_verify_audits.py`)
- Live curl test through CloudFlare Worker returns full analysis response
- Integration test failure is pre-existing Docker environment issue

## Risk Assessment

- **Low risk:** CloudFront endpoint remains active as fallback until Step 6
- **No breaking change:** Extensions will use new endpoint after store update
- **Rollback:** Revert endpoint constants to CloudFront URL
