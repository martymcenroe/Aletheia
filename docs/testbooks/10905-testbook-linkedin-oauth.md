# 10905 — LinkedIn OAuth Manual Testbook

**Issue:** #443
**Related:** #396 (Firefox popup-close bug), #405 (Auth readiness checklist)
**Last updated:** 2026-02-24

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

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click extension icon to open popup | Popup opens with "Sign in with LinkedIn" button |
| 2 | Click "Sign in with LinkedIn" | New tab opens to LinkedIn authorization page |
| 3 | Enter LinkedIn credentials and authorize | Tab redirects to callback URL, then closes automatically |
| 4 | Check popup | Shows user display name, "Sign Out" button visible |
| 5 | Check DevTools > Application > Session Storage | `accessToken`, `expiresAt`, `jwt` keys present |
| 6 | Check DevTools > Application > Local Storage | `refreshToken`, `userId`, `displayName` keys present |

**Pass criteria:** User is authenticated, tokens stored correctly, popup reflects login state.

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

> **Known bug (#396):** Firefox popup closes when the auth tab opens, which may prevent
> the popup's message listener from receiving the token callback. The service worker
> handles the OAuth flow to mitigate this, but verify behavior carefully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click extension icon to open popup | Popup opens with "Sign in with LinkedIn" button |
| 2 | Click "Sign in with LinkedIn" | New tab opens to LinkedIn authorization page |
| 3 | **Observe:** Does popup remain open? | **Known issue:** Popup may close (#396) |
| 4 | Enter LinkedIn credentials and authorize | Tab redirects to callback URL, then closes |
| 5 | Click extension icon to reopen popup | Check if user is shown as authenticated |
| 6 | Check `about:devtools-toolbox` > Storage | Session: tokens present. Local: user info present |

**Pass criteria (partial):** If popup closes (#396), tokens should still be stored by the service worker. User should see authenticated state when reopening popup.

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
| TC-01 | Chrome | | |
| TC-02 | Chrome | | |
| TC-03 | Chrome | | |
| TC-04 | Chrome | | |
| TC-05 | Firefox | | Known #396 bug may affect |
| TC-06 | Firefox | | Depends on TC-05 |

---

## Evidence Recording

| Test Case | Date | Tester | Result | Screenshot/Log |
|-----------|------|--------|--------|----------------|
| TC-01 | | | | |
| TC-02 | | | | |
| TC-03 | | | | |
| TC-04 | | | | |
| TC-05 | | | | |
| TC-06 | | | | |
