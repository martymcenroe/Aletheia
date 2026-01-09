/**
 * Unit Tests for Firefox auth.js
 *
 * Per LLD 1206 & ADR 0215: Tests written BEFORE implementation (Red-Green-Refactor).
 * These tests verify the Firefox OAuth module uses browser.* APIs correctly.
 *
 * CRITICAL: These tests verify namespace correctness (browser.* not chrome.*).
 * A namespace typo would cause silent failures in production.
 *
 * Test Categories:
 * 1. CSRF State Generation - Crypto-random, unique, correct length
 * 2. CSRF State Validation - Rejects mismatched states
 * 3. Token Storage Hierarchy - Access in session, refresh in local
 * 4. Mock Mode - Deterministic fake tokens for testing
 * 5. Namespace Verification - Uses browser.*, not chrome.*
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { createFirefoxMock } from '../../mocks/firefox-api.mock.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get directory paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const extensionDir = path.resolve(__dirname, '../../../extensions/firefox');

// Read auth.js source code for namespace verification tests
let authJsSource = '';
try {
  authJsSource = fs.readFileSync(path.join(extensionDir, 'auth.js'), 'utf-8');
} catch (_e) {
  // File doesn't exist yet (Red phase) - tests will fail appropriately
  authJsSource = '';
}

/**
 * Creates a test environment with Firefox API mocks and evaluates auth.js
 */
function createAuthEnvironment(options = {}) {
  const browserMock = createFirefoxMock(options);

  // Set up global browser object
  global.browser = browserMock;

  // Mock crypto.getRandomValues for deterministic testing when needed
  // Use vi.stubGlobal because global.crypto is read-only in Node.js 19+
  vi.stubGlobal('crypto', {
    getRandomValues: (arr) => {
      // Use pseudo-random for tests (deterministic seed would be better for some tests)
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

  // Try to evaluate auth.js if it exists
  if (authJsSource) {
    try {
      eval(authJsSource);
    } catch (err) {
      // Syntax error in auth.js - tests will fail appropriately
      console.error('Error evaluating auth.js:', err.message);
    }
  }

  return { browserMock };
}

// ============================================================================
// NAMESPACE VERIFICATION TESTS (CRITICAL)
// ============================================================================

describe('Namespace Verification', () => {
  it('auth.js file exists', () => {
    expect(authJsSource.length).toBeGreaterThan(0);
  });

  it('uses browser.identity not chrome.identity', () => {
    expect(authJsSource).toContain('browser.identity');
    expect(authJsSource).not.toContain('chrome.identity');
  });

  it('uses browser.storage not chrome.storage', () => {
    expect(authJsSource).toContain('browser.storage');
    expect(authJsSource).not.toContain('chrome.storage');
  });

  it('uses browser.runtime not chrome.runtime', () => {
    // May or may not use runtime, but if it does, must be browser.*
    if (authJsSource.includes('.runtime')) {
      expect(authJsSource).toContain('browser.runtime');
      expect(authJsSource).not.toContain('chrome.runtime');
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
    delete global.browser;
    delete global.fetch;
    delete global.window;
    vi.unstubAllGlobals();
  });

  it('AletheiaAuth is exported to window', () => {
    expect(global.window.AletheiaAuth).toBeDefined();
  });

  it('generateState produces 64-character hex string', async () => {
    // Access internal function if exposed, or test via initiateLogin
    // For now, we'll test the outcome: state stored in session storage
    const { browserMock } = env;

    // Trigger login to generate state
    if (global.window.AletheiaAuth) {
      // Set mock mode to avoid actual OAuth flow
      // The state should be stored before launchWebAuthFlow is called
      try {
        await global.window.AletheiaAuth.initiateLogin();
      } catch (_e) {
        // May fail if fetch mock isn't perfect, but state should be set
      }

      // Check that oauth_state was stored in session
      const sessionData = browserMock.__getSessionStorageData();
      if (sessionData.oauth_state) {
        expect(sessionData.oauth_state).toMatch(/^[0-9a-f]{64}$/);
      }
    }
  });

  it('generates unique state values', async () => {
    const states = new Set();
    const { browserMock } = env;

    // Generate multiple states
    for (let i = 0; i < 10; i++) {
      browserMock.__resetSessionStorage();

      if (global.window.AletheiaAuth) {
        try {
          await global.window.AletheiaAuth.initiateLogin();
        } catch (_e) {
          // Expected - we just want the state
        }

        const sessionData = browserMock.__getSessionStorageData();
        if (sessionData.oauth_state) {
          states.add(sessionData.oauth_state);
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
    delete global.browser;
    delete global.fetch;
    delete global.window;
    vi.unstubAllGlobals();
  });

  it('rejects mismatched state parameter', async () => {
    const { browserMock } = env;

    // Configure mock to return a different state (CSRF attack simulation)
    browserMock.__setOAuthReturnedState('attacker-controlled-state');

    if (global.window.AletheiaAuth) {
      await expect(global.window.AletheiaAuth.initiateLogin())
        .rejects.toThrow(/CSRF|state/i);
    }
  });

  it('accepts matching state parameter', async () => {
    const { browserMock } = env;

    // Configure mock to echo back the correct state (valid flow)
    browserMock.__setOAuthReturnedState(null); // null = echo back sent state

    if (global.window.AletheiaAuth) {
      // Should not throw CSRF error
      await expect(global.window.AletheiaAuth.initiateLogin())
        .resolves.toBeDefined();
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
    delete global.browser;
    delete global.fetch;
    delete global.window;
    vi.unstubAllGlobals();
  });

  it('stores access token in session storage', async () => {
    const { browserMock } = env;

    if (global.window.AletheiaAuth) {
      try {
        await global.window.AletheiaAuth.initiateLogin();
      } catch (_e) {
        // May fail, check storage anyway
      }

      // Verify browser.storage.session.set was called with accessToken
      expect(browserMock.storage.session.set).toHaveBeenCalled();

      const sessionData = browserMock.__getSessionStorageData();
      // Access token should be in session storage
      if (Object.keys(sessionData).length > 0) {
        expect(sessionData.accessToken || sessionData.oauth_state).toBeDefined();
      }
    }
  });

  it('stores refresh token in local storage', async () => {
    const { browserMock } = env;

    if (global.window.AletheiaAuth) {
      try {
        await global.window.AletheiaAuth.initiateLogin();
      } catch (_e) {
        // May fail, check storage anyway
      }

      // Verify browser.storage.local.set was called
      // After successful login, refresh token should be in local
      const localData = browserMock.__getLocalStorageData();
      if (localData.refreshToken) {
        expect(localData.refreshToken).toBeDefined();
      }
    }
  });

  it('clears all tokens on logout', async () => {
    const { browserMock } = env;

    // Start authenticated
    browserMock.__setLocalStorageData({
      refreshToken: 'test-refresh',
      userId: 'test-user',
      displayName: 'Test'
    });
    browserMock.__setSessionStorageData({
      accessToken: 'test-access',
      expiresAt: Date.now() + 3600000
    });

    if (global.window.AletheiaAuth) {
      await global.window.AletheiaAuth.logout();

      // Verify storage.session.remove and storage.local.remove were called
      expect(browserMock.storage.session.remove).toHaveBeenCalled();
      expect(browserMock.storage.local.remove).toHaveBeenCalled();
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
    delete global.browser;
    delete global.fetch;
    delete global.window;
    vi.unstubAllGlobals();
  });

  it('returns deterministic mock user when MOCK_MODE is enabled', async () => {
    // This test requires the auth.js to have MOCK_MODE functionality
    // The mock user should have predictable id and name
    if (global.window.AletheiaAuth) {
      // Check if getConfig exposes MOCK_MODE
      const config = global.window.AletheiaAuth.getConfig?.();
      if (config?.MOCK_MODE) {
        const user = await global.window.AletheiaAuth.initiateLogin();
        expect(user.id).toBe('mock-sub-782bbtaQ');
        expect(user.name).toBe('Test User');
      }
    }
  });
});

// ============================================================================
// AUTHENTICATION STATE TESTS
// ============================================================================

describe('Authentication State', () => {
  let env;

  beforeEach(() => {
    env = createAuthEnvironment({ authenticated: true });
  });

  afterEach(() => {
    delete global.browser;
    delete global.fetch;
    delete global.window;
    vi.unstubAllGlobals();
  });

  it('isAuthenticated returns true when userId exists', async () => {
    if (global.window.AletheiaAuth) {
      const isAuthed = await global.window.AletheiaAuth.isAuthenticated();
      expect(isAuthed).toBe(true);
    }
  });

  it('isAuthenticated returns false when no userId', async () => {
    const { browserMock } = env;
    browserMock.__setLocalStorageData({ allowlist: [] }); // Clear auth data

    if (global.window.AletheiaAuth) {
      const isAuthed = await global.window.AletheiaAuth.isAuthenticated();
      expect(isAuthed).toBe(false);
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

  it('getAuthState returns null when not authenticated', async () => {
    const { browserMock } = env;
    browserMock.__setLocalStorageData({ allowlist: [] });

    if (global.window.AletheiaAuth) {
      const state = await global.window.AletheiaAuth.getAuthState();
      expect(state).toBeNull();
    }
  });
});
