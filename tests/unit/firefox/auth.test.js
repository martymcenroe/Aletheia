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

  // Auth config from the source file (for test assertions)
  const authConfig = {
    LAMBDA_AUTH_URL: 'https://sk33bz56yi5qlbrrwzqnprmeuy0xwhzn.lambda-url.us-east-1.on.aws'
  };

  return { browserMock, authConfig };
}

// ============================================================================
// NAMESPACE VERIFICATION TESTS (CRITICAL)
// ============================================================================

describe('Namespace Verification', () => {
  it('auth.js file exists', () => {
    expect(authJsSource.length).toBeGreaterThan(0);
  });

  it('does NOT use browser.identity (Firefox MV3 does not have it)', () => {
    // Firefox MV3 doesn't have browser.identity API
    // We use a tabs-based OAuth flow instead
    // See: docs/0826-audit-cross-browser-testing.md, Issue #256
    expect(authJsSource).not.toContain('browser.identity.launchWebAuthFlow');
    expect(authJsSource).not.toContain('browser.identity.getRedirectURL');
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

  it('generateState produces 64-character hex string', () => {
    // Use the exposed generateState function directly
    if (global.window.AletheiaAuth && global.window.AletheiaAuth.generateState) {
      const state = global.window.AletheiaAuth.generateState();
      expect(state).toMatch(/^[0-9a-f]{64}$/);
    }
  });

  it('generates unique state values', () => {
    const states = new Set();

    // Generate multiple states
    if (global.window.AletheiaAuth && global.window.AletheiaAuth.generateState) {
      for (let i = 0; i < 10; i++) {
        const state = global.window.AletheiaAuth.generateState();
        states.add(state);
      }

      // All states should be unique
      expect(states.size).toBe(10);
    }
  });
});

// ============================================================================
// CSRF STATE VALIDATION TESTS (Tabs-based flow - Issue #256)
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

    if (!global.window.AletheiaAuth) return;

    // Start login - this will create a tab
    const loginPromise = global.window.AletheiaAuth.initiateLogin();

    // Wait for tab to be created
    await new Promise(resolve => setTimeout(resolve, 10));

    // Get the stored state (we don't use it - attacker uses different state)
    const stored = await browserMock.storage.session.get(['oauth_state']);
    const _correctState = stored.oauth_state;

    // Simulate LinkedIn callback with WRONG state (CSRF attack)
    const callbackUrl = `${env.authConfig.LAMBDA_AUTH_URL}/auth/callback?code=fake-code&state=attacker-controlled-state`;
    browserMock.__simulateTabUpdate(100, callbackUrl, 'complete');

    // Should reject with CSRF error
    await expect(loginPromise).rejects.toThrow(/CSRF|state/i);
  });

  it('accepts matching state parameter', async () => {
    const { browserMock } = env;

    if (!global.window.AletheiaAuth) return;

    // Mock successful token exchange
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        accessToken: 'new-access-token',
        refreshToken: 'new-refresh-token',
        expiresIn: 3600,
        user: { id: 'test-user-id', name: 'Test User' }
      })
    });

    // Start login - this will create a tab
    const loginPromise = global.window.AletheiaAuth.initiateLogin();

    // Wait for tab to be created
    await new Promise(resolve => setTimeout(resolve, 10));

    // Get the stored state (this is what the extension expects back)
    const stored = await browserMock.storage.session.get(['oauth_state']);
    const correctState = stored.oauth_state;

    // Simulate LinkedIn callback with CORRECT state
    const callbackUrl = `${env.authConfig.LAMBDA_AUTH_URL}/auth/callback?code=valid-auth-code&state=${correctState}`;
    browserMock.__simulateTabUpdate(100, callbackUrl, 'complete');

    // Should succeed
    const user = await loginPromise;
    expect(user).toEqual({ id: 'test-user-id', name: 'Test User' });
  });

  it('handles user closing auth tab', async () => {
    const { browserMock } = env;

    if (!global.window.AletheiaAuth) return;

    // Start login - this will create a tab
    const loginPromise = global.window.AletheiaAuth.initiateLogin();

    // Wait for tab to be created
    await new Promise(resolve => setTimeout(resolve, 10));

    // Simulate user closing the auth tab
    browserMock.__triggerTabRemoved(100, {});

    // Should reject with cancelled error
    await expect(loginPromise).rejects.toThrow(/cancelled|closed/i);
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
    const { browserMock, authConfig } = env;

    if (!global.window.AletheiaAuth) return;

    // Mock successful token exchange
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        accessToken: 'test-access-token',
        refreshToken: 'test-refresh-token',
        expiresIn: 3600,
        user: { id: 'test-user-id', name: 'Test User' }
      })
    });

    // Start login
    const loginPromise = global.window.AletheiaAuth.initiateLogin();

    // Wait for tab to be created
    await new Promise(resolve => setTimeout(resolve, 10));

    // Get the stored state
    const stored = await browserMock.storage.session.get(['oauth_state']);
    const correctState = stored.oauth_state;

    // Simulate successful OAuth callback
    const callbackUrl = `${authConfig.LAMBDA_AUTH_URL}/auth/callback?code=test-code&state=${correctState}`;
    browserMock.__simulateTabUpdate(100, callbackUrl, 'complete');

    // Complete login
    await loginPromise;

    // Verify access token is in session storage
    const sessionData = browserMock.__getSessionStorageData();
    expect(sessionData.accessToken).toBe('test-access-token');
    expect(sessionData.expiresAt).toBeDefined();
  });

  it('stores refresh token in local storage', async () => {
    const { browserMock, authConfig } = env;

    if (!global.window.AletheiaAuth) return;

    // Mock successful token exchange
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        accessToken: 'test-access-token',
        refreshToken: 'test-refresh-token',
        expiresIn: 3600,
        user: { id: 'test-user-id', name: 'Test User' }
      })
    });

    // Start login
    const loginPromise = global.window.AletheiaAuth.initiateLogin();

    // Wait for tab to be created
    await new Promise(resolve => setTimeout(resolve, 10));

    // Get the stored state
    const stored = await browserMock.storage.session.get(['oauth_state']);
    const correctState = stored.oauth_state;

    // Simulate successful OAuth callback
    const callbackUrl = `${authConfig.LAMBDA_AUTH_URL}/auth/callback?code=test-code&state=${correctState}`;
    browserMock.__simulateTabUpdate(100, callbackUrl, 'complete');

    // Complete login
    await loginPromise;

    // Verify refresh token and user info are in local storage
    const localData = browserMock.__getLocalStorageData();
    expect(localData.refreshToken).toBe('test-refresh-token');
    expect(localData.userId).toBe('test-user-id');
    expect(localData.displayName).toBe('Test User');
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
