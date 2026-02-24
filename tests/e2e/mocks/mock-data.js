/**
 * Mock data for Aletheia E2E and visual regression tests
 * Issue #173 - Visual Regression Infrastructure
 *
 * These mock states allow deterministic testing without Lambda dependency.
 */

/**
 * Mock authentication states for visual testing.
 * Matches the storage format used by popup.js for auth state.
 */
const AUTH_STATES = {
    /**
     * Unauthenticated state - user not logged in.
     * Popup will show login view.
     */
    unauthenticated: {},

    /**
     * Authenticated state - user logged in via LinkedIn OAuth.
     * Popup will show main view.
     */
    authenticated: {
        userId: 'test-user-12345',
        displayName: 'Test User',
        refreshToken: 'mock-refresh-token'
    },

    /**
     * Authenticated with JWT in session storage.
     * Used for E2E auth flow tests (Issue #403).
     */
    authenticatedWithJwt: {
        userId: 'test-user-12345',
        displayName: 'Test User',
        refreshToken: 'mock-refresh-token',
        jwt: 'mock-jwt-for-testing'
    },

    /**
     * Authenticated with specific display name.
     * @param {string} name - Display name to show
     * @returns {object} Auth state object
     */
    withName: (name) => ({
        userId: 'test-user-12345',
        displayName: name,
        refreshToken: 'mock-refresh-token'
    })
};

/**
 * Mock allowlist states for visual testing.
 * Matches the storage format used by popup.js for allowlist.
 */
const ALLOWLIST_STATES = {
    /**
     * Empty allowlist - no domains enabled.
     * Power button will show inactive state.
     */
    empty: {
        allowlist: []
    },

    /**
     * Single domain allowlisted.
     */
    single: {
        allowlist: ['example.com']
    },

    /**
     * Multiple domains allowlisted.
     * Good for testing the manage view list.
     */
    populated: {
        allowlist: ['example.com', 'github.com', 'stackoverflow.com']
    },

    /**
     * Create allowlist with specific domains.
     * @param {string[]} domains - Array of domain strings
     * @returns {object} Allowlist state object
     */
    withDomains: (domains) => ({
        allowlist: domains
    })
};

/**
 * Tab states matching service-worker.js TabState enum.
 * Used to simulate different age gate states.
 */
const TAB_STATES = {
    UNKNOWN: 'unknown',
    RESTRICTED: 'restricted',
    ALLOWED: 'allowed'
};

/**
 * Combined mock states for common test scenarios.
 * Use these for quick setup of typical visual regression tests.
 */
const SCENARIOS = {
    /**
     * Login view - unauthenticated user.
     */
    loginView: {
        ...AUTH_STATES.unauthenticated
    },

    /**
     * Main view inactive - authenticated but site not allowlisted.
     * This is the POC test target per Gemini review.
     */
    mainInactive: {
        ...AUTH_STATES.authenticated,
        ...ALLOWLIST_STATES.empty
    },

    /**
     * Main view active - authenticated and current site allowlisted.
     */
    mainActive: {
        ...AUTH_STATES.authenticated,
        allowlist: ['localhost']  // Matches test server domain
    },

    /**
     * Manage view with populated list.
     */
    managePopulated: {
        ...AUTH_STATES.authenticated,
        ...ALLOWLIST_STATES.populated
    }
};

module.exports = {
    AUTH_STATES,
    ALLOWLIST_STATES,
    TAB_STATES,
    SCENARIOS
};
