# Idea: Tiered Rate Limiting with Multi-Window Caps

**Status:** Active
**Effort:** Medium (1-2 sessions)
**Value:** Critical
**Blocked by:** None (builds on Issue #341 token cap)

---

## Problem

The current daily token cap (Issue #341) is a flat limit — every user gets the same 20 requests/day. Before Chrome Store launch, we need:

1. **Multiple time windows** — hourly, daily, and monthly caps to prevent burst abuse while allowing sustained use
2. **User tiers** — free users get conservative limits, subscribers get higher limits, admin gets the highest (but still finite — no unlimited tier)
3. **Tier-aware enforcement** — the auth middleware must look up the user's tier and apply the correct cap set

Without this, either the cap is too generous (cost risk at scale) or too restrictive (bad UX for paying users).

---

## Proposal

### Tier Definitions

| Tier | Hourly | Daily | Monthly | Assignment |
|------|--------|-------|---------|------------|
| free | 5 | 15 | 100 | Default on signup |
| subscriber | 20 | 200 | 2,000 | Via subscription/coupon |
| admin | 50 | 500 | 10,000 | Manual (CLI tool) |

Caps are configurable in DynamoDB (not hardcoded) so they can be tuned without redeployment.

These are not rolling caps. Month starts when they first log in and that anniversery day is immutable. Day is either in their local time ( needs s future issue) or UTC (simpler).

### Multi-Window Enforcement

Each request checks three counters (hourly, daily, monthly). All three must be under their respective caps. Atomic increment on all three in a single DynamoDB transaction.


### Communication and upgrade nudge
If a user exceeds one of the caps then they get a message telling them when their cap resets (this will have to be calculated). They will be presented with a link to upgrade and that will take them to the sign-up path. There needs to be good UX to manage the pop-up window, to clear it, to bring it up again if they try again before their limit resets.

### Tier Lookup

User's tier stored in `aletheia-users` table (already exists from Issue #116). Auth middleware reads tier from JWT claims (embedded at token issuance) — no extra DynamoDB read per request.

---

## Implementation

- Extend `token_cap_service.py` with `HourlyCounter`, `DailyCounter`, `MonthlyCounter` using SK prefixes (`COUNT#HOUR#`, `COUNT#DAY#`, `COUNT#MONTH#`)
- Add tier config items to `aletheia-token-cap` table: `CONFIG#free`, `CONFIG#subscriber`, `CONFIG#admin`
- Modify `auth_middleware.py` to extract tier from JWT and pass to cap check
- Modify `lambda_auth_function.py` to embed `tier` claim in JWT at issuance
- Update `admin_token_cap.py` CLI to manage tier configs and set user tiers
- TTL on all counters (hourly: 2h, daily: 2d, monthly: 35d)

---

## Next Steps

1. [ ] Run requirements workflow to generate issue
2. [ ] LLD with DynamoDB key schema for multi-window counters
3. [ ] Implementation
