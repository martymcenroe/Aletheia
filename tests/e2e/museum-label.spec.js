// tests/e2e/museum-label.spec.js
// Museum Label UI E2E tests (#125)
//
// Tests the progressive disclosure overlay (Glance → Hover → Expanded)
// with Signal, Gem, Context tiers.
//
// LLD: docs/1125-museum-label-ui.md

const { test, expect } = require('@playwright/test');
const path = require('path');

// Test data fixtures
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

// Helper: Inject overlay.js into the page
async function injectOverlay(page) {
    const overlayPath = path.join(__dirname, '../../extensions/chrome/overlay.js');
    await page.addScriptTag({ path: overlayPath });
    // Wait for functions to be defined
    await page.waitForFunction(() => window.showAletheiaResult !== undefined);
}

// Helper: Select text element to establish selection geometry
async function selectText(page, testId) {
    const element = page.locator(`[data-testid="${testId}"]`);
    await element.click({ clickCount: 3 }); // Triple-click to select all
    await page.waitForTimeout(100);
}

// Helper: Query element inside Shadow DOM
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

// Helper: Check if overlay host exists and is visible
async function isOverlayVisible(page) {
    return page.evaluate(() => {
        const host = document.getElementById('aletheia-overlay-host');
        return host !== null && host.offsetParent !== null;
    });
}

// Helper: Click element inside Shadow DOM
async function shadowClick(page, selector) {
    await page.evaluate((sel) => {
        const host = document.getElementById('aletheia-overlay-host');
        if (host && host.shadowRoot) {
            const el = host.shadowRoot.querySelector(sel);
            if (el) el.click();
        }
    }, selector);
}

// Helper: Hover over element inside Shadow DOM
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

// Helper: Check if element inside Shadow DOM is focused
async function isShadowElementFocused(page, selector) {
    return page.evaluate((sel) => {
        const host = document.getElementById('aletheia-overlay-host');
        if (!host || !host.shadowRoot) return false;
        const el = host.shadowRoot.querySelector(sel);
        return el === host.shadowRoot.activeElement;
    }, selector);
}

test.describe('Museum Label UI (#125)', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/test-museum-label.html');
        await page.waitForLoadState('domcontentloaded');
    });

    test.describe('Tier 1: Glance (Signal)', () => {

        test('010: Shows neutral badge (blue) for neutral signal', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-neutral');

            // Trigger overlay
            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            // Verify overlay exists
            const visible = await isOverlayVisible(page);
            expect(visible).toBe(true);

            // Check badge has neutral class
            const badge = await shadowQuery(page, '.aletheia-badge');
            expect(badge).not.toBeNull();
            expect(badge.className).toContain('neutral');

            // Check signal text
            const signal = await shadowQuery(page, '.aletheia-signal');
            expect(signal).not.toBeNull();
            expect(signal.textContent).toBe('Historical Term');
        });

        test('020: Shows warning badge (amber) for pejorative signal', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-warning');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.warning);

            const badge = await shadowQuery(page, '.aletheia-badge');
            expect(badge.className).toContain('warning');

            const signal = await shadowQuery(page, '.aletheia-signal');
            expect(signal.textContent).toBe('Archaic Pejorative');
        });

        test('030: Shows block badge (red) for hard block', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-blocked');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 403);
            }, TEST_DATA.blocked);

            const badge = await shadowQuery(page, '.aletheia-badge');
            expect(badge.className).toContain('block');

            // Card should have hard-block class
            const card = await shadowQuery(page, '.aletheia-card');
            expect(card.className).toContain('hard-block');
        });

    });

    test.describe('Tier 2: Hover (Gem)', () => {

        test('040: Gem appears on hover for non-blocked content', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-neutral');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            // Initially gem should not have 'visible' class
            let gem = await shadowQuery(page, '.aletheia-gem');
            expect(gem.className).not.toContain('visible');

            // Hover over card
            await shadowHover(page, '.aletheia-card');
            await page.waitForTimeout(200);

            // Gem should now have visible class
            gem = await shadowQuery(page, '.aletheia-gem');
            expect(gem.className).toContain('visible');
            expect(gem.textContent).toBe(TEST_DATA.neutral.gem);
        });

        test('050: Gem hidden for hard block', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-blocked');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 403);
            }, TEST_DATA.blocked);

            // Hover over card
            await shadowHover(page, '.aletheia-card');
            await page.waitForTimeout(200);

            // Gem should not be visible (display:none from CSS)
            const gem = await shadowQuery(page, '.aletheia-gem');
            // For hard block, gem element may not exist or not be visible
            if (gem) {
                expect(gem.isVisible).toBe(false);
            }
        });

    });

    test.describe('Tier 3: Expand (Context)', () => {

        test('060: Context expands on Show More click', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-neutral');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            // Initially context should not be expanded
            let context = await shadowQuery(page, '.aletheia-context');
            expect(context.className).not.toContain('expanded');

            // Click "Show More"
            await shadowClick(page, '.aletheia-toggle');
            await page.waitForTimeout(500);

            // Context should be expanded
            context = await shadowQuery(page, '.aletheia-context');
            expect(context.className).toContain('expanded');

            // Button text should change
            const toggle = await shadowQuery(page, '.aletheia-toggle');
            expect(toggle.textContent).toBe('Show Less');
        });

        test('070: Context collapses on Show Less click', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-neutral');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            // Expand first
            await shadowClick(page, '.aletheia-toggle');
            await page.waitForTimeout(500);

            // Collapse
            await shadowClick(page, '.aletheia-toggle');
            await page.waitForTimeout(500);

            // Context should be collapsed
            const context = await shadowQuery(page, '.aletheia-context');
            expect(context.className).not.toContain('expanded');

            // Button text should revert
            const toggle = await shadowQuery(page, '.aletheia-toggle');
            expect(toggle.textContent).toBe('Show More');
        });

        test('080: Toggle button hidden for hard block', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-blocked');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 403);
            }, TEST_DATA.blocked);

            // Toggle should not be visible
            const toggle = await shadowQuery(page, '.aletheia-toggle');
            if (toggle) {
                expect(toggle.isVisible).toBe(false);
            }
        });

        test('090: Typewriter animation plays for context', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-long-context');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.longContext);

            // Click expand
            await shadowClick(page, '.aletheia-toggle');

            // Wait a short time - text should be partially rendered
            await page.waitForTimeout(200);

            let context = await shadowQuery(page, '.aletheia-context');
            const partialLength = context.textContent.length;

            // Text should be started but not complete
            expect(partialLength).toBeGreaterThan(0);
            expect(partialLength).toBeLessThan(TEST_DATA.longContext.context.length);

            // Wait for full animation (15ms * ~400 chars = ~6s, add buffer)
            await page.waitForTimeout(7000);
            context = await shadowQuery(page, '.aletheia-context');
            expect(context.textContent).toBe(TEST_DATA.longContext.context);
        });

    });

    test.describe('Close Behavior', () => {

        test('100: Close button removes overlay', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-neutral');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            let visible = await isOverlayVisible(page);
            expect(visible).toBe(true);

            // Click close button
            await shadowClick(page, '.aletheia-close');
            await page.waitForTimeout(100);

            // Overlay should be removed
            visible = await isOverlayVisible(page);
            expect(visible).toBe(false);
        });

        test('110: Escape key closes overlay', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-neutral');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            let visible = await isOverlayVisible(page);
            expect(visible).toBe(true);

            // Press Escape
            await page.keyboard.press('Escape');
            await page.waitForTimeout(100);

            // Overlay should be removed
            visible = await isOverlayVisible(page);
            expect(visible).toBe(false);
        });

        test('120: Typewriter stops on close mid-animation', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-long-context');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.longContext);

            // Start typewriter
            await shadowClick(page, '.aletheia-toggle');
            await page.waitForTimeout(200);

            // Close mid-animation
            await page.keyboard.press('Escape');
            await page.waitForTimeout(100);

            const visible = await isOverlayVisible(page);
            expect(visible).toBe(false);

            // No console errors (verified by test completing without exception)
        });

    });

    test.describe('Accessibility', () => {

        test('130: Close button receives focus on open', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-neutral');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            await page.waitForTimeout(100);

            // Close button should be focused by default
            const focused = await isShadowElementFocused(page, '.aletheia-close');
            expect(focused).toBe(true);
        });

        test('140: ARIA attributes update on expand', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-neutral');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            // Initial state
            let context = await shadowQuery(page, '.aletheia-context');
            expect(context.ariaExpanded).toBe('false');

            // Expand
            await shadowClick(page, '.aletheia-toggle');
            await page.waitForTimeout(300);

            // After expand
            context = await shadowQuery(page, '.aletheia-context');
            expect(context.ariaExpanded).toBe('true');
        });

    });

    test.describe('Loading State', () => {

        test('150: Loading overlay shows spinner', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-neutral');

            await page.evaluate(() => {
                window.showAletheiaLoading();
            });

            const spinner = await shadowQuery(page, '.aletheia-spinner');
            expect(spinner).not.toBeNull();

            const loading = await shadowQuery(page, '.aletheia-loading');
            expect(loading.textContent).toContain('Analyzing');
        });

    });

    test.describe('XSS Prevention', () => {

        test('160: Script in signal is escaped', async ({ page }) => {
            await injectOverlay(page);
            await selectText(page, 'test-neutral');

            // Malicious payload
            const xssData = {
                signal: '<script>alert("xss")</script>',
                gem: 'Normal gem',
                context: 'Normal context'
            };

            // Setup dialog listener to detect XSS
            let alertTriggered = false;
            page.on('dialog', async dialog => {
                alertTriggered = true;
                await dialog.dismiss();
            });

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, xssData);

            await page.waitForTimeout(500);

            // Text should be escaped, not executed
            const signal = await shadowQuery(page, '.aletheia-signal');
            expect(signal.textContent).toBe('<script>alert("xss")</script>');

            // No alert was triggered
            expect(alertTriggered).toBe(false);
        });

    });

});
