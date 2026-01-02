# Gemini Handoff: Firefox/Chrome Extension Overlay Timing Issue

## Context

You are reviewing the Aletheia browser extension, which has separate codebases for Chrome (Manifest V3) and Firefox (Manifest V2):
- `extension-chrome-V3/` - Chrome MV3
- `extension-firefox-V2/` - Firefox MV2

The extension adds a right-click context menu item "Explain with AI" that:
1. Checks if the current domain is in the user's allowlist
2. If not allowlisted: shows warning overlay "Enable Aletheia for this site"
3. If allowlisted: sends selected text + page context to AWS Lambda, shows feedback overlay

## The Problem

There is a **perceptible delay** between clicking "Explain with AI" and seeing the overlay feedback. The delay occurs on BOTH Chrome and Firefox, so it's not browser-specific.

The delay is most noticeable in the "allowlisted" path where we call the Lambda API.

## What We Tried

### 1. First-Click Bug (FIXED)
Originally, the first click after extension load produced no overlay. Second click worked.

**Root cause:** `browser.runtime.onInstalled` only fires on install/update, not on browser restart or extension reload during development.

**Fix:** Create context menu at script load, not just in `onInstalled`:
```javascript
// Create immediately when script loads
createContextMenu();

// Also create on install (for first install)
browser.runtime.onInstalled.addListener(() => {
    createContextMenu();
});
```

### 2. Immediate "Saving..." Feedback (PARTIALLY WORKING)
To eliminate perceived delay, we show "Saving..." immediately before the Lambda call:

```javascript
// IMMEDIATE FEEDBACK - show "Saving..." right away
await browser.tabs.executeScript(tab.id, { file: 'overlay.js' });
await browser.tabs.executeScript(tab.id, {
    code: `window.showAletheiaOverlay("Saving...", "warning");`
});

// Then do the Lambda call...
const response = await fetch(API_ENDPOINT, {...});

// Then update to final status
await browser.tabs.executeScript(tab.id, {
    code: `window.updateAletheiaOverlay("Context Saved", "success");`
});
```

**Result:** "Saving..." appears, but there's still a delay before it shows.

### 3. In-Place Overlay Update (ATTEMPTED, REVERTED)
To avoid flicker between "Saving..." and "Context Saved", we added `updateAletheiaOverlay()` that changes text/color without removing the DOM element.

**Attempted approaches:**
- `window._aletheiaShadow` stored reference - didn't work across executeScript calls
- `world: 'MAIN'` on Chrome - broke everything (no overlay, no badge)
- `mode: 'open'` shadow DOM + find by ID - reverted to this, works but still has delay

### 4. Current State
The extension NOW works:
- First click works
- "Saving..." shows
- "Context Saved" shows (with badge)
- No flicker between states

**BUT:** There is still a noticeable delay (~0.5-1 second) before "Saving..." appears after clicking the context menu.

## Current Code Structure

### service-worker.js (Firefox MV2 version)
```javascript
browser.contextMenus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId === "explain-with-ai") {

        // ALLOWLIST GATE
        const domain = extractDomain(info.pageUrl);
        const result = await browser.storage.local.get('allowlist');
        const allowlist = result.allowlist || [];

        if (!allowlist.includes(domain)) {
            await showFeedback(tab.id, "Enable Aletheia for this site", "warning");
            return;
        }

        try {
            // IMMEDIATE FEEDBACK - show "Saving..." right away
            await browser.tabs.executeScript(tab.id, { file: 'overlay.js' });
            await browser.tabs.executeScript(tab.id, {
                code: `window.showAletheiaOverlay("Saving...", "warning");`
            });

            // Get page text
            const results = await browser.tabs.executeScript(tab.id, {
                code: 'document.body.innerText'
            });
            const fullPageText = results[0];

            // Send to Lambda
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: info.selectionText,
                    url: info.pageUrl,
                    title: tab.title,
                    domContext: fullPageText
                })
            });

            // Update overlay in place
            if (response.ok) {
                await browser.tabs.executeScript(tab.id, {
                    code: `window.updateAletheiaOverlay("Context Saved", "success");`
                });
            } else {
                await browser.tabs.executeScript(tab.id, {
                    code: `window.updateAletheiaOverlay("Error Saving", "error");`
                });
            }

        } catch (error) {
            await browser.tabs.executeScript(tab.id, {
                code: `window.updateAletheiaOverlay("Connection Error", "error");`
            });
        }
    }
});
```

### overlay.js (Firefox MV2 version)
```javascript
if (!window.updateAletheiaOverlay) {
    window.updateAletheiaOverlay = function(message, type) {
        const host = document.getElementById('aletheia-overlay-host');
        if (!host || !host.shadowRoot) {
            window.showAletheiaOverlay(message, type);
            return;
        }

        const colors = {
            'warning': '#FBBF24',
            'success': '#22C55E',
            'error':   '#EF4444'
        };
        const borderColor = colors[type] || colors['warning'];

        const overlay = host.shadowRoot.querySelector('.overlay');
        if (overlay) {
            overlay.textContent = message;
            overlay.style.borderLeftColor = borderColor;
        }
    };
}

if (!window.showAletheiaOverlay) {
    window.showAletheiaOverlay = function(message, type) {
        // 1. Cleanup existing overlay
        const existing = document.getElementById('aletheia-overlay-host');
        if (existing) existing.remove();

        // 2. Get Selection Geometry (with fallback)
        const selection = window.getSelection();
        let rect;
        if (selection.rangeCount > 0) {
            rect = selection.getRangeAt(0).getBoundingClientRect();
            if (rect.width === 0 && rect.height === 0) rect = null;
        }
        if (!rect) {
            rect = { top: 20, bottom: 60, left: window.innerWidth - 250, ... };
        }

        // 3. Create Shadow DOM
        const host = document.createElement('div');
        host.id = 'aletheia-overlay-host';
        const shadow = host.attachShadow({ mode: 'open' });

        // 4-7. Position and render overlay...
        // 8. Auto-dismiss after 4 seconds
    };
}
```

## The Remaining Problem

The delay happens BEFORE "Saving..." appears. The async chain is:
1. `contextMenus.onClicked` fires
2. `storage.local.get('allowlist')` - async
3. `executeScript` to inject overlay.js - async
4. `executeScript` to call showAletheiaOverlay - async

Each of these is an async operation. The cumulative latency is noticeable.

## Questions for Gemini

1. **Is there a way to pre-inject overlay.js** so it's already present when needed? Content scripts in manifest? But we only want it on allowlisted domains...

2. **Can we parallelize the async operations?** For example, inject overlay.js while simultaneously checking the allowlist?

3. **Is there a faster way to show feedback** than executeScript? The badge updates instantly - can we use a similar mechanism for visual feedback?

4. **Should we use a content script approach** instead of injecting on-demand? Trade-offs?

5. **Any Chrome MV3 vs Firefox MV2 specific optimizations** we're missing?

## Files to Review

- `extension-firefox-V2/service-worker.js` - Background script
- `extension-firefox-V2/overlay.js` - Injected overlay code
- `extension-firefox-V2/manifest.json` - MV2 manifest
- `extension-chrome-V3/service-worker.js` - Chrome version
- `extension-chrome-V3/overlay.js` - Chrome overlay
- `extension-chrome-V3/manifest.json` - MV3 manifest

## Constraints

- Must work on both Chrome and Firefox
- Cannot use `world: 'MAIN'` on Chrome (broke everything)
- Shadow DOM must be `mode: 'open'` for updates to work
- Overlay must appear near the selected text (or fallback position)
- Must respect the allowlist (don't inject into non-allowlisted sites)

## Success Criteria

User clicks "Explain with AI" → overlay appears **instantly** (within ~100ms) showing "Saving..." → transitions smoothly to "Context Saved" when Lambda responds.

Currently: ~500-1000ms delay before "Saving..." appears.
