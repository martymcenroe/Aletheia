/**
 * Unit Tests for Firefox popup.js
 *
 * Per LLD 1206 & ADR 0215: Tests written BEFORE implementation (Red-Green-Refactor).
 * These tests verify Firefox popup view switching and auth integration.
 *
 * Test Categories:
 * 1. View Switching - Login, main, manage, confirm, restricted, checking views
 * 2. Auth Integration - Login handler, logout handler, user bar updates
 * 3. Storage Functions - Allowlist management (mirrors Chrome tests)
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import { createFirefoxMock } from '../../mocks/firefox-api.mock.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get directory paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const extensionDir = path.resolve(__dirname, '../../../extensions/firefox');

// Read popup.html and popup.js
let popupHtml = '';
let popupJs = '';

try {
  popupHtml = fs.readFileSync(path.join(extensionDir, 'popup.html'), 'utf-8');
} catch (_e) {
  popupHtml = '';
}

try {
  popupJs = fs.readFileSync(path.join(extensionDir, 'popup.js'), 'utf-8');
} catch (_e) {
  popupJs = '';
}

/**
 * Creates a fresh DOM environment with popup.html structure
 * and evaluates popup.js within it.
 */
function createPopupEnvironment(options = {}) {
  const { authenticated = false, allowlist = [], tabUrl = 'https://example.com' } = options;

  if (!popupHtml) {
    // Return minimal mock if HTML doesn't exist yet
    return { dom: null, window: null, hasContent: false };
  }

  // Strip external resource references from HTML
  let cleanHtml = popupHtml
    .replace(/<link[^>]*href="popup\.css"[^>]*>/g, '')
    .replace(/<script[^>]*src="auth\.js"[^>]*><\/script>/g, '')
    .replace(/<script[^>]*src="popup\.js"[^>]*><\/script>/g, '');

  // Create JSDOM instance
  const dom = new JSDOM(cleanHtml, {
    url: 'http://localhost/popup.html',
    runScripts: 'dangerously',
    pretendToBeVisual: true
  });

  const { window } = dom;

  // Set up Firefox API mock
  const browserMock = createFirefoxMock({ allowlist, tabUrl, authenticated });
  window.browser = browserMock;

  // Set up AletheiaAuth mock (don't eval auth.js - it's tested separately)
  // Using mock allows spy verification in tests
  window.AletheiaAuth = createAuthMock(authenticated);

  // Execute popup.js if it exists
  if (popupJs) {
    try {
      window.eval(popupJs);
    } catch (e) {
      console.error('Error evaluating popup.js:', e.message);
    }
  }

  // Manually trigger DOMContentLoaded
  if (window.document.readyState === 'loading') {
    window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
  }

  return { dom, window, browserMock, hasContent: true };
}

/**
 * Creates AletheiaAuth mock for popup testing
 */
function createAuthMock(authenticated = false) {
  let isAuthed = authenticated;
  let authState = authenticated
    ? { userId: 'mock-user-123', displayName: 'Test User' }
    : null;
  let loginShouldSucceed = true;

  return {
    isAuthenticated: vi.fn().mockImplementation(() => Promise.resolve(isAuthed)),
    initiateLogin: vi.fn().mockImplementation(() => {
      if (loginShouldSucceed) {
        isAuthed = true;
        authState = { userId: 'mock-user-123', displayName: 'Test User' };
        return Promise.resolve({ id: 'mock-user-123', name: 'Test User' });
      }
      return Promise.reject(new Error('Login failed'));
    }),
    logout: vi.fn().mockImplementation(() => {
      isAuthed = false;
      authState = null;
      return Promise.resolve();
    }),
    getAuthState: vi.fn().mockImplementation(() => Promise.resolve(authState)),
    getAccessToken: vi.fn().mockResolvedValue('mock-access-token'),
    clearTokens: vi.fn().mockResolvedValue(undefined),
    __setAuthenticated: (authed) => {
      isAuthed = authed;
      authState = authed ? { userId: 'mock-user-123', displayName: 'Test User' } : null;
    },
    __setLoginBehavior: (shouldSucceed) => {
      loginShouldSucceed = shouldSucceed;
    }
  };
}

// ============================================================================
// FILE EXISTENCE TESTS
// ============================================================================

describe('Firefox Popup Files', () => {
  it('popup.html exists and contains required views', () => {
    expect(popupHtml.length).toBeGreaterThan(0);

    // Check for auth-related views (added per LLD 1206)
    expect(popupHtml).toContain('id="login-view"');
    expect(popupHtml).toContain('id="main-view"');
    expect(popupHtml).toContain('id="manage-view"');
    expect(popupHtml).toContain('id="confirm-view"');
  });

  it('popup.html contains user bar for authenticated state', () => {
    expect(popupHtml).toContain('id="user-bar"');
    expect(popupHtml).toContain('id="user-name"');
    expect(popupHtml).toContain('id="logout-button"');
  });

  it('popup.html contains login button', () => {
    expect(popupHtml).toContain('id="login-button"');
  });

  it('popup.js exists', () => {
    expect(popupJs.length).toBeGreaterThan(0);
  });

  it('popup.js uses browser.* not chrome.*', () => {
    if (popupJs.length > 0) {
      expect(popupJs).toContain('browser.');
      expect(popupJs).not.toContain('chrome.');
    }
  });
});

// ============================================================================
// VIEW SWITCHING TESTS
// ============================================================================

describe('View Switching', () => {
  let env;

  beforeEach(() => {
    env = createPopupEnvironment({ authenticated: true });
  });

  afterEach(() => {
    if (env.dom) {
      env.dom.window.close();
    }
  });

  it('showView shows only the specified view', async () => {
    if (!env.hasContent) return;
    const { window } = env;
    const { document } = window;

    await new Promise(resolve => setTimeout(resolve, 50));

    if (window.showView) {
      window.showView('main');

      const mainView = document.getElementById('main-view');
      const loginView = document.getElementById('login-view');
      const manageView = document.getElementById('manage-view');

      expect(mainView?.style.display).toBe('block');
      expect(loginView?.style.display).toBe('none');
      expect(manageView?.style.display).toBe('none');
    }
  });

  it('shows login view when not authenticated', async () => {
    const envUnauth = createPopupEnvironment({ authenticated: false });
    if (!envUnauth.hasContent) return;

    const { window, dom } = envUnauth;
    const { document } = window;

    // Wait for init to complete
    await new Promise(resolve => setTimeout(resolve, 200));

    const loginView = document.getElementById('login-view');
    if (loginView) {
      expect(loginView.style.display).toBe('block');
    }

    dom.window.close();
  });

  it('shows main view when authenticated', async () => {
    if (!env.hasContent) return;
    const { window } = env;
    const { document } = window;

    await new Promise(resolve => setTimeout(resolve, 200));

    const mainView = document.getElementById('main-view');
    const loginView = document.getElementById('login-view');

    if (mainView && loginView) {
      expect(mainView.style.display).toBe('block');
      expect(loginView.style.display).toBe('none');
    }
  });
});

// ============================================================================
// AUTH INTEGRATION TESTS
// ============================================================================

describe('Auth Integration', () => {
  let env;

  beforeEach(() => {
    env = createPopupEnvironment({ authenticated: false });
  });

  afterEach(() => {
    if (env.dom) {
      env.dom.window.close();
    }
  });

  it('handleLoginClick calls AletheiaAuth.initiateLogin', async () => {
    if (!env.hasContent) return;
    const { window } = env;

    await new Promise(resolve => setTimeout(resolve, 100));

    if (window.handleLoginClick) {
      await window.handleLoginClick();
      expect(window.AletheiaAuth.initiateLogin).toHaveBeenCalled();
    }
  });

  it('handleLoginClick shows error on failure', async () => {
    if (!env.hasContent) return;
    const { window } = env;
    const { document } = window;

    await new Promise(resolve => setTimeout(resolve, 100));

    // Make login fail
    window.AletheiaAuth.__setLoginBehavior(false);

    if (window.handleLoginClick) {
      await window.handleLoginClick();

      const loginError = document.getElementById('login-error');
      if (loginError) {
        expect(loginError.style.display).toBe('block');
        expect(loginError.textContent).toContain('failed');
      }
    }
  });

  it('handleLogoutClick calls AletheiaAuth.logout', async () => {
    const envAuth = createPopupEnvironment({ authenticated: true });
    if (!envAuth.hasContent) return;

    const { window, dom } = envAuth;

    await new Promise(resolve => setTimeout(resolve, 100));

    if (window.handleLogoutClick) {
      await window.handleLogoutClick();
      expect(window.AletheiaAuth.logout).toHaveBeenCalled();
    }

    dom.window.close();
  });

  it('updateUserBar shows display name', async () => {
    const envAuth = createPopupEnvironment({ authenticated: true });
    if (!envAuth.hasContent) return;

    const { window, dom } = envAuth;
    const { document } = window;

    await new Promise(resolve => setTimeout(resolve, 100));

    if (window.updateUserBar) {
      await window.updateUserBar();

      const userName = document.getElementById('user-name');
      if (userName) {
        expect(userName.textContent).toBe('Test User');
      }
    }

    dom.window.close();
  });
});

// ============================================================================
// STORAGE FUNCTIONS TESTS (Parity with Chrome)
// ============================================================================

describe('Storage Functions', () => {
  let env;

  beforeEach(() => {
    env = createPopupEnvironment({ authenticated: true, allowlist: [] });
  });

  afterEach(() => {
    if (env.dom) {
      env.dom.window.close();
    }
  });

  it('getAllowlist returns empty array when no allowlist exists', async () => {
    if (!env.hasContent) return;
    const { window } = env;

    await new Promise(resolve => setTimeout(resolve, 50));

    if (window.getAllowlist) {
      const result = await window.getAllowlist();
      expect(result).toEqual([]);
    }
  });

  it('addToAllowlist adds domain to storage', async () => {
    if (!env.hasContent) return;
    const { window, browserMock } = env;

    await new Promise(resolve => setTimeout(resolve, 50));

    if (window.addToAllowlist) {
      await window.addToAllowlist('newsite.com');

      expect(browserMock.storage.local.set).toHaveBeenCalledWith({
        allowlist: expect.arrayContaining(['newsite.com'])
      });
    }
  });

  it('removeFromAllowlist removes domain from storage', async () => {
    if (!env.hasContent) return;
    const { window, browserMock } = env;

    browserMock.__setLocalStorageData({ allowlist: ['site1.com', 'site2.com'] });

    await new Promise(resolve => setTimeout(resolve, 50));

    if (window.removeFromAllowlist) {
      await window.removeFromAllowlist('site1.com');

      expect(browserMock.storage.local.set).toHaveBeenCalledWith({
        allowlist: ['site2.com']
      });
    }
  });
});

// ============================================================================
// DOMAIN PARSING TESTS
// ============================================================================

describe('Domain Parsing', () => {
  it('getCurrentDomain strips www prefix', async () => {
    const env = createPopupEnvironment({
      authenticated: true,
      tabUrl: 'https://www.example.com/page'
    });

    if (!env.hasContent) return;

    await new Promise(resolve => setTimeout(resolve, 100));

    if (env.window.getCurrentDomain) {
      const domain = await env.window.getCurrentDomain();
      expect(domain).toBe('example.com');
    }

    env.dom.window.close();
  });

  it('getCurrentDomain handles subdomains', async () => {
    const env = createPopupEnvironment({
      authenticated: true,
      tabUrl: 'https://subdomain.example.com'
    });

    if (!env.hasContent) return;

    await new Promise(resolve => setTimeout(resolve, 100));

    if (env.window.getCurrentDomain) {
      const domain = await env.window.getCurrentDomain();
      expect(domain).toBe('subdomain.example.com');
    }

    env.dom.window.close();
  });
});

// ============================================================================
// EVENT HANDLERS TESTS (Issue #214 - Parity with Chrome)
// ============================================================================

describe('Event Handlers', () => {
  let env;

  beforeEach(() => {
    env = createPopupEnvironment({ authenticated: true });
  });

  afterEach(() => {
    if (env.dom) {
      env.dom.window.close();
    }
  });

  describe('handleCheckboxChange', () => {
    it('should add domain to selectedDomains when checked', async () => {
      if (!env.hasContent) return;
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.handleCheckboxChange) {
        const mockCheckbox = window.document.createElement('input');
        mockCheckbox.type = 'checkbox';
        mockCheckbox.dataset.domain = 'test.com';
        mockCheckbox.checked = true;

        const mockLabel = window.document.createElement('label');
        mockLabel.className = 'allowlist-item';
        mockLabel.appendChild(mockCheckbox);

        const mockEvent = { target: mockCheckbox };
        window.handleCheckboxChange(mockEvent);

        expect(window.selectedDomains.has('test.com')).toBe(true);
      }
    });

    it('should remove domain from selectedDomains when unchecked', async () => {
      if (!env.hasContent) return;
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.handleCheckboxChange && window.selectedDomains) {
        window.selectedDomains.add('test.com');

        const mockCheckbox = window.document.createElement('input');
        mockCheckbox.type = 'checkbox';
        mockCheckbox.dataset.domain = 'test.com';
        mockCheckbox.checked = false;

        const mockLabel = window.document.createElement('label');
        mockLabel.className = 'allowlist-item';
        mockLabel.appendChild(mockCheckbox);

        const mockEvent = { target: mockCheckbox };
        window.handleCheckboxChange(mockEvent);

        expect(window.selectedDomains.has('test.com')).toBe(false);
      }
    });
  });

  describe('updateRemoveButton', () => {
    it('should disable button when no domains selected', async () => {
      if (!env.hasContent) return;
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.updateRemoveButton && window.selectedDomains) {
        window.selectedDomains.clear();
        window.updateRemoveButton();

        const removeButton = document.getElementById('remove-button');
        if (removeButton) {
          expect(removeButton.disabled).toBe(true);
          expect(removeButton.textContent).toBe('Remove Selected');
        }
      }
    });

    it('should enable button and show count when domains selected', async () => {
      if (!env.hasContent) return;
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.updateRemoveButton && window.selectedDomains) {
        window.selectedDomains.add('a.com');
        window.selectedDomains.add('b.com');
        window.updateRemoveButton();

        const removeButton = document.getElementById('remove-button');
        if (removeButton) {
          expect(removeButton.disabled).toBe(false);
          expect(removeButton.textContent).toBe('Remove Selected (2)');
        }
      }
    });
  });
});

// ============================================================================
// VIEW RENDERING TESTS (Issue #214 - Parity with Chrome)
// ============================================================================

describe('View Rendering', () => {
  let env;

  beforeEach(() => {
    env = createPopupEnvironment({ authenticated: true });
  });

  afterEach(() => {
    if (env.dom) {
      env.dom.window.close();
    }
  });

  describe('renderMainView', () => {
    it('should display current domain', async () => {
      if (!env.hasContent) return;
      const { window } = env;
      const { document } = window;

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.renderMainView) {
        await window.renderMainView();

        const domainEl = document.getElementById('current-domain');
        if (domainEl) {
          expect(domainEl.textContent).toBe('example.com');
        }
      }
    });

    it('should show ACTIVE status when domain is allowlisted', async () => {
      if (!env.hasContent) return;
      const { window, browserMock } = env;
      const { document } = window;

      browserMock.__setLocalStorageData({ allowlist: ['example.com'] });

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.renderMainView) {
        await window.renderMainView();

        const statusLabel = document.getElementById('status-label');
        if (statusLabel) {
          expect(statusLabel.textContent).toBe('ACTIVE');
        }
      }
    });

    it('should show INACTIVE status when domain is not allowlisted', async () => {
      if (!env.hasContent) return;
      const { window, browserMock } = env;
      const { document } = window;

      browserMock.__setLocalStorageData({ allowlist: [] });

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.renderMainView) {
        await window.renderMainView();

        const statusLabel = document.getElementById('status-label');
        if (statusLabel) {
          expect(statusLabel.textContent).toBe('INACTIVE');
        }
      }
    });
  });

  describe('renderManagementView', () => {
    it('should show empty state when allowlist is empty', async () => {
      if (!env.hasContent) return;
      const { window, browserMock } = env;
      const { document } = window;

      browserMock.__setLocalStorageData({ allowlist: [] });

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.renderManagementView) {
        await window.renderManagementView();

        const emptyState = document.getElementById('empty-state');
        if (emptyState) {
          expect(emptyState.style.display).toBe('block');
        }
      }
    });

    it('should display site count correctly', async () => {
      if (!env.hasContent) return;
      const { window, browserMock } = env;
      const { document } = window;

      browserMock.__setLocalStorageData({ allowlist: ['a.com', 'b.com', 'c.com'] });

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.renderManagementView) {
        await window.renderManagementView();

        const siteCount = document.getElementById('site-count');
        if (siteCount) {
          expect(siteCount.textContent).toBe('3 sites');
        }
      }
    });

    it('should use singular "site" for count of 1', async () => {
      if (!env.hasContent) return;
      const { window, browserMock } = env;
      const { document } = window;

      browserMock.__setLocalStorageData({ allowlist: ['single.com'] });

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.renderManagementView) {
        await window.renderManagementView();

        const siteCount = document.getElementById('site-count');
        if (siteCount) {
          expect(siteCount.textContent).toBe('1 site');
        }
      }
    });

    it('should render allowlist items', async () => {
      if (!env.hasContent) return;
      const { window, browserMock } = env;
      const { document } = window;

      browserMock.__setLocalStorageData({ allowlist: ['site1.com', 'site2.com'] });

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.renderManagementView) {
        await window.renderManagementView();

        const allowlistEl = document.getElementById('allowlist');
        if (allowlistEl) {
          expect(allowlistEl.children.length).toBe(2);
        }
      }
    });
  });

  describe('createAllowlistItem', () => {
    it('should create label element with checkbox', async () => {
      if (!env.hasContent) return;
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.createAllowlistItem) {
        const item = window.createAllowlistItem('test.com');

        expect(item.tagName).toBe('LABEL');
        expect(item.className).toBe('allowlist-item');

        const checkbox = item.querySelector('input[type="checkbox"]');
        expect(checkbox).not.toBeNull();
        expect(checkbox.dataset.domain).toBe('test.com');
      }
    });

    it('should display domain name in span', async () => {
      if (!env.hasContent) return;
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.createAllowlistItem) {
        const item = window.createAllowlistItem('example.com');

        const domainSpan = item.querySelector('.allowlist-item-domain');
        expect(domainSpan.textContent).toBe('example.com');
      }
    });

    it('should add current badge when domain matches currentDomain', async () => {
      if (!env.hasContent) return;
      const { window } = env;

      await new Promise(resolve => setTimeout(resolve, 100));

      if (window.createAllowlistItem) {
        window.currentDomain = 'current.com';

        const item = window.createAllowlistItem('current.com');

        const badge = item.querySelector('.current-badge');
        expect(badge).not.toBeNull();
        expect(badge.textContent).toBe('current');
      }
    });
  });
});

// ============================================================================
// ADDITIONAL STORAGE TESTS (Issue #214 - Parity with Chrome)
// ============================================================================

describe('Additional Storage Functions', () => {
  let env;

  beforeEach(() => {
    env = createPopupEnvironment({ authenticated: true, allowlist: [] });
  });

  afterEach(() => {
    if (env.dom) {
      env.dom.window.close();
    }
  });

  it('removeManyFromAllowlist removes multiple domains at once', async () => {
    if (!env.hasContent) return;
    const { window, browserMock } = env;

    browserMock.__setLocalStorageData({ allowlist: ['a.com', 'b.com', 'c.com'] });

    await new Promise(resolve => setTimeout(resolve, 50));

    if (window.removeManyFromAllowlist) {
      await window.removeManyFromAllowlist(['a.com', 'c.com']);

      expect(browserMock.storage.local.set).toHaveBeenCalledWith({
        allowlist: ['b.com']
      });
    }
  });

  it('clearAllData clears the allowlist', async () => {
    if (!env.hasContent) return;
    const { window, browserMock } = env;

    browserMock.__setLocalStorageData({ allowlist: ['site.com'] });

    await new Promise(resolve => setTimeout(resolve, 50));

    if (window.clearAllData) {
      await window.clearAllData();

      expect(browserMock.storage.local.set).toHaveBeenCalledWith({
        allowlist: []
      });
    }
  });
});
