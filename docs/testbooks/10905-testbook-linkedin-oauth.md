# 10905 — LinkedIn OAuth Manual Testbook

**Issue:** #443 | **Parent:** #405 | **Auth System:** AletheiaAuth Lambda
**Last Updated:** 2026-02-24

---

## 1. Prerequisites

| Requirement | Details |
|-------------|---------|
| LinkedIn account | Any valid LinkedIn account (personal or test) |
| Chrome | Latest stable, extension loaded unpacked from `extensions/chrome/` |
| Firefox | v140.0+, extension loaded temporarily from `extensions/firefox/manifest.json` |
| AUTH_ENABLED | Must be `true` on the Lambda (`AletheiaAgent`) |
| Auth Lambda | `AletheiaAuth` deployed and reachable |
| Network | Internet access to LinkedIn OAuth and `api.aletheia.study` |

---

## 2. Chrome Test Procedure

### Step 1: Load Extension
1. Navigate to `chrome://extensions`
2. Enable Developer Mode
3. Load unpacked from `extensions/chrome/`
4. Verify extension icon appears in toolbar

### Step 2: Login
1. Click the Aletheia extension icon to open popup
2. Click "Sign in with LinkedIn"
3. LinkedIn OAuth page opens in a new tab
4. Authorize the application
5. Tab closes automatically after authorization
6. Popup shows logged-in state with user name

**Expected:** Popup displays user name and "Sign out" button.

### Step 3: Verify Tokens
1. Open DevTools on any page
2. Run in console: `chrome.runtime.sendMessage({ type: 'AUTH_STATUS' }, r => console.log(r))`
3. Verify response contains `{ authenticated: true }` (or check via popup UI)
4. In DevTools Application tab > Extension Storage, verify `jwt` exists in session storage

**Expected:** JWT is present in session storage, refresh token in local storage.

### Step 4: Analyze with Auth
1. Navigate to an allowlisted site
2. Select text, right-click, choose "Explain with AI"
3. Open DevTools Network tab, find the POST to `api.aletheia.study`
4. Inspect request headers

**Expected:** `Authorization: Bearer <jwt>` header is present in the request.

### Step 5: Logout
1. Click the Aletheia extension icon
2. Click "Sign out"
3. Verify popup returns to "Sign in" state
4. Repeat Step 4 — analyze text again

**Expected:** After logout, the POST request has no `Authorization` header.

---

## 3. Firefox Test Procedure

### Step 1: Load Extension
1. Navigate to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select `extensions/firefox/manifest.json`
4. Verify extension icon appears in toolbar

### Step 2: Login
1. Click the Aletheia extension icon to open popup
2. Click "Sign in with LinkedIn"
3. LinkedIn OAuth page opens in a new tab

> **Known Issue (#396):** The popup may close when the auth tab opens. This is expected behavior in Firefox — the service worker continues the OAuth flow independently. Wait for the auth tab to close automatically after authorization.

4. Authorize the application on LinkedIn
5. Auth tab closes automatically
6. Re-open popup — should show logged-in state

**Expected:** After re-opening popup, user name and "Sign out" button are displayed.

### Step 3: Verify Tokens
1. Open DevTools (F12) on the extension's background page (via `about:debugging`)
2. Check storage via the Storage tab or console
3. Verify JWT exists in session storage

**Expected:** JWT is present in session storage, refresh token in local storage.

### Step 4: Analyze with Auth
1. Navigate to an allowlisted site
2. Select text, right-click, choose "Explain with AI"
3. Open DevTools Network tab, find the POST to `api.aletheia.study`
4. Inspect request headers

**Expected:** `Authorization: Bearer <jwt>` header is present in the request.

### Step 5: Logout
1. Click the Aletheia extension icon
2. Click "Sign out"
3. Verify popup returns to "Sign in" state
4. Repeat Step 4 — analyze text again

**Expected:** After logout, the POST request has no `Authorization` header.

---

## 4. Pass/Fail Criteria

### Chrome

| Step | Criterion | Pass | Fail |
|------|-----------|------|------|
| 2 | OAuth completes, popup shows user name | User visible | Error or blank |
| 3 | JWT in session storage | Present | Missing |
| 4 | Authorization header in network request | `Bearer <jwt>` | Missing header |
| 5 | Tokens cleared after logout | No Authorization header | Header still present |

### Firefox

| Step | Criterion | Pass | Fail |
|------|-----------|------|------|
| 2 | OAuth completes (popup may close — #396) | User visible on re-open | Error or stuck |
| 3 | JWT in session storage | Present | Missing |
| 4 | Authorization header in network request | `Bearer <jwt>` | Missing header |
| 5 | Tokens cleared after logout | No Authorization header | Header still present |

---

## 5. Evidence Recording

| Date | Browser | Version | Tester | Steps Passed | Overall | Notes |
|------|---------|---------|--------|--------------|---------|-------|
| | Chrome | | | /5 | | |
| | Firefox | | | /5 | | |
