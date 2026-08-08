# Implementation Report — Issue #811

## Problem

A signed-in user was locked out 24 hours after login, or the moment the browser
closed, with a full LinkedIn re-login as the only recovery. Two independent
server-side defects made silent renewal impossible:

1. **LinkedIn never issues us a refresh token.** The extension requests
   `SCOPES: 'openid profile'`. LinkedIn returns `refresh_token` only to approved
   partner programs, not for these scopes. `tokens.get("refresh_token")` was
   therefore always `None`, and the client stored `refreshToken: null`.
2. **`/auth/refresh` could not return a JWT.** `handle_token_refresh` called
   LinkedIn's `grant_type=refresh_token` endpoint and returned only
   `accessToken` + `expiresIn`. It never called `create_jwt`. Since the analysis
   API authenticates on the JWT, even a fully successful refresh handed back
   something the API rejects.

The entire refresh subsystem was unreachable code that had never worked.

Expiry itself is not the defect. A JWT is a stateless bearer credential, and
expiry is its only revocation mechanism. Expiry *without a renewal path* is the
defect.

## Change

LinkedIn now proves identity exactly once, at first login, and is never called
again for session maintenance.

### New — `src/auth/refresh_token_service.py`

Aletheia-issued refresh tokens, long-lived and revocable.

- `generate_refresh_token()` — 32 bytes of entropy via `secrets.token_urlsafe`.
- `hash_token()` — SHA-256. Appropriate here rather than a slow KDF: the token
  already carries 256 bits of entropy, so there is nothing to brute-force.
- `store_refresh_token()` — persists **only the hash**, plus `user_id`,
  `created_at`, `last_used_at`, `revoked`, and a `ttl`. A read of the table
  yields nothing usable.
- `validate_refresh_token()` — returns the owning `user_id`, or `None` if the
  token is unknown, revoked, or expired.
- `revoke_refresh_token()` — sets the `revoked` flag, ending that session.

Two deliberate properties:

- **Expiry is enforced in code, not delegated to DynamoDB TTL.** TTL deletion is
  best-effort and can lag by up to 48 hours, so it is storage cleanup only and
  never the security boundary.
- **Datastore failures fail closed.** A lookup error denies rather than admits.
  The one exception is `_touch_last_used`, which is best-effort by design:
  bookkeeping must never be able to lock a user out.

### Changed — `src/lambda_auth_function.py`

- `handle_token_exchange` now also mints and stores an Aletheia refresh token,
  returning it as `aletheiaRefreshToken`. A failure to issue it is a hard 500
  rather than a silent success, since a login without a renewable session is the
  exact bug being fixed.
- `handle_token_refresh` was rewritten to accept `aletheiaRefreshToken`,
  resolve it to a `user_id`, and mint a fresh JWT — with no LinkedIn round-trip.

Two safety properties in the rewrite:

- **The stored `user_id` is authoritative.** No client-supplied identifier is
  read anywhere on this path, which is what prevents a valid refresh token from
  minting a JWT for a different user.
- **Tier is re-read on every refresh.** `create_jwt` defaults `tier` to `"free"`.
  Had the refresh path omitted the `get_user_tier` lookup, every renewal would
  have silently stripped a paying user's entitlement — a regression that would
  have been invisible until a billing complaint. It also means an upgrade takes
  effect without forcing a re-login.

### Changed — `provision.sh`

- Creates `aletheia-refresh-tokens` (hash key `token_hash`, PAY_PER_REQUEST).
- Enables TTL on the `ttl` attribute.
- Adds the table ARN to the Lambda role policy.
- Adds `REFRESH_TOKENS_TABLE` to the auth Lambda environment.

## Deliberately not done

`refresh_access_token()` (the LinkedIn `grant_type=refresh_token` call) is now
unreferenced by every route but was **left in place**. Its only remaining caller
is a privacy regression test from #648 asserting that LinkedIn response bodies
never reach logs. Deleting the function inside this change would have deleted
that assertion as a side effect. Removal is tracked in #816, which requires
confirming equivalent log-hygiene coverage on the remaining LinkedIn call sites
first.

## Client work not included

This change makes silent renewal *possible*. It does not yet make the extension
use it. The client-side work is tracked separately: #812 (credential must
survive browser restart), #813 (popup must stop reporting signed-in from
`userId` alone), #814 (401 must trigger renewal and one retry instead of a dead
end). Until those land and ship, users see no behavioral change.

## Deploy

Server-side only; requires a deploy to take effect. Merging does not deploy.

`provision.sh` re-applies the entire Lambda environment on every run and can
clobber `CLOUDFLARE_ORIGIN_SECRET` on a transient SSM failure (#779). However,
this change adds a new table, an IAM statement, and an env var, so a code-only
`update-function-code` is **not** sufficient. `provision.sh` must run, and
`CLOUDFLARE_ORIGIN_SECRET` must be verified non-empty immediately afterward.

## Rollback

```
aws lambda update-function-code --function-name AletheiaAuth --zip-file fileb://<previous>.zip
```

The new table and IAM statement are additive and harmless if left in place. The
response-shape change is additive; clients ignore unknown fields.
