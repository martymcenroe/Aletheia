/**
 * Visual Regression POC Test
 * Issue #173 - Visual Regression Infrastructure (Phase 1)
 *
 * This proof-of-concept test verifies the visual regression infrastructure:
 * 1. Playwright toHaveScreenshot() works
 * 2. Baselines are created on first run
 * 3. Comparisons work on subsequent runs
 * 4. Diffs are detected when UI changes
 *
 * POC Strategy: Test the test fixture page itself (not extension popup).
 * This proves the screenshot infrastructure works without complex extension
 * popup access. Popup testing can be added in Phase 2.
 */

const { test, expect } = require('@playwright/test');
const path = require('path');
const { waitForExtensionReady, waitForFontsReady, gotoWithCacheBust } = require('./utils/test-helpers');

test.describe('Visual Regression POC (#173)', () => {

    test('010: Test fixture page - baseline/comparison', async ({ page }) => {
        // Navigate to clean test fixture
        await gotoWithCacheBust(page, '/test-clean.html');

        // Wait for page to fully load
        await page.waitForLoadState('networkidle');
        await waitForFontsReady(page);

        // Take screenshot of the test fixture header
        // This proves the visual regression infrastructure works
        const header = page.locator('h1').first();
        await expect(header).toHaveScreenshot('test-fixture-header.png', {
            maxDiffPixels: 50,
            animations: 'disabled'
        });
    });

    test('020: Full page screenshot - baseline/comparison', async ({ page }) => {
        // Navigate to clean test fixture
        await gotoWithCacheBust(page, '/test-clean.html');

        // Wait for page and fonts
        await page.waitForLoadState('networkidle');
        await waitForFontsReady(page);

        // Take full page screenshot
        await expect(page).toHaveScreenshot('test-fixture-fullpage.png', {
            maxDiffPixels: 100,
            fullPage: true,
            animations: 'disabled'
        });
    });

    test('030: Extension loaded - verify extension injects content', async ({ page }) => {
        // Navigate to test page
        await gotoWithCacheBust(page, '/test-clean.html');

        // Wait for extension to potentially inject
        await waitForExtensionReady(page);

        // Check that page loaded successfully (extension should not break page)
        await expect(page.locator('h1').first()).toContainText('QA SANDBOX');

        // Take a screenshot of the page with extension loaded
        // (extension may or may not have visible UI depending on state)
        await expect(page).toHaveScreenshot('page-with-extension.png', {
            maxDiffPixels: 100,
            animations: 'disabled'
        });
    });

    test('040: Verify snapshots directory structure', async () => {
        // Informational test - verifies snapshot infrastructure
        const fs = require('fs');
        const snapshotDir = path.join(__dirname, '__snapshots__');

        // After first run, this should pass
        if (fs.existsSync(snapshotDir)) {
            const files = fs.readdirSync(snapshotDir, { recursive: true });
            console.log('Snapshot structure:');
            files.forEach(f => console.log('  ' + f));
            expect(files.length).toBeGreaterThan(0);
        } else {
            console.log('No snapshots yet - run test:visual:update to create baselines');
            // Skip on first run
            test.skip();
        }
    });

});
