// extensions/chrome/service-worker.js
// Chrome Manifest V3 version

// [CV-7] CONSTANTS - WIRED TO CLOUDFRONT (WAF-protected)
// Direct Lambda URL: https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/
const API_ENDPOINT = "https://d1fkpkls2wesse.cloudfront.net/";

// [#95] Client version for WAF header validation
// Must start with "1." to pass WAF rule (see docs/1095-security-hardening.md)
const CLIENT_VERSION = "1.0";

// =============================================================================
// AGE GATE - Tab State Management (Issue #104)
// =============================================================================

// Three-state model for race condition handling
const TabState = {
    UNKNOWN: 'unknown',      // Not yet checked (initial state)
    RESTRICTED: 'restricted', // Adult content detected
    ALLOWED: 'allowed'        // No adult content
};

// In-memory tab states (no persistence - privacy by design)
const tabStates = new Map();

/**
 * Check if a URL should be checked for age-restricted content.
 * Only check navigable web pages (http/https).
 */
function shouldCheckTab(url) {
    if (!url) return false;
    return url.startsWith('http://') || url.startsWith('https://');
}

/**
 * Check a tab for age-restricted content by injecting content-check.js
 */
async function checkTabForAgeRestriction(tabId, url) {
    if (!shouldCheckTab(url)) {
        // Non-web pages are allowed (chrome://, file://, etc.)
        tabStates.set(tabId, TabState.ALLOWED);
        return;
    }

    try {
        // Inject and execute content-check.js
        const results = await chrome.scripting.executeScript({
            target: { tabId },
            files: ['content-check.js']
        });

        // The script returns the result from checkPageRating()
        const result = results?.[0]?.result;

        if (result?.isRestricted) {
            tabStates.set(tabId, TabState.RESTRICTED);
            await setRestrictedBadge(tabId);
            console.log(`[Aletheia] Age-restricted content detected on tab ${tabId}:`, result.ratingValue);
        } else {
            tabStates.set(tabId, TabState.ALLOWED);
            console.log(`[Aletheia] Tab ${tabId} allowed:`, result?.ratingValue || 'no rating');
        }
    } catch (error) {
        // FAIL OPEN: If we can't inject (CSP, etc.), allow the tab
        tabStates.set(tabId, TabState.ALLOWED);
        console.log(`[Aletheia] Tab ${tabId} check failed (fail open):`, error.message);
    }
}

/**
 * Set the prohibition badge icon for a restricted tab
 */
async function setRestrictedBadge(tabId) {
    try {
        // Red prohibition badge
        await chrome.action.setBadgeText({ tabId, text: '⊘' });
        await chrome.action.setBadgeBackgroundColor({ tabId, color: '#DC2626' });
    } catch (error) {
        console.error('[Aletheia] Failed to set restricted badge:', error);
    }
}

/**
 * Clear the restriction badge when state changes
 * @unused Reserved for future navigation handling
 */
async function _clearRestrictedBadge(tabId) {
    try {
        await chrome.action.setBadgeText({ tabId, text: '' });
    } catch (_err) {
        // Tab may have closed - ignore
    }
}

/**
 * Get the current state for a tab
 */
function getTabState(tabId) {
    return tabStates.get(tabId) || TabState.UNKNOWN;
}

/**
 * Check if a tab is restricted
 */
function isTabRestricted(tabId) {
    return getTabState(tabId) === TabState.RESTRICTED;
}

// =============================================================================
// TAB EVENT LISTENERS (Age Gate)
// =============================================================================

// NOTE: We do NOT proactively check tabs on load - that would require <all_urls>.
// Instead, we check ON-DEMAND when user interacts (activeTab grants permission).
// See ADR 0201: Privacy-First Extension Permissions.

// Clean up state when tabs close (memory hygiene)
chrome.tabs.onRemoved.addListener((tabId) => {
    tabStates.delete(tabId);
});

// =============================================================================
// MESSAGE HANDLERS (Issue #104 - Popup Communication)
// Security: ADR 0213 - Validate sender.id to prevent message spoofing
// =============================================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Security: Validate message comes from our extension (not a hostile page/extension)
    // sender.id is the extension ID for extension messages, undefined for content scripts
    // We accept messages from our own extension (popup) or our own content scripts
    if (sender.id && sender.id !== chrome.runtime.id) {
        console.warn('[Aletheia] Rejected message from unknown sender:', sender.id);
        return false;
    }

    if (message.type === 'GET_TAB_STATE') {
        const state = getTabState(message.tabId);
        sendResponse({ state });
        return false; // Synchronous response
    }

    if (message.type === 'RECHECK_TAB') {
        // Async operation - need to return true and call sendResponse later
        (async () => {
            try {
                const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
                if (tab && tab.url) {
                    await checkTabForAgeRestriction(tab.id, tab.url);
                }
                sendResponse({ success: true });
            } catch (error) {
                console.error('[Aletheia] Recheck failed:', error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true; // Will respond asynchronously
    }

    return false;
});

// =============================================================================
// CORE EXTENSION LOGIC
// =============================================================================

function extractDomain(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return null;
  }
}

// === HELPER FUNCTION ===
async function showFeedback(tabId, message, type) {
    try {
        // 1. Inject Library (Idempotent)
        await chrome.scripting.executeScript({
            target: { tabId },
            files: ['overlay.js']
        });

        // 2. Call Function
        await chrome.scripting.executeScript({
            target: { tabId },
            func: (m, t) => window.showAletheiaOverlay(m, t),
            args: [message, type]
        });

        // 3. Set Toolbar Badge
        const badgeText = type === 'success' ? '✓' : (type === 'error' ? '✗' : '!');
        const badgeColor = type === 'success' ? '#22C55E' : (type === 'error' ? '#EF4444' : '#FBBF24');

        chrome.action.setBadgeText({ tabId, text: badgeText });
        chrome.action.setBadgeBackgroundColor({ tabId, color: badgeColor });

        setTimeout(() => chrome.action.setBadgeText({ tabId, text: '' }), 3000);

    } catch (e) {
        console.error("Overlay Injection Failed:", e);
    }
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "explain-with-ai",
    title: "Explain with AI",
    contexts: ["selection"],
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "explain-with-ai") {
    const domain = extractDomain(info.pageUrl);

    // [#156] PARALLEL OPTIMIZATION: Start all checks and overlay injection simultaneously
    // This reduces click-to-glass latency from ~500-1000ms to <200ms target
    console.log("[Aletheia] Starting parallel operations (age gate, allowlist, overlay)...");

    // Helper to inject overlay (returns success boolean)
    const injectOverlayPromise = (async () => {
        try {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['overlay.js']
            });
            return true;
        } catch (e) {
            console.log("[Aletheia] Overlay injection failed (CSP?):", e.message);
            return false;
        }
    })();

    // Helper to check allowlist
    const allowlistPromise = (async () => {
        const { allowlist = [] } = await chrome.storage.local.get('allowlist');
        return allowlist.includes(domain);
    })();

    // Helper for age gate (already mutates tabStates, returns void)
    const ageGatePromise = checkTabForAgeRestriction(tab.id, tab.url);

    // CRITICAL: Wait for ALL operations to complete before checking results
    // This prevents race conditions where cleanup runs before injection finishes
    const [overlayInjected, isAllowlisted] = await Promise.all([
        injectOverlayPromise,
        allowlistPromise,
        ageGatePromise  // We don't need its return value, just wait for completion
    ]);

    // Now check results - age gate first (most severe)
    if (isTabRestricted(tab.id)) {
        console.log(`[Aletheia] Blocked: Age-restricted content on tab ${tab.id}`);
        if (overlayInjected) {
            // Overlay was injected optimistically, show error message
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => window.showAletheiaOverlay("Not permitted on this site", "error")
            });
        } else {
            await showFeedback(tab.id, "Not permitted on this site", "error");
        }
        return;
    }

    // Check allowlist
    if (!isAllowlisted) {
        console.log(`[Aletheia] Blocked: ${domain} not in allowlist`);
        if (overlayInjected) {
            // Overlay was injected optimistically, show warning message
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => window.showAletheiaOverlay("Enable Aletheia for this site", "warning")
            });
            // [FIX] Also set the warning badge (was missing when overlay pre-injected)
            chrome.action.setBadgeText({ tabId: tab.id, text: '!' });
            chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: '#FBBF24' });
            setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: '' }), 3000);
        } else {
            await showFeedback(tab.id, "Enable Aletheia for this site", "warning");
        }
        return;
    }

    try {
        // [#125] MUSEUM LABEL UI - Show loading state
        console.log("[Aletheia] Showing loading overlay...");
        if (overlayInjected) {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => window.showAletheiaLoading()
            });
        } else {
            // Fallback: inject and show (shouldn't happen often)
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['overlay.js']
            });
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => window.showAletheiaLoading()
            });
        }

        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => document.body.innerText,
        });

        const fullPageText = injectionResults[0].result;

        const payload = {
            text: info.selectionText,
            url: info.pageUrl,
            title: tab.title,
            domContext: fullPageText
        };

        console.log("[Aletheia] Sending payload to AWS:", payload.text);

        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Aletheia-Client-Version': CLIENT_VERSION  // [#95] WAF header validation
            },
            body: JSON.stringify(payload)
        });

        // [#125] MUSEUM LABEL UI - Parse response and show structured result
        const httpStatus = response.status;
        let responseData;

        try {
            responseData = await response.json();
        } catch (parseError) {
            console.error("[Aletheia] Failed to parse response JSON:", parseError);
            responseData = { signal: "Error", gem: "Failed to parse server response." };
        }

        console.log("[Aletheia] Response:", httpStatus, responseData);

        // Show Museum Label overlay with structured data
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: (data, status) => window.showAletheiaResult(data, status),
            args: [responseData, httpStatus]
        });

        // Set badge based on status
        const badgeText = response.ok ? '✓' : (httpStatus === 403 ? '⊘' : '✗');
        const badgeColor = response.ok ? '#22C55E' : '#EF4444';
        chrome.action.setBadgeText({ tabId: tab.id, text: badgeText });
        chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: badgeColor });
        setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: '' }), 5000);

    } catch (error) {
        console.error("[Aletheia] Error:", error);
        // Show error in Museum Label format
        const errorResponse = {
            signal: "Connection Error",
            gem: "Could not reach the server. Please try again.",
            context: ""
        };
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: (data) => window.showAletheiaResult(data, 500),
            args: [errorResponse]
        });
        chrome.action.setBadgeText({ tabId: tab.id, text: '✗' });
        chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: '#EF4444' });
        setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: '' }), 5000);
    }
  }
});
