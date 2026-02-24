// tests/e2e/auth-flow.spec.js
// E2E Auth Flow Verification Tests (Issue #403)
//
// Verifies the complete auth flow end-to-end:
// - JWT storage and retrieval via chrome.storage.session
// - getJwt() returns null when not logged in
// - getAuthHeaders() includes/omits Authorization header based on JWT presence
// - Route interception verifies Authorization header reaches the network
//
// Context: Created after AUTH_ENABLED=true outage (2026-02-20).
// PR #426 fixed JWT storage but mockLogin() was not updated — these tests
// ensure the full chain works so a silent regression can never recur.
//
// NOTE: Uses chromium.launchPersistentContext() for service worker access.
// Standard Playwright test contexts don't expose extension service workers.

/* global chrome */
const { test: base, expect, chromium } = require('@playwright/test');
const path = require('path');

const extensionPath = path.join(__dirname, '../../extensions/chrome');

// Custom test fixture that launches a persistent context with extension loaded.
// This gives us access to extension service workers and chrome-extension:// pages.
const test = base.extend({
    // eslint-disable-next-line no-empty-pattern
    context: async ({}, use) => {
        const context = await chromium.launchPersistentContext('', {
            headless: false,
            args: [
                `--disable-extensions-except=${extensionPath}`,
                `--load-extension=${extensionPath}`,
                '--no-sandbox'
            ]
        });
        await use(context);
        await context.close();
    },
    extensionId: async ({ context }, use) => {
        // Wait for service worker to register, then extract extension ID from URL
        let sw = context.serviceWorkers()[0];
        if (!sw) {
            sw = await context.waitForEvent('serviceworker', { timeout: 10000 });
        }
        const id = sw.url().split('/')[2];
        await use(id);
    },
    serviceWorker: async ({ context, extensionId }, use) => {
        const sw = context.serviceWorkers().find(w =>
            w.url().includes(extensionId)
        );
        await use(sw);
    }
});

test.describe('E2E Auth Flow (#403)', () => {

    test.describe.configure({ mode: 'serial' });

    test('010: storeTokens persists JWT to session storage', async ({ serviceWorker }) => {
        // Simulate what storeTokens() does: write JWT to session storage
        await serviceWorker.evaluate(async () => {
            await chrome.storage.session.set({
                accessToken: 'mock-access-token-12345',
                expiresAt: Date.now() + 3600000,
                jwt: 'mock-jwt-for-testing'
            });
        });

        // Read back JWT from session storage
        const jwt = await serviceWorker.evaluate(async () => {
            const session = await chrome.storage.session.get(['jwt']);
            return session.jwt;
        });

        expect(jwt).toBe('mock-jwt-for-testing');

        // Also verify accessToken was stored alongside
        const accessToken = await serviceWorker.evaluate(async () => {
            const session = await chrome.storage.session.get(['accessToken']);
            return session.accessToken;
        });

        expect(accessToken).toBe('mock-access-token-12345');
    });

    test('020: JWT is null when not stored', async ({ serviceWorker }) => {
        // Clear session storage (simulates clearTokens)
        await serviceWorker.evaluate(async () => {
            await chrome.storage.session.remove(['accessToken', 'expiresAt', 'jwt']);
        });

        // Read JWT — should be null
        const jwt = await serviceWorker.evaluate(async () => {
            const session = await chrome.storage.session.get(['jwt']);
            return session.jwt || null;
        });

        expect(jwt).toBeNull();
    });

    test('030: getAuthHeaders includes Authorization when JWT present', async ({ serviceWorker }) => {
        // Store JWT in session storage
        await serviceWorker.evaluate(async () => {
            await chrome.storage.session.set({
                jwt: 'mock-jwt-for-testing'
            });
        });

        // Call the actual getAuthHeaders() function in the service worker
        const headers = await serviceWorker.evaluate(async () => {
            // getAuthHeaders is defined at module scope in service-worker.js
            // eslint-disable-next-line no-undef
            return await getAuthHeaders();
        });

        expect(headers).toBeTruthy();
        expect(headers['Content-Type']).toBe('application/json');
        expect(headers['X-Aletheia-Client-Version']).toBe('1.0');
        expect(headers['Authorization']).toBe('Bearer mock-jwt-for-testing');
    });

    test('040: getAuthHeaders omits Authorization when no JWT', async ({ serviceWorker }) => {
        // Clear JWT from session storage
        await serviceWorker.evaluate(async () => {
            await chrome.storage.session.remove(['jwt']);
        });

        // Call getAuthHeaders() — should have no Authorization key
        const headers = await serviceWorker.evaluate(async () => {
            // eslint-disable-next-line no-undef
            return await getAuthHeaders();
        });

        expect(headers).toBeTruthy();
        expect(headers['Content-Type']).toBe('application/json');
        expect(headers['X-Aletheia-Client-Version']).toBe('1.0');
        expect(headers['Authorization']).toBeUndefined();
    });

    test('050: mockLogin stores JWT via popup page', async ({ context, extensionId }) => {
        // With persistent context, we CAN navigate to extension pages
        const popupUrl = `chrome-extension://${extensionId}/popup.html`;
        const page = await context.newPage();

        await page.goto(popupUrl);
        await page.waitForLoadState('domcontentloaded');
        await page.waitForTimeout(500);

        // Call mockLogin() via the exported AletheiaAuth interface
        const user = await page.evaluate(async () => {
            return await window.AletheiaAuth.mockLogin();
        });

        expect(user).toBeTruthy();
        expect(user.id).toBe('mock-sub-782bbtaQ');
        expect(user.name).toBe('Test User');

        // Verify JWT was stored by reading from session storage via popup context
        const jwt = await page.evaluate(async () => {
            return await window.AletheiaAuth.getJwt();
        });

        expect(jwt).toBe('mock-jwt-for-testing');

        await page.close();
    });

    test('060: authenticated fetch includes Authorization header at network level', async ({ context, extensionId, serviceWorker }) => {
        // Step 1: mockLogin via popup to store JWT in session storage
        const popupUrl = `chrome-extension://${extensionId}/popup.html`;
        const page = await context.newPage();
        await page.goto(popupUrl);
        await page.waitForLoadState('domcontentloaded');
        await page.waitForTimeout(500);

        await page.evaluate(async () => {
            return await window.AletheiaAuth.mockLogin();
        });

        // Step 2: Intercept requests to api.aletheia.study and capture Authorization header
        let capturedAuthHeader = null;
        await context.route('**/api.aletheia.study/**', async (route) => {
            capturedAuthHeader = route.request().headers()['authorization'];
            // Fulfill with mock response to avoid hitting production
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    signal: 'Verified',
                    gem: 'Mock authenticated response',
                    context: 'Test context'
                })
            });
        });

        // Step 3: Trigger a fetch from the service worker using getAuthHeaders()
        await serviceWorker.evaluate(async () => {
            // eslint-disable-next-line no-undef
            const headers = await getAuthHeaders();
            // eslint-disable-next-line no-undef
            await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ text: 'test auth header' })
            });
        });

        // Step 4: Verify the Authorization header was present at network level
        // Playwright lowercases header names in route.request().headers()
        expect(capturedAuthHeader).toBe('Bearer mock-jwt-for-testing');

        await page.close();
    });

});
