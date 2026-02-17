# LinkedIn Follower Incentive (Coupon for Follows)

## User Story
As a free-tier Aletheia user,
I want to earn bonus requests by following ThriveTech.ai on LinkedIn,
So that I can access more features without paying while helping grow the product's reach.

## Objective
Enable users to exchange LinkedIn follows for one-time bonus request credits, creating a viral growth loop through professional network discovery.

## UX Flow

### Scenario 1: Successful Follow Verification (New User)
1. User sees "Get bonus requests: Follow us on LinkedIn" CTA in extension popup
2. User clicks CTA → LinkedIn ThriveTech.ai company page opens in new tab
3. User follows the company page on LinkedIn
4. User returns to extension and clicks "I followed"
5. Extension checks if LinkedIn account is linked
6. If not linked: OAuth popup triggers immediately to link LinkedIn account
7. After linking (or if already linked): Extension calls `/verify-follow` API endpoint
8. API verifies follow via LinkedIn Marketing API
9. System generates unique single-use coupon code for +50 bonus requests
10. Popup displays coupon code immediately with copy-to-clipboard button
11. Email with coupon code sent to user's registered email
12. Result: User applies coupon to receive 50 bonus requests

### Scenario 2: Follow Not Detected
1. User clicks "I followed" without actually following
2. Extension calls `/verify-follow` API endpoint
3. API cannot verify follow status via LinkedIn API
4. System returns verification failure
5. Popup displays: "We couldn't verify your follow. Please ensure you've followed ThriveTech.ai on LinkedIn and try again."
6. Result: No coupon issued, user can retry

### Scenario 3: User Already Claimed Follow Incentive
1. User who previously claimed follow incentive clicks "Get bonus requests"
2. Extension calls `/verify-follow` API endpoint
3. API detects existing coupon for this user_id
4. System returns existing coupon code
5. Popup displays: "You've already claimed this offer. Your coupon code is: {code}"
6. Result: Original coupon redisplayed (no duplicate generation)

### Scenario 4: LinkedIn API Unavailable
1. User clicks "I followed"
2. Extension calls `/verify-follow` API endpoint
3. LinkedIn API returns error or times out
4. System logs error and returns graceful failure
5. Popup displays: "Verification temporarily unavailable. Please try again in a few minutes."
6. Result: User prompted to retry later

## Requirements

### LinkedIn Integration
1. Integrate with LinkedIn Marketing API for organization follower verification
2. OAuth app authorized by ThriveTech.ai organization admin
3. Use `GET /organizationalEntityFollowerStatistics` endpoint to verify follower status
4. Handle LinkedIn API rate limits gracefully (100 requests/day for basic tier)
5. Personal profile follows excluded from MVP (API limitation)
6. Implement inline OAuth flow: trigger account linking when user clicks "I followed" if not already linked

### Coupon Generation
1. Generate unique single-use coupon codes tied to user_id
2. Coupon grants +50 bonus requests (one-time resource boost, not tier upgrade)
3. Store coupon in database with: code, user_id, created_at, redeemed_at, source='linkedin_follow', reward_type='bonus_requests', reward_amount=50
4. Coupon has no expiration date
5. Coupon code format: `FOLLOW-{8_RANDOM_CHARS}` (e.g., `FOLLOW-X7K9M2PQ`)
6. One follow incentive coupon per user (enforced by user_id uniqueness)

### Extension UI
1. Add "Get bonus requests: Follow us on LinkedIn" CTA to popup
2. CTA opens `https://www.linkedin.com/company/thrivetech-ai` in new tab
3. "I followed" verification button appears after CTA clicked
4. Loading state during API verification call
5. Success state shows coupon code with copy-to-clipboard button
6. Error states with clear retry guidance

### API Endpoint
1. New Lambda endpoint: `POST /verify-follow`
2. Request body: `{ "user_id": "string", "platform": "linkedin" }`
3. Response (success): `{ "verified": true, "coupon_code": "FOLLOW-X7K9M2PQ", "reward": { "type": "bonus_requests", "amount": 50 } }`
4. Response (failure): `{ "verified": false, "reason": "not_following" | "already_claimed" | "api_error" }`
5. Rate limit: 3 verification attempts per user per hour
6. Idempotency check performed at API level (mandatory for security)

### Email Notification
1. Send coupon code to user's registered email upon successful verification
2. Email template includes: coupon code, reward description (+50 bonus requests), how to redeem
3. Fail gracefully if email send fails (coupon still displayed in popup)

## Technical Approach
- **LinkedIn OAuth:** Register LinkedIn app, obtain Marketing API access, implement inline OAuth flow that triggers during verification if account not linked
- **Follower Verification:** Call LinkedIn Organizations API with ThriveTech.ai URN, check if requesting user's LinkedIn ID appears in follower list
- **User Linking:** Inline OAuth during "I followed" click if not already linked (maps LinkedIn ID to internal user_id)
- **Lambda Integration:** New `verify-follow` Lambda function in Auth service, integrates with existing coupon system from subscription-model
- **Extension Popup:** React component with conditional rendering based on verification state
- **Data Residency:** All data processed and stored in AWS US-East-1

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [x] **Architecture:** Adds LinkedIn OAuth flow and new API endpoint
- [x] **Cost:** LinkedIn API calls (limited), Lambda invocations (~$15/mo at 10k users), email sends via SES (~$1/1k emails). Estimated monthly budget: $50/mo scaling to 10k users
- [x] **Legal/PII:** LinkedIn profile data (public follows only, no scraping). User_id to LinkedIn_id mapping stored. LinkedIn access tokens stored encrypted.
- [x] **Legal/External Data:** LinkedIn API usage per LinkedIn Developer Terms of Service (compliant for follower verification). Coupon_code stored alongside user_id does not constitute a "profile" under LinkedIn's data retention policies (verified: no LinkedIn-derived data stored beyond the mapping).
- [ ] **Safety:** No data loss risk; rate limiting prevents abuse

## Security Considerations
- **OAuth Token Storage:** LinkedIn access tokens encrypted at rest in database (AWS KMS)
- **Input Sanitization:** Validate user_id format (UUID), sanitize platform parameter against allowlist (`["linkedin"]`)
- **Rate Limiting:** 3 attempts/hour/user prevents brute-force coupon farming
- **Coupon Uniqueness:** Cryptographically random 8-char suffix (alphanumeric) prevents guessing
- **API Authentication:** `/verify-follow` requires valid JWT from existing auth system
- **Idempotency:** Duplicate claim check at API level (mandatory), optional UI-level check for UX improvement

## Files to Create/Modify
- `lambda/auth/verify_follow.py` — New Lambda handler for follow verification
- `lambda/auth/linkedin_client.py` — LinkedIn Marketing API client wrapper
- `extension/src/components/FollowIncentive.tsx` — New popup component for follow CTA
- `extension/src/api/follow.ts` — API client for verify-follow endpoint
- `database/migrations/XXX_add_linkedin_coupons.sql` — Coupon table modifications for source tracking and reward_type
- `docs/wiki/linkedin-integration.md` — Integration documentation

## Dependencies
- Issue #412 (subscription-model) must be completed first — requires coupon system infrastructure with support for "bonus_requests" reward type
- LinkedIn Marketing API access must be provisioned (manual step, not issue-tracked)

## Out of Scope (Future)
- Personal profile follow verification — deferred pending LinkedIn API capabilities
- Multi-platform support (Twitter/X follows) — future growth channel
- Referral codes (user-to-user sharing) — separate viral mechanism
- Follow-back detection (if user unfollows later) — honor system for MVP
- UI-level idempotency caching — optional UX enhancement

## Open Questions
- None (all questions resolved)
- [x] Does LinkedIn API allow follower verification? → Resolved: Yes, via Organizations API for company pages; No for personal profiles
- [x] Personal follows: honor system or skip? → Resolved: Skip for MVP, company page follows only (verifiable)
- [x] LinkedIn account linking: require before "I followed" or inline OAuth? → Resolved: Inline OAuth (trigger during "I followed" if not linked to maximize conversion)
- [x] Coupon value: what tier/duration does the follow incentive provide? → Resolved: +50 bonus requests (one-time resource boost, not tier upgrade)

## Acceptance Criteria
- [ ] Extension popup displays "Get bonus requests: Follow us on LinkedIn" CTA for free-tier users
- [ ] Clicking CTA opens `https://www.linkedin.com/company/thrivetech-ai` in new browser tab
- [ ] "I followed" button appears after CTA click
- [ ] If LinkedIn account not linked, clicking "I followed" triggers OAuth popup for account linking
- [ ] After successful linking (or if already linked), extension calls `/verify-follow` API
- [ ] `/verify-follow` returns `{ "verified": true, "coupon_code": "FOLLOW-XXXXXXXX", "reward": { "type": "bonus_requests", "amount": 50 } }` when user is verified follower
- [ ] `/verify-follow` returns `{ "verified": false, "reason": "not_following" }` when user is not a follower
- [ ] `/verify-follow` returns `{ "verified": false, "reason": "already_claimed" }` when user has existing coupon
- [ ] Coupon code displayed in popup with functional copy-to-clipboard button on success
- [ ] Success message states "+50 bonus requests" as the reward
- [ ] Email containing coupon code and "+50 bonus requests" reward description sent to user's registered email within 60 seconds of verification
- [ ] Second verification request by same user returns original coupon (no duplicate generation)
- [ ] More than 3 verification attempts in 1 hour returns HTTP 429 with `Retry-After` header
- [ ] LinkedIn API failure returns `{ "verified": false, "reason": "api_error" }` and popup shows "Verification temporarily unavailable. Please try again in a few minutes."

## Definition of Done

### Implementation
- [ ] Core feature implemented (Lambda, extension component, LinkedIn client)
- [ ] Unit tests written and passing (>90% coverage for verify_follow.py)
- [ ] Integration tests for LinkedIn API mock scenarios

### Tools
- [ ] Admin CLI for manual coupon verification: `tools/verify_linkedin_coupon.py`
- [ ] Document tool usage in tools/README.md

### Documentation
- [ ] Update wiki: `docs/wiki/linkedin-integration.md` created
- [ ] Update README.md with LinkedIn follow incentive feature
- [ ] Create ADR for LinkedIn API integration decision
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS (OAuth token handling, rate limiting)
- [ ] Run 0810 Privacy Audit - PASS (LinkedIn profile data minimal, user_id mapping only, data residency: US-East-1)
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes
- **Verify follow flow:** Use LinkedIn test account that follows ThriveTech.ai page
- **Non-follower flow:** Use LinkedIn test account that does NOT follow ThriveTech.ai
- **Inline OAuth flow:** Use account without LinkedIn linked, verify OAuth popup triggers on "I followed" click
- **Rate limit testing:** Trigger 4+ verification attempts in rapid succession to confirm 429 response with Retry-After header
- **LinkedIn API failure:** Mock API timeout or 500 response to verify graceful degradation message
- **Email testing:** Use test email address, verify coupon code and "+50 bonus requests" text matches popup display
- **Idempotency testing:** Call `/verify-follow` twice for same user, confirm same coupon returned both times
- **Reward application:** Verify coupon redemption adds exactly 50 requests to user's balance
