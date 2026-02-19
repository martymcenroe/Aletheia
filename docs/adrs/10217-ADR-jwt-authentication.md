# 10217 - ADR: JWT Authentication Architecture

**Status:** Implemented
**Date:** 2026-02-17
**Categories:** Security, Authentication, Infrastructure

## 1. Context

Aletheia needed an authentication mechanism for the Chrome extension to verify user identity on each API request. The extension uses LinkedIn OAuth for sign-in (Issue #116), but validating the LinkedIn token on every request would add network latency and create a dependency on LinkedIn's availability.

**Requirements:**
- Sub-10ms auth validation latency per request
- No external network call per request (LinkedIn API is ~200ms)
- Support for secret rotation without downtime
- Cost-effective at low traffic volumes
- Fail-closed security model

The system needed to bridge LinkedIn OAuth (used once at sign-in) with per-request authentication for the analysis Lambda.

## 2. Decision

**We will use JWT (JSON Web Tokens) with HS256 symmetric signing, secrets stored in AWS Secrets Manager with 5-minute caching, and dual-secret validation for zero-downtime key rotation.**

### Token Structure

```json
{
  "user_id": "linkedin_sub_claim",
  "tier": "free|subscriber|admin",
  "billing_anchor_day": 1,
  "exp": 1739900000,
  "iat": 1739813600,
  "jti": "uuid-for-future-revocation"
}
```

### Validation Flow

1. Extract `Authorization: Bearer <token>` header
2. Retrieve signing secret from Secrets Manager (cached 5 minutes)
3. Validate signature with primary secret
4. If signature fails AND secondary secret exists, try secondary (rotation window)
5. Check expiration with 5-minute leeway for clock skew
6. Require claims: `exp`, `iat`, `jti`, `user_id`
7. Return structured `AuthResult` to caller

## 3. Alternatives Considered

### Option A: JWT with Local Validation (HS256) — SELECTED

**Pros:**
- Sub-10ms validation (local symmetric crypto, no network call)
- Simple secret management (single string in Secrets Manager)
- 5-minute cache reduces Secrets Manager calls to ~1 per 300 seconds
- Dual-secret supports zero-downtime rotation

**Cons:**
- Same key signs and verifies (symmetric) — acceptable since both operations happen in Lambda
- No token revocation until expiration (mitigated by 24h lifetime + `jti` for future revocation list)

### Option B: API Gateway Authorizer Lambda — Rejected

**Pros:**
- AWS-managed auth layer
- Built-in caching

**Cons:**
- Extra Lambda invocation per request (~$0.20/million + latency)
- More complex deployment topology
- We don't use API Gateway (direct Function URLs via CloudFlare)

### Option C: Session Tokens in DynamoDB — Rejected

**Pros:**
- Easy revocation (delete token from table)
- Simple implementation

**Cons:**
- DynamoDB read per request (~20ms latency)
- Higher cost at scale ($0.25 per million reads)
- No offline validation capability

### Option D: RS256 (Asymmetric JWT) — Rejected

**Pros:**
- Public key can be distributed (not needed — single validator)
- Stronger cryptographic guarantees

**Cons:**
- Slower validation than HS256
- Key pair management complexity (rotation requires coordinating public/private keys)
- Overkill for monolithic auth (same Lambda issues and validates)

## 4. Rationale

HS256 with Secrets Manager caching gives the best performance-to-complexity ratio:

| Metric | HS256 + Cache | API Gateway | DynamoDB Sessions |
|--------|--------------|-------------|-------------------|
| Validation latency | <1ms (cached) | ~50ms | ~20ms |
| Cost per million requests | ~$0.005 | ~$0.20 | ~$0.25 |
| Secret rotation | Dual-secret (zero downtime) | Redeploy authorizer | N/A |
| Token revocation | At expiration (24h) | At expiration | Immediate |

The 24-hour token lifetime balances security (short-lived) with user experience (no frequent re-auth). The `jti` claim enables future token revocation lists if needed.

## 5. Security Risk Analysis

| Risk | Impact | Likelihood | Severity | Mitigation |
|------|--------|------------|----------|------------|
| JWT secret leaked | High (3) | Low (1) | 3 - Low | Secrets Manager encryption at rest, no secret in code/env vars, rotation capability |
| Token replay | Med (2) | Med (2) | 4 - Moderate | 24h expiration, future `jti` revocation list, HTTPS-only transport |
| Clock skew rejection | Low (1) | Med (2) | 2 - Low | 5-minute leeway on expiration validation |
| Secrets Manager outage | High (3) | Low (1) | 3 - Low | 5-minute cache means outage must exceed cache TTL; fail-closed prevents unauthorized access |
| Brute-force secret guessing | High (3) | Very Low (0) | 0 - None | 256-bit secret, rate limiting at CloudFlare edge |

**Residual Risk:** A compromised Lambda environment could expose the cached secret. Mitigated by: Lambda execution isolation, IAM scoping to single secret, 90-day planned rotation schedule.

## 6. Consequences

### Positive
- Sub-millisecond auth validation (cached secret path)
- Zero-downtime secret rotation via dual-secret support
- Minimal cost (~$0.73/month for Secrets Manager + DynamoDB reads)
- Tier and billing info embedded in token, reducing DynamoDB reads for rate limiting

### Negative
- No immediate token revocation (must wait up to 24h or deploy revocation list)
- Symmetric key means compromise of Lambda compromises signing capability

### Neutral
- PyJWT library added to Lambda layer (~200KB)
- 5-minute cache TTL means secret rotation takes up to 5 minutes to propagate

## 7. Implementation

- **Related Issues:** #341 (JWT auth), #362 (auth infrastructure), #364 (tiered rate limiting)
- **Related LLDs:** LLD-341 (JWT Authentication & Daily Token Cap)
- **Key Files:**
  - `src/auth/jwt_service.py` — Token creation, validation, dual-secret rotation
  - `src/auth/auth_middleware.py` — `@require_auth` decorator
  - `provision.sh` — Secrets Manager secret creation, IAM permissions

## 8. References

- Issue #341: JWT auth implementation
- Issue #362: Auth infrastructure deployment
- Issue #364: Tiered rate limiting (added `tier` and `billing_anchor_day` to JWT claims)
- LLD-341: Full design specification
- [RFC 7519: JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-19 | Claude Opus 4.6 | Initial draft |
