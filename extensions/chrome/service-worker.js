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
// =============================================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
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

    // AGE GATE CHECK (Issue #104) - On-demand check using activeTab permission
    // We check NOW when user interacts, not proactively (respects ADR 0201)
    await checkTabForAgeRestriction(tab.id, tab.url);
    if (isTabRestricted(tab.id)) {
      console.log(`[Aletheia] Blocked: Age-restricted content on tab ${tab.id}`);
      await showFeedback(tab.id, "Not permitted on this site", "error");
      return;
    }

    // ALLOWLIST GATE
    const domain = extractDomain(info.pageUrl);
    const { allowlist = [] } = await chrome.storage.local.get('allowlist');

    if (!allowlist.includes(domain)) {
      console.log(`[Aletheia] Blocked: ${domain}`);
      await showFeedback(tab.id, "Enable Aletheia for this site", "warning");
      return;
    }

    try {
        // IMMEDIATE FEEDBACK - show "Saving..." with long timeout (won't expire before response)
        console.log("[Aletheia] Showing immediate 'Saving...' feedback");
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['overlay.js']
        });
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => window.showAletheiaOverlay("Saving...", "warning", 30000)
        });

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

        console.log("[CAV-3] Sending payload to AWS:", payload.text);

        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Aletheia-Client-Version': CLIENT_VERSION  // [#95] WAF header validation
            },
            body: JSON.stringify(payload)
        });

        // === UPDATE OVERLAY IN PLACE (no flicker) ===
        if (response.ok) {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => window.updateAletheiaOverlay("Context Saved", "success")
            });
        } else {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => window.updateAletheiaOverlay("Error Saving", "error")
            });
        }

        // Set badge
        const badgeText = response.ok ? '✓' : '✗';
        const badgeColor = response.ok ? '#22C55E' : '#EF4444';
        chrome.action.setBadgeText({ tabId: tab.id, text: badgeText });
        chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: badgeColor });
        setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: '' }), 3000);

    } catch (error) {
        console.error("[CV-6] Error:", error);
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => window.updateAletheiaOverlay("Connection Error", "error")
        });
        chrome.action.setBadgeText({ tabId: tab.id, text: '✗' });
        chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: '#EF4444' });
        setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: '' }), 3000);
    }
  }
});
