// extensions/chrome/auth.js
// LinkedIn OAuth Authentication Module
// See: docs/1116-linkedin-oauth.md

// =============================================================================
// CONFIGURATION
// =============================================================================

const AUTH_CONFIG = {
    // Set to true for automated tests (returns deterministic mock tokens)
    MOCK_MODE: false,

    // LinkedIn OAuth endpoints
    AUTH_URL: 'https://www.linkedin.com/oauth/v2/authorization',

    // Auth endpoint (routed through CloudFlare Worker to Auth Lambda)
    LAMBDA_AUTH_URL: 'https://api.aletheia.study',

    // LinkedIn OAuth scopes (minimal - r_liteprofile only)
    SCOPES: 'openid profile',

    // LinkedIn Client ID (public, safe to include in extension)
    CLIENT_ID: '86yrqtke9ewvhk', // gitleaks:allow
};

// =============================================================================
// CSRF STATE MANAGEMENT
// =============================================================================

/**
 * Generate a cryptographically secure random state string.
 * Used for CSRF protection in OAuth flow.
 * @returns {string} 64-character hex string
 */
function generateState() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, b => b.toString(16).padStart(2, '0')).join('');
}

// =============================================================================
// SESSION LIFETIME (Issues #811, #812, #814)
// =============================================================================

// Server mints JWTs with a 24h life. Mirrored here only to schedule renewal;
// the server's `expiresIn` is preferred whenever the response carries one.
const JWT_LIFETIME_SECONDS = 24 * 3600;

// Renew this far ahead of expiry so an in-flight request cannot race the
// boundary and arrive just after the token dies.
const JWT_RENEWAL_BUFFER_MS = 5 * 60 * 1000;

// Shared across concurrent callers so a cold start issues one renewal, not N.
let _inFlightRenewal = null;

// =============================================================================
// TOKEN STORAGE (Hierarchy per LLD Section 6.3)
// =============================================================================

/**
 * Store tokens with proper security hierarchy.
 *
 * Issue #812: the Aletheia refresh token goes to LOCAL storage so the session
 * survives a browser restart. Previously the only credential the API accepts
 * (the JWT) lived solely in session storage, which the browser clears on close,
 * while the identity fields in local storage persisted forever — so a restart
 * destroyed the credential and left every field the popup inspects intact.
 *
 * @param {string} accessToken
 * @param {string} refreshToken - LinkedIn's; effectively always null for the
 *   'openid profile' scopes. Retained only so stored shape is unchanged.
 * @param {number} expiresIn - Seconds until the LinkedIn access token expires
 * @param {object} user - User info {id, name}
 * @param {string} jwt - The credential the analysis API accepts
 * @param {string} aletheiaRefreshToken - Renews the JWT indefinitely (#811)
 */
async function storeTokens(accessToken, refreshToken, expiresIn, user, jwt, aletheiaRefreshToken) {
    await chrome.storage.session.set({
        accessToken,
        expiresAt: Date.now() + (expiresIn * 1000),
        jwt: jwt || null,
        jwtExpiresAt: jwt ? Date.now() + (JWT_LIFETIME_SECONDS * 1000) : 0
    });

    const localData = {
        refreshToken,
        userId: user.id,
        displayName: user.name
    };

    // Only overwrite a stored refresh token when a new one was actually issued,
    // so a re-login that omits it cannot silently strip renewal ability.
    if (aletheiaRefreshToken) {
        localData.aletheiaRefreshToken = aletheiaRefreshToken;
    }

    await chrome.storage.local.set(localData);

    console.log('[Aletheia Auth] Tokens stored successfully');
}

/**
 * Clear all auth data (logout).
 */
async function clearTokens() {
    _inFlightRenewal = null;
    await chrome.storage.session.remove(['accessToken', 'expiresAt', 'jwt', 'jwtExpiresAt']);
    await chrome.storage.local.remove([
        'refreshToken', 'userId', 'displayName', 'aletheiaRefreshToken'
    ]);
    console.log('[Aletheia Auth] Tokens cleared');
}

/**
 * Get the cached JWT without attempting renewal.
 * Prefer getValidJwt() on any request path.
 * @returns {Promise<string | null>}
 */
async function getJwt() {
    const session = await chrome.storage.session.get(['jwt']);
    return session.jwt || null;
}

/**
 * Get a usable JWT, renewing silently when the cached one is missing or stale.
 *
 * Issue #814. This is the only accessor a request path should use. Callers must
 * treat null as "cannot authenticate" and NOT dispatch the request anyway.
 *
 * @returns {Promise<string | null>} A live JWT, or null if renewal is impossible
 */
async function getValidJwt() {
    const session = await chrome.storage.session.get(['jwt', 'jwtExpiresAt']);

    const stillFresh = session.jwt &&
        session.jwtExpiresAt &&
        Date.now() < (session.jwtExpiresAt - JWT_RENEWAL_BUFFER_MS);

    if (stillFresh) {
        return session.jwt;
    }

    const renewed = await renewJwt();
    if (renewed) return renewed;

    // Legacy session from a build predating jwtExpiresAt (#812): renewal is
    // impossible because no refresh token was ever issued, but the cached JWT
    // may still be valid. Use it and let the 401 path decide, rather than
    // forcing a sign-in we cannot prove is needed.
    return session.jwt || null;
}

/**
 * Get current auth state.
 *
 * Issue #813: previously this reported a user as signed in whenever `userId`
 * was present. `userId` never expires and has no relationship to whether any
 * request can succeed, so the popup claimed an active session indefinitely
 * while every request failed. Authentication now means "a credential is
 * obtainable" — a stored refresh token — not merely "a name is remembered".
 *
 * @returns {Promise<{userId: string, displayName: string} | null>}
 */
async function getAuthState() {
    const local = await chrome.storage.local.get([
        'userId', 'displayName', 'aletheiaRefreshToken'
    ]);

    if (local.userId && local.aletheiaRefreshToken) {
        return {
            userId: local.userId,
            displayName: local.displayName || 'User'
        };
    }

    return null;
}

/**
 * Whether a usable session exists (identity present AND renewable).
 * @returns {Promise<boolean>}
 */
async function isAuthenticated() {
    const state = await getAuthState();
    return state !== null;
}

/**
 * Whether identity is remembered but the session can no longer be renewed.
 * Lets the UI say "signed out" honestly instead of claiming an active session.
 * @returns {Promise<boolean>}
 */
async function isSessionUnrecoverable() {
    const local = await chrome.storage.local.get(['userId', 'aletheiaRefreshToken']);
    return Boolean(local.userId) && !local.aletheiaRefreshToken;
}

// =============================================================================
// TOKEN REFRESH (Issue #811 / #814)
// =============================================================================

/**
 * Renew the JWT from the persisted Aletheia refresh token.
 *
 * Concurrent callers share one in-flight request: several extension contexts
 * can hit this simultaneously on a cold start, and firing N parallel renewals
 * would multiply load on the auth Lambda for no benefit.
 *
 * @returns {Promise<string | null>} A fresh JWT, or null if renewal failed
 */
async function renewJwt() {
    if (_inFlightRenewal) {
        return await _inFlightRenewal;
    }

    _inFlightRenewal = (async () => {
        const local = await chrome.storage.local.get(['aletheiaRefreshToken']);

        if (!local.aletheiaRefreshToken) {
            console.log('[Aletheia Auth] No refresh token; sign-in required');
            return null;
        }

        try {
            const response = await fetch(`${AUTH_CONFIG.LAMBDA_AUTH_URL}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ aletheiaRefreshToken: local.aletheiaRefreshToken })
            });

            if (!response.ok) {
                console.error('[Aletheia Auth] JWT renewal failed:', response.status);
                // 401 means the refresh token is revoked or expired: renewal can
                // never succeed again, so drop it and require a real sign-in.
                // Any other status (5xx, offline) is transient — keep the token.
                if (response.status === 401) {
                    await chrome.storage.local.remove(['aletheiaRefreshToken']);
                }
                return null;
            }

            const data = await response.json();
            if (!data.jwt) {
                console.error('[Aletheia Auth] Renewal response carried no JWT');
                return null;
            }

            const lifetimeSeconds = data.expiresIn || JWT_LIFETIME_SECONDS;
            await chrome.storage.session.set({
                jwt: data.jwt,
                jwtExpiresAt: Date.now() + (lifetimeSeconds * 1000)
            });

            console.log('[Aletheia Auth] JWT renewed silently');
            return data.jwt;

        } catch (error) {
            // Network failure is transient. Do not discard the refresh token.
            console.error('[Aletheia Auth] JWT renewal error:', error.name);
            return null;
        }
    })();

    try {
        return await _inFlightRenewal;
    } finally {
        _inFlightRenewal = null;
    }
}

// =============================================================================
// MOCK MODE (for testing)
// =============================================================================

/**
 * Mock login for automated tests.
 * Returns deterministic mock tokens without calling LinkedIn.
 */
async function mockLogin() {
    console.log('[Aletheia Auth] MOCK MODE - Using fake credentials');

    const mockUser = {
        accessToken: 'mock-access-token-12345',
        refreshToken: 'mock-refresh-token-67890',
        expiresIn: 3600,
        jwt: 'mock-jwt-for-testing',
        aletheiaRefreshToken: 'mock-aletheia-refresh-token',
        user: {
            id: 'mock-sub-782bbtaQ',  // Mimics OIDC 'sub' format
            name: 'Test User'
        }
    };

    await storeTokens(
        mockUser.accessToken,
        mockUser.refreshToken,
        mockUser.expiresIn,
        mockUser.user,
        mockUser.jwt,
        mockUser.aletheiaRefreshToken
    );

    return mockUser.user;
}

// =============================================================================
// OAUTH FLOW
// =============================================================================

/**
 * Build LinkedIn authorization URL with required parameters.
 * @param {string} state - CSRF state parameter
 * @returns {string} Full authorization URL
 */
function buildAuthUrl(state) {
    const redirectUri = chrome.identity.getRedirectURL();
    const params = new URLSearchParams({
        response_type: 'code',
        client_id: AUTH_CONFIG.CLIENT_ID,
        redirect_uri: redirectUri,
        state: state,
        scope: AUTH_CONFIG.SCOPES
    });

    return `${AUTH_CONFIG.AUTH_URL}?${params.toString()}`;
}

/**
 * Initiate LinkedIn OAuth login flow.
 *
 * Uses chrome.identity.launchWebAuthFlow for Chrome-compliant OAuth.
 * Includes CSRF protection via state parameter.
 *
 * @returns {Promise<{id: string, name: string}>} User info on success
 * @throws {Error} On authentication failure
 */
async function initiateLogin() {
    // Mock mode for testing
    if (AUTH_CONFIG.MOCK_MODE) {
        return await mockLogin();
    }

    // 1. Generate CSRF state
    const state = generateState();

    // 2. Store state for validation (shared across extension contexts via session storage)
    await chrome.storage.session.set({ oauth_state: state });

    // 3. Build auth URL
    const authUrl = buildAuthUrl(state);

    console.log('[Aletheia Auth] Delegating OAuth flow to service worker...');

    // 4. Delegate to service worker — survives popup closure (Issue #480)
    const response = await chrome.runtime.sendMessage({
        type: 'START_OAUTH',
        authUrl: authUrl,
        lambdaAuthUrl: AUTH_CONFIG.LAMBDA_AUTH_URL
    });

    if (!response || !response.success) {
        throw new Error(response?.error || 'OAuth flow failed');
    }

    console.log('[Aletheia Auth] Login successful:', response.user.name);
    return response.user;
}

/**
 * Logout - clear all tokens and auth state.
 */
async function logout() {
    await clearTokens();
    console.log('[Aletheia Auth] Logged out');
}

// =============================================================================
// EXPORTS (for use in other extension scripts)
// =============================================================================

// Make functions available globally for other scripts
window.AletheiaAuth = {
    initiateLogin,
    mockLogin,
    logout,
    isAuthenticated,
    isSessionUnrecoverable,
    getAuthState,
    getValidJwt,
    getJwt,
    renewJwt,
    clearTokens,
    // Config for debugging
    getConfig: () => ({ ...AUTH_CONFIG, CLIENT_ID: '***' })  // Hide client ID in logs
};
