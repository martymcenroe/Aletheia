/**
 * Session persistence and silent renewal.
 *
 * Issue #812 - the JWT lived only in session storage, so a browser restart
 *              destroyed it while identity fields persisted forever.
 * Issue #813 - the popup reported "signed in" from userId alone, contradicting
 *              every failing request.
 * Issue #814 - the request path sent knowingly-unauthenticated requests and
 *              treated the resulting 401 as terminal.
 *
 * Together those produced the field report this suite exists to prevent: the
 * popup showing an active session while every analysis returned
 * "Sign In Required", recoverable only by a manual logout and re-login.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';
import { createChromeMock } from '../../mocks/chrome-api.mock.js';

const authJsSource = fs.readFileSync(
  path.resolve(__dirname, '../../../extensions/chrome/auth.js'),
  'utf-8'
);

function loadAuth(chromeMock) {
  global.chrome = chromeMock;
  global.window = {};
  // crypto is a getter-only global in this environment; stubGlobal handles it.
  vi.stubGlobal('crypto', { getRandomValues: (a) => a });
  vi.spyOn(console, 'log').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});
  eval(authJsSource);
  return global.window.AletheiaAuth;
}

describe('Session persistence and silent renewal', () => {
  let chromeMock;

  beforeEach(() => {
    chromeMock = createChromeMock({ authenticated: true });
  });

  afterEach(() => {
    delete global.chrome;
    delete global.window;
    delete global.fetch;
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  // ---------------------------------------------------------------- #812 ---

  it('persists the refresh token to LOCAL storage, not session storage', async () => {
    const auth = loadAuth(chromeMock);
    global.fetch = vi.fn();

    await auth.clearTokens();
    chromeMock.storage.local.set.mockClear?.();

    // Simulate a fresh login writing its credentials.
    const local = chromeMock.__getLocalStorageData();
    expect(local.aletheiaRefreshToken).toBeUndefined();

    chromeMock.__setLocalStorageData({
      userId: 'u1',
      displayName: 'Test User',
      aletheiaRefreshToken: 'persisted-token'
    });

    // Session storage is what a browser restart destroys. Emptying it must NOT
    // cost the user their session.
    chromeMock.__setSessionStorageData({});

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ jwt: 'renewed-after-restart', expiresIn: 86400 })
    });

    const jwt = await auth.getValidJwt();
    expect(jwt).toBe('renewed-after-restart');
  });

  it('survives a simulated browser restart with no user interaction', async () => {
    const auth = loadAuth(chromeMock);

    // A restart clears session storage and leaves local storage intact.
    chromeMock.__setSessionStorageData({});

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ jwt: 'post-restart-jwt', expiresIn: 86400 })
    });

    expect(await auth.isAuthenticated()).toBe(true);
    expect(await auth.getValidJwt()).toBe('post-restart-jwt');
  });

  // ---------------------------------------------------------------- #813 ---

  it('does NOT report a session when identity remains but renewal is impossible', async () => {
    const auth = loadAuth(chromeMock);

    // Exactly the field-reported state: name remembered, credential gone.
    chromeMock.__setLocalStorageData({
      userId: 'u1',
      displayName: 'Martin McEnroe, P.E.'
    });
    chromeMock.__setSessionStorageData({});

    expect(await auth.getAuthState()).toBeNull();
    expect(await auth.isAuthenticated()).toBe(false);
    expect(await auth.isSessionUnrecoverable()).toBe(true);
  });

  it('reports a session when identity AND a refresh token are present', async () => {
    const auth = loadAuth(chromeMock);

    const state = await auth.getAuthState();
    expect(state).not.toBeNull();
    expect(state.displayName).toBe('Test User');
    expect(await auth.isSessionUnrecoverable()).toBe(false);
  });

  // ---------------------------------------------------------------- #814 ---

  it('issues ONE renewal when several callers race on a cold start', async () => {
    const auth = loadAuth(chromeMock);
    chromeMock.__setSessionStorageData({});

    // Build the deferred up-front: getValidJwt awaits storage before it ever
    // reaches fetch, so capturing the resolver inside the mock would race.
    let resolveFetch;
    const pending = new Promise((r) => { resolveFetch = r; });
    global.fetch = vi.fn(() => pending);

    const calls = [auth.getValidJwt(), auth.getValidJwt(), auth.getValidJwt()];

    // Let all three reach the renewal before any response lands.
    await new Promise((r) => setTimeout(r, 10));

    resolveFetch({
      ok: true,
      json: () => Promise.resolve({ jwt: 'shared-jwt', expiresIn: 86400 })
    });
    const results = await Promise.all(calls);

    // Three callers, one network round-trip.
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(results).toEqual(['shared-jwt', 'shared-jwt', 'shared-jwt']);
  });

  it('drops the refresh token on 401 so a revoked session stops retrying', async () => {
    const auth = loadAuth(chromeMock);
    chromeMock.__setSessionStorageData({});

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ error: 'Unauthorized' })
    });

    expect(await auth.getValidJwt()).toBeNull();
    expect(chromeMock.__getLocalStorageData().aletheiaRefreshToken).toBeUndefined();
  });

  it('KEEPS the refresh token on a transient failure', async () => {
    const auth = loadAuth(chromeMock);
    chromeMock.__setSessionStorageData({});

    // A 5xx or an offline browser must not cost the user their session —
    // discarding the token here would force a re-login over a blip.
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: () => Promise.resolve({ error: 'Service Unavailable' })
    });

    expect(await auth.getValidJwt()).toBeNull();
    expect(chromeMock.__getLocalStorageData().aletheiaRefreshToken)
      .toBe('mock-aletheia-refresh-token');
  });

  it('KEEPS the refresh token when the network throws', async () => {
    const auth = loadAuth(chromeMock);
    chromeMock.__setSessionStorageData({});

    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    expect(await auth.getValidJwt()).toBeNull();
    expect(chromeMock.__getLocalStorageData().aletheiaRefreshToken)
      .toBe('mock-aletheia-refresh-token');
  });

  it('sends the Aletheia refresh token, never LinkedIn\'s', async () => {
    const auth = loadAuth(chromeMock);
    chromeMock.__setSessionStorageData({});

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ jwt: 'j', expiresIn: 86400 })
    });

    await auth.getValidJwt();

    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.aletheiaRefreshToken).toBe('mock-aletheia-refresh-token');
    // LinkedIn cannot refresh these scopes; sending its token would 401.
    expect(body.refreshToken).toBeUndefined();
  });

  it('logout clears the refresh token so the session cannot resurrect', async () => {
    const auth = loadAuth(chromeMock);

    await auth.clearTokens();

    const local = chromeMock.__getLocalStorageData();
    expect(local.aletheiaRefreshToken).toBeUndefined();
    expect(local.userId).toBeUndefined();
    expect(await auth.isAuthenticated()).toBe(false);
  });
});
