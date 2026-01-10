/**
 * Unit Tests for Chrome popup.js
 *
 * Per ADR 0215: Tests written BEFORE refactoring to verify current behavior.
 * These tests enable safe innerHTML removal by confirming behavior is preserved.
 *
 * Test Categories:
 * 1. Storage Functions - getAllowlist, addToAllowlist, etc.
 * 2. View Rendering - showView, renderMainView, etc.
 * 3. Event Handlers - handlePowerToggle, handleCheckboxChange, etc.
 * 4. Auth Flow - handleLoginClick, handleLogoutClick, etc.
 * 5. Age Gate - checkAgeGate, getTabState, etc.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get directory paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const extensionDir = path.resolve(__dirname, '../../../extensions/chrome');

// Read popup.html and popup.js
const popupHtml = fs.readFileSync(path.join(extensionDir, 'popup.html'), 'utf-8');
const popupJs = fs.readFileSync(path.join(extensionDir, 'popup.js'), 'utf-8');

/**
 * Creates a fresh DOM environment with popup.html structure
 * and evaluates popup.js within it.
 */
function createPopupEnvironment(options = {}) {
  const { authenticated = false, allowlist = [], tabUrl = 'https://example.com' } = options;

  // Strip external resource references from HTML to prevent JSDOM fetch errors
  // Remove CSS link and script tags (we mock everything anyway)
  let cleanHtml = popupHtml
    .replace(/<link[^>]*href="popup\.css"[^>]*>/g, '')
    .replace(/<script[^>]*src="auth\.js"[^>]*><\/script>/g, '')
    .replace(/<script[^>]*src="popup\.js"[^>]*><\/script>/g, '');

  // Create JSDOM instance without resource loading
  const dom = new JSDOM(cleanHtml, {
    url: 'http://localhost/popup.html',
    runScripts: 'dangerously',
    pretendToBeVisual: true
  });

  const { window } = dom;

  // Set up Chrome API mock
  window.chrome = createChromeMockForWindow(window, { allowlist, tabUrl });

  // Set up AletheiaAuth mock
  window.AletheiaAuth = createAuthMockForWindow(window, { authenticated });

  // Execute popup.js in the window context
  window.eval(popupJs);

  // Manually trigger DOMContentLoaded if not already fired
  if (window.document.readyState === 'loading') {
    window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
  }

  return { dom, window };
}

/**
 * Creates Chrome mock for a specific window context
 */
function createChromeMockForWindow(window, options = {}) {
  const { allowlist = [], tabUrl = 'https://example.com' } = options;

  let storageData = { allowlist: [...allowlist] };
  let messageResponses = {};

  return {
    runtime: {
      id: 'mock-extension-id-12345',
      sendMessage: vi.fn().mockImplementation((message) => {
        return Promise.resolve(messageResponses[message.type] || { state: 'allowed' });
      }),
      onMessage: {
        addListener: vi.fn(),
        removeListener: vi.fn()
      }
    },
    tabs: {
      query: vi.fn().mockImplementation(() => {
        return Promise.resolve([{
          id: 1,
          url: tabUrl,
          active: true,
          currentWindow: true
        }]);
      })
    },
    storage: {
      local: {
        get: vi.fn().mockImplementation((keys) => {
          if (typeof keys === 'string') {
            return Promise.resolve({ [keys]: storageData[keys] });
          }
          return Promise.resolve({ ...storageData });
        }),
        set: vi.fn().mockImplementation((items) => {
          Object.assign(storageData, items);
          return Promise.resolve();
        })
      }
    },
    __setMessageResponse: (type, response) => {
      messageResponses[type] = response;
    },
    __getStorageData: () => storageData,
    __setStorageData: (data) => { storageData = data; }
  };
}

/**
 * Creates AletheiaAuth mock for a specific window context
 */
function createAuthMockForWindow(window, options = {}) {
  const { authenticated = false } = options;

  let isAuthed = authenticated;
  let authState = authenticated ? { displayName: 'Test User', name: 'Test User' } : null;
  let loginShouldSucceed = true;

  return {
    isAuthenticated: vi.fn().mockImplementation(() => Promise.resolve(isAuthed)),
    initiateLogin: vi.fn().mockImplementation(() => {
      if (loginShouldSucceed) {
        isAuthed = true;
        authState = { name: 'Test User', displayName: 'Test User' };
        return Promise.resolve(authState);
      }
      return Promise.reject(new Error('Login failed'));
    }),
    logout: vi.fn().mockImplementation(() => {
      isAuthed = false;
      authState = null;
      return Promise.resolve();
    }),
    getAuthState: vi.fn().mockImplementation(() => Promise.resolve(authState)),
    __setAuthenticated: (authed) => {
      isAuthed = authed;
      authState = authed ? { displayName: 'Test User', name: 'Test User' } : null;
    },
    __setLoginBehavior: (shouldSucceed) => { loginShouldSucceed = shouldSucceed; }
  };
}

// ============================================================================
// STORAGE FUNCTION TESTS
// ============================================================================

describe('Storage Functions', () => {
  let env;

  beforeEach(() => {
    env = createPopupEnvironment({ authenticated: true, allowlist: [] });
  });

  afterEach(() => {
    env.dom.window.close();
  });

  describe('getAllowlist', () => {
    it('should return empty array when no allowlist exists', async () => {
      const { window } = env;

      // Wait for DOMContentLoaded
      await new Promise(resolve => setTimeout(resolve, 50));

      const result = await window.getAllowlist();
      expect(result).toEqual([]);
    });

    it('should return existing allowlist', async () => {
      const { window } = env;
      window.chrome.__setStorageData({ allowlist: ['example.com', 'test.com'] });

      await new Promise(resolve => setTimeout(resolve, 50));

      const result = await window.getAllowlist();
      expect(result).toEqual(['example.com', 'test.com']);
    });

    it('should handle storage errors gracefully', async () => {
      const { window } = env;
      window.chrome.storage.local.get.mockRejectedValueOnce(new Error('Storage error'));

      await new Promise(resolve => setTimeout(resolve, 50));

      const result = await window.getAllowlist();
      expect(result).toEqual([]);
    });
  });

  describe('addToAllowlist', () => {
    it('should add domain to empty allowlist', async () => {
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 50));

      await window.addToAllowlist('newsite.com');

      expect(window.chrome.storage.local.set).toHaveBeenCalledWith({
        allowlist: ['newsite.com']
      });
    });

    it('should not add duplicate domain', async () => {
      const { window } = env;
      window.chrome.__setStorageData({ allowlist: ['existing.com'] });

      await new Promise(resolve => setTimeout(resolve, 50));

      await window.addToAllowlist('existing.com');

      // Should not call set since domain already exists
      const setCalls = window.chrome.storage.local.set.mock.calls;
      const lastCall = setCalls[setCalls.length - 1];
      if (lastCall) {
        expect(lastCall[0].allowlist).not.toContain('existing.com');
      }
    });
  });

  describe('removeFromAllowlist', () => {
    it('should remove domain from allowlist', async () => {
      const { window } = env;
      window.chrome.__setStorageData({ allowlist: ['site1.com', 'site2.com'] });

      await new Promise(resolve => setTimeout(resolve, 50));

      await window.removeFromAllowlist('site1.com');

      expect(window.chrome.storage.local.set).toHaveBeenCalledWith({
        allowlist: ['site2.com']
      });
    });
  });

  describe('removeManyFromAllowlist', () => {
    it('should remove multiple domains at once', async () => {
      const { window } = env;
      window.chrome.__setStorageData({ allowlist: ['a.com', 'b.com', 'c.com'] });

      await new Promise(resolve => setTimeout(resolve, 50));

      await window.removeManyFromAllowlist(['a.com', 'c.com']);

      expect(window.chrome.storage.local.set).toHaveBeenCalledWith({
        allowlist: ['b.com']
      });
    });
  });

  describe('clearAllData', () => {
    it('should clear the allowlist', async () => {
      const { window } = env;
      window.chrome.__setStorageData({ allowlist: ['site.com'] });

      await new Promise(resolve => setTimeout(resolve, 50));

      await window.clearAllData();

      expect(window.chrome.storage.local.set).toHaveBeenCalledWith({
        allowlist: []
      });
    });
  });
});

// ============================================================================
// VIEW RENDERING TESTS
// ============================================================================

describe('View Rendering', () => {
  let env;

  beforeEach(() => {
    env = createPopupEnvironment({ authenticated: true });
  });

  afterEach(() => {
    env.dom.window.close();
  });

  describe('showView', () => {
    it('should show only the specified view', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 50));

      window.showView('main');

      expect(document.getElementById('main-view').style.display).toBe('block');
      expect(document.getElementById('login-view').style.display).toBe('none');
      expect(document.getElementById('manage-view').style.display).toBe('none');
      expect(document.getElementById('confirm-view').style.display).toBe('none');
    });

    it('should show login view', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 50));

      window.showView('login');

      expect(document.getElementById('login-view').style.display).toBe('block');
      expect(document.getElementById('main-view').style.display).toBe('none');
    });

    it('should show manage view', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 50));

      window.showView('manage');

      expect(document.getElementById('manage-view').style.display).toBe('block');
      expect(document.getElementById('main-view').style.display).toBe('none');
    });

    it('should show confirm view', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 50));

      window.showView('confirm');

      expect(document.getElementById('confirm-view').style.display).toBe('block');
    });

    it('should show restricted view', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 50));

      window.showView('restricted');

      expect(document.getElementById('restricted-view').style.display).toBe('block');
    });

    it('should show checking view', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 50));

      window.showView('checking');

      expect(document.getElementById('checking-view').style.display).toBe('block');
    });
  });

  describe('renderMainView', () => {
    it('should display current domain', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      await window.renderMainView();

      const domainEl = document.getElementById('current-domain');
      expect(domainEl.textContent).toBe('example.com');
    });

    it('should show ACTIVE status when domain is allowlisted', async () => {
      const { window } = env;
      const { document } = window;
      window.chrome.__setStorageData({ allowlist: ['example.com'] });

      await new Promise(resolve => setTimeout(resolve, 100));

      await window.renderMainView();

      const statusLabel = document.getElementById('status-label');
      expect(statusLabel.textContent).toBe('ACTIVE');
    });

    it('should show INACTIVE status when domain is not allowlisted', async () => {
      const { window } = env;
      const { document } = window;
      window.chrome.__setStorageData({ allowlist: [] });

      await new Promise(resolve => setTimeout(resolve, 100));

      await window.renderMainView();

      const statusLabel = document.getElementById('status-label');
      expect(statusLabel.textContent).toBe('INACTIVE');
    });

    // TODO: Fix legacy scope issue (See Issue #215)
    it.skip('should handle null domain gracefully', async () => {
      const { window } = env;
      const { document } = window;

      // Make tabs.query return no URL
      window.chrome.tabs.query.mockResolvedValueOnce([{ id: 1, url: null }]);

      await new Promise(resolve => setTimeout(resolve, 100));

      await window.renderMainView();

      const domainEl = document.getElementById('current-domain');
      expect(domainEl.textContent).toBe('Unknown');
    });
  });

  describe('renderManagementView', () => {
    it('should show empty state when allowlist is empty', async () => {
      const { window } = env;
      const { document } = window;
      window.chrome.__setStorageData({ allowlist: [] });

      await new Promise(resolve => setTimeout(resolve, 100));

      await window.renderManagementView();

      const emptyState = document.getElementById('empty-state');
      expect(emptyState.style.display).toBe('block');
    });

    it('should display site count correctly', async () => {
      const { window } = env;
      const { document } = window;
      window.chrome.__setStorageData({ allowlist: ['a.com', 'b.com', 'c.com'] });

      await new Promise(resolve => setTimeout(resolve, 100));

      await window.renderManagementView();

      const siteCount = document.getElementById('site-count');
      expect(siteCount.textContent).toBe('3 sites');
    });

    it('should use singular "site" for count of 1', async () => {
      const { window } = env;
      const { document } = window;
      window.chrome.__setStorageData({ allowlist: ['single.com'] });

      await new Promise(resolve => setTimeout(resolve, 100));

      await window.renderManagementView();

      const siteCount = document.getElementById('site-count');
      expect(siteCount.textContent).toBe('1 site');
    });

    it('should render allowlist items', async () => {
      const { window } = env;
      const { document } = window;
      window.chrome.__setStorageData({ allowlist: ['site1.com', 'site2.com'] });

      await new Promise(resolve => setTimeout(resolve, 100));

      await window.renderManagementView();

      const allowlistEl = document.getElementById('allowlist');
      expect(allowlistEl.children.length).toBe(2);
    });

    it('should clear allowlist element before re-rendering (innerHTML = "" behavior)', async () => {
      const { window } = env;
      const { document } = window;

      // First render with 2 items
      window.chrome.__setStorageData({ allowlist: ['a.com', 'b.com'] });
      await new Promise(resolve => setTimeout(resolve, 100));
      await window.renderManagementView();

      // Then render with 1 item
      window.chrome.__setStorageData({ allowlist: ['c.com'] });
      await window.renderManagementView();

      const allowlistEl = document.getElementById('allowlist');
      // Should have only 1 item, not 3 (old items should be cleared)
      expect(allowlistEl.children.length).toBe(1);
    });
  });

  describe('createAllowlistItem', () => {
    it('should create label element with checkbox', async () => {
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      const item = window.createAllowlistItem('test.com');

      expect(item.tagName).toBe('LABEL');
      expect(item.className).toBe('allowlist-item');

      const checkbox = item.querySelector('input[type="checkbox"]');
      expect(checkbox).not.toBeNull();
      expect(checkbox.dataset.domain).toBe('test.com');
    });

    it('should display domain name in span', async () => {
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      const item = window.createAllowlistItem('example.com');

      const domainSpan = item.querySelector('.allowlist-item-domain');
      expect(domainSpan.textContent).toBe('example.com');
    });

    // TODO: Fix legacy scope issue (See Issue #215)
    it.skip('should add current badge when domain matches currentDomain', async () => {
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      // Set currentDomain
      window.currentDomain = 'current.com';

      const item = window.createAllowlistItem('current.com');

      const badge = item.querySelector('.current-badge');
      expect(badge).not.toBeNull();
      expect(badge.textContent).toBe('current');
    });
  });
});

// ============================================================================
// EVENT HANDLER TESTS
// ============================================================================

describe('Event Handlers', () => {
  let env;

  beforeEach(() => {
    env = createPopupEnvironment({ authenticated: true });
  });

  afterEach(() => {
    env.dom.window.close();
  });

  describe('handleCheckboxChange', () => {
    // TODO: Fix legacy scope issue (See Issue #215)
    it.skip('should add domain to selectedDomains when checked', async () => {
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      // Create a mock event
      const mockCheckbox = window.document.createElement('input');
      mockCheckbox.type = 'checkbox';
      mockCheckbox.dataset.domain = 'test.com';
      mockCheckbox.checked = true;

      const mockLabel = window.document.createElement('label');
      mockLabel.className = 'allowlist-item';
      mockLabel.appendChild(mockCheckbox);

      const mockEvent = {
        target: mockCheckbox
      };

      window.handleCheckboxChange(mockEvent);

      expect(window.selectedDomains.has('test.com')).toBe(true);
    });

    // TODO: Fix legacy scope issue (See Issue #215)
    it.skip('should remove domain from selectedDomains when unchecked', async () => {
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      // Pre-add the domain
      window.selectedDomains.add('test.com');

      const mockCheckbox = window.document.createElement('input');
      mockCheckbox.type = 'checkbox';
      mockCheckbox.dataset.domain = 'test.com';
      mockCheckbox.checked = false;

      const mockLabel = window.document.createElement('label');
      mockLabel.className = 'allowlist-item';
      mockLabel.appendChild(mockCheckbox);

      const mockEvent = {
        target: mockCheckbox
      };

      window.handleCheckboxChange(mockEvent);

      expect(window.selectedDomains.has('test.com')).toBe(false);
    });
  });

  describe('updateRemoveButton', () => {
    // TODO: Fix legacy scope issue (See Issue #215)
    it.skip('should disable button when no domains selected', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      window.selectedDomains.clear();
      window.updateRemoveButton();

      const removeButton = document.getElementById('remove-button');
      expect(removeButton.disabled).toBe(true);
      expect(removeButton.textContent).toBe('Remove Selected');
    });

    // TODO: Fix legacy scope issue (See Issue #215)
    it.skip('should enable button and show count when domains selected', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      window.selectedDomains.add('a.com');
      window.selectedDomains.add('b.com');
      window.updateRemoveButton();

      const removeButton = document.getElementById('remove-button');
      expect(removeButton.disabled).toBe(false);
      expect(removeButton.textContent).toBe('Remove Selected (2)');
    });
  });
});

// ============================================================================
// AUTH FLOW TESTS
// ============================================================================

describe('Auth Flow', () => {
  describe('when not authenticated', () => {
    let env;

    beforeEach(() => {
      env = createPopupEnvironment({ authenticated: false });
    });

    afterEach(() => {
      env.dom.window.close();
    });

    it('should show login view on init', async () => {
      const { window } = env;
      const { document } = window;

      // Wait for init to complete
      await new Promise(resolve => setTimeout(resolve, 200));

      const loginView = document.getElementById('login-view');
      expect(loginView.style.display).toBe('block');
    });
  });

  describe('when authenticated', () => {
    let env;

    beforeEach(() => {
      env = createPopupEnvironment({ authenticated: true });
    });

    afterEach(() => {
      env.dom.window.close();
    });

    it('should not show login view on init', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 200));

      const loginView = document.getElementById('login-view');
      expect(loginView.style.display).toBe('none');
    });

    it('should update user bar with display name', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 200));

      await window.updateUserBar();

      const userName = document.getElementById('user-name');
      expect(userName.textContent).toBe('Test User');
    });
  });

  describe('handleLoginClick', () => {
    let env;

    beforeEach(() => {
      env = createPopupEnvironment({ authenticated: false });
    });

    afterEach(() => {
      env.dom.window.close();
    });

    it('should disable button during login attempt', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      const loginButton = document.getElementById('login-button');

      // Start login (don't await)
      window.handleLoginClick();

      expect(loginButton.disabled).toBe(true);
      expect(loginButton.textContent).toBe('Signing in...');
    });

    it('should show error message on login failure', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      // Make login fail
      window.AletheiaAuth.__setLoginBehavior(false);

      await window.handleLoginClick();

      const loginError = document.getElementById('login-error');
      expect(loginError.style.display).toBe('block');
      expect(loginError.textContent).toContain('Login failed');
    });

    it('should reset button after login failure (innerHTML behavior)', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      // Make login fail
      window.AletheiaAuth.__setLoginBehavior(false);

      await window.handleLoginClick();

      const loginButton = document.getElementById('login-button');
      expect(loginButton.disabled).toBe(false);

      // Check that button has LinkedIn icon span
      const iconSpan = loginButton.querySelector('.linkedin-icon');
      expect(iconSpan).not.toBeNull();
      expect(iconSpan.textContent).toBe('in');
    });
  });

  describe('handleLogoutClick', () => {
    let env;

    beforeEach(() => {
      env = createPopupEnvironment({ authenticated: true });
    });

    afterEach(() => {
      env.dom.window.close();
    });

    it('should show login view after logout', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      await window.handleLogoutClick();

      const loginView = document.getElementById('login-view');
      expect(loginView.style.display).toBe('block');
    });

    it('should call AletheiaAuth.logout', async () => {
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      await window.handleLogoutClick();

      expect(window.AletheiaAuth.logout).toHaveBeenCalled();
    });
  });
});

// ============================================================================
// AGE GATE TESTS
// ============================================================================

describe('Age Gate', () => {
  let env;

  beforeEach(() => {
    env = createPopupEnvironment({ authenticated: true });
  });

  afterEach(() => {
    env.dom.window.close();
  });

  describe('getTabState', () => {
    it('should return state from service worker response', async () => {
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      window.chrome.__setMessageResponse('GET_TAB_STATE', { state: 'allowed' });

      const state = await window.getTabState(1);
      expect(state).toBe('allowed');
    });

    it('should return unknown on error', async () => {
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      window.chrome.runtime.sendMessage.mockRejectedValueOnce(new Error('Error'));

      const state = await window.getTabState(1);
      expect(state).toBe('unknown');
    });
  });

  describe('checkAgeGate', () => {
    it('should show restricted view when tab is restricted', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      window.chrome.__setMessageResponse('GET_TAB_STATE', { state: 'restricted' });

      await window.checkAgeGate();

      // Allow async operations to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      const restrictedView = document.getElementById('restricted-view');
      expect(restrictedView.style.display).toBe('block');
    });

    it('should show main view when tab is allowed', async () => {
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      window.chrome.__setMessageResponse('GET_TAB_STATE', { state: 'allowed' });

      await window.checkAgeGate();

      await new Promise(resolve => setTimeout(resolve, 100));

      const mainView = document.getElementById('main-view');
      expect(mainView.style.display).toBe('block');
    });
  });
});

// ============================================================================
// DOMAIN PARSING TESTS
// ============================================================================

describe('Domain Parsing', () => {
  describe('getCurrentDomain', () => {
    it('should strip www prefix', async () => {
      const env = createPopupEnvironment({
        authenticated: true,
        tabUrl: 'https://www.example.com/page'
      });

      await new Promise(resolve => setTimeout(resolve, 100));

      const domain = await env.window.getCurrentDomain();
      expect(domain).toBe('example.com');

      env.dom.window.close();
    });

    it('should handle URLs without www', async () => {
      const env = createPopupEnvironment({
        authenticated: true,
        tabUrl: 'https://subdomain.example.com'
      });

      await new Promise(resolve => setTimeout(resolve, 100));

      const domain = await env.window.getCurrentDomain();
      expect(domain).toBe('subdomain.example.com');

      env.dom.window.close();
    });

    it('should return null for invalid URLs', async () => {
      const env = createPopupEnvironment({ authenticated: true });

      await new Promise(resolve => setTimeout(resolve, 100));

      // Mock tabs.query to return invalid URL
      env.window.chrome.tabs.query.mockResolvedValueOnce([{ id: 1, url: 'not-a-url' }]);

      const domain = await env.window.getCurrentDomain();
      expect(domain).toBeNull();

      env.dom.window.close();
    });
  });
});
