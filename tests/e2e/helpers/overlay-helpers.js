// tests/e2e/helpers/overlay-helpers.js
// Shared helper functions for overlay E2E tests
// Extracted from museum-label.spec.js for reuse in Firefox tests (#265)

const path = require('path');

/**
 * Inject overlay.js into the page
 * @param {import('@playwright/test').Page} page - Playwright page
 * @param {string} browser - 'chrome' or 'firefox'
 */
async function injectOverlay(page, browser = 'chrome') {
    // Patch attachShadow to use 'open' mode for testing
    // Closed shadow roots return null for host.shadowRoot, breaking test queries
    // This patch is required for BOTH Chrome and Firefox (#272)
    await page.evaluate(() => {
        const originalAttachShadow = Element.prototype.attachShadow;
        Element.prototype.attachShadow = function(options) {
            // Force open mode for testing
            return originalAttachShadow.call(this, { ...options, mode: 'open' });
        };
    });

    const overlayPath = browser === 'firefox'
        ? path.join(__dirname, '../../../extensions/firefox/overlay.js')
        : path.join(__dirname, '../../../extensions/chrome/overlay.js');
    await page.addScriptTag({ path: overlayPath });
    // Wait for functions to be defined
    await page.waitForFunction(() => window.showAletheiaResult !== undefined);
}

/**
 * Select text element to establish selection geometry
 * @param {import('@playwright/test').Page} page
 * @param {string} testId - data-testid attribute value
 */
async function selectText(page, testId) {
    const element = page.locator(`[data-testid="${testId}"]`);
    await element.click({ clickCount: 3 }); // Triple-click to select all
    await page.waitForTimeout(100);
}

/**
 * Query element inside Shadow DOM
 * @param {import('@playwright/test').Page} page
 * @param {string} selector - CSS selector within shadow root
 * @returns {Promise<{className: string, textContent: string, ariaExpanded: string|null, isVisible: boolean}|null>}
 */
async function shadowQuery(page, selector) {
    return page.evaluate((sel) => {
        const host = document.getElementById('aletheia-overlay-host');
        if (!host || !host.shadowRoot) return null;
        const el = host.shadowRoot.querySelector(sel);
        return el ? {
            className: el.className,
            textContent: el.textContent,
            ariaExpanded: el.getAttribute('aria-expanded'),
            isVisible: el.offsetParent !== null || getComputedStyle(el).display !== 'none'
        } : null;
    }, selector);
}

/**
 * Check if overlay host exists and is visible
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<boolean>}
 */
async function isOverlayVisible(page) {
    return page.evaluate(() => {
        const host = document.getElementById('aletheia-overlay-host');
        return host !== null && host.offsetParent !== null;
    });
}

/**
 * Click element inside Shadow DOM
 * @param {import('@playwright/test').Page} page
 * @param {string} selector - CSS selector within shadow root
 */
async function shadowClick(page, selector) {
    await page.evaluate((sel) => {
        const host = document.getElementById('aletheia-overlay-host');
        if (host && host.shadowRoot) {
            const el = host.shadowRoot.querySelector(sel);
            if (el) el.click();
        }
    }, selector);
}

/**
 * Hover over element inside Shadow DOM
 * @param {import('@playwright/test').Page} page
 * @param {string} selector - CSS selector within shadow root
 */
async function shadowHover(page, selector) {
    await page.evaluate((sel) => {
        const host = document.getElementById('aletheia-overlay-host');
        if (host && host.shadowRoot) {
            const el = host.shadowRoot.querySelector(sel);
            if (el) {
                el.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
            }
        }
    }, selector);
}

/**
 * Check if element inside Shadow DOM is focused
 * @param {import('@playwright/test').Page} page
 * @param {string} selector - CSS selector within shadow root
 * @returns {Promise<boolean>}
 */
async function isShadowElementFocused(page, selector) {
    return page.evaluate((sel) => {
        const host = document.getElementById('aletheia-overlay-host');
        if (!host || !host.shadowRoot) return false;
        const el = host.shadowRoot.querySelector(sel);
        return el === host.shadowRoot.activeElement;
    }, selector);
}

/**
 * Get computed z-index of overlay card (inside shadow DOM)
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<number>}
 */
async function getOverlayZIndex(page) {
    return page.evaluate(() => {
        const host = document.getElementById('aletheia-overlay-host');
        if (!host || !host.shadowRoot) return 0;
        const card = host.shadowRoot.querySelector('.aletheia-card');
        if (!card) return 0;
        return parseInt(getComputedStyle(card).zIndex, 10) || 0;
    });
}

/**
 * Verify Shadow DOM isolation - styles don't leak in or out
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<{hostStylesIsolated: boolean, pageStylesUnaffected: boolean}>}
 */
async function verifyShadowDOMIsolation(page) {
    return page.evaluate(() => {
        const host = document.getElementById('aletheia-overlay-host');
        if (!host || !host.shadowRoot) {
            return { hostStylesIsolated: false, pageStylesUnaffected: false };
        }

        // Check that shadow elements aren't affected by page styles
        const card = host.shadowRoot.querySelector('.aletheia-card');
        if (!card) {
            return { hostStylesIsolated: false, pageStylesUnaffected: false };
        }

        // The card should have its own font-family, not inherit from page
        const cardStyle = getComputedStyle(card);
        const hasOwnFont = cardStyle.fontFamily.includes('system') ||
                          cardStyle.fontFamily.includes('Segoe') ||
                          cardStyle.fontFamily.includes('Roboto');

        // Check page elements aren't affected by shadow styles
        const pageBody = document.body;
        const bodyStyle = getComputedStyle(pageBody);
        // Body should NOT have aletheia-specific styles
        const pageUnaffected = !bodyStyle.fontFamily.includes('aletheia');

        return {
            hostStylesIsolated: hasOwnFont,
            pageStylesUnaffected: pageUnaffected
        };
    });
}

// Test data fixtures (shared across Chrome and Firefox tests)
const TEST_DATA = {
    neutral: {
        signal: 'Historical Term',
        gem: 'A word from early 20th century usage.',
        context: 'First documented in 1923. Common in academic writing. Still used in historical contexts today.'
    },
    warning: {
        signal: 'Archaic Pejorative',
        gem: 'Once clinical, now outdated and considered offensive.',
        context: 'First used in 18th century medicine. Fell out of clinical use by 1950. Now recognized as dehumanizing.'
    },
    blocked: {
        signal: 'Hard Block',
        gem: 'This content is blocked.',
        context: 'Content blocked by safety filter.',
        blocked: 'Content blocked by safety filter'
    },
    longContext: {
        signal: 'Etymological Analysis',
        gem: 'A term with complex historical roots spanning multiple centuries.',
        context: 'This is a much longer context that will test the typewriter animation. The word originated in ancient Greek, traveled through Latin during the Roman Empire, was adopted into Old French during the medieval period, and finally entered English through Norman influence. Its meaning has shifted considerably over the centuries, from a technical term to everyday usage.'
    }
};

module.exports = {
    injectOverlay,
    selectText,
    shadowQuery,
    isOverlayVisible,
    shadowClick,
    shadowHover,
    isShadowElementFocused,
    getOverlayZIndex,
    verifyShadowDOMIsolation,
    TEST_DATA
};
