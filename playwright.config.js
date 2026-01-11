// @ts-check
/* global require, module, process, __dirname */
const { defineConfig } = require('@playwright/test');
const path = require('path');

/**
 * Playwright configuration for Aletheia E2E tests
 *
 * Usage:
 *   npm run test:e2e           # Run all E2E tests
 *   npm run test:e2e:headed    # Run with browser visible
 *   npm run test:waf           # Run only WAF integration tests
 *   npm run test:visual        # Run visual regression tests
 *   npm run test:visual:update # Update visual baselines
 *
 * Environment Variables:
 *   TEST_BASE_URL      - Base URL for test fixtures (default: localhost:3000)
 *   SKIP_LAMBDA_TESTS  - Set to 'true' to skip tests requiring Lambda ON
 *   UPDATE_SNAPSHOTS   - Set to 'true' to update visual baselines
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
        timeout: 5000,
        // Visual regression settings (Issue #173)
        toHaveScreenshot: {
            maxDiffPixels: 100,        // Antialiasing tolerance
            threshold: 0.2,            // Per-pixel color threshold (0-1)
            animations: 'disabled',    // Disable animations for deterministic captures
        }
    },

    // Visual regression snapshot directory
    snapshotDir: './tests/e2e/__snapshots__',

    // Snapshots: Use --update-snapshots CLI flag to update baselines
    // Default: only create missing baselines (don't overwrite existing)

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

    // Browser projects
    // - chromium: Full extension loading (requires headed mode)
    // - firefox-overlay: Script injection only (headless OK) - Issue #265
    projects: [
        {
            name: 'chromium',
            use: {
                browserName: 'chromium',
                // Extensions require headed mode
                headless: false
            }
        },
        {
            // Issue #263: Edge E2E test matrix
            name: 'edge',
            use: {
                channel: 'msedge',
                // Extensions require headed mode
                headless: false
                // Inherits launchOptions from global use block (extension loading)
            }
        },
        {
            name: 'firefox-overlay',
            testMatch: /firefox\/.*\.spec\.js/,
            use: {
                browserName: 'firefox',
                // Script injection doesn't require extension loading
                headless: true,
                // Remove Chrome extension args for Firefox
                launchOptions: {
                    args: []
                }
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
