# Implementation Report — Issues #812, #813, #814

## Problem

Field report on Firefox 1.1.1 (the current AMO build), on a machine rebooted
repeatedly over 60 days: the popup showed the user signed in and Aletheia
"ACTIVE", while every analysis on the page returned "Sign In Required". The only
recovery was a manual logout and re-login, and it recurred.

Three client defects combined to produce that.

**#812 — the credential did not survive a restart.** `storeTokens` wrote the JWT
to `storage.session`, which the browser clears on close, while identity
(`userId`, `displayName`) went to `storage.local`, which persists forever.
Closing the browser destroyed the only credential the API accepts and left
every field the popup inspects intact.

**#813 — the popup reported a session that did not exist.** `getAuthState`
returned "signed in" whenever `userId` was present. That value never expires and
has no relationship to whether any request can succeed, so the popup asserted an
active session indefinitely. This is what made the failure undiagnosable from
the UI: the thing that was broken was reported as fine.

**#814 — a recoverable condition was presented as terminal.** `getAuthHeaders`
read the JWT, found nothing, and dispatched the request anyway with no
`Authorization` header — a request it knew would fail. No 401 handler attempted
renewal. The 401 mapped straight to a terminal "Sign In Required".

## Change

Applied to both `extensions/chrome/` and `extensions/firefox/`.

### Persistence (#812)

The Aletheia refresh token from #811 is stored in `storage.local`, so it
survives restarts and reboots. The JWT remains in `storage.session`: it is
short-lived, and with the refresh token persisted a cold start simply re-mints
it. `jwtExpiresAt` is now stored alongside the JWT — without it, freshness is
unknowable and every request path has to guess.

`storeTokens` only overwrites a stored refresh token when a new one was actually
issued, so a re-login that omits it cannot silently strip renewal ability.

### Honest auth state (#813)

`getAuthState` now requires `userId` **and** a stored refresh token. Being
authenticated means "a credential is obtainable", not "a name is remembered".
Added `isSessionUnrecoverable()` so the UI can distinguish "signed out" from
"identity remembered but the session is dead" and say so honestly.

### Renewal and recovery (#814)

- `getValidJwt()` is the only accessor a request path may use. It returns the
  cached JWT while fresh, otherwise renews silently.
- `renewJwt()` shares one in-flight promise across concurrent callers. Several
  extension contexts hit this simultaneously on a cold start; N parallel
  renewals would multiply load on the auth Lambda for no benefit.
- `getAuthHeaders()` returns `null` when no credential is obtainable, and
  callers must not dispatch. It no longer sends a request known to 401.
- `authedPost()` retries **exactly once** after renewing on a 401. No loop, no
  recursion — a renewal storm would turn a transient failure into an outage.
  It forwards caller fetch options (Chrome's 30s abort signal) to both the
  initial request and the retry, so a caller's timeout still governs the retry.

### Failure handling

A 401 from `/auth/refresh` means the refresh token is revoked or expired:
renewal can never succeed again, so the token is dropped and a real sign-in is
required. **Any other outcome — 5xx, or a thrown network error — retains the
token.** Discarding it on a transient blip would force a re-login over a
momentary outage, which is the class of failure this work exists to remove.

## Migration

An existing signed-in user upgrading to this build has a JWT but no
`jwtExpiresAt` and no refresh token. A strict freshness check would have logged
out every current user.

`getValidJwt` therefore falls back to the cached JWT when renewal is impossible
and a JWT is present: its validity is unknown but plausible, so it is used and
the 401 path decides. That converts a guaranteed forced re-login into one that
happens only if the token has genuinely expired.

## Version

Both manifests bumped to **1.1.3**.

## Not included

- **#815** (opaque 401 discriminator) is server-side and tracked separately.
  The client currently infers intent from the 401 status alone, which is
  sufficient because renewal is attempted before any sign-in prompt.
- The Firefox and Chrome service workers cannot import `auth.js`, so each
  carries its own copy of the renewal logic. The shared contract is the
  `/auth/refresh` payload. This duplication is a known cost of the MV3 worker
  boundary, not an oversight.

## Deploy

Extension-only; requires no AWS change. The server half (#811) is already
deployed and verified in production. Reaching users requires a store upload —
AMO is tracked in #559.
