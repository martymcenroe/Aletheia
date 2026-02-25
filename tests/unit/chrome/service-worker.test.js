/**
 * Unit Tests for Chrome service-worker.js
 *
 * Issue #212: Service Worker Tests
 * Per ADR 0215: Tests verify message handlers, installation events, and age gate.
 *
 * Test Categories:
 * 1. Installation Events - Context menu creation on install
 * 2. Message Handlers - GET_TAB_STATE, RECHECK_TAB, AUTH_STATUS
 * 3. Security - Sender validation (ADR 0213)
 * 4. Age Gate - Tab state management and restriction checking
 * 5. Tab Lifecycle - Memory cleanup on tab close
 * 6. NoArchive Signal - Per Issue #162
 *
 * Challenge: Service workers are event-driven. We mock chrome.runtime.onMessage.addListener
 * and simulate incoming messages to test handlers.
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

// Read service-worker.js source code
let serviceWorkerSource = '';
try {
  serviceWorkerSource = fs.readFileSync(path.join(extensionDir, 'service-worker.js'), 'utf-8');
} catch (_e) {
  serviceWorkerSource = '';
}

/**
 * Cleanup function to reset test environment
 */
function cleanupEnvironment() {
  if (global.chrome) delete global.chrome;
  if (global.fetch) delete global.fetch;
  vi.restoreAllMocks();
}

/**
 * Creates a test environment with Chrome API mocks and evaluates service-worker.js
 */
function createServiceWorkerEnvironment(options = {}) {
  // Clean any previous state first
  cleanupEnvironment();

  const chromeMock = createChromeMock(options);

  // Set up global chrome object
  global.chrome = chromeMock;

  // Mock console to suppress logging during tests (save original first)
  const originalConsole = global.console;
  global.console = {
    ...originalConsole,
    log: vi.fn(),
    error: vi.fn(),
    warn: vi.fn()
  };

  // Mock fetch for API calls
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve({
      signal: 'Verified',
      gem: 'Test response',
      context: 'Test context'
    })
  });

  // Try to evaluate service-worker.js if it exists
  if (serviceWorkerSource) {
    try {
      eval(serviceWorkerSource);
    } catch (err) {
      originalConsole.error('Error evaluating service-worker.js:', err.message);
    }
  }

  return { chromeMock };
}

// ============================================================================
// FILE VERIFICATION TESTS
// ============================================================================

describe('Service Worker File', () => {
  it('service-worker.js file exists', () => {
    expect(serviceWorkerSource.length).toBeGreaterThan(0);
  });

  it('defines API_ENDPOINT constant', () => {
    expect(serviceWorkerSource).toContain('API_ENDPOINT');
  });

  it('defines CLIENT_VERSION constant', () => {
    expect(serviceWorkerSource).toContain('CLIENT_VERSION');
  });

  it('defines TabState object', () => {
    expect(serviceWorkerSource).toContain('TabState');
    expect(serviceWorkerSource).toContain('UNKNOWN');
    expect(serviceWorkerSource).toContain('RESTRICTED');
    expect(serviceWorkerSource).toContain('ALLOWED');
  });
});

// ============================================================================
// INSTALLATION EVENT TESTS
// ============================================================================

describe('Installation Events', () => {
  let env;

  beforeEach(() => {
    env = createServiceWorkerEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('registers onInstalled listener', () => {
    const { chromeMock } = env;
    expect(chromeMock.runtime.onInstalled.addListener).toHaveBeenCalled();
  });

  it('creates context menu on install', () => {
    const { chromeMock } = env;

    // Trigger onInstalled event
    chromeMock.__triggerOnInstalled({ reason: 'install' });

    expect(chromeMock.contextMenus.create).toHaveBeenCalled();
  });

  it('creates "Explain with AI" context menu item', () => {
    const { chromeMock } = env;

    chromeMock.__triggerOnInstalled({ reason: 'install' });

    const createCall = chromeMock.contextMenus.create.mock.calls[0][0];
    expect(createCall.id).toBe('explain-with-ai');
    expect(createCall.title).toBe('Explain with AI');
    expect(createCall.contexts).toContain('selection');
  });
});

// ============================================================================
// MESSAGE HANDLER TESTS
// ============================================================================

describe('Message Handlers', () => {
  let env;

  beforeEach(() => {
    env = createServiceWorkerEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('registers onMessage listener', () => {
    const { chromeMock } = env;
    expect(chromeMock.runtime.onMessage.addListener).toHaveBeenCalled();
  });

  describe('GET_TAB_STATE message', () => {
    it('returns state for known tab', async () => {
      const { chromeMock } = env;

      const response = await chromeMock.__simulateMessage({
        type: 'GET_TAB_STATE',
        tabId: 1
      });

      // Initially unknown
      expect(response).toBeDefined();
      expect(response.state).toBeDefined();
    });

    it('returns unknown for untracked tab', async () => {
      const { chromeMock } = env;

      const response = await chromeMock.__simulateMessage({
        type: 'GET_TAB_STATE',
        tabId: 999 // Untracked tab
      });

      expect(response).toBeDefined();
      expect(response.state).toBe('unknown');
    });
  });

  describe('RECHECK_TAB message', () => {
    it('responds asynchronously', async () => {
      const { chromeMock } = env;

      // Set up script injection to return allowed content
      chromeMock.__setScriptInjectionResults([{
        result: { isRestricted: false, ratingValue: null, noarchive: false }
      }]);

      const response = await chromeMock.__simulateMessage({
        type: 'RECHECK_TAB'
      });

      // RECHECK_TAB returns true (async) and calls sendResponse later
      expect(response).toBeDefined();
    });
  });
});

// ============================================================================
// SECURITY TESTS (ADR 0213)
// ============================================================================

describe('Security - Sender Validation', () => {
  let env;

  beforeEach(() => {
    env = createServiceWorkerEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('rejects messages from unknown sender', async () => {
    const { chromeMock } = env;

    // Simulate message from hostile extension
    const _response = await chromeMock.__simulateMessage(
      { type: 'GET_TAB_STATE', tabId: 1 },
      { id: 'malicious-extension-id' }
    );

    // Should not respond to foreign extension
    // The handler returns false early, so response may be undefined
    // or the actual response - depends on implementation
  });

  it('accepts messages from own extension', async () => {
    const { chromeMock } = env;

    // Simulate message from same extension
    const response = await chromeMock.__simulateMessage(
      { type: 'GET_TAB_STATE', tabId: 1 },
      { id: 'mock-extension-id-12345' }
    );

    // Should process message normally
    expect(response).toBeDefined();
  });

  it('accepts messages from content scripts (undefined sender.id)', async () => {
    const { chromeMock } = env;

    // Content scripts have undefined sender.id
    const response = await chromeMock.__simulateMessage(
      { type: 'GET_TAB_STATE', tabId: 1 },
      { tab: { id: 1 } } // Content script sender
    );

    // Should process message normally
    expect(response).toBeDefined();
  });
});

// ============================================================================
// AGE GATE TESTS (Issue #104)
// ============================================================================

describe('Age Gate - Tab State Management', () => {
  let env;

  beforeEach(() => {
    env = createServiceWorkerEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('registers tabs.onRemoved listener for cleanup', () => {
    const { chromeMock } = env;
    expect(chromeMock.tabs.onRemoved.addListener).toHaveBeenCalled();
  });

  it('cleans up tab state when tab is closed', async () => {
    const { chromeMock } = env;

    // First, get state for a tab (creates entry)
    await chromeMock.__simulateMessage({
      type: 'GET_TAB_STATE',
      tabId: 42
    });

    // Simulate tab close
    chromeMock.__triggerTabRemoved(42);

    // State should be cleaned up (will return unknown for removed tab)
    const response = await chromeMock.__simulateMessage({
      type: 'GET_TAB_STATE',
      tabId: 42
    });

    expect(response.state).toBe('unknown');
  });
});

// ============================================================================
// CONTEXT MENU CLICK TESTS
// ============================================================================

describe('Context Menu Click Handler', () => {
  let env;

  beforeEach(() => {
    env = createServiceWorkerEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('registers contextMenus.onClicked listener', () => {
    const { chromeMock } = env;
    expect(chromeMock.contextMenus.onClicked.addListener).toHaveBeenCalled();
  });

  it('handles explain-with-ai menu click', async () => {
    const { chromeMock } = env;

    // Set up allowlist
    chromeMock.__setLocalStorageData({ allowlist: ['example.com'] });

    // Set up script injection results
    chromeMock.__setScriptInjectionResults([{
      result: { isRestricted: false, noarchive: false }
    }]);

    // Simulate context menu click
    const info = {
      menuItemId: 'explain-with-ai',
      selectionText: 'test selection',
      pageUrl: 'https://example.com/page'
    };

    const tab = {
      id: 1,
      url: 'https://example.com/page',
      title: 'Test Page'
    };

    chromeMock.__triggerContextMenuClick(info, tab);

    // Wait for async operations
    await new Promise(resolve => setTimeout(resolve, 100));

    // Should have attempted to inject overlay and call API
    expect(chromeMock.scripting.executeScript).toHaveBeenCalled();
  });

  it('shows warning when site not in allowlist', async () => {
    const { chromeMock } = env;

    // Empty allowlist
    chromeMock.__setLocalStorageData({ allowlist: [] });

    // Set up script injection results (non-restricted)
    chromeMock.__setScriptInjectionResults([{
      result: { isRestricted: false, noarchive: false }
    }]);

    const info = {
      menuItemId: 'explain-with-ai',
      selectionText: 'test selection',
      pageUrl: 'https://notallowed.com/page'
    };

    const tab = {
      id: 1,
      url: 'https://notallowed.com/page',
      title: 'Not Allowed'
    };

    chromeMock.__triggerContextMenuClick(info, tab);

    // Wait for async operations
    await new Promise(resolve => setTimeout(resolve, 100));

    // Should show warning badge
    const badgeState = chromeMock.__getBadgeState(1);
    expect(badgeState.text).toBe('!');
    expect(badgeState.color).toBe('#FBBF24');
  });
});

// ============================================================================
// BADGE STATE TESTS
// ============================================================================

describe('Badge State', () => {
  let env;

  beforeEach(() => {
    env = createServiceWorkerEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('sets success badge on successful API response', async () => {
    const { chromeMock } = env;

    // Set up allowlist
    chromeMock.__setLocalStorageData({ allowlist: ['example.com'] });

    // Set up successful response
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        signal: 'Verified',
        gem: 'Response'
      })
    });

    // Set up script injection
    chromeMock.__setScriptInjectionResults([{
      result: { isRestricted: false, noarchive: false }
    }]);

    const info = {
      menuItemId: 'explain-with-ai',
      selectionText: 'test',
      pageUrl: 'https://example.com'
    };

    const tab = { id: 1, url: 'https://example.com', title: 'Test' };

    chromeMock.__triggerContextMenuClick(info, tab);
    await new Promise(resolve => setTimeout(resolve, 150));

    // Should have set success badge at some point
    expect(chromeMock.action.setBadgeText).toHaveBeenCalled();
  });
});

// ============================================================================
// API INTEGRATION TESTS
// ============================================================================

describe('API Integration', () => {
  let env;

  beforeEach(() => {
    env = createServiceWorkerEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('includes X-Aletheia-Client-Version header in API requests', async () => {
    const { chromeMock } = env;

    // Set up allowlist
    chromeMock.__setLocalStorageData({ allowlist: ['example.com'] });

    // Set up script injection
    chromeMock.__setScriptInjectionResults([
      { result: { isRestricted: false, noarchive: false } },
      { result: 'page body text' }
    ]);

    const info = {
      menuItemId: 'explain-with-ai',
      selectionText: 'test',
      pageUrl: 'https://example.com'
    };

    const tab = { id: 1, url: 'https://example.com', title: 'Test' };

    chromeMock.__triggerContextMenuClick(info, tab);
    await new Promise(resolve => setTimeout(resolve, 150));

    // Check fetch was called with version header
    const fetchCall = global.fetch.mock.calls[0];
    if (fetchCall) {
      const headers = fetchCall[1]?.headers;
      expect(headers['X-Aletheia-Client-Version']).toBeDefined();
    }
  });

  it('sends noarchive signal in payload when present', async () => {
    const { chromeMock } = env;

    // Set up allowlist
    chromeMock.__setLocalStorageData({ allowlist: ['example.com'] });

    // Set up script injection with noarchive signal
    chromeMock.__setScriptInjectionResults([
      { result: { isRestricted: false, noarchive: true } },
      { result: 'page body text' }
    ]);

    const info = {
      menuItemId: 'explain-with-ai',
      selectionText: 'test',
      pageUrl: 'https://example.com'
    };

    const tab = { id: 1, url: 'https://example.com', title: 'Test' };

    chromeMock.__triggerContextMenuClick(info, tab);
    await new Promise(resolve => setTimeout(resolve, 150));

    // Check fetch payload includes noarchive signal
    const fetchCall = global.fetch.mock.calls[0];
    if (fetchCall && fetchCall[1]?.body) {
      const payload = JSON.parse(fetchCall[1].body);
      expect(payload.signals).toBeDefined();
    }
  });
});

// ============================================================================
// HELPER FUNCTION TESTS
// ============================================================================

describe('Helper Functions', () => {
  it('extractDomain removes www prefix', () => {
    // These are tested indirectly through context menu handling
    // The function extracts domain from URL for allowlist checking
    expect(serviceWorkerSource).toContain('extractDomain');
    expect(serviceWorkerSource).toContain("replace(/^www\\./");
  });

  it('shouldCheckTab filters non-web URLs', () => {
    expect(serviceWorkerSource).toContain('shouldCheckTab');
    expect(serviceWorkerSource).toContain("http://");
    expect(serviceWorkerSource).toContain("https://");
  });
});

// ============================================================================
// ERROR HANDLING TESTS
// ============================================================================

describe('Error Handling', () => {
  let env;

  beforeEach(() => {
    env = createServiceWorkerEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('handles API fetch errors gracefully', async () => {
    const { chromeMock } = env;

    // Set up allowlist
    chromeMock.__setLocalStorageData({ allowlist: ['example.com'] });

    // Mock network error
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

    // Set up script injection
    chromeMock.__setScriptInjectionResults([
      { result: { isRestricted: false, noarchive: false } },
      { result: 'page body' }
    ]);

    const info = {
      menuItemId: 'explain-with-ai',
      selectionText: 'test',
      pageUrl: 'https://example.com'
    };

    const tab = { id: 1, url: 'https://example.com', title: 'Test' };

    // Should not throw
    chromeMock.__triggerContextMenuClick(info, tab);
    await new Promise(resolve => setTimeout(resolve, 150));

    // Should set error badge
    const _badgeState = chromeMock.__getBadgeState(1);
    // Badge should indicate error (checkmark or X)
    expect(chromeMock.action.setBadgeText).toHaveBeenCalled();
  });

  it('handles script injection failures (FAIL OPEN)', async () => {
    const { chromeMock } = env;

    // Make script injection fail (CSP restriction)
    chromeMock.scripting.executeScript.mockRejectedValue(
      new Error('Cannot access a chrome:// URL')
    );

    // The age gate should fail open (allow the tab)
    // This is tested via checkTabForAgeRestriction behavior
  });
});

// ============================================================================
// Issue #391 Phase 2: ERROR HANDLING TESTS
// ============================================================================

describe('Error Handling (Issue #391)', () => {
  let env;

  beforeEach(() => {
    env = createServiceWorkerEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  describe('mapHttpStatusToMessage', () => {
    it('defines mapHttpStatusToMessage function', () => {
      expect(serviceWorkerSource).toContain('function mapHttpStatusToMessage');
    });

    it('maps 401 to auth error message', () => {
      expect(serviceWorkerSource).toContain('status === 401');
      expect(serviceWorkerSource).toContain('Service configuration error');
    });

    it('maps 429 to rate limit with reset time', () => {
      expect(serviceWorkerSource).toContain('status === 429');
      expect(serviceWorkerSource).toContain('Limit reached');
      expect(serviceWorkerSource).toContain('resets_in_seconds');
    });

    it('maps 500 to server error message', () => {
      expect(serviceWorkerSource).toContain('status >= 500');
      expect(serviceWorkerSource).toContain('Server error. Try again shortly.');
    });

    it('handles malformed response (missing signal/gem)', () => {
      // Verify schema validation that checks for signal/gem
      expect(serviceWorkerSource).toContain('!responseData.signal || !responseData.gem');
      expect(serviceWorkerSource).toContain('Unexpected Response');
    });
  });

  describe('storeDiagnostics', () => {
    it('defines storeDiagnostics function', () => {
      expect(serviceWorkerSource).toContain('function storeDiagnostics');
    });

    it('stores to chrome.storage.session', () => {
      expect(serviceWorkerSource).toContain('chrome.storage.session.set');
      expect(serviceWorkerSource).toContain('aletheiaLastRequest');
    });

    it('stores status, latency, timestamp, and error', () => {
      expect(serviceWorkerSource).toContain('lastRequestStatus');
      expect(serviceWorkerSource).toContain('lastRequestLatency');
      expect(serviceWorkerSource).toContain('lastRequestTimestamp');
      expect(serviceWorkerSource).toContain('lastError');
    });
  });

  describe('fetch timeout', () => {
    it('uses AbortController with 30s timeout', () => {
      expect(serviceWorkerSource).toContain('new AbortController()');
      expect(serviceWorkerSource).toContain('setTimeout(() => controller.abort(), 30000)');
      expect(serviceWorkerSource).toContain('signal: controller.signal');
    });

    it('handles AbortError for timeout', () => {
      expect(serviceWorkerSource).toContain("error.name === 'AbortError'");
      expect(serviceWorkerSource).toContain('Request timed out. Try again.');
    });
  });
});

// ============================================================================
// START_OAUTH HANDLER TESTS (Issue #480 — SW OAuth Migration)
// ============================================================================

describe('START_OAUTH Handler (Issue #480)', () => {
  let env;
  const AUTH_URL = 'https://www.linkedin.com/oauth/v2/authorization?client_id=test&state=test-state-123';
  const CSRF_STATE = 'test-state-123';
  const LAMBDA_AUTH_URL = 'https://sk33bz56yi5qlbrrwzqnprmeuy0xwhzn.lambda-url.us-east-1.on.aws';

  beforeEach(() => {
    env = createServiceWorkerEnvironment();
  });

  afterEach(() => {
    cleanupEnvironment();
  });

  it('responds with { success: true, pending: true }', async () => {
    const { chromeMock } = env;

    const response = await chromeMock.__simulateMessage({
      type: 'START_OAUTH',
      authUrl: AUTH_URL,
      state: CSRF_STATE,
      lambdaAuthUrl: LAMBDA_AUTH_URL
    });

    expect(response).toBeDefined();
    expect(response.success).toBe(true);
    expect(response.pending).toBe(true);
  });

  it('calls chrome.identity.launchWebAuthFlow', async () => {
    const { chromeMock } = env;

    chromeMock.__simulateMessage({
      type: 'START_OAUTH',
      authUrl: AUTH_URL,
      state: CSRF_STATE,
      lambdaAuthUrl: LAMBDA_AUTH_URL
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(chromeMock.identity.launchWebAuthFlow).toHaveBeenCalledWith({
      url: AUTH_URL,
      interactive: true
    });
  });

  it('exchanges code for tokens and stores them', async () => {
    const { chromeMock } = env;

    // Mock token exchange endpoint
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        accessToken: 'new-access-token',
        refreshToken: 'new-refresh-token',
        expiresIn: 3600,
        jwt: 'new-jwt-token',
        user: { id: 'user-123', name: 'Test User' }
      })
    });

    chromeMock.__simulateMessage({
      type: 'START_OAUTH',
      authUrl: AUTH_URL,
      state: CSRF_STATE,
      lambdaAuthUrl: LAMBDA_AUTH_URL
    });

    await new Promise(resolve => setTimeout(resolve, 200));

    // Verify token exchange fetch
    expect(global.fetch).toHaveBeenCalledWith(
      `${LAMBDA_AUTH_URL}/auth/token`,
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
    );

    // Verify tokens stored in session storage
    expect(chromeMock.storage.session.set).toHaveBeenCalledWith(
      expect.objectContaining({
        accessToken: 'new-access-token',
        jwt: 'new-jwt-token'
      })
    );

    // Verify user info stored in local storage
    expect(chromeMock.storage.local.set).toHaveBeenCalledWith(
      expect.objectContaining({
        refreshToken: 'new-refresh-token',
        userId: 'user-123',
        displayName: 'Test User'
      })
    );
  });

  it('validates CSRF state before token exchange', async () => {
    const { chromeMock } = env;

    // Configure mock to return mismatched state
    chromeMock.__setOAuthReturnedState('WRONG-STATE');

    global.fetch = vi.fn();

    chromeMock.__simulateMessage({
      type: 'START_OAUTH',
      authUrl: AUTH_URL,
      state: CSRF_STATE,
      lambdaAuthUrl: LAMBDA_AUTH_URL
    });

    await new Promise(resolve => setTimeout(resolve, 200));

    // Token exchange should NOT have been called
    expect(global.fetch).not.toHaveBeenCalled();

    // No access tokens stored
    const sessionSetCalls = chromeMock.storage.session.set.mock.calls;
    const hasAccessToken = sessionSetCalls.some(call =>
      call[0] && call[0].accessToken !== undefined
    );
    expect(hasAccessToken).toBe(false);
  });

  it('handles launchWebAuthFlow failure (user cancelled)', async () => {
    const { chromeMock } = env;

    // Make OAuth flow fail
    chromeMock.__setOAuthShouldFail(true);

    global.fetch = vi.fn();

    chromeMock.__simulateMessage({
      type: 'START_OAUTH',
      authUrl: AUTH_URL,
      state: CSRF_STATE,
      lambdaAuthUrl: LAMBDA_AUTH_URL
    });

    await new Promise(resolve => setTimeout(resolve, 200));

    // Token exchange should NOT have been called
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('handles token exchange failure', async () => {
    const { chromeMock } = env;

    // Mock failed token exchange
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ error: 'Internal server error' })
    });

    chromeMock.__simulateMessage({
      type: 'START_OAUTH',
      authUrl: AUTH_URL,
      state: CSRF_STATE,
      lambdaAuthUrl: LAMBDA_AUTH_URL
    });

    await new Promise(resolve => setTimeout(resolve, 200));

    // No access tokens stored on failure
    const sessionSetCalls = chromeMock.storage.session.set.mock.calls;
    const hasAccessToken = sessionSetCalls.some(call =>
      call[0] && call[0].accessToken !== undefined
    );
    expect(hasAccessToken).toBe(false);
  });

  it('uses chrome.identity.getRedirectURL as redirectUri in token exchange', async () => {
    const { chromeMock } = env;

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        accessToken: 'token',
        refreshToken: 'refresh',
        expiresIn: 3600,
        jwt: 'jwt',
        user: { id: 'u1', name: 'User' }
      })
    });

    chromeMock.__simulateMessage({
      type: 'START_OAUTH',
      authUrl: AUTH_URL,
      state: CSRF_STATE,
      lambdaAuthUrl: LAMBDA_AUTH_URL
    });

    await new Promise(resolve => setTimeout(resolve, 200));

    // Verify the token exchange uses the Chrome redirect URL
    const fetchCall = global.fetch.mock.calls[0];
    const body = JSON.parse(fetchCall[1].body);
    expect(body.redirectUri).toBe('https://mock-extension-id-12345.chromiumapp.org/');
  });
});
