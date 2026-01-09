/**
 * AletheiaAuth Mock
 *
 * Provides mock implementation of window.AletheiaAuth used by popup.js:
 * - isAuthenticated()
 * - initiateLogin()
 * - logout()
 * - getAuthState()
 *
 * Per ADR 0215: These mocks enable unit testing auth flows.
 */

import { vi } from 'vitest';

/**
 * Creates a fresh AletheiaAuth mock instance.
 *
 * @returns {object} Mock AletheiaAuth object
 */
export function createAletheiaAuthMock() {
  // Internal auth state
  let isAuthed = false;
  let authState = null;

  // Mock user for successful login
  const mockUser = {
    name: 'Test User',
    displayName: 'Test User',
    email: 'test@example.com',
    id: 'user-123'
  };

  // Whether login should succeed or fail
  let loginShouldSucceed = true;
  let loginError = new Error('Login failed');

  const authMock = {
    isAuthenticated: vi.fn().mockImplementation(() => {
      return Promise.resolve(isAuthed);
    }),

    initiateLogin: vi.fn().mockImplementation(() => {
      return new Promise((resolve, reject) => {
        if (loginShouldSucceed) {
          isAuthed = true;
          authState = mockUser;
          resolve(mockUser);
        } else {
          reject(loginError);
        }
      });
    }),

    logout: vi.fn().mockImplementation(() => {
      return new Promise((resolve) => {
        isAuthed = false;
        authState = null;
        resolve();
      });
    }),

    getAuthState: vi.fn().mockImplementation(() => {
      return Promise.resolve(authState);
    }),

    // Test utilities (not part of real API)
    __setAuthenticated: (authed, state = null) => {
      isAuthed = authed;
      authState = state || (authed ? mockUser : null);
    },

    __setLoginBehavior: (shouldSucceed, error = null) => {
      loginShouldSucceed = shouldSucceed;
      if (error) {
        loginError = error;
      }
    },

    __getMockUser: () => {
      return { ...mockUser };
    },

    __reset: () => {
      isAuthed = false;
      authState = null;
      loginShouldSucceed = true;
      loginError = new Error('Login failed');
      vi.clearAllMocks();
    }
  };

  return authMock;
}

export default createAletheiaAuthMock;
