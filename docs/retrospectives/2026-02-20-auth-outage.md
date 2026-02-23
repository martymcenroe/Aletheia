# Incident: AUTH_ENABLED=true Outage

**Date:** 2026-02-20
**Severity:** S1 Total Outage (all analysis requests failed)
**Duration:** Unknown exact window — detected same day, mitigated by reverting to AUTH_ENABLED=false

## Timeline

| Time (CT) | Event |
|-----------|-------|
| ~2026-02-20 | `AUTH_ENABLED=true` set on AletheiaAgent Lambda |
| ~2026-02-20 | All extension analysis requests begin returning 401 |
| ~2026-02-20 | Outage detected (manual observation) |
| ~2026-02-20 | `AUTH_ENABLED=false` restored, service recovered |
| 2026-02-21 00:47 | Root cause identified, issues #402–#407 filed |
| 2026-02-23 | Fix merged (PR #426, close #402) |

> **Note:** Exact times were not recorded. This is itself a lesson learned.

## Impact

- **Who:** All users — every analysis request returned 401 Unauthorized
- **Duration:** Unknown (no alerting in place)
- **Scope:** 100% of POST requests to `/` (health endpoint was exempt)

## Root Cause (5 Whys)

1. **Why** did all analysis requests return 401? — Because the Lambda required a JWT in the Authorization header and none was sent.
2. **Why** was no JWT sent? — Because none of the 6 fetch calls in the Chrome/Firefox extensions included an Authorization header.
3. **Why** were there no Authorization headers? — Because nobody wired `getJwt()` into the fetch calls — the function didn't exist.
4. **Why** didn't `getJwt()` exist? — Because `storeTokens()` silently discarded the `jwt` field from the token exchange response, so there was nothing to retrieve.
5. **Why** was AUTH_ENABLED set to true without verifying the extension sent JWTs? — Because there was no readiness checklist, no E2E auth test, and no pre-deployment verification process.

## Evidence

- `extensions/chrome/auth.js:55` — `storeTokens(accessToken, refreshToken, expiresIn, user)` had no `jwt` parameter
- `extensions/chrome/service-worker.js:462` — hardcoded headers with no Authorization
- `extensions/chrome/popup.js:691` — coupon code referenced `authState.jwt` which `getAuthState()` never returned
- All 6 fetch call sites across Chrome and Firefox had the same gap

## Action Items

| Issue | Description | Status |
|-------|-------------|--------|
| #402 | Store JWT and send Authorization headers in extension | Closed (PR #426) |
| #403 | E2E auth flow verification test | Open |
| #404 | CI: require E2E smoke test on config changes | Open |
| #405 | Auth enablement readiness checklist | Open |
| #406 | Incident retrospective template | Closed (this document) |
| #407 | Pre-deployment checklist for Lambda config changes | Closed (runbook 10903) |
| #417 | Enable AUTH_ENABLED=true (blocked on #405) | Open |

## Lessons Learned

### What went well
- Revert was quick — setting AUTH_ENABLED=false immediately restored service
- Comprehensive follow-up — 7 issues filed covering fix, testing, process

### What didn't go well
- No E2E test caught the missing headers before the config change
- No alerting — outage duration is unknown because there were no 401 alerts
- No readiness checklist — AUTH_ENABLED was toggled without verifying extension readiness
- Exact incident timeline was not recorded

### What to change
- Never enable a feature flag without an E2E test proving the full flow works (#403)
- Add CloudWatch alarm for 401 spike on AletheiaAgent
- Use the Lambda config change runbook (10903) for all future env var changes
- Track readiness gates in a checklist issue before flipping production flags (#405)
