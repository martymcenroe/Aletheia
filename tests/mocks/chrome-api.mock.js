/**
 * Chrome Extension API Mock
 *
 * Provides mock implementations of Chrome APIs used by popup.js, auth.js, and service-worker.js:
 * - chrome.tabs.query() / onRemoved
 * - chrome.storage.local.get() / set() / remove()
 * - chrome.storage.session.get() / set() / remove()
 * - chrome.identity.launchWebAuthFlow()
 * - chrome.identity.getRedirectURL()
 * - chrome.runtime.sendMessage()
 * - chrome.runtime.onMessage.addListener()
 * - chrome.runtime.onInstalled.addListener()
 * - chrome.runtime.id
 * - chrome.contextMenus.create() / onClicked.addListener()
 * - chrome.scripting.executeScript()
 * - chrome.action.setBadgeText() / setBadgeBackgroundColor()
 *
 * Per ADR 0215: These mocks enable unit testing without Chrome runtime.
 */

import { vi } from 'vitest';

/**
 * Creates a fresh Chrome API mock instance.
 * Call chrome.__reset() to clear all state between tests.
 *
 * @param {object} options - Configuration options
 * @param {string[]} options.allowlist - Initial allowlist domains
 * @param {string} options.tabUrl - URL for mock active tab
 * @param {boolean} options.authenticated - Whether to start authenticated
 * @returns {object} Mock chrome object
 */
export function createChromeMock(options = {}) {
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

  // Internal tab state for mocking
  let mockTabs = [];

  // Message handler responses
  let messageResponses = {};

  // OAuth flow configuration
  let oauthConfig = {
    shouldSucceed: true,
    mockCode: 'mock-auth-code-abc123',
    // State returned in callback - defaults to matching stored state
    returnedState: null
  };

  // Message listeners registered via onMessage.addListener
  let messageListeners = [];

  // Context menu click handlers
  let contextMenuClickHandlers = [];

  // Install handlers
  let installHandlers = [];

  // Tab removed handlers
  let tabRemovedHandlers = [];

  // Badge state per tab
  let badgeState = {};

  // Script injection results
  let scriptInjectionResults = [{ result: null }];

  const chromeMock = {
    // Runtime API
    runtime: {
      id: 'mock-extension-id-12345',
      sendMessage: vi.fn().mockImplementation((message) => {
        return new Promise((resolve) => {
          const response = messageResponses[message.type] || { state: 'unknown' };
          resolve(response);
        });
      }),
      onMessage: {
        addListener: vi.fn().mockImplementation((handler) => {
          messageListeners.push(handler);
        }),
        removeListener: vi.fn().mockImplementation((handler) => {
          const idx = messageListeners.indexOf(handler);
          if (idx > -1) messageListeners.splice(idx, 1);
        })
      },
      onInstalled: {
        addListener: vi.fn().mockImplementation((handler) => {
          installHandlers.push(handler);
        })
      },
      lastError: null
    },

    // Identity API (OAuth support - Chrome MV3)
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
          const redirectUri = chromeMock.identity.getRedirectURL();
          const redirectUrl = `${redirectUri}?code=${oauthConfig.mockCode}&state=${returnState}`;
          resolve(redirectUrl);
        });
      }),
      getRedirectURL: vi.fn().mockReturnValue('https://mock-extension-id-12345.chromiumapp.org/')
    },

    // Tabs API
    tabs: {
      query: vi.fn().mockImplementation((queryInfo) => {
        return new Promise((resolve) => {
          if (mockTabs.length > 0) {
            // Filter by active/currentWindow if specified
            let results = mockTabs;
            if (queryInfo.active !== undefined) {
              results = results.filter(t => t.active === queryInfo.active);
            }
            if (queryInfo.currentWindow !== undefined) {
              results = results.filter(t => t.currentWindow === queryInfo.currentWindow);
            }
            resolve(results);
          } else {
            // Default: return mock active tab
            resolve([{
              id: 1,
              url: tabUrl,
              title: 'Mock Page Title',
              active: true,
              currentWindow: true
            }]);
          }
        });
      }),
      onRemoved: {
        addListener: vi.fn().mockImplementation((handler) => {
          tabRemovedHandlers.push(handler);
        }),
        removeListener: vi.fn()
      }
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

    // Context Menus API (Service Worker)
    contextMenus: {
      create: vi.fn().mockImplementation((props) => {
        return props.id;
      }),
      onClicked: {
        addListener: vi.fn().mockImplementation((handler) => {
          contextMenuClickHandlers.push(handler);
        }),
        removeListener: vi.fn()
      }
    },

    // Scripting API (MV3)
    scripting: {
      executeScript: vi.fn().mockImplementation(() => {
        return Promise.resolve(scriptInjectionResults);
      })
    },

    // Action API (MV3 toolbar badge)
    action: {
      setBadgeText: vi.fn().mockImplementation(({ tabId, text }) => {
        if (!badgeState[tabId]) badgeState[tabId] = {};
        badgeState[tabId].text = text;
        return Promise.resolve();
      }),
      setBadgeBackgroundColor: vi.fn().mockImplementation(({ tabId, color }) => {
        if (!badgeState[tabId]) badgeState[tabId] = {};
        badgeState[tabId].color = color;
        return Promise.resolve();
      })
    },

    // =========================================================================
    // Test utilities (not part of Chrome API)
    // =========================================================================

    /** Reset local storage to initial state */
    __resetLocalStorage: () => {
      localStorageData = { allowlist: [] };
    },

    /** Reset session storage to initial state */
    __resetSessionStorage: () => {
      sessionStorageData = {};
    },

    /** Legacy alias for backward compatibility */
    __resetStorage: () => {
      localStorageData = { allowlist: [] };
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

    /** Legacy alias for backward compatibility */
    __setStorageData: (data) => {
      localStorageData = { ...data };
    },

    /** Legacy alias for backward compatibility */
    __getStorageData: () => {
      return { ...localStorageData };
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

    /**
     * Simulate a message being received by all registered listeners.
     * Returns the response from the first listener that calls sendResponse.
     */
    __simulateMessage: async (message, sender = { id: 'mock-extension-id-12345' }) => {
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
        }
      }

      return response;
    },

    /**
     * Trigger onInstalled handlers (simulates extension installation)
     */
    __triggerOnInstalled: (details = { reason: 'install' }) => {
      installHandlers.forEach(handler => handler(details));
    },

    /**
     * Trigger context menu click (simulates user selecting context menu)
     */
    __triggerContextMenuClick: (info, tab) => {
      contextMenuClickHandlers.forEach(handler => handler(info, tab));
    },

    /**
     * Trigger tab removed event
     */
    __triggerTabRemoved: (tabId, removeInfo = {}) => {
      tabRemovedHandlers.forEach(handler => handler(tabId, removeInfo));
    },

    /** Get badge state for a tab */
    __getBadgeState: (tabId) => {
      return badgeState[tabId] || {};
    },

    /** Set script injection results */
    __setScriptInjectionResults: (results) => {
      scriptInjectionResults = results;
    },

    /** Get all registered message listeners */
    __getMessageListeners: () => [...messageListeners],

    /** Full reset - clears all state and mocks */
    __reset: () => {
      localStorageData = { allowlist: [] };
      sessionStorageData = {};
      mockTabs = [];
      messageResponses = {};
      oauthConfig = {
        shouldSucceed: true,
        mockCode: 'mock-auth-code-abc123',
        returnedState: null
      };
      messageListeners = [];
      contextMenuClickHandlers = [];
      installHandlers = [];
      tabRemovedHandlers = [];
      badgeState = {};
      scriptInjectionResults = [{ result: null }];
      vi.clearAllMocks();
    }
  };

  return chromeMock;
}

export default createChromeMock;
