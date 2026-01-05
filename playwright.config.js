// @ts-check
const { defineConfig } = require('@playwright/test');
const path = require('path');

/**
 * Playwright configuration for Aletheia E2E tests
 *
 * Usage:
 *   npm run test:e2e           # Run all E2E tests
 *   npm run test:e2e:headed    # Run with browser visible
 *   npm run test:waf           # Run only WAF integration tests
 *
 * Environment Variables:
 *   TEST_BASE_URL     - Base URL for test fixtures (default: GitHub Pages)
 *   SKIP_LAMBDA_TESTS - Set to 'true' to skip tests requiring Lambda ON
 */

// Extension path - use Chrome MV3 extension
const extensionPath = path.join(__dirname, 'extensions/chrome');

// Support TEST_BASE_URL env var for flexibility
const TEST_BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:3000';

module.exports = defineConfig({
    testDir: './tests/e2e',

    // Fail fast on CI, allow retries locally
    retries: process.env.CI ? 0 : 1,

    // Parallel execution
    fullyParallel: false, // Serial for extension tests
    workers: 1,

    // Reporter
    reporter: [
        ['html', { open: 'never' }],
        ['list']
    ],

    // Timeouts
    timeout: 30000,
    expect: {
        timeout: 5000
    },

    // Use Chromium with extension
    use: {
        // Base URL for test fixtures (supports TEST_BASE_URL env var)
        baseURL: TEST_BASE_URL,

        // Browser context options
        viewport: { width: 1280, height: 720 },
        actionTimeout: 10000,

        // Screenshot on failure
        screenshot: 'only-on-failure',
        trace: 'retain-on-failure',

        // Chrome-specific options for extension loading
        launchOptions: {
            args: [
                `--disable-extensions-except=${extensionPath}`,
                `--load-extension=${extensionPath}`,
                '--no-sandbox'
            ]
        }
    },

    // Only use Chromium (extensions not supported in Firefox/WebKit)
    projects: [
        {
            name: 'chromium',
            use: {
                browserName: 'chromium',
                // Extensions require headed mode
                headless: false
            }
        }
    ],

    // Output directory for test artifacts
    outputDir: './test-results/',

    // Web server for local testing
    webServer: {
        command: 'npx serve tests/fixtures/html -p 3000 -C',
        port: 3000,
        reuseExistingServer: !process.env.CI
    }
});
