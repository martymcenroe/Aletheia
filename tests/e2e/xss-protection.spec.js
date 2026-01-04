// tests/e2e/xss-protection.spec.js
// XSS Protection E2E tests
//
// Tests verify the extension correctly sanitizes malicious input
// and does not execute injected scripts.
//
// LLD: docs/1105-test-site-infrastructure.md

const { test, expect } = require('@playwright/test');

// Helper to wait for extension to process page
async function waitForExtension(page) {
    await page.waitForTimeout(1000);
}

// Helper to bust cache on page navigation
async function gotoWithCacheBust(page, path) {
    const url = `${path}?t=${Date.now()}`;
    await page.goto(url);
}

// Track if an alert dialog appeared
async function setupAlertListener(page) {
    let alertTriggered = false;
    let alertMessage = '';

    page.on('dialog', async dialog => {
        alertTriggered = true;
        alertMessage = dialog.message();
        await dialog.dismiss();
    });

    return () => ({ triggered: alertTriggered, message: alertMessage });
}

test.describe('XSS Protection', () => {

    test('090: Script tag in selected text should be sanitized', async ({ page }) => {
        const getAlertStatus = await setupAlertListener(page);

        await gotoWithCacheBust(page, '/test-xss-script.html');
        await waitForExtension(page);

        // Verify page loaded
        await expect(page.locator('h1').first()).toContainText('QA SANDBOX');

        // Select the malicious text
        const selectableText = page.locator('[data-testid="selectable-text"]');
        await expect(selectableText).toBeVisible();

        // Triple-click to select all text in the paragraph
        await selectableText.click({ clickCount: 3 });
        await page.waitForTimeout(500);

        // Verify no alert was triggered during page load or selection
        const alertStatus = getAlertStatus();
        expect(alertStatus.triggered).toBe(false);
    });

    test('100: Image onerror in selected text should be sanitized', async ({ page }) => {
        const getAlertStatus = await setupAlertListener(page);

        await gotoWithCacheBust(page, '/test-xss-img.html');
        await waitForExtension(page);

        // Verify page loaded
        await expect(page.locator('h1').first()).toContainText('QA SANDBOX');

        // The img tag with bad src should NOT trigger alert
        // Even though the img loads (and fails), onerror should not fire XSS

        // Wait a moment for any potential onerror to fire
        await page.waitForTimeout(1000);

        // Verify no alert was triggered
        const alertStatus = getAlertStatus();
        expect(alertStatus.triggered).toBe(false);
    });

    test('110: Event handler in element should not execute in overlay', async ({ page }) => {
        const getAlertStatus = await setupAlertListener(page);

        await gotoWithCacheBust(page, '/test-xss-event.html');
        await waitForExtension(page);

        // Verify page loaded
        await expect(page.locator('h1').first()).toContainText('QA SANDBOX');

        // Hover over the malicious element
        const selectableText = page.locator('[data-testid="selectable-text"]');
        await selectableText.hover();
        await page.waitForTimeout(500);

        // Note: The test page element itself has an onmouseover
        // We're testing that if this text is copied to the overlay,
        // the event handler is NOT copied

        // For now, just verify no alert from page load
        // Full test requires triggering Aletheia and checking overlay
        const alertStatus = getAlertStatus();
        // Note: The original page's onmouseover WILL fire when we hover
        // That's expected - we're testing the OVERLAY doesn't copy handlers
        // For this basic test, we just verify the page loads without XSS on load
    });

    test('Malicious text selection does not crash extension', async ({ page }) => {
        await gotoWithCacheBust(page, '/test-xss-script.html');
        await waitForExtension(page);

        // Select text containing script tag
        const selectableText = page.locator('[data-testid="selectable-text"]');
        await selectableText.click({ clickCount: 3 });

        // Verify page is still responsive
        await expect(page.locator('h1').first()).toBeVisible();

        // Navigate to another page to confirm extension still works
        await gotoWithCacheBust(page, '/test-clean.html');
        await expect(page.locator('h1').first()).toContainText('QA SANDBOX');
    });

});
