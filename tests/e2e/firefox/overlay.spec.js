// tests/e2e/firefox/overlay.spec.js
// Firefox Overlay E2E tests (#265)
//
// Verifies Firefox overlay.js rendering and behavior in Gecko engine.
// Uses script injection approach (no full extension loading).
//
// LLD: docs/lld/active/1265-firefox-overlay-e2e.md

const { test, expect } = require('@playwright/test');
const {
    injectOverlay,
    selectText,
    shadowQuery,
    isOverlayVisible,
    shadowClick,
    isShadowElementFocused,
    getOverlayZIndex,
    verifyShadowDOMIsolation,
    TEST_DATA
} = require('../helpers/overlay-helpers');

test.describe('Firefox Overlay (#265)', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/test-museum-label.html');
        await page.waitForLoadState('domcontentloaded');
    });

    test.describe('Rendering (Gecko)', () => {

        test('010: Neutral badge renders correctly in Firefox', async ({ page }) => {
            await injectOverlay(page, 'firefox');
            await selectText(page, 'test-neutral');

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

            // Check signal text renders correctly
            const signal = await shadowQuery(page, '.aletheia-signal');
            expect(signal).not.toBeNull();
            expect(signal.textContent).toBe('Historical Term');
        });

        test('020: Warning badge renders correctly in Firefox', async ({ page }) => {
            await injectOverlay(page, 'firefox');
            await selectText(page, 'test-warning');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.warning);

            const badge = await shadowQuery(page, '.aletheia-badge');
            expect(badge.className).toContain('warning');

            const signal = await shadowQuery(page, '.aletheia-signal');
            expect(signal.textContent).toBe('Archaic Pejorative');
        });

        test('030: Block badge renders correctly in Firefox', async ({ page }) => {
            await injectOverlay(page, 'firefox');
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

    test.describe('Shadow DOM Isolation (Gecko-specific)', () => {

        test('040: Styles do not bleed in or out in Firefox', async ({ page }) => {
            // Add conflicting page styles
            await page.addStyleTag({
                content: `
                    body { font-family: 'Comic Sans MS', cursive !important; }
                    .aletheia-card { background: pink !important; }
                    .aletheia-badge { display: none !important; }
                `
            });

            await injectOverlay(page, 'firefox');
            await selectText(page, 'test-neutral');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            const isolation = await verifyShadowDOMIsolation(page);

            // Shadow DOM should protect overlay from page styles
            expect(isolation.hostStylesIsolated).toBe(true);

            // Page styles should not be affected by shadow styles
            expect(isolation.pageStylesUnaffected).toBe(true);

            // Badge should still be visible despite page trying to hide it
            const badge = await shadowQuery(page, '.aletheia-badge');
            expect(badge).not.toBeNull();
            expect(badge.isVisible).toBe(true);
        });

        test('050: Z-index stacking above complex page elements', async ({ page }) => {
            // First inject overlay and show it
            await injectOverlay(page, 'firefox');
            await selectText(page, 'test-neutral');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            // Now add high z-index elements AFTER the overlay is shown
            await page.addStyleTag({
                content: `
                    .high-z-modal { position: fixed; z-index: 999999; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); pointer-events: none; }
                    .higher-z-dialog { position: fixed; z-index: 9999999; top: 50%; left: 50%; pointer-events: none; }
                `
            });
            await page.evaluate(() => {
                const modal = document.createElement('div');
                modal.className = 'high-z-modal';
                document.body.appendChild(modal);

                const dialog = document.createElement('div');
                dialog.className = 'higher-z-dialog';
                dialog.textContent = 'High z-index dialog';
                document.body.appendChild(dialog);
            });

            // Overlay should have max z-index (higher than the elements we added)
            const overlayZIndex = await getOverlayZIndex(page);
            expect(overlayZIndex).toBe(2147483647); // Max 32-bit signed int

            // Overlay should still be visible above the modal
            const visible = await isOverlayVisible(page);
            expect(visible).toBe(true);
        });

    });

    test.describe('Interaction', () => {

        test('060: Expand/collapse context works in Firefox', async ({ page }) => {
            await injectOverlay(page, 'firefox');
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

        test('070: Close button works in Firefox', async ({ page }) => {
            await injectOverlay(page, 'firefox');
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

        test('080: Escape key closes overlay in Firefox', async ({ page }) => {
            await injectOverlay(page, 'firefox');
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

    });

    test.describe('Accessibility', () => {

        test('090: Focus management works in Firefox', async ({ page }) => {
            await injectOverlay(page, 'firefox');
            await selectText(page, 'test-neutral');

            await page.evaluate((data) => {
                window.showAletheiaResult(data, 200);
            }, TEST_DATA.neutral);

            await page.waitForTimeout(100);

            // Close button should be focused by default
            const focused = await isShadowElementFocused(page, '.aletheia-close');
            expect(focused).toBe(true);
        });

    });

    test.describe('Security', () => {

        test('100: XSS prevention works in Firefox', async ({ page }) => {
            await injectOverlay(page, 'firefox');
            await selectText(page, 'test-neutral');

            // Malicious payload
            const xssData = {
                signal: '<script>alert("xss")</script>',
                gem: '<img src=x onerror=alert("img-xss")>',
                context: '<svg onload=alert("svg-xss")>'
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
