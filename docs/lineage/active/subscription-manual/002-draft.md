# Manual Subscriptions with Coupon Codes (MVP)

## User Story
As an Aletheia administrator,
I want to assign subscription tiers to users via coupon codes,
So that I can monetize the service and distribute promotional access before implementing full payment processing.

## Objective
Enable manual tier upgrades through admin-generated coupon codes that users redeem in the extension, with email collection for account communication.

## UX Flow

### Scenario 1: Admin Generates Coupon Codes
1. Admin runs `poetry run python tools/admin_coupons.py generate --tier subscriber --count 10 --expires 30d`
2. System generates 10 unique codes with 30-day expiry
3. System outputs codes to stdout in copy-paste format
4. Result: Codes are stored in DynamoDB and ready for distribution

### Scenario 2: User Redeems Valid Coupon Code
1. User opens extension popup and navigates to profile section
2. User enters coupon code in redemption field
3. User clicks "Redeem"
4. System validates code (exists, not expired, uses remaining)
5. System upgrades user tier from free to subscriber
6. System increments code usage count
7. Result: User sees "Success! You're now a subscriber" and UI reflects new tier

### Scenario 3: User Redeems Invalid/Expired Code
1. User enters coupon code in redemption field
2. User clicks "Redeem"
3. System validates code and finds it invalid (expired, exhausted, or non-existent)
4. Result: User sees specific error message: "Code expired", "Code already used", or "Invalid code"

### Scenario 4: User Provides Email Address
1. User opens extension popup profile section
2. User enters email address in optional email field
3. User clicks "Save"
4. System validates email format
5. System stores encrypted email in user record
6. Result: User sees "Email saved" confirmation

### Scenario 5: Admin Lists and Revokes Codes
1. Admin runs `poetry run python tools/admin_coupons.py list --active`
2. System displays all active codes with usage stats
3. Admin runs `poetry run python tools/admin_coupons.py revoke --code PROMO2026`
4. System marks code as revoked
5. Result: Code can no longer be redeemed

## Requirements

### Coupon Management
1. Admin CLI tool generates cryptographically random coupon codes (16 alphanumeric characters)
2. Codes support configurable expiry (days from creation)
3. Codes support single-use (max_uses=1) or multi-use (max_uses=N)
4. Codes are tied to a specific tier (subscriber, premium, etc.)
5. Admin can list codes filtered by status (active, expired, exhausted, revoked)
6. Admin can revoke codes before expiry

### Coupon Redemption
1. API endpoint validates code exists in DynamoDB
2. API endpoint validates code is not expired (current_time < expiry)
3. API endpoint validates code has uses remaining (uses < max_uses)
4. API endpoint validates code is not revoked
5. Successful redemption upgrades user tier atomically with usage increment
6. Redemption returns specific error messages for each failure mode

### Email Collection
1. Extension popup includes optional email input field in profile section
2. Email is validated client-side for format before submission
3. Email is stored in aletheia-users table, encrypted at rest (DynamoDB default encryption)
4. User can update or remove their email at any time
5. Privacy policy must be updated before this feature ships

### DynamoDB Schema
1. New table `aletheia-coupons` with partition key `code` (String)
2. Attributes: tier (String), expiry (Number/epoch), max_uses (Number), uses (Number), created_by (String), created_at (Number/epoch), revoked (Boolean)
3. GSI on `created_by` for admin auditing

## Technical Approach
- **DynamoDB:** New `aletheia-coupons` table with atomic counter updates for `uses` field via UpdateExpression
- **Admin CLI:** Python tool using boto3 with assumed admin role, outputs codes as JSON or plain text
- **Auth Lambda:** New `/redeem-coupon` POST endpoint, uses conditional writes to prevent race conditions
- **Extension Popup:** New React components for email input and coupon redemption in profile section
- **Code Generation:** `secrets.token_urlsafe(12)` truncated to 16 chars, uppercase for readability

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [x] **Architecture:** Adds new DynamoDB table and API endpoint; extends existing auth infrastructure
- [x] **Cost:** DynamoDB read/write costs negligible; no new API provider costs
- [x] **Legal/PII:** Collects user email addresses; requires privacy policy update before shipping
- [ ] **Legal/External Data:** N/A — no external data fetching
- [ ] **Safety:** No data loss risk; tier upgrades are additive

## Security Considerations
- **Input Sanitization:** Coupon codes validated as alphanumeric only (16 chars max); email validated via RFC 5322 regex
- **Rate Limiting:** Redemption endpoint rate-limited to 5 attempts per minute per user to prevent brute force
- **Access Control:** Admin CLI requires AWS credentials with explicit `aletheia-admin` IAM policy; API endpoint requires valid user JWT
- **Atomic Operations:** DynamoDB conditional writes prevent race conditions on multi-use codes

## Files to Create/Modify
- `tools/admin_coupons.py` — CLI for generate, list, revoke operations
- `lambda/auth/coupon_handler.py` — Redemption endpoint logic
- `lambda/auth/serverless.yml` — Add `/redeem-coupon` route
- `terraform/dynamodb.tf` — Add aletheia-coupons table definition
- `extension/src/components/Profile/CouponRedemption.tsx` — Redemption UI component
- `extension/src/components/Profile/EmailInput.tsx` — Email collection component
- `extension/src/api/coupon.ts` — API client for redemption
- `docs/privacy-policy.md` — Update with email collection disclosure

## Dependencies
- Depends on tiered-rate-limiting issue (need tiers defined before subscriptions can upgrade to them)
- None other — builds on existing auth infrastructure

## Out of Scope (Future)
- Payment processing (Stripe integration) — deferred to future issue
- Automated coupon delivery via email — deferred until email system established
- Referral codes that credit existing users — future enhancement
- Subscription expiry and renewal — future issue
- Email verification workflow — deferred to future issue

## Open Questions
- None (all questions resolved)
- [x] Should codes be case-sensitive? → Resolved: No, convert to uppercase on input for UX
- [x] Should we track which user redeemed each code? → Resolved: Yes, add `redeemed_by` array attribute for audit trail
- [x] Email required or optional? → Resolved: Optional for MVP, may require for certain features later

## Acceptance Criteria
- [ ] `poetry run python tools/admin_coupons.py generate --tier subscriber --count 5 --expires 30d` outputs 5 unique 16-character alphanumeric codes
- [ ] Generated codes appear in DynamoDB `aletheia-coupons` table with correct attributes
- [ ] `POST /redeem-coupon` with valid code and authenticated user returns `{"success": true, "tier": "subscriber"}`
- [ ] `POST /redeem-coupon` with expired code returns `{"error": "code_expired", "message": "This code has expired"}`
- [ ] `POST /redeem-coupon` with exhausted code returns `{"error": "code_exhausted", "message": "This code has reached its usage limit"}`
- [ ] `POST /redeem-coupon` with non-existent code returns `{"error": "invalid_code", "message": "Invalid coupon code"}`
- [ ] User tier in `aletheia-users` table updates to redeemed tier after successful redemption
- [ ] Code `uses` counter increments by 1 after successful redemption
- [ ] Extension popup displays email input field in profile section
- [ ] Submitting valid email format stores email in user's DynamoDB record
- [ ] Submitting invalid email format shows client-side validation error before API call
- [ ] `poetry run python tools/admin_coupons.py list --active` displays all non-expired, non-revoked codes
- [ ] `poetry run python tools/admin_coupons.py revoke --code TESTCODE` sets revoked=true and code cannot be redeemed

## Definition of Done

### Implementation
- [ ] Core feature implemented
- [ ] Unit tests written and passing

### Tools
- [ ] `tools/admin_coupons.py` created with generate, list, revoke subcommands
- [ ] Document tool usage in tool docstring and --help output

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Update README.md if user-facing
- [ ] Update privacy policy with email collection disclosure
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS (coupon validation, rate limiting)
- [ ] Run 0810 Privacy Audit - PASS (email collection, PII handling)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes
- **Generate exhausted code:** Create code with `--max-uses 1`, redeem once, attempt second redemption
- **Test expiry:** Create code with `--expires 0d` (immediate expiry), attempt redemption
- **Test revocation:** Generate code, revoke it, attempt redemption
- **Race condition test:** Concurrent redemption attempts on single-use code should result in exactly one success
- **Email validation:** Test with `invalid`, `@nodomain`, `valid@test.com` inputs
