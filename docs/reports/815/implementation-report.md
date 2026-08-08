# Implementation Report — Issues #815, #816, #819, #824

Four server-side items sharing the auth-Lambda and provisioning scope.

## #815 — 401 responses carry a discriminator

`auth_middleware.py` returned an identical opaque `{"error": "Unauthorized"}`
from all three 401 branches. Missing, expired, and invalid credentials were
indistinguishable on the wire.

That distinction is load-bearing for the client shipped in #814: an expired
credential is renewable and should be retried silently, while a revoked one
means renewal is futile and the user must sign in. Without a discriminator the
client has to guess, and guessing wrong either strands the user or hammers the
auth Lambda with pointless renewals.

`validate_jwt` already computed a precise reason (`token_expired`,
`invalid_signature`, `malformed`) and the middleware discarded it. The fix maps
those internal reasons onto a **fixed, closed public enum** and returns it:

- `missing_token` — absent or malformed `Authorization` header
- `expired_token` — renewable; retry silently
- `invalid_token` — signature/malformed/unknown; sign-in required
- `server_error` — our failure, not the user's

Two deliberate properties:

- **`secret_unavailable` maps to `server_error`, not `invalid_token`.** A
  missing signing secret is a server problem. Reporting it as a bad credential
  would make a client discard a perfectly good session over a transient outage.
- **Unknown internal reasons collapse to `invalid_token` rather than being
  echoed**, so a future internal reason string can never leak through this
  boundary.

The response body remains exactly `{"error", "reason"}`. No token material,
claims, identifiers, or exception text.

## #824 — LinkedIn response body no longer logged

Found while working #816's pre-removal gate, which requires confirming
log-hygiene coverage on every remaining LinkedIn call site before deleting the
unwired one. It was not covered — it was actively leaking.

`fetch_linkedin_profile` logged `f"LinkedIn API error: {status} - {response.text}"`.
A provider error body is untrusted third-party content that can carry
user-identifying data, and it persists in CloudWatch. Reduced to the status code
only, matching the two siblings repaired in #648.

This surface is absent from the #637 audit table, so that audit's count of 14
is an undercount rather than a complete inventory.

## #816 — dead LinkedIn refresh path removed

`refresh_access_token()` called LinkedIn's `grant_type=refresh_token`. It became
unreachable when #811 rewired `/auth/refresh`, and it could never have worked
regardless: LinkedIn issues no refresh token for the `openid profile` scopes the
extension requests. A plausible-looking but non-functional auth path in the tree
is what made the original session defect hard to diagnose.

It was deliberately left in place during #811 because its only caller was a
privacy regression test from #648. That test has been **retargeted, not
deleted** — it now guards the live `fetch_linkedin_profile` call site fixed
above, so log-hygiene coverage increased rather than decreased.

Added `test_linkedin_refresh_path_no_longer_exists` so the path cannot quietly
return.

## #819 — provisioning summary lists the refresh-tokens table

`provision.sh` created and TTL-enabled `aletheia-refresh-tokens` but omitted it
from the completion summary, so the printed output understated what the deploy
had actually provisioned. Added with the same `(TTL enabled)` annotation its
siblings carry.

## Follow-up filed

**#825** — `get_linkedin_user_info` and `fetch_linkedin_profile` are
near-duplicate callers of the same endpoint with divergent error handling. That
duplication is precisely why the #648 sweep repaired two call sites and passed
over the third: the function whose name did not contain "userinfo" was the one
that leaked. Consolidation is tracked separately rather than bundled here,
because it touches the login path and deserves its own blast-radius review.

## Deploy

Server-side; merging does not deploy.

- #815 changes `AletheiaAgent` (the analysis Lambda's middleware).
- #816 and #824 change `AletheiaAuth`.
- #819 changes `provision.sh` output only.

No new table, IAM statement, or environment variable, so a **code-only** deploy
is sufficient and preferred:

```
aws lambda update-function-code --function-name AletheiaAgent --zip-file fileb://<new>.zip
aws lambda update-function-code --function-name AletheiaAuth  --zip-file fileb://<new>.zip
```

Avoid a full `provision.sh` run for this change — it re-applies the entire
environment and can blank `CLOUDFLARE_ORIGIN_SECRET` on a transient SSM failure
(#779). The #819 fix only affects text `provision.sh` prints on its next
legitimate run.

## Rollback

`git revert <sha>` plus the same code-only deploy. The added `reason` field is
additive; clients ignoring it are unaffected.
