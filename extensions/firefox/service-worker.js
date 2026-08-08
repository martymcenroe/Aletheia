// extensions/firefox/service-worker.js
// Firefox Manifest V3 version

// [CV-7] CONSTANTS - WIRED TO CLOUDFLARE (Worker-proxied, rate-limited)
const API_ENDPOINT = "https://api.aletheia.study/";

// [#95] Client version for Lambda header validation (Issue #349: moved from WAF to Lambda)
const CLIENT_VERSION = "1.0";

// Server mints JWTs with a 24h life (Issue #811).
const JWT_LIFETIME_SECONDS = 24 * 3600;

// Renew ahead of expiry so a request cannot race the boundary.
const JWT_RENEWAL_BUFFER_MS = 5 * 60 * 1000;

// One renewal shared across concurrent callers, not N parallel ones.
let _inFlightRenewal = null;

/**
 * Renew the JWT from the persisted Aletheia refresh token (Issue #811).
 *
 * The service worker cannot import auth.js, so this mirrors its renewal logic.
 * Both must stay in step; the shared contract is the /auth/refresh payload.
 *
 * @returns {Promise<string | null>} Fresh JWT, or null if renewal is impossible
 */
async function renewJwt() {
    if (_inFlightRenewal) return await _inFlightRenewal;

    _inFlightRenewal = (async () => {
        const local = await chrome.storage.local.get(['aletheiaRefreshToken']);
        if (!local.aletheiaRefreshToken) return null;

        try {
            const response = await fetch("https://api.aletheia.study/auth/refresh", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ aletheiaRefreshToken: local.aletheiaRefreshToken })
            });

            if (!response.ok) {
                // 401 means revoked or expired: renewal can never succeed again,
                // so drop the token and require a real sign-in. Any other status
                // (5xx, offline) is transient — keep it and retry later.
                if (response.status === 401) {
                    await chrome.storage.local.remove(['aletheiaRefreshToken']);
                }
                console.error('[Aletheia] JWT renewal failed:', response.status);
                return null;
            }

            const data = await response.json();
            if (!data.jwt) return null;

            await chrome.storage.session.set({
                jwt: data.jwt,
                jwtExpiresAt: Date.now() + ((data.expiresIn || JWT_LIFETIME_SECONDS) * 1000)
            });
            console.log('[Aletheia] JWT renewed silently');
            return data.jwt;

        } catch (error) {
            console.error('[Aletheia] JWT renewal error:', error.name);
            return null;
        }
    })();

    try {
        return await _inFlightRenewal;
    } finally {
        _inFlightRenewal = null;
    }
}

/**
 * Get a usable JWT, renewing silently when the cached one is stale or absent.
 * @returns {Promise<string | null>}
 */
async function getValidJwt() {
    const session = await chrome.storage.session.get(['jwt', 'jwtExpiresAt']);

    const stillFresh = session.jwt &&
        session.jwtExpiresAt &&
        Date.now() < (session.jwtExpiresAt - JWT_RENEWAL_BUFFER_MS);

    if (stillFresh) return session.jwt;

    const renewed = await renewJwt();
    if (renewed) return renewed;

    // Legacy session from a build predating jwtExpiresAt (#812): renewal is
    // impossible because no refresh token was ever issued, but the cached JWT
    // may still be valid. Use it and let the 401 path decide, rather than
    // forcing a sign-in we cannot prove is needed.
    return session.jwt || null;
}

/**
 * Issue #402: Auth header injection. Issue #814: renew rather than dispatch
 * a request already known to fail.
 *
 * Previously this read the JWT, found nothing, and sent the request anyway
 * with no Authorization header — turning a recoverable missing-credential
 * condition into a terminal "Sign In Required".
 *
 * @returns {Promise<object|null>} Headers, or null when no credential is
 *   obtainable. Callers MUST NOT dispatch on null.
 */
async function getAuthHeaders() {
    const jwt = await getValidJwt();
    if (!jwt) return null;

    return {
        'Content-Type': 'application/json',
        'X-Aletheia-Client-Version': CLIENT_VERSION,
        'Authorization': `Bearer ${jwt}`
    };
}

/**
 * POST to the API with a live credential, recovering once from a 401.
 *
 * Issue #814. A 401 can mean the cached JWT died between the freshness check
 * and the server receiving it. That is recoverable, so renew and retry exactly
 * once. Strictly one retry: no loop, no recursion — a renewal storm against
 * the auth Lambda would turn a transient failure into an outage.
 *
 * @param {object} payload - JSON body
 * @returns {Promise<Response|null>} Response, or null if no credential exists
 */
async function authedPost(payload) {
    const headers = await getAuthHeaders();

    // No credential obtainable: do not dispatch a request known to fail.
    if (!headers) return null;

    const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
    });

    if (response.status !== 401) return response;

    console.log('[Aletheia] 401 received; renewing once and retrying');
    const freshJwt = await renewJwt();
    if (!freshJwt) return response;

    return await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: { ...headers, 'Authorization': `Bearer ${freshJwt}` },
        body: JSON.stringify(payload)
    });
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
// OAUTH TAB LISTENERS (Issue #396 - Persistent State)
// Top-level listeners survive Firefox background script suspension/restart.
// State is stored in chrome.storage.session as `pendingOAuth`.
// =============================================================================

// Issue #396: Detect OAuth callback in auth tab
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    // Only process 'complete' status changes
    if (changeInfo.status !== 'complete') return;

    (async () => {
        try {
            const { pendingOAuth } = await chrome.storage.session.get('pendingOAuth');
            if (!pendingOAuth) return;
            if (tabId !== pendingOAuth.tabId) return;

            // Stale check: ignore if older than 5 minutes
            if (Date.now() - pendingOAuth.startedAt > 5 * 60 * 1000) {
                console.log('[Aletheia Auth SW] Stale OAuth detected, clearing');
                await chrome.storage.session.remove('pendingOAuth');
                chrome.tabs.remove(tabId).catch(() => {});
                return;
            }

            // Check if this tab navigated to the callback URL
            if (!tab.url || !tab.url.startsWith(pendingOAuth.callbackUrl)) return;

            // Parse the callback URL
            const url = new URL(tab.url);
            const code = url.searchParams.get('code');
            const returnedState = url.searchParams.get('state');
            const error = url.searchParams.get('error');
            const errorDesc = url.searchParams.get('error_description');

            // Close the auth tab
            chrome.tabs.remove(tabId).catch(() => {});

            if (error) {
                console.error('[Aletheia Auth SW] OAuth error:', errorDesc || error);
                await chrome.storage.session.remove('pendingOAuth');
                return;
            }

            if (!code) {
                console.error('[Aletheia Auth SW] No authorization code received');
                await chrome.storage.session.remove('pendingOAuth');
                return;
            }

            // Validate CSRF state
            if (returnedState !== pendingOAuth.state) {
                console.error('[Aletheia Auth SW] CSRF detected: state mismatch');
                await chrome.storage.session.remove('pendingOAuth');
                return;
            }

            // Exchange code for tokens
            console.log('[Aletheia Auth SW] Exchanging code for tokens...');
            const tokenResponse = await fetch(
                `${pendingOAuth.lambdaAuthUrl}/auth/token`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code: code,
                        redirectUri: pendingOAuth.callbackUrl
                    })
                }
            );

            if (!tokenResponse.ok) {
                const errorData = await tokenResponse.json().catch(() => ({}));
                console.error('[Aletheia Auth SW] Token exchange failed:', errorData.error || tokenResponse.status);
                await chrome.storage.session.remove('pendingOAuth');
                return;
            }

            const tokenData = await tokenResponse.json();

            // Store tokens. Issue #812: the Aletheia refresh token goes to LOCAL
            // storage so the session survives a browser restart — session storage
            // is cleared on close, which is what previously destroyed the only
            // credential the API accepts while leaving identity intact.
            await chrome.storage.session.set({
                accessToken: tokenData.accessToken,
                expiresAt: Date.now() + (tokenData.expiresIn * 1000),
                jwt: tokenData.jwt || null,
                jwtExpiresAt: tokenData.jwt
                    ? Date.now() + (JWT_LIFETIME_SECONDS * 1000)
                    : 0
            });

            const localData = {
                refreshToken: tokenData.refreshToken,
                userId: tokenData.user.id,
                displayName: tokenData.user.name
            };

            if (tokenData.aletheiaRefreshToken) {
                localData.aletheiaRefreshToken = tokenData.aletheiaRefreshToken;
            } else {
                // A login that yields no refresh token produces a session that
                // dies in 24h with no recovery — the original defect. Surface it
                // rather than letting it look like a clean login.
                console.error(
                    '[Aletheia Auth SW] Login returned no aletheiaRefreshToken; ' +
                    'session cannot renew. Auth Lambda may predate issue #811.'
                );
            }

            await chrome.storage.local.set(localData);

            // Clear pending state
            await chrome.storage.session.remove('pendingOAuth');

            console.log('[Aletheia Auth SW] Login successful:', tokenData.user.name);
        } catch (error) {
            console.error('[Aletheia Auth SW] OAuth callback error:', error);
            await chrome.storage.session.remove('pendingOAuth').catch(() => {});
        }
    })();
});

// Issue #396: Clean up pendingOAuth when auth tab is closed by user
chrome.tabs.onRemoved.addListener((tabId) => {
    (async () => {
        try {
            const { pendingOAuth } = await chrome.storage.session.get('pendingOAuth');
            if (pendingOAuth && pendingOAuth.tabId === tabId) {
                console.log('[Aletheia Auth SW] Auth tab closed, clearing pendingOAuth');
                await chrome.storage.session.remove('pendingOAuth');
            }
        } catch (_e) {
            // Ignore - tab may have been removed during shutdown
        }
    })();
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
    if (message.type === 'DEEP_POETIC_ANALYSIS') {
        (async () => {
            try {
                const payload = message.payload;
                console.log('[Aletheia] Deep poetic analysis request:', payload.text);

                const response = await authedPost(payload);

                if (response === null) {
                    sendResponse({
                        status: 'error',
                        error: 'Sign in with LinkedIn to use Aletheia.'
                    });
                    return;
                }

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

    // Issue #396: OAuth flow — open auth tab and store persistent state
    // Top-level onUpdated listener handles callback detection (survives SW restart)
    if (message.type === 'START_OAUTH') {
        (async () => {
            try {
                const { authUrl, callbackUrl, state, lambdaAuthUrl } = message;

                // 1. Open LinkedIn auth tab
                const tab = await chrome.tabs.create({ url: authUrl });
                console.log('[Aletheia Auth SW] Opened auth tab:', tab.id);

                // 2. Store pending OAuth state (survives SW suspension/restart)
                await chrome.storage.session.set({
                    pendingOAuth: {
                        tabId: tab.id,
                        state,
                        callbackUrl,
                        lambdaAuthUrl,
                        startedAt: Date.now()
                    }
                });

                // 3. Respond immediately — popup may close, tokens arrive via top-level listener
                try {
                    sendResponse({ success: true, pending: true });
                } catch (_e) {
                    // Popup already closed — expected behavior
                }
            } catch (error) {
                console.error('[Aletheia Auth SW] OAuth start failed:', error);
                try {
                    sendResponse({ success: false, error: error.message });
                } catch (_e) {
                    // Popup already closed
                }
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

        // Issue #528: Extract focused context window around selected text
        // ~1000 chars before and after selection instead of full page DOM
        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: (selectedText) => {
                const fullText = document.body.innerText;
                const WINDOW = 1000;
                const pos = fullText.indexOf(selectedText);
                if (pos === -1) return fullText.slice(0, 2000);
                const start = Math.max(0, pos - WINDOW);
                const end = Math.min(fullText.length, pos + selectedText.length + WINDOW);
                return fullText.slice(start, end);
            },
            args: [info.selectionText]
        });

        const contextText = injectionResults[0].result;

        // Issue #162: Include noarchive signal in payload
        const hasNoArchive = tabNoArchive.get(tab.id) || false;

        const payload = {
            text: info.selectionText,
            url: info.pageUrl,
            title: tab.title,
            domContext: contextText,
            signals: {
                noarchive: hasNoArchive
            }
        };

        console.log("[Aletheia] Sending payload to AWS:", payload.text);

        const response = await authedPost(payload);

        // Issue #814: null means no credential could be obtained even after a
        // renewal attempt. This is the genuine sign-in case — distinct from a
        // 401, which now only survives after renewal has already been tried.
        if (response === null) {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: (data, status) => window.showAletheiaResult(data, status),
                args: [{
                    signal: "Sign In Required",
                    gem: "Please sign in with LinkedIn to use Aletheia.",
                    context: "",
                    warning: true,
                    selectedText: info.selectionText,
                    domContext: contextText
                }, 401]
            });
            chrome.action.setBadgeText({ tabId: tab.id, text: '✗' });
            chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: '#EF4444' });
            setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: '' }), 5000);
            return;
        }

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

        // Map HTTP errors to user-friendly messages (parity with Chrome SW)
        if (httpStatus === 401) {
            responseData = {
                signal: "Sign In Required",
                gem: "Please sign in with LinkedIn to use Aletheia.",
                context: "",
                warning: true
            };
        } else if (httpStatus === 429) {
            const resetSeconds = responseData?.resets_in_seconds || 0;
            const resetMinutes = Math.ceil(resetSeconds / 60);
            const resetText = resetMinutes > 0 ? ` Resets in ${resetMinutes} minutes.` : "";
            responseData = {
                signal: "Rate Limited",
                gem: `Limit reached.${resetText}`,
                context: "",
                warning: true
            };
        } else if (httpStatus >= 500) {
            responseData = {
                signal: "Server Error",
                gem: "Server error. Try again shortly.",
                context: "",
                warning: true
            };
        } else if (httpStatus >= 400) {
            responseData = {
                signal: responseData?.signal || "Error",
                gem: responseData?.gem || responseData?.error || `Request failed (${httpStatus}).`,
                context: responseData?.context || "",
                warning: true
            };
        }

        // Issue #310: Add selectedText and domContext for deep poetic analysis
        responseData.selectedText = info.selectionText;
        responseData.domContext = contextText;

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
