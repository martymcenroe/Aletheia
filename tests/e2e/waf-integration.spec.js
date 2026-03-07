// tests/e2e/waf-integration.spec.js
// API tests for header enforcement (#95, updated for CloudFlare Worker #349)
// Uses Playwright's request API (Node.js, no CORS issues)

const { test, expect } = require('@playwright/test');

// CloudFlare Worker URL (CloudFront deleted in #349)
const API_URL = 'https://api.aletheia.study/';

test.describe('Header Enforcement (#95, #349)', () => {

    // CloudFlare rate limit: 3 req/10s/IP — run serial with delay to avoid 429
    test.describe.configure({ mode: 'serial' });

    test('020: API returns 401 for unauthenticated request with valid header', async ({ request }) => {
        // AUTH_ENABLED=true — valid client header passes CloudFlare Worker
        // but Lambda requires JWT authentication
        const response = await request.post(API_URL, {
            headers: {
                'Content-Type': 'application/json',
                'X-Aletheia-Client-Version': '1.0'
            },
            data: {
                text: 'etymology',
                url: 'https://example.com',
                title: 'Test',
                context: 'Test context'
            }
        });

        expect(response.status()).toBe(401);
    });

    test('030: Worker blocks request without header', async ({ request }) => {
        const response = await request.post(API_URL, {
            headers: {
                'Content-Type': 'application/json'
                // Missing X-Aletheia-Client-Version
            },
            data: { text: 'test' }
        });

        expect(response.status()).toBe(403);
    });

    test('040: Worker blocks invalid version', async ({ request }) => {
        const response = await request.post(API_URL, {
            headers: {
                'Content-Type': 'application/json',
                'X-Aletheia-Client-Version': '0.9' // Invalid
            },
            data: { text: 'test' }
        });

        expect(response.status()).toBe(403);
    });

    test('050: Future version returns 401 (passes Worker, blocked by auth)', async ({ request }) => {
        // Wait for CloudFlare rate-limit window to reset (3 req/10s)
        await new Promise(r => setTimeout(r, 11_000));
        const response = await request.post(API_URL, {
            headers: {
                'Content-Type': 'application/json',
                'X-Aletheia-Client-Version': '1.99'
            },
            data: {
                text: 'test',
                url: 'https://example.com',
                title: 'Test',
                context: 'Test'
            }
        });

        expect(response.status()).toBe(401);
    });

});
