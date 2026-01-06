// extensions/firefox/service-worker.js
// Firefox Manifest V2 version

// [CV-7] CONSTANTS - WIRED TO AWS LAMBDA
const API_ENDPOINT = "https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/";

console.log("[Aletheia] Background script loaded");

function extractDomain(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return null;
  }
}

// === HELPER FUNCTION (MV2 API) ===
async function showFeedback(tabId, message, type) {
    console.log(`[Aletheia] showFeedback called: ${message}, ${type}`);
    try {
        // 1. Inject Library
        console.log("[Aletheia] Injecting overlay.js...");
        await browser.tabs.executeScript(tabId, { file: 'overlay.js' });
        console.log("[Aletheia] overlay.js injected");

        // 2. Call Function (MV2 uses code string, not func)
        const code = `window.showAletheiaOverlay(${JSON.stringify(message)}, ${JSON.stringify(type)});`;
        console.log("[Aletheia] Executing overlay function...");
        await browser.tabs.executeScript(tabId, { code });
        console.log("[Aletheia] Overlay function executed");

        // 3. Set Toolbar Badge (MV2: browserAction, not action)
        const badgeText = type === 'success' ? '✓' : (type === 'error' ? '✗' : '!');
        const badgeColor = type === 'success' ? '#22C55E' : (type === 'error' ? '#EF4444' : '#FBBF24');

        browser.browserAction.setBadgeText({ tabId, text: badgeText });
        browser.browserAction.setBadgeBackgroundColor({ tabId, color: badgeColor });

        setTimeout(() => browser.browserAction.setBadgeText({ tabId, text: '' }), 3000);

    } catch (e) {
        console.error("[Aletheia] Overlay Injection Failed:", e);
    }
}

// === CONTEXT MENU CREATION ===
// FIX: Create context menu at script load, not just onInstalled
// onInstalled doesn't fire on browser restart or extension reload
function createContextMenu() {
    console.log("[Aletheia] Creating context menu...");
    browser.contextMenus.removeAll(() => {
        browser.contextMenus.create({
            id: "explain-with-ai",
            title: "Explain with AI",
            contexts: ["selection"],
        }, () => {
            if (browser.runtime.lastError) {
                console.log("[Aletheia] Context menu error (expected if already exists):", browser.runtime.lastError);
            } else {
                console.log("[Aletheia] Context menu created successfully");
            }
        });
    });
}

// Create immediately when script loads
createContextMenu();

// Also create on install (for first install)
browser.runtime.onInstalled.addListener(() => {
    console.log("[Aletheia] onInstalled fired");
    createContextMenu();
});

// === CONTEXT MENU HANDLER ===
browser.contextMenus.onClicked.addListener(async (info, tab) => {
    console.log("[Aletheia] Context menu clicked:", info.menuItemId);

    if (info.menuItemId === "explain-with-ai") {
        console.log("[Aletheia] Processing 'Explain with AI'...");

        const domain = extractDomain(info.pageUrl);
        console.log("[Aletheia] Domain:", domain);

        // [#156] PARALLEL OPTIMIZATION: Start allowlist check and overlay injection simultaneously
        // This reduces click-to-glass latency from ~500-1000ms to <200ms target
        console.log("[Aletheia] Starting parallel operations (allowlist, overlay)...");

        // Helper to inject overlay (returns success boolean)
        const injectOverlayPromise = (async () => {
            try {
                await browser.tabs.executeScript(tab.id, { file: 'overlay.js' });
                return true;
            } catch (e) {
                console.log("[Aletheia] Overlay injection failed (CSP?):", e.message);
                return false;
            }
        })();

        // Helper to check allowlist
        const allowlistPromise = (async () => {
            const result = await browser.storage.local.get('allowlist');
            const allowlist = result.allowlist || [];
            console.log("[Aletheia] Allowlist:", allowlist);
            return allowlist.includes(domain);
        })();

        // CRITICAL: Wait for BOTH operations to complete before checking results
        // This prevents race conditions where cleanup runs before injection finishes
        const [overlayInjected, isAllowlisted] = await Promise.all([
            injectOverlayPromise,
            allowlistPromise
        ]);

        // Check allowlist result
        if (!isAllowlisted) {
            console.log(`[Aletheia] Blocked: ${domain} not in allowlist`);
            if (overlayInjected) {
                // Overlay was injected optimistically, show warning message
                await browser.tabs.executeScript(tab.id, {
                    code: `window.showAletheiaOverlay("Enable Aletheia for this site", "warning");`
                });
            } else {
                await showFeedback(tab.id, "Enable Aletheia for this site", "warning");
            }
            return;
        }

        console.log("[Aletheia] Domain is allowlisted, proceeding...");

        try {
            // IMMEDIATE FEEDBACK - overlay already injected, just show "Saving..."
            console.log("[Aletheia] Showing immediate 'Saving...' feedback");
            if (overlayInjected) {
                await browser.tabs.executeScript(tab.id, {
                    code: `window.showAletheiaOverlay("Saving...", "warning", 30000);`
                });
            } else {
                // Fallback: inject and show (shouldn't happen often)
                await browser.tabs.executeScript(tab.id, { file: 'overlay.js' });
                await browser.tabs.executeScript(tab.id, {
                    code: `window.showAletheiaOverlay("Saving...", "warning", 30000);`
                });
            }

            // MV2: executeScript returns array of results
            console.log("[Aletheia] Getting page text...");
            const results = await browser.tabs.executeScript(tab.id, {
                code: 'document.body.innerText'
            });

            const fullPageText = results[0];
            console.log("[Aletheia] Got page text, length:", fullPageText?.length);

            const payload = {
                text: info.selectionText,
                url: info.pageUrl,
                title: tab.title,
                domContext: fullPageText
            };

            console.log("[Aletheia] Sending payload to AWS, text:", payload.text);

            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            console.log("[Aletheia] Response status:", response.status);

            // === UPDATE OVERLAY IN PLACE (no flicker) ===
            if (response.ok) {
                console.log("[Aletheia] Success, updating overlay...");
                await browser.tabs.executeScript(tab.id, {
                    code: `window.updateAletheiaOverlay("Context Saved", "success");`
                });
            } else {
                console.log("[Aletheia] Error response, updating overlay...");
                await browser.tabs.executeScript(tab.id, {
                    code: `window.updateAletheiaOverlay("Error Saving", "error");`
                });
            }

            // Set badge
            const badgeText = response.ok ? '✓' : '✗';
            const badgeColor = response.ok ? '#22C55E' : '#EF4444';
            browser.browserAction.setBadgeText({ tabId: tab.id, text: badgeText });
            browser.browserAction.setBadgeBackgroundColor({ tabId: tab.id, color: badgeColor });
            setTimeout(() => browser.browserAction.setBadgeText({ tabId: tab.id, text: '' }), 3000);

        } catch (error) {
            console.error("[Aletheia] Error:", error);
            await browser.tabs.executeScript(tab.id, {
                code: `window.updateAletheiaOverlay("Connection Error", "error");`
            });
            browser.browserAction.setBadgeText({ tabId: tab.id, text: '✗' });
            browser.browserAction.setBadgeBackgroundColor({ tabId: tab.id, color: '#EF4444' });
            setTimeout(() => browser.browserAction.setBadgeText({ tabId: tab.id, text: '' }), 3000);
        }
    }
});

console.log("[Aletheia] Background script initialization complete");
