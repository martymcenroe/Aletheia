
# LinkedIn Authentication Gate for Context-Aware Vocabulary

## 1. Context and current behavior

Extension: **Context-Aware Vocabulary**  
Files involved so far:

- `manifest.json`
- `service-worker.js`

Today:

- On install, the extension registers a context-menu item:

  - ID: `"explain-with-ai"`
  - Contexts: `["selection"]`

- When the user selects text and chooses **Explain with AI**:

  1. `service-worker.js` injects a small script via `chrome.scripting.executeScript` to read `document.body.innerText` from the active tab.
  2. It builds a JSON payload:

     - `word`: the selected text
     - `url`: `info.pageUrl`
     - `title`: `tab.title`
     - `context`: full page text from the injected script

  3. It sends this payload via `fetch` to:

     - `https://webhook.site/1a0e08a8-a013-480f-8e03-ee34930a1d26`

  4. It logs the response status.

There is currently **no authentication requirement**. The extension runs on any site and for any user.

---

## 2. Goal of this change

Only allow the **Explain with AI** workflow to execute when the user is **logged into LinkedIn**.

For this first version:

- We use a simple heuristic: the presence of any cookies for the domain `.linkedin.com` is treated as “user is logged into LinkedIn”.
- If no LinkedIn cookies are found:

  - The extension **does not** send a request to the webhook.
  - The user receives a clear failure message: `Not authenticated with LinkedIn.`

We **do not**:

- Open login windows, redirect the user, or run an OAuth dance.
- Persist any tokens or LinkedIn identifiers.
- Add any UI beyond a simple notification (or console log fallback).

---

## 3. High-level behavior after the change

When the user triggers **Explain with AI**:

1. The `service-worker.js` checks LinkedIn authentication state by inspecting cookies for `.linkedin.com` through the Chrome `cookies` API.
2. If at least one cookie exists for `.linkedin.com`:

   - Proceed exactly as today:
     - Inject script to get `document.body.innerText`.
     - Build payload.
     - Send payload to the configured webhook endpoint.
     - Log the response.

3. If no cookies exist for `.linkedin.com`:

   - Do **not** call the webhook.
   - Show a user-visible message:

     - Preferred: `chrome.notifications.create(...)` with message `Not authenticated with LinkedIn.`
     - Fallback: log a warning to the console if notifications are not available.

---

## 4. Required platform and manifest permissions

To implement this gate, the extension must be able to:

- Inspect cookies for `.linkedin.com`.
- Optionally show a notification.

This requires updates to `manifest.json`.

### 4.1. Current `manifest.json`

```json
{
  "manifest_version": 3,
  "name": "Context-Aware Vocabulary",
  "version": "1.0",
  "description": "Explain highlighted text using AI.",
  "permissions": [
    "contextMenus",
    "scripting"
  ],
  "host_permissions": [
    "https://webhook.site/1a0e08a8-a013-480f-8e03-ee34930a1d26"
  ],
  "background": {
    "service_worker": "service-worker.js"
  }
}
````

### 4.2. Target `manifest.json` changes

Add:

* `"cookies"` and `"notifications"` to `permissions`.
* LinkedIn host patterns to `host_permissions` so the extension is allowed to inspect those cookies.

Result:

```json
{
  "manifest_version": 3,
  "name": "Context-Aware Vocabulary",
  "version": "1.0",
  "description": "Explain highlighted text using AI.",
  "permissions": [
    "contextMenus",
    "scripting",
    "cookies",
    "notifications"
  ],
  "host_permissions": [
    "https://webhook.site/1a0e08a8-a013-480f-8e03-ee34930a1d26",
    "https://www.linkedin.com/*",
    "https://*.linkedin.com/*"
  ],
  "background": {
    "service_worker": "service-worker.js"
  }
}
```

Non-goals:

* No additional content scripts are required.
* No changes to `action`, `popup`, or options pages (none defined yet).

---

## 5. Detailed service worker design

File: `service-worker.js`

### 5.1. New constants

Add:

* `LINKEDIN_COOKIE_DOMAIN = ".linkedin.com"`

This keeps the cookie filter logic simple and central.

### 5.2. Helper: `isLinkedInAuthenticated`

Add a helper that returns a `Promise<boolean>`:

* Calls `chrome.cookies.getAll({ domain: LINKEDIN_COOKIE_DOMAIN })`.

* On error (via `chrome.runtime.lastError`):

  * Log the error.
  * Resolve to `false`.

* On success:

  * If the returned cookie array is non-empty, resolve to `true`.
  * Otherwise resolve to `false`.

Pseudo-implementation:

```js
function isLinkedInAuthenticated() {
  return new Promise((resolve) => {
    chrome.cookies.getAll({ domain: LINKEDIN_COOKIE_DOMAIN }, (cookies) => {
      if (chrome.runtime.lastError) {
        console.error("[CV-6] Error checking LinkedIn cookies:", chrome.runtime.lastError);
        resolve(false);
        return;
      }

      const hasCookies = Array.isArray(cookies) && cookies.length > 0;
      resolve(hasCookies);
    });
  });
}
```

### 5.3. Helper: user-visible failure message

Add a helper that shows `Not authenticated with LinkedIn.`:

* If `chrome.notifications.create` is available:

  * Show a basic notification with:

    * Title: `Context-Aware Vocabulary`
    * Message: `Not authenticated with LinkedIn.`

* Otherwise:

  * Log a warning.

Pseudo-implementation:

```js
function showNotAuthenticatedMessage() {
  const message = "Not authenticated with LinkedIn.";

  if (chrome.notifications && chrome.notifications.create) {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icon128.png", // must correspond to an icon included in the extension
      title: "Context-Aware Vocabulary",
      message
    });
  } else {
    console.warn("[CV-6]", message);
  }
}
```

If there is no suitable icon asset yet, this helper can initially be wired to only log, and the icon can be added in a later change.

### 5.4. Gating the context-menu handler

Current handler (simplified):

* Checks `info.menuItemId === "explain-with-ai"`.
* Injects script to get full page text.
* Builds payload and sends it to `API_ENDPOINT`.

New behavior:

1. At the very start of the `onClicked` handler, after confirming `menuItemId`:

   * Call `await isLinkedInAuthenticated()`.

2. If not authenticated:

   * Log a message indicating gate failure.
   * Call `showNotAuthenticatedMessage()`.
   * `return` early (do not inject script or call `fetch`).

3. If authenticated:

   * Proceed with existing logic unchanged.

Pseudo-change:

```js
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "explain-with-ai") return;

  const authenticated = await isLinkedInAuthenticated();
  if (!authenticated) {
    console.log("[CV-6] LinkedIn not authenticated – aborting request.");
    showNotAuthenticatedMessage();
    return;
  }

  // existing logic:
  // - executeScript to get document.body.innerText
  // - build payload
  // - fetch(API_ENDPOINT, ...)
});
```

This keeps the impact localized to `service-worker.js` and uses the same style and logging convention already present in the file.

---

## 6. Edge cases and limitations

* **Heuristic nature**

  * Presence of cookies for `.linkedin.com` does not guarantee that a user is actively logged in, only that LinkedIn has set cookies in this browser profile.
  * For this version, this heuristic is accepted as “good enough”.

* **Multiple Chrome profiles**

  * Auth state is profile-specific. If the user runs the extension in a profile that is not logged into LinkedIn, the gate will correctly treat them as unauthenticated.

* **Incognito windows**

  * If the extension is allowed in incognito:

    * Behavior will depend on whether LinkedIn cookies are present in that incognito context.
    * This design does not treat incognito differently.

* **Cookies disabled**

  * If cookies are disabled or unavailable, `isLinkedInAuthenticated` will effectively always return `false`, so the user will see `Not authenticated with LinkedIn.` and the extension will refuse to call the webhook.

These limitations are acceptable for this initial gate, which is intended as a simple authentication signal rather than a secure authorization mechanism.

---

## 7. Test scenarios

1. **User has never visited LinkedIn in this profile**

   * Expected:

     * `isLinkedInAuthenticated()` returns `false`.
     * Right-click → **Explain with AI**:

       * No network call to `API_ENDPOINT`.
       * User sees `Not authenticated with LinkedIn.` message.

2. **User has an active LinkedIn session in this profile**

   * Expected:

     * LinkedIn cookies exist.
     * `isLinkedInAuthenticated()` returns `true`.
     * Right-click → **Explain with AI**:

       * Behavior matches current implementation (inject script, send payload, log status).

3. **Error in cookies API (rare)**

   * Simulated by forcing `chrome.runtime.lastError` in tests.
   * Expected:

     * Error is logged with `[CV-6] Error checking LinkedIn cookies: ...`.
     * Function resolves to `false`.
     * User sees `Not authenticated with LinkedIn.` message when using the context menu.

---

## 8. Future enhancements (out of scope for this change)

* Replace cookie-based heuristic with a proper OAuth-backed flow.
* Store a stable LinkedIn identifier or Aletheia session token in `chrome.storage`.
* Expose a settings page or popup to show auth status and let the user “Disconnect LinkedIn”.
* Add structured error reporting back to Aletheia when the gate blocks a request.
