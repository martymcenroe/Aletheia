/**
 * Firefox Extension API Mock
 *
 * Provides mock implementations of Firefox APIs used by popup.js, auth.js, and service-worker.js:
 * - browser.tabs.query()
 * - browser.tabs.onRemoved
 * - browser.storage.local.get() / set() / remove()
 * - browser.storage.session.get() / set() / remove()
 * - browser.identity.launchWebAuthFlow()
 * - browser.identity.getRedirectURL()
 * - browser.runtime.sendMessage()
 * - browser.runtime.onMessage
 * - browser.runtime.onInstalled
 * - browser.runtime.id
 * - browser.contextMenus.create() / onClicked
 * - browser.scripting.executeScript()
 * - browser.action.setBadgeText() / setBadgeBackgroundColor()
 *
 * Per ADR 0215 & LLD 1206: These mocks enable unit testing without Firefox runtime.
 *
 * CRITICAL: This mock uses `browser.*` namespace, NOT `chrome.*`.
 * Tests MUST verify the correct namespace is called.
 */

import { vi } from 'vitest';

/**
 * Creates a fresh Firefox API mock instance.
 * Call browser.__reset() to clear all state between tests.
 *
 * @param {object} options - Configuration options
 * @param {string[]} options.allowlist - Initial allowlist domains
 * @param {string} options.tabUrl - URL for mock active tab
 * @param {boolean} options.authenticated - Whether to start authenticated
 * @returns {object} Mock browser object
 */
export function createFirefoxMock(options = {}) {
  const {
    allowlist = [],
    tabUrl = 'https://example.com',
    authenticated = false
  } = options;

  // Internal storage state (local)
  let localStorageData = {
    allowlist: [...allowlist],
    ...(authenticated ? {
      refreshToken: 'mock-refresh-token-67890',
      userId: 'mock-sub-782bbtaQ',
      displayName: 'Test User'
    } : {})
  };

  // Internal storage state (session - MV3)
  let sessionStorageData = authenticated ? {
    accessToken: 'mock-access-token-12345',
    expiresAt: Date.now() + 3600000,
    oauth_state: null
  } : {};

  // Internal tab state
  let mockTabs = [];

  // Message handler responses
  let messageResponses = {};

  // Service worker event listeners (for testing)
  const messageListeners = [];
  const installHandlers = [];
  const contextMenuClickHandlers = [];
  const tabRemovedHandlers = [];

  // Badge state per tab
  const badgeState = new Map();

  // Script injection results (configurable per test)
  let scriptInjectionResults = [{ result: {} }];

  // OAuth flow configuration
  let oauthConfig = {
    shouldSucceed: true,
    mockCode: 'mock-auth-code-abc123',
    // State returned in callback - defaults to matching stored state
    returnedState: null
  };

  const browserMock = {
    // Runtime API
    runtime: {
      id: 'extension@aletheia.study',
      sendMessage: vi.fn().mockImplementation((message) => {
        return new Promise((resolve) => {
          const response = messageResponses[message.type] || { state: 'unknown' };
          resolve(response);
        });
      }),
      onMessage: {
        addListener: vi.fn().mockImplementation((listener) => {
          messageListeners.push(listener);
        }),
        removeListener: vi.fn()
      },
      onInstalled: {
        addListener: vi.fn().mockImplementation((handler) => {
          installHandlers.push(handler);
        })
      },
      lastError: null
    },

    // Identity API (OAuth support)
    identity: {
      launchWebAuthFlow: vi.fn().mockImplementation(({ url, interactive: _interactive }) => {
        return new Promise((resolve, reject) => {
          if (!oauthConfig.shouldSucceed) {
            reject(new Error('OAuth flow cancelled by user'));
            return;
          }

          // Extract state from the auth URL for CSRF validation
          const authUrl = new URL(url);
          const stateParam = authUrl.searchParams.get('state');

          // Use configured returnedState or echo back the sent state (valid flow)
          const returnState = oauthConfig.returnedState !== null
            ? oauthConfig.returnedState
            : stateParam;

          // Return mock redirect URL with code and state
          const redirectUrl = `https://mock-extension-id.extensions.allizom.org/?code=${oauthConfig.mockCode}&state=${returnState}`;
          resolve(redirectUrl);
        });
      }),
      getRedirectURL: vi.fn().mockReturnValue('https://mock-extension-id.extensions.allizom.org/')
    },

    // Tabs API
    tabs: {
      query: vi.fn().mockImplementation((queryInfo) => {
        return new Promise((resolve) => {
          if (mockTabs.length > 0) {
            let results = mockTabs;
            if (queryInfo.active !== undefined) {
              results = results.filter(t => t.active === queryInfo.active);
            }
            if (queryInfo.currentWindow !== undefined) {
              results = results.filter(t => t.currentWindow === queryInfo.currentWindow);
            }
            resolve(results);
          } else {
            resolve([{
              id: 1,
              url: tabUrl,
              active: true,
              currentWindow: true
            }]);
          }
        });
      }),
      onRemoved: {
        addListener: vi.fn().mockImplementation((handler) => {
          tabRemovedHandlers.push(handler);
        })
      }
    },

    // Context Menus API
    contextMenus: {
      create: vi.fn().mockImplementation(() => {
        // Firefox contextMenus.create returns undefined (not a promise)
      }),
      onClicked: {
        addListener: vi.fn().mockImplementation((handler) => {
          contextMenuClickHandlers.push(handler);
        })
      }
    },

    // Scripting API (MV3)
    scripting: {
      executeScript: vi.fn().mockImplementation(() => {
        return Promise.resolve(scriptInjectionResults);
      })
    },

    // Action API (browser action / toolbar icon)
    action: {
      setBadgeText: vi.fn().mockImplementation(({ tabId, text }) => {
        const state = badgeState.get(tabId) || {};
        state.text = text;
        badgeState.set(tabId, state);
        return Promise.resolve();
      }),
      setBadgeBackgroundColor: vi.fn().mockImplementation(({ tabId, color }) => {
        const state = badgeState.get(tabId) || {};
        state.color = color;
        badgeState.set(tabId, state);
        return Promise.resolve();
      })
    },

    // Storage API
    storage: {
      // Local storage (persists)
      local: {
        get: vi.fn().mockImplementation((keys) => {
          return new Promise((resolve) => {
            if (typeof keys === 'string') {
              resolve({ [keys]: localStorageData[keys] });
            } else if (Array.isArray(keys)) {
              const result = {};
              keys.forEach(key => {
                result[key] = localStorageData[key];
              });
              resolve(result);
            } else {
              resolve({ ...localStorageData });
            }
          });
        }),
        set: vi.fn().mockImplementation((items) => {
          return new Promise((resolve) => {
            Object.assign(localStorageData, items);
            resolve();
          });
        }),
        remove: vi.fn().mockImplementation((keys) => {
          return new Promise((resolve) => {
            const keyArray = Array.isArray(keys) ? keys : [keys];
            keyArray.forEach(key => {
              delete localStorageData[key];
            });
            resolve();
          });
        }),
        clear: vi.fn().mockImplementation(() => {
          return new Promise((resolve) => {
            localStorageData = { allowlist: [] };
            resolve();
          });
        })
      },

      // Session storage (cleared on browser close - MV3 only)
      session: {
        get: vi.fn().mockImplementation((keys) => {
          return new Promise((resolve) => {
            if (typeof keys === 'string') {
              resolve({ [keys]: sessionStorageData[keys] });
            } else if (Array.isArray(keys)) {
              const result = {};
              keys.forEach(key => {
                result[key] = sessionStorageData[key];
              });
              resolve(result);
            } else {
              resolve({ ...sessionStorageData });
            }
          });
        }),
        set: vi.fn().mockImplementation((items) => {
          return new Promise((resolve) => {
            Object.assign(sessionStorageData, items);
            resolve();
          });
        }),
        remove: vi.fn().mockImplementation((keys) => {
          return new Promise((resolve) => {
            const keyArray = Array.isArray(keys) ? keys : [keys];
            keyArray.forEach(key => {
              delete sessionStorageData[key];
            });
            resolve();
          });
        }),
        clear: vi.fn().mockImplementation(() => {
          return new Promise((resolve) => {
            sessionStorageData = {};
            resolve();
          });
        })
      }
    },

    // =========================================================================
    // Test utilities (not part of Firefox API)
    // =========================================================================

    /** Reset local storage to initial state */
    __resetLocalStorage: () => {
      localStorageData = { allowlist: [] };
    },

    /** Reset session storage to initial state */
    __resetSessionStorage: () => {
      sessionStorageData = {};
    },

    /** Set local storage data directly */
    __setLocalStorageData: (data) => {
      localStorageData = { ...data };
    },

    /** Set session storage data directly */
    __setSessionStorageData: (data) => {
      sessionStorageData = { ...data };
    },

    /** Get current local storage data */
    __getLocalStorageData: () => {
      return { ...localStorageData };
    },

    /** Get current session storage data */
    __getSessionStorageData: () => {
      return { ...sessionStorageData };
    },

    /** Set mock tabs for tabs.query() */
    __setMockTabs: (tabs) => {
      mockTabs = tabs;
    },

    /** Set response for runtime.sendMessage() by message type */
    __setMessageResponse: (type, response) => {
      messageResponses[type] = response;
    },

    /** Configure OAuth flow behavior */
    __setOAuthConfig: (config) => {
      Object.assign(oauthConfig, config);
    },

    /**
     * Set a mismatched state for CSRF testing.
     * Call with null to reset to valid (echoed) state.
     */
    __setOAuthReturnedState: (state) => {
      oauthConfig.returnedState = state;
    },

    /** Make OAuth flow fail */
    __setOAuthShouldFail: (shouldFail) => {
      oauthConfig.shouldSucceed = !shouldFail;
    },

    // =========================================================================
    // Service Worker Test Utilities
    // =========================================================================

    /**
     * Simulate a message to registered onMessage listeners.
     * Returns the response from the first listener that calls sendResponse.
     */
    __simulateMessage: async (message, sender = { id: 'extension@aletheia.study' }) => {
      let response = undefined;
      let _asyncResponse = false;

      for (const listener of messageListeners) {
        const sendResponse = vi.fn((resp) => {
          response = resp;
        });

        const result = listener(message, sender, sendResponse);

        // If listener returns true, it will respond asynchronously
        if (result === true) {
          _asyncResponse = true;
          // Wait for async response
          await new Promise(resolve => setTimeout(resolve, 50));
          if (sendResponse.mock.calls.length > 0) {
            response = sendResponse.mock.calls[0][0];
          }
        } else if (sendResponse.mock.calls.length > 0) {
          // Synchronous response
          response = sendResponse.mock.calls[0][0];
        }

        if (response !== undefined) break;
      }

      return response;
    },

    /** Trigger onInstalled handlers */
    __triggerOnInstalled: (details = { reason: 'install' }) => {
      for (const handler of installHandlers) {
        handler(details);
      }
    },

    /** Trigger context menu click handlers */
    __triggerContextMenuClick: (info, tab) => {
      for (const handler of contextMenuClickHandlers) {
        handler(info, tab);
      }
    },

    /** Trigger tab removed handlers */
    __triggerTabRemoved: (tabId, removeInfo = {}) => {
      for (const handler of tabRemovedHandlers) {
        handler(tabId, removeInfo);
      }
    },

    /** Get badge state for a tab */
    __getBadgeState: (tabId) => {
      return badgeState.get(tabId) || { text: '', color: '' };
    },

    /** Set script injection results for scripting.executeScript */
    __setScriptInjectionResults: (results) => {
      scriptInjectionResults = results;
    },

    /** Full reset - clears all state and mocks */
    __reset: () => {
      localStorageData = { allowlist: [] };
      sessionStorageData = {};
      mockTabs = [];
      messageResponses = {};
      messageListeners.length = 0;
      installHandlers.length = 0;
      contextMenuClickHandlers.length = 0;
      tabRemovedHandlers.length = 0;
      badgeState.clear();
      scriptInjectionResults = [{ result: {} }];
      oauthConfig = {
        shouldSucceed: true,
        mockCode: 'mock-auth-code-abc123',
        returnedState: null
      };
      vi.clearAllMocks();
    }
  };

  return browserMock;
}

export default createFirefoxMock;
