/**
 * Vitest Setup File
 *
 * Runs before all tests to set up the global environment.
 * Per ADR 0215: Tests require proper mocking of Chrome APIs.
 */

import { vi } from 'vitest';
import { createChromeMock } from './mocks/chrome-api.mock.js';
import { createAletheiaAuthMock } from './mocks/aletheia-auth.mock.js';

// Set up global Chrome API mock
globalThis.chrome = createChromeMock();

// Set up global AletheiaAuth mock
globalThis.AletheiaAuth = createAletheiaAuthMock();

// Attach to window for popup.js compatibility
if (typeof window !== 'undefined') {
  window.AletheiaAuth = globalThis.AletheiaAuth;
}

// Reset mocks between tests
beforeEach(() => {
  vi.clearAllMocks();

  // Reset Chrome storage state
  globalThis.chrome.__resetStorage();

  // Reset auth state
  globalThis.AletheiaAuth.__reset();
});
