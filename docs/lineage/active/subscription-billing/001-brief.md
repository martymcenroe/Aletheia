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
