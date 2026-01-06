/**
 * Shared test utilities for Aletheia E2E and visual regression tests
 * Issue #173 - Visual Regression Infrastructure
 */

/**
 * Extension ID derived from manifest.json key field.
 * This ID is stable across installs due to the explicit key.
 *
 * Calculated from manifest key using Chrome's algorithm:
 * 1. Base64-decode the public key from manifest.json
 * 2. SHA-256 hash the decoded bytes
 * 3. Take first 32 hex chars, map 0-9a-f to a-p
 *
 * See extensions/chrome/manifest.json for the source key.
 */
const EXTENSION_ID = 'hgkgcicdgpckniojmneapkafkklhnbdj';

function getExtensionId() {
    return EXTENSION_ID;
}

/**
 * Wait for extension to fully initialize after page load.
 * Includes font loading wait to prevent flaky text rendering.
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {number} timeout - Max wait time in ms (default: 1500)
 */
async function waitForExtensionReady(page, timeout = 1500) {
    // Wait for network to settle
    await page.waitForLoadState('networkidle');

    // Wait for fonts to load
    await waitForFontsReady(page);

    // Additional wait for extension injection
    await page.waitForTimeout(timeout);
}

/**
 * Wait for all fonts to load before taking screenshots.
 * Prevents flaky text rendering differences.
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 */
async function waitForFontsReady(page) {
    await page.evaluate(() => document.fonts.ready);
}

/**
 * Inject mock data into chrome.storage.local before popup loads.
 * Must be called before page.goto().
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {object} storageData - Object to set in chrome.storage.local
 */
async function injectStorageState(page, storageData) {
    await page.addInitScript((data) => {
        // This runs before any page scripts
        // We store the data for the extension to pick up
        window.__ALETHEIA_MOCK_STORAGE__ = data;
    }, storageData);
}

/**
 * Get the extension popup URL for a given extension ID.
 *
 * @param {string} extensionId - The Chrome extension ID
 * @returns {string} The popup URL
 */
function getPopupUrl(extensionId) {
    return `chrome-extension://${extensionId}/popup.html`;
}

/**
 * Navigate to a test fixture with cache busting.
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} path - Path to the fixture (e.g., '/test-clean.html')
 */
async function gotoWithCacheBust(page, path) {
    const url = `${path}?t=${Date.now()}`;
    await page.goto(url);
}

/**
 * Configure screenshot options with sensible defaults.
 *
 * @param {string} name - Screenshot filename (without path)
 * @param {object} options - Override options
 * @returns {object} Playwright screenshot options
 */
function screenshotOptions(name, options = {}) {
    return {
        animations: 'disabled',
        ...options
    };
}

module.exports = {
    getExtensionId,
    waitForExtensionReady,
    waitForFontsReady,
    injectStorageState,
    getPopupUrl,
    gotoWithCacheBust,
    screenshotOptions
};
