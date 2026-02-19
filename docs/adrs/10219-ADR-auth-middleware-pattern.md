# 10219 - ADR: Decorator-Based Auth Middleware for Lambda

**Status:** Implemented
**Date:** 2026-02-17
**Categories:** Architecture, Security, Patterns

## 1. Context

Aletheia has two Lambda functions: the Analysis Lambda (processes user requests) and the Auth Lambda (handles OAuth flows, billing, admin endpoints). Both need authentication, but with different strategies:

- **Analysis Lambda:** Every HTTP request must be JWT-authenticated. Direct SDK invocations (tests, internal calls) must bypass auth for backward compatibility.
- **Auth Lambda:** Different routes have different auth requirements — OAuth endpoints are public, billing/admin endpoints require JWT, Stripe webhooks use signature-based verification.

We needed a pattern that:
- Separates auth logic from business logic cleanly
- Supports conditional auth (HTTP vs direct invocation)
- Is testable in isolation
- Handles auth failures with structured logging and consistent error responses

## 2. Decision

**We will use a Python decorator (`@require_auth`) for the Analysis Lambda and per-route manual validation for the Auth Lambda. The decorator wraps handlers with an 8-step validation pipeline and injects authenticated user context into the event.**

### Analysis Lambda Pattern

```python
def lambda_handler(event, context):
    if "requestContext" in event:
        # HTTP request — enforce JWT auth
        @require_auth
        def _authenticated_handler(event, context, **kwargs):
            return _analysis_handler(event, context)
        return _authenticated_handler(event, context)
    else:
        # Direct invocation — no auth (backward compat)
        return _analysis_handler(event, context)
```

### Auth Lambda Pattern

```python
def lambda_handler(event, context):
    path = event.get("rawPath", "")
    if path == "/auth/token":
        return handle_token_exchange(body)       # Public
    elif path == "/metrics":
        return handle_metrics(event, body)       # JWT validated inside handler
    elif path == "/stripe-webhook":
        return handle_stripe_webhook(event)      # Stripe signature verified inside
```

### Decorator Validation Pipeline (8 Steps)

1. Extract `Authorization: Bearer <token>` header
2. Reject missing/malformed tokens → 401
3. Retrieve JWT secret from Secrets Manager (5-min cache)
4. Validate JWT signature (dual-secret for rotation)
5. Log auth failure with structured JSON → 401
6. Check multi-window rate limits → 429
7. Emit CloudWatch metrics (fail-open)
8. Inject `auth_user_id` into event → call wrapped handler

## 3. Alternatives Considered

### Option A: Decorator on Analysis Lambda + Per-Route on Auth Lambda — SELECTED

**Pros:**
- Clean separation: auth logic lives in `auth_middleware.py`, business logic in handlers
- Testable: decorator can be tested independently with mock events
- Flexible: Auth Lambda routes choose their own auth strategy
- Backward compatible: direct invocations bypass decorator

**Cons:**
- Two different patterns for two Lambdas (but they have genuinely different needs)

### Option B: Middleware Chain (Express.js-style) — Rejected

**Pros:**
- Single pattern for both Lambdas
- Composable middleware stack

**Cons:**
- Python Lambda doesn't have a natural middleware framework
- Would require building a mini-framework (over-engineering for 2 Lambdas)
- Lambda functions are not web servers — they handle discrete events

### Option C: API Gateway Authorizer — Rejected

**Pros:**
- Externalized auth (Lambda never sees unauthenticated requests)
- AWS-managed caching

**Cons:**
- We use Lambda Function URLs, not API Gateway
- Extra Lambda invocation per request (cost + latency)
- Can't differentiate auth strategies per route

### Option D: Auth Check at Top of Every Handler — Rejected

**Pros:**
- Explicit, no magic
- Easy to understand

**Cons:**
- Duplicated auth logic across handlers
- Easy to forget auth check on new endpoints
- No consistent error response format

## 4. Rationale

The decorator pattern is the Python-native way to add cross-cutting concerns. It provides:

| Concern | How Addressed |
|---------|---------------|
| Separation of concerns | Auth logic in one file, business logic in another |
| Consistency | All auth failures produce identical structured JSON logs |
| Testability | Decorator testable with mock events; handlers testable without auth |
| Fail modes | Centralized fail-closed (auth) and fail-open (metrics) behavior |
| Extensibility | Rate limiting, metrics, and logging all added to decorator without touching handlers |

The Auth Lambda uses per-route validation because its routes have fundamentally different auth requirements (public OAuth, JWT-protected billing, Stripe signature). A decorator would need complex configuration that's harder to read than explicit per-route checks.

## 5. Security Risk Analysis

| Risk | Impact | Likelihood | Severity | Mitigation |
|------|--------|------------|----------|------------|
| Developer forgets `@require_auth` on new endpoint | High (3) | Med (2) | 6 - High | Lambda handler conditional check (HTTP → decorator, always); code review required |
| Direct invocation bypasses auth | Med (2) | Low (1) | 2 - Low | Intentional for backward compat; CloudFlare shared secret prevents public direct calls |
| Log injection via malformed user_id | Med (2) | Low (1) | 2 - Low | `sanitize_for_logging()`: strips control chars, truncates to 128 chars |
| Auth failure leaks implementation details | Low (1) | Med (2) | 2 - Low | Error responses are generic ("Unauthorized"); detailed reason in server-side logs only |

## 6. Consequences

### Positive
- Single point of auth enforcement for Analysis Lambda
- Structured logging on all auth events (success and failure)
- Rate limiting, metrics, and auth validation in one composable decorator
- Handlers receive clean `auth_user_id` in event — no auth awareness needed

### Negative
- Two patterns across two Lambdas (acceptable given different requirements)
- Decorator hides auth logic from handler authors (mitigated by clear documentation)

### Neutral
- `@require_auth` adds ~10ms overhead per request (secret cache hit + rate limit check)
- Direct SDK invocations remain unauthenticated (test convenience vs security trade-off)

## 7. Implementation

- **Related Issues:** #341 (JWT auth), #362 (auth infrastructure), #364 (rate limiting), #369 (metrics)
- **Related LLDs:** LLD-341 (§2.5 Analysis Lambda JWT Validation)
- **Key Files:**
  - `src/auth/auth_middleware.py` — `@require_auth` decorator (330 lines)
  - `src/auth/jwt_service.py` — JWT validation called by middleware
  - `src/auth/tier_config_service.py` — Tier configs for rate limiting
  - `src/lambda_function.py` — Conditional decorator application
  - `src/lambda_auth_function.py` — Per-route auth handling

### Route Auth Matrix

| Lambda | Route | Auth Method |
|--------|-------|-------------|
| Analysis | `/*` (HTTP) | `@require_auth` (JWT) |
| Analysis | `/*` (direct) | None (backward compat) |
| Auth | `/auth/token` | None (public OAuth) |
| Auth | `/auth/refresh` | None (public) |
| Auth | `/auth/validate` | Bearer token in header |
| Auth | `/auth/callback` | None (OAuth callback) |
| Auth | `/my-data` | Bearer token (GDPR) |
| Auth | `/metrics` | JWT (admin) |
| Auth | `/redeem-coupon` | JWT |
| Auth | `/create-checkout-session` | JWT |
| Auth | `/subscription-status` | JWT |
| Auth | `/stripe-webhook` | Stripe signature |

## 8. References

- Issue #341: JWT auth implementation
- Issue #364: Tiered rate limiting (added rate limit step to decorator)
- Issue #369: CloudWatch metrics (added metrics emission step to decorator)
- Python `functools.wraps` documentation

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-19 | Claude Opus 4.6 | Initial draft |
