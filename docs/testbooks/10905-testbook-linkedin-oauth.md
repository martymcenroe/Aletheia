# 10905 — LinkedIn OAuth Manual Testbook

**Issue:** #443
**Related:** #396 (Firefox popup-close bug), #405 (Auth readiness checklist), #480 (Chrome OAuth SW migration)
**Last updated:** 2026-02-25

---

## Prerequisites

| Item | Details |
|------|---------|
| LinkedIn account | Personal or test account with valid credentials |
| Chrome browser | Latest stable, extension loaded unpacked from `extensions/chrome/` |
| Firefox browser | v140.0+, extension loaded from `extensions/firefox/` |
| Auth Lambda | `AletheiaAuth` deployed and accessible |
| Auth enabled | `AUTH_ENABLED=true` on `AletheiaAgent` Lambda (or test with auth Lambda directly) |
| Network | Internet access for LinkedIn OAuth flow |

---

## Chrome Test Procedures

### TC-01: Login via LinkedIn (Chrome)

> **Note (Issue #480):** Chrome now delegates OAuth to the service worker, same pattern
> as Firefox (#396). The popup sends `START_OAUTH` to the SW, which calls
> `chrome.identity.launchWebAuthFlow`. The popup may close when the auth window opens
> (MV3 behavior). On reopen, `init()` finds stored tokens via `isAuthenticated()`.
> If OAuth failed, the popup displays the error from `authError` in session storage.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click extension icon to open popup | Popup opens with "Sign in with LinkedIn" button |
| 2 | Click "Sign in with LinkedIn" | Chrome auth window opens to LinkedIn authorization page; popup may close (expected) |
| 3 | Enter LinkedIn credentials and authorize | Auth window closes automatically after redirect |
| 4 | Click extension icon to reopen popup | Shows user display name, "Sign Out" button visible |
| 5 | Check DevTools > Application > Session Storage | `accessToken`, `expiresAt`, `jwt` keys present |
| 6 | Check DevTools > Application > Local Storage | `refreshToken`, `userId`, `displayName` keys present |

**Pass criteria:** Tokens stored by service worker via `launchWebAuthFlow`. Popup shows authenticated state on reopen.

### TC-01a: Login Error Feedback (Chrome)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click extension icon to open popup | Popup opens with "Sign in with LinkedIn" button |
| 2 | Click "Sign in with LinkedIn" | Chrome auth window opens |
| 3 | Close the auth window without completing login | Auth window closes |
| 4 | Click extension icon to reopen popup | Popup shows "Sign in with LinkedIn" button (no error — cancellation is not an error) |
| 5 | Disconnect network, then repeat steps 1-3 (complete LinkedIn auth with network off) | On reopen, popup shows error message (token exchange failed) |

**Pass criteria:** User cancellation shows no error. Actual failures display a message.

### TC-02: JWT Verification (Chrome)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Complete TC-01 (logged in) | User authenticated |
| 2 | Open DevTools > Application > Session Storage | Copy `jwt` value |
| 3 | Decode JWT at jwt.io | Header: `alg: HS256`. Payload: contains `sub`, `name`, `iat`, `exp` |
| 4 | Verify `exp` claim | Expiration is in the future (typically 1 hour from login) |

**Pass criteria:** JWT is well-formed with expected claims.

### TC-03: Authenticated API Call (Chrome)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Complete TC-01 (logged in) | User authenticated |
| 2 | Navigate to an allowlisted site | Page loads normally |
| 3 | Select text, right-click > "Explain with AI" | Analysis overlay appears |
| 4 | Check DevTools > Network tab | POST to `api.aletheia.study` includes `Authorization: Bearer <jwt>` header |

**Pass criteria:** API request includes valid Authorization header.

### TC-04: Logout (Chrome)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Complete TC-01 (logged in) | User authenticated |
| 2 | Click extension icon to open popup | Popup shows logged-in state |
| 3 | Click "Sign Out" | Popup reverts to "Sign in with LinkedIn" button |
| 4 | Check Session Storage | `accessToken`, `jwt` keys removed |
| 5 | Check Local Storage | `refreshToken`, `userId`, `displayName` keys removed |
| 6 | Right-click > "Explain with AI" on allowlisted site | API call does NOT include Authorization header |

**Pass criteria:** All tokens cleared, subsequent API calls are unauthenticated.

---

## Firefox Test Procedures

### TC-05: Login via LinkedIn (Firefox)

> **Note:** Firefox popup closes when the auth tab opens — this is expected behavior.
> The service worker stores OAuth state in `chrome.storage.session` and top-level
> listeners handle the callback (PR #478, persistent state pattern). The popup
> detects authentication on reopen via `isAuthenticated()`.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click extension icon to open popup | Popup opens with "Sign in with LinkedIn" button |
| 2 | Click "Sign in with LinkedIn" | New tab opens to LinkedIn authorization page; popup closes (expected) |
| 3 | Enter LinkedIn credentials and authorize | Tab redirects to callback URL, then closes automatically |
| 4 | Click extension icon to reopen popup | Shows user display name, "Sign Out" button visible |
| 5 | Check `about:devtools-toolbox` > Storage | Session: `accessToken`, `expiresAt`, `jwt` present. Local: `refreshToken`, `userId`, `displayName` present |

**Pass criteria:** Tokens stored by service worker via persistent state. Popup shows authenticated state on reopen.

### TC-06: JWT Verification (Firefox)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Complete TC-05 (logged in, if possible) | User authenticated |
| 2 | Open Storage Inspector | Copy `jwt` value from session storage |
| 3 | Decode JWT at jwt.io | Same structure as TC-02 |

**Pass criteria:** JWT is well-formed (same as Chrome).

---

## Pass/Fail Criteria

| Test Case | Browser | Status | Notes |
|-----------|---------|--------|-------|
| TC-01 | Chrome | | Popup may close (expected); tokens via SW launchWebAuthFlow |
| TC-01a | Chrome | | Error feedback on failure, no error on cancellation |
| TC-02 | Chrome | | |
| TC-03 | Chrome | | |
| TC-04 | Chrome | | |
| TC-05 | Firefox | | Popup closes (expected); tokens via SW persistent state |
| TC-06 | Firefox | | Depends on TC-05 |

---

## Evidence Recording

| Test Case | Date | Tester | Result | Screenshot/Log |
|-----------|------|--------|--------|----------------|
| TC-01 | | | | |
| TC-01a | | | | |
| TC-02 | | | | |
| TC-03 | | | | |
| TC-04 | | | | |
| TC-05 | | | | |
| TC-06 | | | | |
