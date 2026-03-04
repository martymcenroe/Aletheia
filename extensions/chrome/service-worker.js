// extensions/chrome/service-worker.js
// Chrome Manifest V3 version

// [CV-7] CONSTANTS - WIRED TO CLOUDFLARE (Worker-proxied, rate-limited)
const API_ENDPOINT = "https://api.aletheia.study/";

// [#95] Client version for Lambda header validation (Issue #349: moved from WAF to Lambda)
const CLIENT_VERSION = "1.0";

// Issue #402: Auth header injection
async function getAuthHeaders() {
    const session = await chrome.storage.session.get(['jwt']);
    const headers = {
        'Content-Type': 'application/json',
        'X-Aletheia-Client-Version': CLIENT_VERSION
    };
    if (session.jwt) headers['Authorization'] = `Bearer ${session.jwt}`;
    return headers;
}

// =============================================================================
// Issue #391 Phase 2: Error Handling Helpers
// =============================================================================

/**
 * Map HTTP status codes to user-friendly error messages.
 * Returns a response object suitable for overlay display.
 */
function mapHttpStatusToMessage(status, responseBody) {
    if (status === 401) {
        return {
            signal: "Sign In Required",
            gem: "Please sign in with LinkedIn to use Aletheia.",
            context: "",
            warning: true
        };
    }
    if (status === 429) {
        const resetSeconds = responseBody?.resets_in_seconds || 0;
        const resetMinutes = Math.ceil(resetSeconds / 60);
        const resetText = resetMinutes > 0 ? ` Resets in ${resetMinutes} minutes.` : "";
        return {
            signal: "Rate Limited",
            gem: `Limit reached.${resetText}`,
            context: "",
            warning: true
        };
    }
    if (status >= 500) {
        return {
            signal: "Server Error",
            gem: "Server error. Try again shortly.",
            context: "",
            warning: true
        };
    }
    // Other 4xx — return original response with fallback
    return {
        signal: responseBody?.signal || "Error",
        gem: responseBody?.gem || responseBody?.error || `Request failed (${status}).`,
        context: responseBody?.context || "",
        warning: true
    };
}

/**
 * Store request diagnostics in chrome.storage.session.
 * Cleared on browser restart. Non-blocking, fail-open.
 */
function storeDiagnostics(status, latencyMs, error) {
    try {
        chrome.storage.session.set({
            aletheiaLastRequest: {
                lastRequestStatus: status,
                lastRequestLatency: latencyMs,
                lastRequestTimestamp: new Date().toISOString(),
                lastError: error || null
            }
        });
    } catch (e) {
        console.warn("[Aletheia] Failed to store diagnostics:", e);
    }
}

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

// Issue #162: Store noarchive signals per tab
const tabNoArchive = new Map();

/**
 * Check if a URL should be checked for age-restricted content.
 * Only check navigable web pages (http/https).
 */
function shouldCheckTab(url) {
    if (!url) return false;
    return url.startsWith('http://') || url.startsWith('https://');
}

/**
 * Check a tab for age-restricted content and noarchive signal by injecting content-check.js
 * Issue #104: Age-Restricted Blocking
 * Issue #162: NoArchive Transform Layer
 */
async function checkTabForAgeRestriction(tabId, url) {
    if (!shouldCheckTab(url)) {
        // Non-web pages are allowed (chrome://, file://, etc.)
        tabStates.set(tabId, TabState.ALLOWED);
        tabNoArchive.set(tabId, false);
        return;
    }

    try {
        // Inject and execute content-check.js
        const results = await chrome.scripting.executeScript({
            target: { tabId },
            files: ['content-check.js']
        });

        // The script returns the result from checkPageSignals()
        const result = results?.[0]?.result;

        // Issue #162: Store noarchive signal
        tabNoArchive.set(tabId, result?.noarchive || false);
        if (result?.noarchive) {
            console.log(`[Aletheia] NoArchive signal detected on tab ${tabId}`);
        }

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
        tabNoArchive.set(tabId, false);
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
    tabNoArchive.delete(tabId);  // Issue #162
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

    // Issue #106: Get noarchive status for full page analysis
    if (message.type === 'GET_NOARCHIVE_STATUS') {
        const noarchive = tabNoArchive.get(message.tabId) || false;
        sendResponse({ noarchive });
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

    // Issue #310: Handle deep poetic analysis request from overlay
    // Issue #480: OAuth flow — delegate from popup to service worker
    // chrome.identity.launchWebAuthFlow survives popup closure when called from SW
    if (message.type === 'START_OAUTH') {
        (async () => {
            try {
                const { authUrl, lambdaAuthUrl } = message;

                // 1. Launch OAuth flow from SW (survives popup closure)
                const responseUrl = await chrome.identity.launchWebAuthFlow({
                    url: authUrl,
                    interactive: true
                });

                // 2. Parse response URL
                const url = new URL(responseUrl);
                const code = url.searchParams.get('code');
                const returnedState = url.searchParams.get('state');
                const error = url.searchParams.get('error');

                if (error) {
                    await chrome.storage.session.set({ authError: error });
                    try { sendResponse({ success: false, error }); } catch (_e) { /* popup closed */ }
                    return;
                }

                if (!code) {
                    await chrome.storage.session.set({ authError: 'No authorization code received' });
                    try { sendResponse({ success: false, error: 'No authorization code' }); } catch (_e) { /* popup closed */ }
                    return;
                }

                // 3. Validate CSRF state
                const stored = await chrome.storage.session.get(['oauth_state']);
                if (returnedState !== stored.oauth_state) {
                    await chrome.storage.session.set({ authError: 'CSRF state mismatch' });
                    try { sendResponse({ success: false, error: 'CSRF state mismatch' }); } catch (_e) { /* popup closed */ }
                    return;
                }
                await chrome.storage.session.remove(['oauth_state']);

                // 4. Exchange code for tokens via Lambda
                const redirectUri = chrome.identity.getRedirectURL();
                console.log('[Aletheia Auth SW] Exchanging code for tokens...');
                const tokenResponse = await fetch(
                    `${lambdaAuthUrl}/auth/token`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ code, redirectUri })
                    }
                );

                if (!tokenResponse.ok) {
                    const errData = await tokenResponse.json().catch(() => ({}));
                    const errMsg = errData.error || `Token exchange failed: ${tokenResponse.status}`;
                    await chrome.storage.session.set({ authError: errMsg });
                    try { sendResponse({ success: false, error: errMsg }); } catch (_e) { /* popup closed */ }
                    return;
                }

                const tokenData = await tokenResponse.json();

                // 5. Store tokens
                await chrome.storage.session.set({
                    accessToken: tokenData.accessToken,
                    expiresAt: Date.now() + (tokenData.expiresIn * 1000),
                    jwt: tokenData.jwt || null
                });
                await chrome.storage.local.set({
                    refreshToken: tokenData.refreshToken,
                    userId: tokenData.user.id,
                    displayName: tokenData.user.name
                });

                // Clear any previous error
                await chrome.storage.session.remove(['authError']);
                console.log('[Aletheia Auth SW] Login successful:', tokenData.user.name);

                try {
                    sendResponse({ success: true, user: tokenData.user });
                } catch (_e) {
                    // Popup already closed — expected
                }
            } catch (error) {
                console.error('[Aletheia Auth SW] OAuth error:', error);
                await chrome.storage.session.set({ authError: error.message || 'OAuth failed' }).catch(() => {});
                try {
                    sendResponse({ success: false, error: error.message });
                } catch (_e) { /* popup closed */ }
            }
        })();
        return true; // Will respond asynchronously
    }

    if (message.type === 'DEEP_POETIC_ANALYSIS') {
        (async () => {
            try {
                const payload = message.payload;
                console.log('[Aletheia] Deep poetic analysis request:', payload.text);

                const response = await fetch(API_ENDPOINT, {
                    method: 'POST',
                    headers: await getAuthHeaders(),
                    body: JSON.stringify(payload)
                });

                const data = await response.json();
                console.log('[Aletheia] Deep poetic analysis response:', data.status);

                if (data.status === 'success') {
                    sendResponse({
                        status: 'success',
                        synthesis: data.synthesis,
                        dimensions: data.dimensions,
                        resonance_strength: data.resonance_strength,
                        latency_ms: data.latency_ms
                    });
                } else {
                    sendResponse({
                        status: 'error',
                        error: 'Analysis failed'
                    });
                }
            } catch (error) {
                console.error('[Aletheia] Deep poetic analysis error:', error);
                sendResponse({
                    status: 'error',
                    error: error.message || 'Network error'
                });
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

        // Issue #162: Include noarchive signal in payload
        const hasNoArchive = tabNoArchive.get(tab.id) || false;

        const payload = {
            text: info.selectionText,
            url: info.pageUrl,
            title: tab.title,
            domContext: fullPageText,
            signals: {
                noarchive: hasNoArchive
            }
        };

        console.log("[Aletheia] Sending payload to AWS:", payload.text);

        // Issue #391 Phase 2: AbortController with 30s timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        const fetchStart = Date.now();

        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify(payload),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        const latencyMs = Date.now() - fetchStart;

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

        // Issue #391 Phase 2: Map HTTP errors to user-friendly messages
        if (httpStatus >= 400) {
            responseData = mapHttpStatusToMessage(httpStatus, responseData);
        }

        // Issue #391 Phase 2: Validate response schema — must have signal/gem
        if (httpStatus < 400 && (!responseData.signal || !responseData.gem)) {
            responseData = {
                signal: "Unexpected Response",
                gem: "The server returned an unexpected response format.",
                context: "",
                warning: true
            };
        }

        // Issue #391 Phase 2: Store diagnostics in chrome.storage.session
        storeDiagnostics(httpStatus, latencyMs, httpStatus >= 400 ? responseData.gem : null);

        // Issue #310: Add selectedText and domContext for deep poetic analysis
        responseData.selectedText = info.selectionText;
        responseData.domContext = fullPageText;

        // Show Museum Label overlay with structured data
        try {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: (data, status) => window.showAletheiaResult(data, status),
                args: [responseData, httpStatus]
            });
        } catch (cspError) {
            // Issue #391 Phase 2: CSP fallback — use chrome.notifications
            console.warn("[Aletheia] CSP blocked overlay injection, using notification fallback:", cspError);
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon128.png',
                title: responseData.signal || 'Aletheia',
                message: responseData.gem || 'Analysis complete.'
            });
        }

        // Set badge based on status
        const badgeText = response.ok ? '✓' : (httpStatus === 403 ? '⊘' : '✗');
        const badgeColor = response.ok ? '#22C55E' : '#EF4444';
        chrome.action.setBadgeText({ tabId: tab.id, text: badgeText });
        chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: badgeColor });
        setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: '' }), 5000);

    } catch (error) {
        console.error("[Aletheia] Error:", error);

        // Issue #391 Phase 2: Distinguish timeout from other errors
        let errorResponse;
        if (error.name === 'AbortError') {
            errorResponse = {
                signal: "Timeout",
                gem: "Request timed out. Try again.",
                context: ""
            };
        } else {
            errorResponse = {
                signal: "Connection Error",
                gem: "Could not reach the server. Please try again.",
                context: ""
            };
        }

        // Store error diagnostics
        storeDiagnostics(0, 0, errorResponse.gem);

        try {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: (data) => window.showAletheiaResult(data, 500),
                args: [errorResponse]
            });
        } catch (_cspError) {
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon128.png',
                title: errorResponse.signal,
                message: errorResponse.gem
            });
        }
        chrome.action.setBadgeText({ tabId: tab.id, text: '✗' });
        chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: '#EF4444' });
        setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: '' }), 5000);
    }
  }
});
