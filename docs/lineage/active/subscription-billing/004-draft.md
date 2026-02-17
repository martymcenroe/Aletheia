# Full Billing with Stripe Integration

## User Story
As a user who has been using Aletheia on the free tier or via a promotional subscription,
I want to upgrade to a paid subscription through self-service payment,
So that I can access premium features without requiring admin intervention.

## Objective
Enable self-service subscription management via Stripe integration, allowing users to upgrade, maintain, and have subscriptions automatically adjusted based on payment status.

## UX Flow

### Scenario 1: User Upgrades to Paid Tier
1. User clicks "Upgrade" button in extension popup
2. Extension redirects to Stripe Checkout with pre-configured subscription plan
3. User completes payment in Stripe Checkout
4. Stripe sends `checkout.session.completed` webhook to Auth Lambda
5. Auth Lambda updates user's tier to paid in database
6. User returns to extension, sees updated subscription status
7. Result: User immediately has access to paid tier features

### Scenario 2: Recurring Payment Succeeds
1. Stripe automatically charges user at billing cycle (monthly)
2. Payment succeeds
3. Stripe sends `invoice.paid` webhook to Auth Lambda
4. Auth Lambda logs successful payment, no tier change needed
5. Result: User retains paid tier access

### Scenario 3: Payment Fails with Grace Period
1. Stripe attempts to charge user at billing cycle
2. Payment fails (insufficient funds, expired card, etc.)
3. Stripe sends `invoice.payment_failed` webhook to Auth Lambda
4. Auth Lambda marks user for grace period (7 days), sends warning notification
5. User sees "Payment failed - update payment method within 7 days" in extension popup
6. Result: User retains access during grace period with clear warning

### Scenario 4: Subscription Cancelled or Expired
1. Grace period expires without successful payment OR user cancels subscription
2. Stripe sends `customer.subscription.deleted` webhook to Auth Lambda
3. Auth Lambda downgrades user to free tier
4. User sees "Subscription ended - you're on the free tier" in extension popup
5. Result: User loses paid features, retains free tier access

### Scenario 5: Admin Views/Cancels Subscription
1. Admin accesses subscription management interface
2. Admin searches for user by email or user ID
3. Admin views subscription status, payment history
4. Admin cancels subscription if needed (refund handled in Stripe dashboard)
5. Result: Admin has oversight without touching Stripe dashboard for basic operations

### Scenario 6: User Updates Payment Method via Stripe Email
1. User receives payment failure email from Stripe with update link
2. User clicks link and updates card directly in Stripe customer portal
3. Stripe retries payment and sends `invoice.paid` webhook on success
4. Auth Lambda clears grace period flag, logs successful payment
5. Result: User retains paid tier, grace period cancelled

## Requirements

### Stripe Integration
1. Stripe account configured with subscription product and pricing
2. API keys stored in AWS Secrets Manager (separate keys for test/prod)
3. Webhook signing secret stored in AWS Secrets Manager
4. Test mode enabled for development/staging environments

### Auth Lambda Endpoints
1. `POST /create-checkout-session` creates Stripe Checkout session with user context
2. `POST /stripe-webhook` receives and validates Stripe webhook events
3. `GET /subscription-status` returns current user subscription state
4. Webhook endpoint validates Stripe signature before processing

### Webhook Event Handling
1. `checkout.session.completed` triggers immediate tier upgrade
2. `invoice.paid` logs successful recurring payment and clears any grace period
3. `invoice.payment_failed` initiates 7-day grace period
4. `customer.subscription.deleted` triggers downgrade to free tier
5. Unknown events logged but not processed (forward compatibility)

### Extension Integration
1. "Upgrade" button visible to free tier users in popup
2. Button opens Stripe Checkout in new tab with user's email pre-filled
3. Subscription status displayed in popup (Free / Premium / Grace Period)
4. Grace period shows days remaining and "Update Payment" link

### Admin Tooling
1. CLI command to view user subscription status
2. CLI command to list users in grace period
3. CLI command to manually adjust tier (emergency override with dry-run mode)

## Technical Approach
- **Secrets Manager:** Store Stripe API keys and webhook signing secret, retrieved at Lambda cold start
- **Auth Lambda:** Add three new endpoints using existing Lambda infrastructure
- **Stripe SDK:** Use official `stripe` Python package for API calls and webhook validation
- **DynamoDB:** Add `stripe_customer_id`, `stripe_subscription_id`, `grace_period_end` fields to user record
- **Extension Popup:** Add subscription UI component with conditional rendering based on tier
- **Idempotency:** Use Stripe event IDs to prevent duplicate webhook processing
- **Data Residency:** All data processing and storage restricted to AWS us-east-1; Stripe processes payments per their regional data handling policies

## Budget Estimate
- **AWS Infrastructure:** Estimated <$5/month additional cost (Lambda invocations for webhooks, Secrets Manager API calls, DynamoDB storage for subscription fields)
- **Stripe Fees:** 2.9% + $0.30 per successful transaction (passed to business, not infrastructure cost)
- **Cost Alert Threshold:** CloudWatch alarm if Lambda invocation costs exceed $10/month (indicates anomaly)

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [x] **Architecture:** Adds Stripe as external dependency; webhook endpoint changes Lambda routing
- [x] **Cost:** Stripe fees (2.9% + $0.30 per transaction); additional Lambda invocations for webhooks; estimated <$5/mo AWS cost
- [x] **Legal/PII:** Stripe handles payment PII; we store only Stripe customer/subscription IDs (no card data); data processed in AWS us-east-1
- [ ] **Legal/External Data:** N/A - Stripe is a contracted payment processor
- [x] **Safety:** Payment failures could incorrectly downgrade users; grace period mitigates risk

## Security Considerations
- **Webhook Validation:** All webhook requests validated using Stripe signing secret before processing
- **API Key Protection:** Keys stored in Secrets Manager, never logged, never sent to client
- **Checkout Session:** Created server-side with user context; user cannot manipulate tier selection
- **Input Sanitization:** Webhook payloads parsed by Stripe SDK; event types whitelisted
- **Idempotency:** Event ID tracked to prevent replay attacks or duplicate processing
- **HTTPS Only:** All Stripe communication over TLS; webhook endpoint requires HTTPS

## Files to Create/Modify
- `auth-lambda/stripe_handler.py` — Webhook handler and checkout session creation
- `auth-lambda/stripe_events.py` — Event type handlers (upgrade, downgrade, grace period)
- `auth-lambda/lambda_function.py` — Add routing for new endpoints
- `auth-lambda/requirements.txt` — Add `stripe` package
- `extension/popup/subscription-status.js` — Subscription UI component
- `extension/popup/popup.html` — Add subscription status section
- `extension/popup/popup.css` — Styles for subscription UI
- `infrastructure/secrets.tf` — Add Stripe secrets to Secrets Manager
- `infrastructure/api-gateway.tf` — Add webhook endpoint route
- `tools/admin_subscriptions.py` — CLI tool for subscription management (includes --dry-run mode)
- `docs/adr/NNNN-stripe-integration.md` — Architecture decision record
- `tests/fixtures/stripe_webhook_events.json` — Static webhook event fixtures for offline testing

## Dependencies
- Issue #TBD (subscription-manual) must be completed first — establishes tier system and coupon infrastructure that Stripe integration builds upon

## Out of Scope (Future)
- Multiple subscription tiers (Premium, Pro, Enterprise) — MVP has single paid tier
- Annual billing option — monthly only for MVP
- Proration for mid-cycle changes — handled by Stripe defaults
- Invoice/receipt generation — users access via Stripe customer portal
- Subscription pause functionality — cancel and re-subscribe flow only
- Usage-based billing — flat monthly rate only
- Multiple payment methods per user — Stripe handles this automatically

## Open Questions
- [x] What is the grace period duration? → Resolved: 7 days, industry standard
- [x] Should we support Stripe customer portal for self-service payment method updates? → Resolved: Yes, link to portal from extension popup
- [x] How do we handle existing promotional subscriptions when Stripe launches? → Resolved: Promotional subscriptions continue unchanged; only new upgrades go through Stripe
- [x] What happens if webhook delivery fails? → Resolved: Stripe retries automatically; implement idempotency to handle duplicates
- [x] Does the "Grace Period" logic handle card updates outside the extension? → Resolved: Yes, Stripe sends `invoice.paid` on successful retry after card update, which clears grace period

## Acceptance Criteria
- [ ] `POST /create-checkout-session` returns valid Stripe Checkout URL with 303 redirect
- [ ] `POST /stripe-webhook` returns 200 for valid signed requests, 400 for invalid signatures
- [ ] User tier changes to "premium" within 5 seconds of `checkout.session.completed` webhook
- [ ] User tier changes to "free" when `customer.subscription.deleted` webhook received
- [ ] Grace period flag set with 7-day expiration on `invoice.payment_failed` webhook
- [ ] Grace period flag cleared when `invoice.paid` webhook received during grace period
- [ ] Extension popup displays "Upgrade" button for free tier users
- [ ] Extension popup displays subscription status (Free/Premium/Grace Period) for all users
- [ ] Extension popup displays "X days remaining" during grace period
- [ ] Duplicate webhook events (same event ID) do not trigger duplicate tier changes
- [ ] Stripe API keys are retrieved from Secrets Manager, not hardcoded
- [ ] `tools/admin_subscriptions.py --status user@email.com` returns subscription details
- [ ] `tools/admin_subscriptions.py --adjust-tier user@email.com premium --dry-run` outputs planned changes without modifying database
- [ ] Webhook endpoint rejects requests without valid Stripe signature header
- [ ] Unit tests pass using `tests/fixtures/stripe_webhook_events.json` without network calls

## Definition of Done

### Implementation
- [ ] Core feature implemented
- [ ] Unit tests written and passing (using static fixtures, no network dependency)
- [ ] Integration tests with Stripe test mode passing

### Tools
- [ ] `tools/admin_subscriptions.py` created with view/list/override commands and --dry-run mode
- [ ] Document tool usage in tool docstring and README

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Update README.md with subscription feature documentation
- [ ] Create ADR for Stripe integration architecture decisions
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS (payment handling is security-critical)
- [ ] Run 0810 Privacy Audit - PASS (handles customer IDs linked to users)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes

### Offline Testing (Static Fixtures)
- Unit tests MUST use `tests/fixtures/stripe_webhook_events.json` for webhook logic validation
- Fixture file includes: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.deleted` event samples
- Tests validate event parsing, tier transitions, and idempotency without network calls

### Integration Testing (Stripe Test Mode)
- Use Stripe test mode with test API keys for all development
- Stripe CLI (`stripe listen --forward-to localhost:3000/stripe-webhook`) for local webhook testing
- Test card numbers: `4242424242424242` (success), `4000000000000341` (attach fails), `4000000000009995` (insufficient funds)
- Trigger `invoice.payment_failed` by creating subscription with `4000000000000341` test card
- Verify grace period by checking DynamoDB `grace_period_end` field after payment failure
- Test idempotency by sending same webhook event twice via Stripe CLI

## Labels
`billing`, `external-dependency`, `critical-path`

## Effort Estimate
**L** (Large) — 3-4 sessions

## Original Brief (user's ideation notes)
# Idea: Full Billing with Stripe Integration

**Status:** Active
**Effort:** High (3-4 sessions)
**Value:** High
**Blocked by:** subscription-manual (need manual subscriptions and coupon system first)

---

## Problem

After manual subscriptions ship, Aletheia needs self-service payment so users can upgrade without admin intervention. Manual tier assignment doesn't scale past early adopters and promotional campaigns.

References original Issue #2 (subscription concept).

---

## Proposal

Stripe integration for self-service subscription:
- Stripe Checkout for payment
- Webhook handler in Auth Lambda for subscription events
- Automatic tier upgrade/downgrade on payment success/failure
- Monthly billing cycle
- Graceful degradation: if payment fails, user drops to free tier after grace period

---

## Implementation

- Stripe account setup and API key management (Secrets Manager)
- `POST /create-checkout-session` endpoint in Auth Lambda
- Stripe webhook handler (`POST /stripe-webhook`) for:
  - `checkout.session.completed` → upgrade tier
  - `invoice.payment_failed` → grace period warning
  - `customer.subscription.deleted` → downgrade to free
- Extension popup: upgrade button → redirects to Stripe Checkout
- Subscription status display in extension popup
- Admin tooling: view/cancel subscriptions

---

## Next Steps

1. [ ] Run requirements workflow to generate issue
