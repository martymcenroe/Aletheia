# 10218 - ADR: Multi-Window Rate Limiting with DynamoDB Atomic Counters

**Status:** Implemented
**Date:** 2026-02-17
**Categories:** Infrastructure, Security, Cost Optimization

## 1. Context

Aletheia runs on AWS Lambda with pay-per-invocation pricing. Each analysis request invokes Amazon Bedrock, which costs real money per token. Without usage limits, a single user (or attacker) could generate unbounded costs — a "denial-of-wallet" attack.

**Evolution:**
- **Issue #341 (v1):** Global daily counter — one counter for all users, resets at UTC midnight
- **Issue #364 (v2):** Per-user multi-window counters — hourly, daily, monthly per user with tiered caps

The v1 global cap solved immediate cost control but was coarse-grained. Once the subscription model was designed (Issue #366), per-user tiered limits were needed to differentiate free and paying users.

## 2. Decision

**We will use DynamoDB atomic counters with TransactWriteItems for per-user, multi-window rate limiting. Three concurrent windows (hourly, daily, monthly) are checked and incremented in a single ACID transaction. Window reset is implicit via date-based sort keys with DynamoDB TTL for automatic cleanup.**

### Key Design Choices

| Choice | Decision | Rationale |
|--------|----------|-----------|
| Counter scope | Per-user | Enables tiered pricing (free vs subscriber) |
| Window types | Hourly + Daily + Monthly | Burst protection, daily cost control, billing-cycle enforcement |
| Atomicity | TransactWriteItems (3 updates) | All-or-nothing — if any window exceeds cap, no counters increment |
| Reset mechanism | Date-based sort keys | No cron jobs, implicit reset when date changes |
| Cleanup | DynamoDB TTL | Automatic deletion of expired counters at zero cost |
| Fail mode | Hybrid | Free tier: fail-closed (503); Subscriber/Admin: fail-open (allow) |

### DynamoDB Schema

```
PK: USER#{user_id}
SK: RATE#HOURLY#{YYYY-MM-DDTHH}    → count, ttl (now + 2h)
SK: RATE#DAILY#{YYYY-MM-DD}         → count, ttl (now + 2d)
SK: RATE#MONTHLY#{YYYY-MM}          → count, ttl (now + 35d)
```

### Tier Caps

| Tier | Hourly | Daily | Monthly |
|------|--------|-------|---------|
| Free | 3 | 20 | 100 |
| Subscriber | 30 | 500 | 5,000 |
| Admin | 1,000 | 10,000 | 100,000 |

## 3. Alternatives Considered

### Option A: DynamoDB Atomic Counters (Fixed Windows) — SELECTED

**Pros:**
- Implicit reset via date-based keys (no scheduled jobs)
- TTL auto-cleanup at zero cost
- TransactWriteItems provides ACID guarantee across 3 counters
- Counter state readable for diagnostics without incrementing

**Cons:**
- Fixed windows, not sliding (user could burst at window boundary)
- TransactWriteItems limited to 100 items per transaction (no issue at 3)

### Option B: Redis/ElastiCache Sliding Window — Rejected

**Pros:**
- True sliding windows (no boundary burst)
- Sub-millisecond operations

**Cons:**
- Minimum ~$13/month for ElastiCache (cache.t3.micro)
- Additional infrastructure to manage
- Overkill for current traffic volume

### Option C: API Gateway Throttling — Rejected

**Pros:**
- Built-in, managed by AWS
- Per-key usage plans

**Cons:**
- We don't use API Gateway (direct Function URLs)
- No per-user granularity without custom authorizer
- Can't differentiate tiers

### Option D: CloudFlare Rate Limiting Only — Rejected

**Pros:**
- Already in place (3 req/10s per IP)
- Edge enforcement (before request reaches AWS)

**Cons:**
- IP-based, not user-based
- Free tier limited to 10-second windows
- Can't enforce daily or monthly caps
- Can't differentiate tiers

### Option E: Global Daily Cap (v1 — Superseded) — Replaced by v2

**Pros:**
- Simplest possible implementation
- Single counter per day

**Cons:**
- One user could exhaust cap for all users
- No tier differentiation
- No hourly burst protection
- No monthly billing-cycle alignment

## 4. Rationale

DynamoDB atomic counters are the natural fit for a serverless architecture that already uses DynamoDB. The cost is effectively zero (counter reads/writes are fraction-of-a-cent at current scale), and the operational overhead is zero (no cron jobs, no cache cluster, no additional services).

The fixed-window approach accepts a theoretical boundary-burst (user could make N requests at 23:59 and N more at 00:00) in exchange for dramatically simpler implementation. At current scale, this is acceptable. Sliding windows can be added later if needed.

The hybrid fail mode reflects business priorities: free users are less impacted by temporary denial (they can retry), while paying users should not be blocked by infrastructure issues.

## 5. Security Risk Analysis

| Risk | Impact | Likelihood | Severity | Mitigation |
|------|--------|------------|----------|------------|
| Counter bypass via direct Lambda call | High (3) | Low (1) | 3 - Low | Lambda validates CloudFlare shared secret header; direct calls rejected |
| DynamoDB throttling during traffic spike | Med (2) | Low (1) | 2 - Low | PAY_PER_REQUEST billing auto-scales; CloudWatch alarm at >100 invocations/5min |
| Transaction timeout (>2s) | Low (1) | Low (1) | 1 - Very Low | Hybrid fail mode; timeout configurable per MultiWindowCounter instance |
| Tier claim tampering in JWT | High (3) | Low (1) | 3 - Low | JWT signed with HS256; tampering invalidates signature |
| Window boundary burst | Low (1) | Med (2) | 2 - Low | Acceptable at current scale; hourly window limits burst damage |

## 6. Consequences

### Positive
- Per-user fairness — one user cannot exhaust quota for others
- Tier differentiation enables subscription pricing
- Zero operational overhead (no cron, no cache cluster)
- Billing-cycle alignment via configurable anchor day
- Counter state inspectable for admin diagnostics

### Negative
- Fixed windows allow theoretical boundary burst
- TransactWriteItems adds ~5ms latency vs simple UpdateItem
- Tier changes require re-authentication (new JWT with updated tier claim)

### Neutral
- Monthly window resets on billing anchor day, not calendar month (intentional for subscription alignment)
- Legacy global cap items remain in table but are unused (TTL will clean up)

## 7. Implementation

- **Related Issues:** #341 (global cap v1), #364 (multi-window v2), #366 (Stripe billing)
- **Related LLDs:** LLD-341 (JWT Auth & Daily Token Cap), LLD-364 (Tiered Rate Limiting)
- **Key Files:**
  - `src/auth/token_cap_service.py` — `MultiWindowCounter` class, `check_and_increment()`
  - `src/auth/tier_config_service.py` — Per-tier cap configuration
  - `src/auth/auth_middleware.py` — Rate limit check integration in `@require_auth`
  - `src/models/rate_limit.py` — `RateLimitResult`, `CounterState` types
  - `tools/admin_token_cap.py` — Admin CLI for cap management

## 8. References

- Issue #341: JWT auth + global daily cap (v1)
- Issue #364: Tiered multi-window rate limiting (v2)
- Issue #366: Stripe billing (tier differentiation driver)
- [DynamoDB TransactWriteItems](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html)
- [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-19 | Claude Opus 4.6 | Initial draft |
