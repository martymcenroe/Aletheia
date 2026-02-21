# Idea: Manual Subscriptions with Coupon Codes (MVP)

**Status:** Active
**Effort:** Medium (2-3 sessions)
**Value:** Critical
**Blocked by:** tiered-rate-limiting (need tiers before subscriptions upgrade them)

---

## Problem

Aletheia needs a monetization path before public launch. The analysis costs real money (Bedrock API calls), and free-tier-only is unsustainable. We need:

1. A way for users to upgrade from free to subscriber tier
2. Coupon codes for promotional distribution (launch, LinkedIn follows, partnerships)
3. Email collection — LinkedIn OAuth doesn't reliably provide email, but we need it for receipts, coupon delivery, and account communication

References original Issue #2 (subscription concept).

---

## Proposal

Admin assigns subscription tier to users via CLI tool. No payment processing — just tier assignment in DynamoDB. Useful for:
- Beta testers
- Coupon code redemptions
- Manual comp accounts

**Coupon system:**
- Admin generates codes: `poetry run python tools/admin_coupons.py generate --tier subscriber --count 10 --expires 30d`
- Codes stored in DynamoDB with: code, tier, expiry, max_uses, current_uses
- User redeems in extension popup → API validates, upgrades tier, marks code used
- Single-use and multi-use codes supported

**Email collection:**
- Add optional email field to extension popup profile section
- Store in `aletheia-users` table (encrypted at rest via DynamoDB default)
- Not collected via LinkedIn (unreliable) — user enters manually
- Required for coupon delivery and subscription receipts
- Privacy policy update needed

---

## Implementation

- DynamoDB: `aletheia-coupons` table (PK: code, attributes: tier, expiry, max_uses, uses, created_by)
- `tools/admin_coupons.py` — CLI for generate, list, revoke
- API endpoint in Auth Lambda: `POST /redeem-coupon` (validates code, upgrades user tier)
- Extension popup: email input field, coupon redemption UI
- Privacy policy update for email collection

---

## Next Steps

1. [ ] Run requirements workflow to generate issue
