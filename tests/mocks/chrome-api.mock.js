/**
 * Chrome Extension API Mock
 *
 * Provides mock implementations of Chrome APIs used by popup.js:
 * - chrome.tabs.query()
 * - chrome.storage.local.get() / set()
 * - chrome.runtime.sendMessage()
 * - chrome.runtime.id
 *
 * Per ADR 0215: These mocks enable unit testing without Chrome runtime.
 */

import { vi } from 'vitest';

/**
 * Creates a fresh Chrome API mock instance.
 * Call chrome.__resetStorage() to clear storage state between tests.
 *
 * @returns {object} Mock chrome object
 */
export function createChromeMock() {
  // Internal storage state
  let storageData = {};

  // Internal tab state for mocking
  let mockTabs = [];

  // Message handler responses
  let messageResponses = {};

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
        addListener: vi.fn(),
        removeListener: vi.fn()
      },
      lastError: null
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
              url: 'https://example.com/page',
              active: true,
              currentWindow: true
            }]);
          }
        });
      })
    },

    // Storage API
    storage: {
      local: {
        get: vi.fn().mockImplementation((keys) => {
          return new Promise((resolve) => {
            if (typeof keys === 'string') {
              resolve({ [keys]: storageData[keys] });
            } else if (Array.isArray(keys)) {
              const result = {};
              keys.forEach(key => {
                result[key] = storageData[key];
              });
              resolve(result);
            } else {
              resolve({ ...storageData });
            }
          });
        }),
        set: vi.fn().mockImplementation((items) => {
          return new Promise((resolve) => {
            Object.assign(storageData, items);
            resolve();
          });
        }),
        remove: vi.fn().mockImplementation((keys) => {
          return new Promise((resolve) => {
            const keyArray = Array.isArray(keys) ? keys : [keys];
            keyArray.forEach(key => {
              delete storageData[key];
            });
            resolve();
          });
        }),
        clear: vi.fn().mockImplementation(() => {
          return new Promise((resolve) => {
            storageData = {};
            resolve();
          });
        })
      },
      session: {
        get: vi.fn().mockResolvedValue({}),
        set: vi.fn().mockResolvedValue(undefined)
      }
    },

    // Test utilities (not part of Chrome API)
    __resetStorage: () => {
      storageData = {};
    },

    __setStorageData: (data) => {
      storageData = { ...data };
    },

    __getStorageData: () => {
      return { ...storageData };
    },

    __setMockTabs: (tabs) => {
      mockTabs = tabs;
    },

    __setMessageResponse: (type, response) => {
      messageResponses[type] = response;
    },

    __reset: () => {
      storageData = {};
      mockTabs = [];
      messageResponses = {};
      vi.clearAllMocks();
    }
  };

  return chromeMock;
}

export default createChromeMock;
