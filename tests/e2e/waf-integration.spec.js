// tests/e2e/waf-integration.spec.js
// API tests for WAF integration (#95)
// Uses Playwright's request API (Node.js, no CORS issues)
//
// LLD: docs/1095-security-hardening.md

const { test, expect } = require('@playwright/test');

// CloudFront URL
const CLOUDFRONT_URL = 'https://d1fkpkls2wesse.cloudfront.net/';

test.describe('WAF Integration (#95)', () => {

    test('020: CloudFront accepts request with valid header', async ({ request }) => {
        const response = await request.post(CLOUDFRONT_URL, {
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

        expect(response.status()).toBe(200);
        expect(response.ok()).toBe(true);
    });

    test('030: WAF blocks request without header', async ({ request }) => {
        const response = await request.post(CLOUDFRONT_URL, {
            headers: {
                'Content-Type': 'application/json'
                // Missing X-Aletheia-Client-Version
            },
            data: { text: 'test' }
        });

        expect(response.status()).toBe(403);
    });

    test('040: WAF blocks invalid version', async ({ request }) => {
        const response = await request.post(CLOUDFRONT_URL, {
            headers: {
                'Content-Type': 'application/json',
                'X-Aletheia-Client-Version': '0.9' // Invalid
            },
            data: { text: 'test' }
        });

        expect(response.status()).toBe(403);
    });

    test('050: Future version accepted', async ({ request }) => {
        const response = await request.post(CLOUDFRONT_URL, {
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

        expect(response.status()).toBe(200);
    });

});
