// extension/service-worker.js

// [CV-7] CONSTANTS - WIRED TO AWS LAMBDA
const API_ENDPOINT = "https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/";

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
 */
async function clearRestrictedBadge(tabId) {
    try {
        await chrome.action.setBadgeText({ tabId, text: '' });
    } catch (error) {
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
// Tab Lifecycle Listeners
// =============================================================================

// Check tabs when they load or navigate
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // Only check when page has completed loading
    if (changeInfo.status === 'complete' && tab.url) {
        // Set to UNKNOWN while checking
        tabStates.set(tabId, TabState.UNKNOWN);
        await checkTabForAgeRestriction(tabId, tab.url);
    }
});

// Clean up state when tabs are closed
chrome.tabs.onRemoved.addListener((tabId) => {
    tabStates.delete(tabId);
    console.log(`[Aletheia] Cleaned up state for closed tab ${tabId}`);
});

// Handle messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'GET_TAB_STATE') {
        sendResponse({ state: getTabState(message.tabId) });
        return true;
    }

    if (message.type === 'RECHECK_TAB') {
        // Re-check a tab (used when popup opens during UNKNOWN state)
        chrome.tabs.get(message.tabId, async (tab) => {
            if (tab?.url) {
                await checkTabForAgeRestriction(message.tabId, tab.url);
                sendResponse({ state: getTabState(message.tabId) });
            } else {
                sendResponse({ state: TabState.ALLOWED });
            }
        });
        return true; // Keep channel open for async response
    }

    return false;
});

// =============================================================================
// Original Functionality
// =============================================================================

function extractDomain(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return null;
  }
}

// === NEW: HELPER FUNCTION ===
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

    // AGE GATE CHECK (Issue #104) - Must come before allowlist check
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
      // === RESTORED FUNCTIONALITY ===
      await showFeedback(tab.id, "Enable Aletheia for this site", "warning");
      return;
    }

    try {
        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => document.body.innerText,
        });

        const fullPageText = injectionResults[0].result;

        const payload = {
            word: info.selectionText,
            url: info.pageUrl,
            title: tab.title,
            context: fullPageText
        };
        
        console.log("[CAV-3] Sending payload to AWS:", payload.word);

        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        // === FEEDBACK FOR SUCCESS/ERROR ===
        if (response.ok) {
            await showFeedback(tab.id, "Context Saved", "success");
        } else {
            await showFeedback(tab.id, "Error Saving", "error");
        }

    } catch (error) {
        console.error("[CV-6] Error:", error);
        // === FEEDBACK FOR NETWORK ERROR ===
        await showFeedback(tab.id, "Connection Error", "error");
    }
  }
});