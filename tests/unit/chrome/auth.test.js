/**
 * Unit Tests for Chrome auth.js
 *
 * Issue #211: Chrome Auth Tests
 * Per ADR 0215: Tests verify OAuth, CSRF, token storage, and auth state.
 *
 * Test Categories:
 * 1. CSRF State Generation - Crypto-random, unique, correct length
 * 2. CSRF State Validation - Rejects mismatched states
 * 3. Token Storage Hierarchy - Access in session, refresh in local
 * 4. Mock Mode - Deterministic fake tokens for testing
 * 5. Namespace Verification - Uses chrome.*, not browser.*
 * 6. Authentication State - isAuthenticated, getAuthState
 * 7. Logout Flow - Clears all tokens
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { createChromeMock } from '../../mocks/chrome-api.mock.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get directory paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const extensionDir = path.resolve(__dirname, '../../../extensions/chrome');

// Read auth.js source code for namespace verification tests
let authJsSource = '';
try {
  authJsSource = fs.readFileSync(path.join(extensionDir, 'auth.js'), 'utf-8');
} catch (_e) {
  // File doesn't exist - tests will fail appropriately
  authJsSource = '';
}

/**
 * Cleanup function to reset test environment
 */
function cleanupEnvironment() {
  if (global.chrome) delete global.chrome;
  if (global.fetch) delete global.fetch;
  if (global.window) delete global.window;
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
}

/**
 * Creates a test environment with Chrome API mocks and evaluates auth.js
 */
function createAuthEnvironment(options = {}) {
  // Clean any previous state first
  cleanupEnvironment();

  const chromeMock = createChromeMock(options);

  // Set up global chrome object
  global.chrome = chromeMock;

  // Mock crypto.getRandomValues for deterministic testing when needed
  vi.stubGlobal('crypto', {
    getRandomValues: (arr) => {
      // Use pseudo-random for tests
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    }
  });

  // Mock fetch for Lambda API calls
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({
      accessToken: 'lambda-access-token',
      refreshToken: 'lambda-refresh-token',
      expiresIn: 3600,
      user: { id: 'lambda-user-id', name: 'Lambda User' }
    })
  });

  // Mock window for AletheiaAuth export
  global.window = {};

  // Mock console to suppress logging during tests (save original first)
  const originalConsole = global.console;
  global.console = {
    ...originalConsole,
    log: vi.fn(),
    error: vi.fn()
  };

  // Try to evaluate auth.js if it exists
  if (authJsSource) {
    try {
      eval(authJsSource);
    } catch (err) {
      // Syntax error in auth.js - tests will fail appropriately
      originalConsole.error('Error evaluating auth.js:', err.message);
    }
  }

  return { chromeMock };
}

// ============================================================================
// NAMESPACE VERIFICATION TESTS (CRITICAL)
// ============================================================================

describe('Namespace Verification', () => {
  it('auth.js file exists', () => {
    expect(authJsSource.length).toBeGreaterThan(0);
  });

  it('uses chrome.identity not browser.identity', () => {
    expect(authJsSource).toContain('chrome.identity');
    expect(authJsSource).not.toContain('browser.identity');
  });

  it('uses chrome.storage not browser.storage', () => {
    expect(authJsSource).toContain('chrome.storage');
    expect(authJsSource).not.toContain('browser.storage');
  });

  it('uses chrome.runtime not browser.runtime', () => {
    // May or may not use runtime, but if it does, must be chrome.*
    if (authJsSource.includes('.runtime')) {
      expect(authJsSource).not.toContain('browser.runtime');
    }
  });
});

// ============================================================================
// CSRF STATE GENERATION TESTS
// ============================================================================

describe('CSRF State Generation', () => {
  let env;

  beforeEach(() => {
    env = createAuthEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('AletheiaAuth is exported to window', () => {
    expect(global.window.AletheiaAuth).toBeDefined();
  });

  it('exports required auth functions', () => {
    const auth = global.window.AletheiaAuth;
    expect(auth.initiateLogin).toBeTypeOf('function');
    expect(auth.logout).toBeTypeOf('function');
    expect(auth.isAuthenticated).toBeTypeOf('function');
    expect(auth.getAuthState).toBeTypeOf('function');
    expect(auth.getAccessToken).toBeTypeOf('function');
    expect(auth.clearTokens).toBeTypeOf('function');
  });

  it('generateState produces 64-character hex string (via sendMessage)', async () => {
    const { chromeMock } = env;

    // Issue #480: initiateLogin now sends START_OAUTH to SW with state param
    chromeMock.__setMessageResponse('START_OAUTH', { success: true, pending: true });

    if (global.window.AletheiaAuth) {
      await global.window.AletheiaAuth.initiateLogin();

      // Check that START_OAUTH message included a 64-char hex state
      const sendCall = chromeMock.runtime.sendMessage.mock.calls.find(
        call => call[0].type === 'START_OAUTH'
      );
      expect(sendCall).toBeDefined();
      expect(sendCall[0].state).toMatch(/^[0-9a-f]{64}$/);
    }
  });

  it('generates unique state values', async () => {
    const states = new Set();
    const { chromeMock } = env;

    chromeMock.__setMessageResponse('START_OAUTH', { success: true, pending: true });

    // Generate multiple states
    for (let i = 0; i < 10; i++) {
      if (global.window.AletheiaAuth) {
        await global.window.AletheiaAuth.initiateLogin();

        const sendCall = chromeMock.runtime.sendMessage.mock.calls[i];
        if (sendCall && sendCall[0].state) {
          states.add(sendCall[0].state);
        }
      }
    }

    // All states should be unique
    if (states.size > 0) {
      expect(states.size).toBe(10);
    }
  });
});

// ============================================================================
// CSRF STATE VALIDATION TESTS
// ============================================================================

describe('CSRF State Validation', () => {
  let env;

  beforeEach(() => {
    env = createAuthEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('sends CSRF state to service worker', async () => {
    const { chromeMock } = env;

    // Issue #480: CSRF validation now happens in SW, not auth.js
    // auth.js sends the state in the START_OAUTH message
    chromeMock.__setMessageResponse('START_OAUTH', { success: true, pending: true });

    if (global.window.AletheiaAuth) {
      await global.window.AletheiaAuth.initiateLogin();

      const sendCall = chromeMock.runtime.sendMessage.mock.calls.find(
        call => call[0].type === 'START_OAUTH'
      );
      expect(sendCall).toBeDefined();
      expect(sendCall[0].state).toBeDefined();
      expect(sendCall[0].state.length).toBe(64);
    }
  });

  it('throws when SW returns failure', async () => {
    const { chromeMock } = env;

    chromeMock.__setMessageResponse('START_OAUTH', { success: false, error: 'OAuth failed' });

    if (global.window.AletheiaAuth) {
      await expect(global.window.AletheiaAuth.initiateLogin())
        .rejects.toThrow(/OAuth failed/i);
    }
  });

  it('returns pending on successful delegation', async () => {
    const { chromeMock } = env;

    chromeMock.__setMessageResponse('START_OAUTH', { success: true, pending: true });

    if (global.window.AletheiaAuth) {
      const result = await global.window.AletheiaAuth.initiateLogin();
      expect(result).toBeDefined();
      expect(result.pending).toBe(true);
    }
  });
});

// ============================================================================
// TOKEN STORAGE HIERARCHY TESTS
// ============================================================================

describe('Token Storage Hierarchy', () => {
  let env;

  beforeEach(() => {
    env = createAuthEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('stores access token in session storage (via mockLogin)', async () => {
    const { chromeMock } = env;

    // Issue #480: initiateLogin delegates to SW for real OAuth.
    // Test token storage via mockLogin, which still stores directly.
    if (global.window.AletheiaAuth) {
      await global.window.AletheiaAuth.mockLogin();

      expect(chromeMock.storage.session.set).toHaveBeenCalled();

      const sessionData = chromeMock.__getSessionStorageData();
      expect(sessionData.accessToken).toBe('mock-access-token-12345');
    }
  });

  it('stores refresh token in local storage (via mockLogin)', async () => {
    const { chromeMock } = env;

    if (global.window.AletheiaAuth) {
      await global.window.AletheiaAuth.mockLogin();

      expect(chromeMock.storage.local.set).toHaveBeenCalled();

      const localData = chromeMock.__getLocalStorageData();
      expect(localData.refreshToken).toBe('mock-refresh-token-67890');
    }
  });

  it('stores user info in local storage (via mockLogin)', async () => {
    const { chromeMock } = env;

    if (global.window.AletheiaAuth) {
      await global.window.AletheiaAuth.mockLogin();

      const localData = chromeMock.__getLocalStorageData();
      expect(localData.userId).toBe('mock-sub-782bbtaQ');
      expect(localData.displayName).toBe('Test User');
    }
  });

  it('stores expiration time with access token (via mockLogin)', async () => {
    const { chromeMock } = env;

    if (global.window.AletheiaAuth) {
      const beforeLogin = Date.now();
      await global.window.AletheiaAuth.mockLogin();

      const sessionData = chromeMock.__getSessionStorageData();
      // expiresIn is 3600 seconds, so expiresAt should be ~3600000ms from now
      expect(sessionData.expiresAt).toBeGreaterThan(beforeLogin + 3500000);
      expect(sessionData.expiresAt).toBeLessThan(beforeLogin + 3700000);
    }
  });

  it('clears all tokens on logout', async () => {
    const { chromeMock } = env;

    // Start authenticated
    chromeMock.__setLocalStorageData({
      refreshToken: 'test-refresh',
      userId: 'test-user',
      displayName: 'Test'
    });
    chromeMock.__setSessionStorageData({
      accessToken: 'test-access',
      expiresAt: Date.now() + 3600000
    });

    if (global.window.AletheiaAuth) {
      await global.window.AletheiaAuth.logout();

      // Verify storage.session.remove and storage.local.remove were called
      expect(chromeMock.storage.session.remove).toHaveBeenCalled();
      expect(chromeMock.storage.local.remove).toHaveBeenCalled();
    }
  });
});

// ============================================================================
// MOCK MODE TESTS
// ============================================================================

describe('Mock Mode', () => {
  let env;

  beforeEach(() => {
    env = createAuthEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('exposes getConfig function', async () => {
    if (global.window.AletheiaAuth) {
      const config = global.window.AletheiaAuth.getConfig?.();
      expect(config).toBeDefined();
      expect(config).toHaveProperty('MOCK_MODE');
    }
  });

  it('hides client ID in getConfig output', async () => {
    if (global.window.AletheiaAuth) {
      const config = global.window.AletheiaAuth.getConfig?.();
      // Client ID should be masked for security
      expect(config.CLIENT_ID).toBe('***');
    }
  });
});

// ============================================================================
// AUTHENTICATION STATE TESTS
// ============================================================================

describe('Authentication State', () => {
  describe('when authenticated', () => {
    let env;

    beforeEach(() => {
      env = createAuthEnvironment({ authenticated: true });
    });

    afterEach(() => {
      delete global.chrome;
      delete global.fetch;
      delete global.window;
      vi.unstubAllGlobals();
      vi.restoreAllMocks();
    });

    it('isAuthenticated returns true when userId exists', async () => {
      if (global.window.AletheiaAuth) {
        const isAuthed = await global.window.AletheiaAuth.isAuthenticated();
        expect(isAuthed).toBe(true);
      }
    });

    it('getAuthState returns user info when authenticated', async () => {
      if (global.window.AletheiaAuth) {
        const state = await global.window.AletheiaAuth.getAuthState();
        expect(state).not.toBeNull();
        expect(state.userId).toBe('mock-sub-782bbtaQ');
        expect(state.displayName).toBe('Test User');
      }
    });

    it('getAccessToken returns token when valid', async () => {
      if (global.window.AletheiaAuth) {
        const token = await global.window.AletheiaAuth.getAccessToken();
        expect(token).toBe('mock-access-token-12345');
      }
    });
  });

  describe('when not authenticated', () => {
    let env;

    beforeEach(() => {
      env = createAuthEnvironment({ authenticated: false });
    });

    afterEach(() => {
      delete global.chrome;
      delete global.fetch;
      delete global.window;
      vi.unstubAllGlobals();
      vi.restoreAllMocks();
    });

    it('isAuthenticated returns false when no userId', async () => {
      if (global.window.AletheiaAuth) {
        const isAuthed = await global.window.AletheiaAuth.isAuthenticated();
        expect(isAuthed).toBe(false);
      }
    });

    it('getAuthState returns null when not authenticated', async () => {
      if (global.window.AletheiaAuth) {
        const state = await global.window.AletheiaAuth.getAuthState();
        expect(state).toBeNull();
      }
    });
  });
});

// ============================================================================
// OAUTH FLOW TESTS
// ============================================================================

describe('OAuth Flow', () => {
  let env;

  beforeEach(() => {
    env = createAuthEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('sends START_OAUTH message to service worker', async () => {
    const { chromeMock } = env;

    // Issue #480: auth.js delegates to SW via message passing
    chromeMock.__setMessageResponse('START_OAUTH', { success: true, pending: true });

    if (global.window.AletheiaAuth) {
      await global.window.AletheiaAuth.initiateLogin();

      expect(chromeMock.runtime.sendMessage).toHaveBeenCalled();
      const sendCall = chromeMock.runtime.sendMessage.mock.calls.find(
        call => call[0].type === 'START_OAUTH'
      );
      expect(sendCall).toBeDefined();
    }
  });

  it('includes correct OAuth parameters in auth URL sent to SW', async () => {
    const { chromeMock } = env;

    chromeMock.__setMessageResponse('START_OAUTH', { success: true, pending: true });

    if (global.window.AletheiaAuth) {
      await global.window.AletheiaAuth.initiateLogin();

      const sendCall = chromeMock.runtime.sendMessage.mock.calls.find(
        call => call[0].type === 'START_OAUTH'
      );
      const url = new URL(sendCall[0].authUrl);

      expect(url.hostname).toBe('www.linkedin.com');
      expect(url.searchParams.get('response_type')).toBe('code');
      expect(url.searchParams.get('client_id')).toBeDefined();
      expect(url.searchParams.get('redirect_uri')).toBeDefined();
      expect(url.searchParams.get('state')).toBeDefined();
      expect(url.searchParams.get('scope')).toContain('openid');
    }
  });

  it('includes lambdaAuthUrl in START_OAUTH message', async () => {
    const { chromeMock } = env;

    chromeMock.__setMessageResponse('START_OAUTH', { success: true, pending: true });

    if (global.window.AletheiaAuth) {
      await global.window.AletheiaAuth.initiateLogin();

      const sendCall = chromeMock.runtime.sendMessage.mock.calls.find(
        call => call[0].type === 'START_OAUTH'
      );
      expect(sendCall[0].lambdaAuthUrl).toContain('lambda-url.us-east-1.on.aws');
    }
  });

  it('returns { pending: true } on successful delegation', async () => {
    const { chromeMock } = env;

    chromeMock.__setMessageResponse('START_OAUTH', { success: true, pending: true });

    if (global.window.AletheiaAuth) {
      const result = await global.window.AletheiaAuth.initiateLogin();
      expect(result.pending).toBe(true);
    }
  });

  it('throws when SW reports failure', async () => {
    const { chromeMock } = env;

    chromeMock.__setMessageResponse('START_OAUTH', { success: false, error: 'User cancelled' });

    if (global.window.AletheiaAuth) {
      await expect(global.window.AletheiaAuth.initiateLogin())
        .rejects.toThrow(/User cancelled/i);
    }
  });

  it('throws when SW returns no response', async () => {
    // sendMessage returns default { state: 'unknown' } — no .success
    if (global.window.AletheiaAuth) {
      await expect(global.window.AletheiaAuth.initiateLogin())
        .rejects.toThrow(/OAuth flow failed/i);
    }
  });
});

// ============================================================================
// TOKEN REFRESH TESTS
// ============================================================================

describe('Token Refresh', () => {
  let env;

  beforeEach(() => {
    env = createAuthEnvironment({ authenticated: true });
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('getAccessToken returns null when no refresh token', async () => {
    const { chromeMock } = env;

    // Remove tokens
    chromeMock.__setLocalStorageData({ allowlist: [] });
    chromeMock.__setSessionStorageData({});

    if (global.window.AletheiaAuth) {
      const token = await global.window.AletheiaAuth.getAccessToken();
      expect(token).toBeNull();
    }
  });

  it('returns cached token when not expired', async () => {
    const { chromeMock } = env;

    // Set valid token
    chromeMock.__setSessionStorageData({
      accessToken: 'cached-token',
      expiresAt: Date.now() + 3600000 // 1 hour from now
    });

    if (global.window.AletheiaAuth) {
      const token = await global.window.AletheiaAuth.getAccessToken();
      expect(token).toBe('cached-token');
    }
  });

  it('attempts refresh when token is expired', async () => {
    const { chromeMock } = env;

    // Set expired token but valid refresh token
    chromeMock.__setSessionStorageData({
      accessToken: 'expired-token',
      expiresAt: Date.now() - 1000 // Expired
    });

    // Mock refresh endpoint
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        accessToken: 'new-access-token',
        expiresIn: 3600
      })
    });

    if (global.window.AletheiaAuth) {
      const _token = await global.window.AletheiaAuth.getAccessToken();

      // Should have called refresh endpoint
      const refreshCall = global.fetch.mock.calls.find(call =>
        call[0].includes('/auth/refresh')
      );
      expect(refreshCall).toBeDefined();
    }
  });
});

// ============================================================================
// ERROR HANDLING TESTS
// ============================================================================

describe('Error Handling', () => {
  let env;

  beforeEach(() => {
    env = createAuthEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('handles SW returning error response', async () => {
    const { chromeMock } = env;

    // Issue #480: Token exchange errors are now reported by the SW
    chromeMock.__setMessageResponse('START_OAUTH', {
      success: false,
      error: 'Token exchange failed: invalid_grant'
    });

    if (global.window.AletheiaAuth) {
      await expect(global.window.AletheiaAuth.initiateLogin())
        .rejects.toThrow(/invalid_grant|failed/i);
    }
  });

  it('handles sendMessage rejection (channel disconnected)', async () => {
    const { chromeMock } = env;

    // Simulate popup closing mid-message
    chromeMock.runtime.sendMessage.mockRejectedValue(
      new Error('Could not establish connection. Receiving end does not exist.')
    );

    if (global.window.AletheiaAuth) {
      await expect(global.window.AletheiaAuth.initiateLogin())
        .rejects.toThrow();
    }
  });
});
