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

    // Lambda Auth endpoint (UPDATE after provisioning)
    LAMBDA_AUTH_URL: 'https://sk33bz56yi5qlbrrwzqnprmeuy0xwhzn.lambda-url.us-east-1.on.aws',

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
// TOKEN STORAGE (Hierarchy per LLD Section 6.3)
// =============================================================================

/**
 * Store tokens with proper security hierarchy.
 * - Access token: session storage (cleared on browser close)
 * - Refresh token + user info: local storage (persists)
 *
 * @param {string} accessToken
 * @param {string} refreshToken
 * @param {number} expiresIn - Seconds until access token expires
 * @param {object} user - User info {id, name}
 */
async function storeTokens(accessToken, refreshToken, expiresIn, user) {
    // Access token - session only (memory, cleared on browser close)
    await chrome.storage.session.set({
        accessToken,
        expiresAt: Date.now() + (expiresIn * 1000)
    });

    // Refresh token + profile - local persistence
    await chrome.storage.local.set({
        refreshToken,
        userId: user.id,
        displayName: user.name
    });

    console.log('[Aletheia Auth] Tokens stored successfully');
}

/**
 * Clear all auth data (logout).
 */
async function clearTokens() {
    await chrome.storage.session.remove(['accessToken', 'expiresAt']);
    await chrome.storage.local.remove(['refreshToken', 'userId', 'displayName']);
    console.log('[Aletheia Auth] Tokens cleared');
}

/**
 * Get current auth state (user info if logged in).
 * @returns {Promise<{userId: string, displayName: string} | null>}
 */
async function getAuthState() {
    const local = await chrome.storage.local.get(['userId', 'displayName', 'refreshToken']);
    console.log('[Aletheia Auth] getAuthState storage:', {
        hasUserId: !!local.userId,
        hasDisplayName: !!local.displayName,
        hasRefreshToken: !!local.refreshToken
    });

    // Note: refreshToken may be null if LinkedIn hasn't approved refresh token access
    // We only require userId to consider the user authenticated
    if (local.userId) {
        return {
            userId: local.userId,
            displayName: local.displayName || 'User'
        };
    }

    return null;
}

/**
 * Check if user is authenticated (has userId stored).
 * Note: We don't require refresh token as LinkedIn may not provide one.
 * @returns {Promise<boolean>}
 */
async function isAuthenticated() {
    const state = await getAuthState();
    return state !== null;
}

/**
 * Get valid access token, refreshing if needed (lazy refresh).
 * @returns {Promise<string | null>} Access token or null if not authenticated
 */
async function getAccessToken() {
    const session = await chrome.storage.session.get(['accessToken', 'expiresAt']);

    // Check if token exists and is not expired (with 60s buffer)
    if (session.accessToken && Date.now() < (session.expiresAt - 60000)) {
        return session.accessToken;
    }

    // Token expired or missing - try to refresh
    console.log('[Aletheia Auth] Access token expired, attempting refresh...');
    return await refreshTokens();
}

// =============================================================================
// TOKEN REFRESH
// =============================================================================

/**
 * Refresh access token using stored refresh token.
 * @returns {Promise<string | null>} New access token or null if refresh fails
 */
async function refreshTokens() {
    const local = await chrome.storage.local.get(['refreshToken']);

    if (!local.refreshToken) {
        console.log('[Aletheia Auth] No refresh token available');
        return null;
    }

    try {
        const response = await fetch(`${AUTH_CONFIG.LAMBDA_AUTH_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refreshToken: local.refreshToken })
        });

        if (!response.ok) {
            console.error('[Aletheia Auth] Token refresh failed:', response.status);
            // Clear tokens on 401 (refresh token invalid)
            if (response.status === 401) {
                await clearTokens();
            }
            return null;
        }

        const data = await response.json();

        // Store new access token
        await chrome.storage.session.set({
            accessToken: data.accessToken,
            expiresAt: Date.now() + (data.expiresIn * 1000)
        });

        console.log('[Aletheia Auth] Token refreshed successfully');
        return data.accessToken;

    } catch (error) {
        console.error('[Aletheia Auth] Token refresh error:', error);
        return null;
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
        user: {
            id: 'mock-sub-782bbtaQ',  // Mimics OIDC 'sub' format
            name: 'Test User'
        }
    };

    await storeTokens(
        mockUser.accessToken,
        mockUser.refreshToken,
        mockUser.expiresIn,
        mockUser.user
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

    // 2. Store state for validation (use session storage for popup context)
    // Note: In MV3, we use chrome.storage.session which is shared across extension contexts
    await chrome.storage.session.set({ oauth_state: state });

    // 3. Build auth URL
    const authUrl = buildAuthUrl(state);
    const redirectUri = chrome.identity.getRedirectURL();

    console.log('[Aletheia Auth] Launching OAuth flow...');
    console.log('[Aletheia Auth] Redirect URI:', redirectUri);

    try {
        // 4. Launch OAuth flow
        const responseUrl = await chrome.identity.launchWebAuthFlow({
            url: authUrl,
            interactive: true
        });

        // 5. Parse response
        const url = new URL(responseUrl);
        const returnedState = url.searchParams.get('state');
        const code = url.searchParams.get('code');
        const error = url.searchParams.get('error');

        // 6. Validate state (CSRF protection)
        const stored = await chrome.storage.session.get(['oauth_state']);
        await chrome.storage.session.remove(['oauth_state']);

        if (returnedState !== stored.oauth_state) {
            throw new Error('CSRF detected: state mismatch');
        }

        // 7. Check for errors
        if (error) {
            throw new Error(`LinkedIn OAuth error: ${error}`);
        }

        if (!code) {
            throw new Error('No authorization code received');
        }

        // 8. Exchange code for tokens via Lambda
        console.log('[Aletheia Auth] Exchanging code for tokens...');
        const tokenResponse = await fetch(`${AUTH_CONFIG.LAMBDA_AUTH_URL}/auth/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                redirectUri: redirectUri
            })
        });

        if (!tokenResponse.ok) {
            const errorData = await tokenResponse.json().catch(() => ({}));
            throw new Error(errorData.error || `Token exchange failed: ${tokenResponse.status}`);
        }

        const tokenData = await tokenResponse.json();

        // 9. Store tokens
        await storeTokens(
            tokenData.accessToken,
            tokenData.refreshToken,
            tokenData.expiresIn,
            tokenData.user
        );

        console.log('[Aletheia Auth] Login successful:', tokenData.user.name);
        return tokenData.user;

    } catch (error) {
        console.error('[Aletheia Auth] Login failed:', error);
        throw error;
    }
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
    logout,
    isAuthenticated,
    getAuthState,
    getAccessToken,
    clearTokens,
    // Config for debugging
    getConfig: () => ({ ...AUTH_CONFIG, CLIENT_ID: '***' })  // Hide client ID in logs
};
