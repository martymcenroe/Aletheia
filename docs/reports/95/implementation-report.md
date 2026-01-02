# 95 - Implementation Report: Security Hardening via CloudFront + WAF

## 1. Metadata

| Field | Value |
|-------|-------|
| **Issue** | #95 |
| **LLD** | `docs/1095-security-hardening.md` |
| **Test Report** | `docs/reports/95/test-report.md` |
| **Implementer** | Claude Opus 4.5 via Claude Code |
| **Date** | 2026-01-01 |
| **PR** | #136 |

## 2. Summary

Implemented CloudFront + AWS WAF protection layer in front of the Lambda Function URL. The WAF enforces header validation (requests must include `X-Aletheia-Client-Version: 1.*`) and rate limiting (10 req/10min dev, 100 req/5min prod). The Chrome extension was updated to route through CloudFront and include the required header.

Key components:
- `tools/aws/waf-setup.sh` - Infrastructure deployment script
- `tests/infra/verify_waf.sh` - Shell-based automated verification
- `tests/e2e/waf-integration.spec.js` - Playwright E2E tests
- Updated `extension/service-worker.js` with CloudFront URL and header

## 3. Files Created

| File | Description |
|------|-------------|
| `tools/aws/waf-setup.sh` | Creates CloudFront distribution + WAF Web ACL with header validation and rate limiting |
| `tests/infra/verify_waf.sh` | Automated shell script testing WAF behavior (4 tests) |
| `tests/e2e/waf-integration.spec.js` | Playwright E2E tests for WAF integration (4 tests) |
| `package.json` | Node.js project config for Playwright |
| `playwright.config.js` | Playwright test configuration |

## 4. Files Modified

| File | Changes | Description |
|------|---------|-------------|
| `extension/service-worker.js` | +8/-3 lines | Added CloudFront URL, CLIENT_VERSION constant, WAF header |
| `docs/1095-security-hardening.md` | +25 lines | Added CORS documentation for OPTIONS preflight |
| `.gitignore` | +3 lines | Added Playwright artifacts (playwright-report/, test-results/) |

## 5. Deviations from LLD

| Deviation | Reason | Impact |
|-----------|--------|--------|
| WAF rule allows OPTIONS method through | CORS preflight: browsers send OPTIONS before POST with custom headers | Required for extension to work |
| Added Playwright E2E tests | User requested automation of manual Scenario 040 | Better test coverage |
| Extension uses `text` field (not `word`) | Lambda API expects `text` - mismatch was causing 400 errors | Fixed API compatibility |
| Base64 encoding for WAF SearchString | AWS WAF API requires base64 for ByteMatchStatement | "1." = "MS4=", "OPTIONS" = "T1BUSU9OUw==" |
| Windows Git Bash compatibility | TMPDIR and file:// paths don't work on Windows | Used $HOME/tmp and cygpath |

## 6. Test Harness

- **Shell Tests:** `tests/infra/verify_waf.sh`
  - Uses curl to test WAF behavior directly
  - Supports `--test-rate-limit` for rate limit testing
  - Colored output with pass/fail summary

- **Playwright Tests:** `tests/e2e/waf-integration.spec.js`
  - Uses Playwright's `request` fixture (Node.js, no CORS issues)
  - 4 tests matching LLD scenarios

- **Test data:** Standard JSON payload with text, url, title, context fields

## 7. Test Coverage

| Area | Coverage | Notes |
|------|----------|-------|
| Header validation (missing) | Covered | Test 010/030 |
| Header validation (valid) | Covered | Test 020 |
| Header validation (invalid version) | Covered | Test 050/040 |
| Future version compatibility | Covered | Test 051/050 |
| Rate limiting | Partial | Shell script only (slow, optional) |
| CORS preflight | Covered | OPTIONS requests pass through |
| Manual extension test | Covered | User verified success overlay |

**Willison Protocol Compliance:**
- [x] Automated tests written
- [x] Tests fail on revert (verified via shell script and Playwright)
- [x] Proof captured in Test Report

## 8. Lessons Learned

1. **CORS preflight requires OPTIONS passthrough**: Browsers send OPTIONS before POST with custom headers. WAF rules must allow OPTIONS through or the extension will fail with CORS errors.

2. **AWS WAF SearchString requires base64**: When using ByteMatchStatement in WAF rules, the SearchString must be base64 encoded in the JSON API.

3. **Windows Git Bash path compatibility**: AWS CLI `file://` references don't work with Git Bash paths like `/c/Users/...`. Use `cygpath -w` to convert to Windows paths.

4. **Lambda API field names matter**: Extension was sending `word` but Lambda expects `text`. Always verify payload field names match the API.

5. **Playwright's `request` fixture bypasses CORS**: Using `page.evaluate()` with fetch from `about:blank` fails due to null origin. Use Playwright's `request` fixture instead.

## 9. Open Issues

| Issue | Type | Description |
|-------|------|-------------|
| N/A | Note | Rate limiting not tested in E2E (too slow for CI) |

## 10. Orchestrator Review Notes

**Reviewer:** Marty (Orchestrator)
**Date:** 2026-01-01

### In-Scope Observations
- CORS issue caught and fixed during testing
- Field name mismatch (`word` vs `text`) caught and fixed

### New-Scope Observations
- None

### Meta Observations
- LLD template should include CORS considerations for browser-to-API features

### Approval
- [x] Code reviewed
- [x] Manual tests passed (see Test Report)
- [x] Ready for merge
