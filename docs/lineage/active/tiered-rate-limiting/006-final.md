# Issue Filed

URL: https://github.com/martymcenroe/Aletheia/issues/364

---

# Tiered Rate Limiting with Multi-Window Caps

## User Story
As a product owner,
I want tiered rate limiting with hourly, daily, and monthly caps,
So that free users are constrained to sustainable limits while paying users get higher allocations, all without manual intervention.

## Objective
Implement multi-window rate limiting (hourly/daily/monthly) with three user tiers (free/subscriber/admin), each with configurable caps stored in DynamoDB and enforced via JWT-embedded tier claims.

## UX Flow

### Scenario 1: Request Within Limits
1. User makes API request with valid JWT
2. Auth middleware extracts `tier` claim from JWT
3. System checks hourly, daily, and monthly counters against tier's caps
4. All counters under limits → request proceeds
5. Counters atomically incremented in single DynamoDB transaction
6. Result: Request processed normally

### Scenario 2: Rate Limit Exceeded (Single Window)
1. User makes API request with valid JWT
2. System checks counters — hourly limit exceeded (e.g., 5/5 for free tier)
3. System calculates reset time for the exceeded window
4. Response: 429 Too Many Requests with JSON body:
   ```json
   {
     "error": "rate_limit_exceeded",
     "window": "hourly",
     "resets_at": "2026-02-16T15:00:00Z",
     "resets_in_seconds": 1847,
     "upgrade_url": "https://aletheia.app/upgrade"
   }
   ```
5. Extension displays modal with reset countdown and upgrade CTA
6. Modal includes "Dismiss" button and reappears on next blocked request

### Scenario 3: User Upgrades Tier
1. User completes subscription flow
2. Lambda issues new JWT with updated `tier: "subscriber"` claim
3. User's next request uses new JWT
4. System applies subscriber caps (20/200/2000 vs 5/15/100)
5. Existing counter values preserved — only cap limits change

### Scenario 4: Admin Sets User Tier via CLI
1. Admin runs: `poetry run python tools/admin_token_cap.py set-tier --user-id abc123 --tier admin`
2. Tool updates user record in `aletheia-users` table
3. User must re-authenticate to get new JWT with updated tier
4. Result: Next login embeds `tier: "admin"` in JWT

### Scenario 5: Anniversary-Based Monthly Reset
1. User first logs in on Feb 16
2. `billing_anchor_day` set to 16 in user record
3. Monthly counter resets on 16th of each month at 00:00 UTC
4. If anchor is 31 and month has fewer days, resets on last day of month

### Scenario 6: DynamoDB Unavailable (Fail-Safe)
1. User makes API request with valid JWT
2. DynamoDB is unreachable, throttled, or times out (>2s)
3. System logs error with correlation ID and increments `rate_limit_db_failures` CloudWatch metric
4. System applies **Fail Open** strategy: request proceeds without counter increment
5. Result: Request processed; counter state potentially stale until DynamoDB recovers
6. Alert triggers if failure rate exceeds 1% over 5-minute window

## Requirements

### Rate Limiting Logic
1. Three time windows: hourly, daily, monthly (non-rolling)
2. All three counters checked per request; ALL must be under cap
3. Atomic increment of all three counters in single DynamoDB transaction
4. Hourly window: top of hour to top of hour (UTC)
5. Daily window: midnight to midnight (UTC)
6. Monthly window: anniversary day to anniversary day (UTC)

### Fail-Safe Strategy
1. **Strategy: Fail Open** — if DynamoDB is unreachable, throttled, or times out (>2s), allow the request
2. Log all failures with correlation ID to CloudWatch Logs
3. Increment `rate_limit_db_failures` CloudWatch metric on each failure
4. CloudWatch Alarm triggers if failure rate >1% over 5-minute window
5. Rationale: Availability prioritized over strict enforcement; transient DB issues should not block paying users

### Tier Definitions
1. Three tiers: `free`, `subscriber`, `admin`
2. Default tier on signup: `free`
3. Tier caps configurable in DynamoDB (not hardcoded)
4. Initial caps:
   - **free:** 5 hourly / 15 daily / 100 monthly
   - **subscriber:** 20 hourly / 200 daily / 2,000 monthly
   - **admin:** 50 hourly / 500 daily / 10,000 monthly

### Tier Management
1. Tier stored in `aletheia-users` table on user record
2. Tier embedded in JWT at token issuance (no per-request DynamoDB read)
3. Admin CLI tool can set any user's tier
4. Tier change requires re-authentication to take effect

### Counter Storage
1. Counters stored in `aletheia-token-cap` table
2. SK prefixes: `COUNT#HOUR#`, `COUNT#DAY#`, `COUNT#MONTH#`
3. TTL on counters: hourly=2h, daily=2d, monthly=35d
4. Counter key includes timestamp component for window identification

### Error Response & UX
1. 429 response includes: exceeded window, reset timestamp, upgrade URL
2. Extension modal displays: reset countdown, upgrade CTA, dismiss button
3. Modal reappears on subsequent blocked requests (not auto-dismissed)
4. Upgrade URL routes to subscription flow

### Configuration Management
1. Tier configs stored as: `PK=CONFIG, SK=TIER#free|subscriber|admin`
2. Config items include: `hourly_cap`, `daily_cap`, `monthly_cap`
3. Admin CLI can read/update tier configurations
4. Config changes apply immediately to subsequent requests

## Technical Approach
- **Counter Service:** Extend `token_cap_service.py` with `MultiWindowCounter` class managing three window types
- **DynamoDB Schema:** Use composite SK with window type and timestamp (`COUNT#HOUR#2026-02-16T14` / `COUNT#DAY#2026-02-16` / `COUNT#MONTH#2026-02`)
- **JWT Enhancement:** Add `tier` claim in `lambda_auth_function.py` during token issuance
- **Middleware Update:** `auth_middleware.py` extracts tier, fetches tier config, enforces all three caps
- **CLI Extension:** `admin_token_cap.py` gains `set-tier`, `get-tier`, `config-tier` subcommands
- **Transactional Writes:** Use DynamoDB `TransactWriteItems` for atomic three-counter increment
- **Fail-Safe Implementation:** Wrap transactional write in try/except with 2s timeout; on failure, log + allow request

## Cost Estimate

### DynamoDB WCU Consumption
- **TransactWriteItems** consumes 2x WCUs per item (6 WCUs total per request: 3 items × 2 WCUs)
- **Standard writes** would consume 3 WCUs per request (1 per item)
- **Overhead:** 2x compared to non-transactional approach

### Projected Monthly Cost (On-Demand Pricing)
| Traffic Volume | Requests/Month | Transactional WCUs | WCU Cost (@$1.25/million) | Config Reads (RCUs) | Total DynamoDB |
|----------------|----------------|--------------------|-----------------------------|---------------------|----------------|
| MVP Launch | 10,000 | 60,000 | $0.08 | ~$0.01 | **$0.09** |
| Growth (1K users) | 100,000 | 600,000 | $0.75 | ~$0.05 | **$0.80** |
| Scale (10K users) | 1,000,000 | 6,000,000 | $7.50 | ~$0.50 | **$8.00** |

### Budget Fit
- Current infrastructure budget: $50/month DynamoDB allocation
- At 10K users (1M requests/month): $8.00 = 16% of budget ✅
- Breakeven vs provisioned capacity: ~5M requests/month

## Risk Checklist

- [x] **Architecture:** Extends existing token cap system with new counter types and tier config items. No new tables required.
- [x] **Cost:** See Cost Estimate section. Transactional writes consume 2x WCUs (6 WCUs/request vs 3 for standard). At projected volumes, remains well under $50/month DynamoDB budget.
- [ ] **Legal/PII:** No new PII handling — tier is not PII.
- [ ] **Legal/External Data:** No external data sources.
- [x] **Safety:** Fail-safe strategy defined (Fail Open). Counter corruption mitigated by TTL auto-cleanup and admin override CLI.

## Security Considerations
- **JWT Integrity:** Tier claim is signed in JWT; cannot be tampered without invalidating signature
- **Admin CLI Access:** `set-tier` requires valid AWS credentials with DynamoDB write permissions
- **Input Validation:** Tier values validated against enum (`free`/`subscriber`/`admin`) — reject unknown tiers
- **Rate Limit Bypass:** No code path allows skipping rate limit check for authenticated requests

## Files to Create/Modify
- `aletheia/services/token_cap_service.py` — Add `MultiWindowCounter`, tier config loading, transactional increment
- `aletheia/middleware/auth_middleware.py` — Extract tier from JWT, pass to rate limit check
- `aletheia/lambda/lambda_auth_function.py` — Embed `tier` claim in JWT at issuance
- `tools/admin_token_cap.py` — Add `set-tier`, `get-tier`, `config-tier` subcommands
- `aletheia/models/user.py` — Add `tier` and `billing_anchor_day` fields
- `extension/src/components/RateLimitModal.tsx` — New component for upgrade nudge UX
- `extension/src/api/client.ts` — Handle 429 responses, trigger modal
- `tests/unit/test_multi_window_counter.py` — Unit tests for counter logic
- `tests/integration/test_tiered_rate_limiting.py` — Integration tests for full flow
- `tests/fixtures/rate_limit_429_response.json` — Static fixture for frontend development

## Dependencies
- Issue #341 must be completed first (base token cap infrastructure)
- Issue #116 must be completed first (user table schema)

## Out of Scope (Future)
- **Local timezone support** — deferred; MVP uses UTC only
- **Rolling window caps** — deferred; MVP uses fixed windows
- **Soft limits with warnings** — deferred; MVP is hard cutoff only
- **Per-endpoint rate limits** — deferred; MVP is global per-user
- **Usage dashboard** — deferred to separate issue
- **Webhook notifications** — deferred; no alerts when approaching limits

## Open Questions
- None (all questions resolved)
- [x] Rolling vs fixed windows? → Resolved: Fixed windows for MVP simplicity
- [x] How to handle tier embedded in JWT when tier changes? → Resolved: User must re-auth to get new JWT
- [x] What happens to counters when tier changes? → Resolved: Counters preserved, only cap limits change
- [x] UTC or local time? → Resolved: UTC for MVP, local time deferred to future issue
- [x] Fail Open vs Fail Closed? → Resolved: Fail Open to prioritize availability; paying users should not be blocked by transient DB issues

## Acceptance Criteria
- [ ] Request with all three counters under caps returns 200 and increments all three counters
- [ ] Request with hourly counter at cap returns 429 with `"window": "hourly"` and `resets_at` within 60 minutes
- [ ] Request with daily counter at cap returns 429 with `"window": "daily"` and `resets_at` within 24 hours
- [ ] Request with monthly counter at cap returns 429 with `"window": "monthly"` and `resets_at` on anniversary day
- [ ] Free tier user hitting 5th hourly request succeeds; 6th returns 429
- [ ] Subscriber tier user hitting 20th hourly request succeeds; 21st returns 429
- [ ] JWT issued for free user contains `"tier": "free"` claim
- [ ] JWT issued for subscriber contains `"tier": "subscriber"` claim
- [ ] `admin_token_cap.py set-tier --user-id X --tier admin` updates user record with `tier: "admin"`
- [ ] `admin_token_cap.py config-tier --tier free --hourly 10` updates free tier hourly cap to 10
- [ ] Counter items have TTL attribute set (hourly: 7200s, daily: 172800s, monthly: 3024000s)
- [ ] Extension displays modal with reset countdown when 429 received
- [ ] Modal includes working "Upgrade" button linking to subscription flow
- [ ] Modal includes "Dismiss" button that closes modal
- [ ] Dismissed modal reappears on next 429 response
- [ ] Transactional write fails atomically if any counter increment would exceed DynamoDB limits
- [ ] Monthly counter resets on user's `billing_anchor_day` (defaults to signup day-of-month)
- [ ] When DynamoDB is unreachable (timeout >2s), request proceeds with 200 status
- [ ] DynamoDB failure logs include correlation ID and increments `rate_limit_db_failures` metric
- [ ] Static fixture `tests/fixtures/rate_limit_429_response.json` exists with valid 429 response body

## Reviewer Suggestions

*Non-blocking recommendations from the reviewer.*

- **Observability:** Consider adding a CloudWatch Dashboard definition to the "Files to Create" or a separate task to visualize the `rate_limit_db_failures` metric, as fail-open errors might otherwise go unnoticed.
- **Client Handling:** In `extension/src/api/client.ts`, ensure the `Retry-After` header is respected if the browser/client logic attempts automatic retries, to prevent exacerbating the rate limit.

## Definition of Done

### Implementation
- [ ] Core feature implemented
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing

### Tools
- [ ] `admin_token_cap.py` extended with tier management subcommands
- [ ] Document tool usage in `tools/README.md`

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Update README.md if user-facing
- [ ] Update relevant ADRs or create new ones
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0810 Privacy Audit - PASS
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes
- **Force hourly limit:** Set free tier hourly cap to 1 via CLI, make 2 requests
- **Force daily limit:** Set free tier daily cap to 1 via CLI, make 2 requests
- **Force monthly limit:** Set free tier monthly cap to 1 via CLI, make 2 requests
- **Test tier change:** Login as free, set tier to subscriber via CLI, verify old JWT still uses free limits until re-auth
- **Test anniversary reset:** Create user with `billing_anchor_day` in past, verify monthly counter reset
- **Test atomic failure:** Simulate DynamoDB error during transaction, verify no partial counter increments
- **Test modal UX:** Use browser devtools to return mock 429, verify modal appears with correct countdown
- **Test fail-safe:** Use LocalStack to simulate DynamoDB timeout, verify request proceeds with 200 and metric incremented
- **Test static fixture:** Load `tests/fixtures/rate_limit_429_response.json` in extension dev mode, verify modal renders correctly
- **Load test (recommended):** Run 100 concurrent requests against same user to verify transactional contention handling

## Labels
`governance`, `scaling`, `rate-limiting`, `mvp`
