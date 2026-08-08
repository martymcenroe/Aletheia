# Test Report — Issues #812, #813, #814

## Result

```
379 passed | 4 skipped (383)
npx eslint extensions/ tests/unit/ tests/mocks/  — clean
node --check on all 6 modified extension files  — clean
```

Up from 357 passing before this change. No regressions.

## New — `tests/unit/chrome/session-persistence.test.js` (10 tests)

### Persistence (#812)
- `survives a simulated browser restart with no user interaction` — clears
  session storage exactly as a restart does, leaves local storage intact, and
  asserts a JWT is obtained with no user action. This is the reported defect,
  reproduced and pinned.
- `persists the refresh token to LOCAL storage, not session storage` — asserts
  the credential is recoverable after session storage is emptied.

### Honest auth state (#813)
- `does NOT report a session when identity remains but renewal is impossible` —
  seeds precisely the field-reported state (display name present, credential
  gone) and asserts `getAuthState()` is null, `isAuthenticated()` is false, and
  `isSessionUnrecoverable()` is true. This is the assertion that fails if the
  popup ever again claims a session it cannot back.
- `reports a session when identity AND a refresh token are present`.

### Renewal and failure handling (#814)
- `issues ONE renewal when several callers race on a cold start` — three
  concurrent `getValidJwt()` calls produce exactly one network round-trip and
  all three receive the same JWT.
- `drops the refresh token on 401 so a revoked session stops retrying`.
- `KEEPS the refresh token on a transient failure` (503) — discarding it would
  force a re-login over a momentary outage.
- `KEEPS the refresh token when the network throws`.
- `sends the Aletheia refresh token, never LinkedIn's` — asserts the request
  body carries `aletheiaRefreshToken` and no `refreshToken`. LinkedIn cannot
  refresh the `openid profile` scopes, so sending its token would 401.
- `logout clears the refresh token so the session cannot resurrect`.

## New — in `tests/unit/firefox/service-worker.test.js`

- `dispatches NO request when no credential can be obtained` — pins the #814
  guarantee directly. Previously the worker sent the request with no
  `Authorization` header, guaranteeing a 401, and surfaced that as terminal.

## Changed — test doubles

`tests/mocks/chrome-api.mock.js` and `firefox-api.mock.js`: the
`authenticated: true` fixture now includes `aletheiaRefreshToken` in local
storage and `jwt` + `jwtExpiresAt` in session storage. The previous fixture
modelled a user who *looked* signed in but held nothing that could authenticate
a request — the defective state itself, used as the definition of "authenticated"
across the suite.

## Changed — tests that encoded the old contract

These asserted the behavior being fixed and were **rewritten, not deleted**:

- `isAuthenticated returns true when userId exists` (chrome + firefox) — the
  literal statement of the #813 defect. Now requires a renewable session.
- `getAccessToken returns token when valid`, `returns cached token when not
  expired`, `attempts refresh when token is expired`, `getAccessToken returns
  null when no refresh token` — all four targeted the LinkedIn access-token
  refresh path, which #811 established has never worked (LinkedIn issues no
  refresh token for `openid profile`). Retargeted at `getValidJwt`, and the
  expired-token case now additionally asserts the renewal request carries
  `aletheiaRefreshToken` and that the caller receives the renewed credential.
- `exports required auth functions` — `getAccessToken` removed; `getValidJwt`,
  `renewJwt`, `isSessionUnrecoverable` asserted instead.

### One vacuous test repaired

`includes X-Aletheia-Client-Version header in API requests` wrapped its
assertion in `if (fetchCall)`. When no request was dispatched, the test passed
having asserted nothing — so it would not have caught this change breaking the
request path. It now asserts unconditionally that a request was made, that the
version header is present, and that an `Authorization` header was attached.

## Not covered by automated tests

- **A real browser restart.** The restart is simulated by clearing the session
  storage double. Nothing here proves Firefox's `storage.session` behaves as
  modelled, or that `storage.local` survives on this machine. That is the one
  thing only a manual test can establish, and it is the exact scenario reported.
- **End-to-end against production.** The tests mock `fetch`; no test exercises
  the deployed `/auth/refresh`. The endpoint was verified live by hand during
  the #811 deploy (`{"error": "Unauthorized", "reason": "invalid_refresh_token"}`
  for a garbage token), but the client-to-server round-trip on a real login is
  unverified until the build is installed.
- **Chrome parity is asserted structurally, not behaviorally.** The dedicated
  session tests run against `extensions/chrome/auth.js`. The Firefox module is
  a `browser.*` transliteration and its own suite passes, but the ten new
  assertions execute only against the Chrome copy.

## Pre-existing failures (not from this change)

- `npx eslint tests/e2e/` reports 9 `no-unused-vars` errors identically on clean
  `main`. Filed as #820. Files not touched here.
- `tests/unit/test_signal_inspector.py::TestLiveWebsites` fails locally against
  live `noarchive.net`; filed as #817. Passes in CI.
