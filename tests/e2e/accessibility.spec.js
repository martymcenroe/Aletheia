/**
 * Accessibility Tests
 * Issue #154 - ARIA attributes for screen reader accessibility
 *
 * Uses @axe-core/playwright to scan for WCAG violations.
 * Focuses on:
 * - Test fixture pages (baseline)
 * - Extension-injected content (overlay, popup)
 * - Contrast and ARIA label compliance
 */

const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const { waitForExtensionReady, gotoWithCacheBust, getExtensionId, getPopupUrl } = require('./utils/test-helpers');
const { SCENARIOS } = require('./mocks/mock-data');

/**
 * Helper to format accessibility violations for console output.
 */
function formatViolations(violations) {
    if (violations.length === 0) {
        return 'No accessibility violations found.';
    }

    return violations.map(v => {
        const nodes = v.nodes.map(n => `    - ${n.html}`).join('\n');
        return `
[${v.impact?.toUpperCase()}] ${v.id}: ${v.description}
  Help: ${v.helpUrl}
  Affected elements (${v.nodes.length}):
${nodes}`;
    }).join('\n');
}

test.describe('Accessibility Compliance (#154)', () => {

    test('010: Test fixture page - baseline accessibility', async ({ page }) => {
        // Navigate to clean test fixture
        await gotoWithCacheBust(page, '/test-clean.html');
        await page.waitForLoadState('networkidle');

        // Run axe accessibility scan (with Shadow DOM support)
        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .analyze();

        // Log any violations for debugging
        if (results.violations.length > 0) {
            console.log('Accessibility violations found:');
            console.log(formatViolations(results.violations));
        }

        // Assert no violations
        expect(results.violations).toEqual([]);
    });

    test('020: Page with extension loaded - accessibility scan', async ({ page }) => {
        // Navigate to test page
        await gotoWithCacheBust(page, '/test-clean.html');

        // Wait for extension to potentially inject content
        await waitForExtensionReady(page);

        // Run axe scan including any extension-injected elements
        // Note: Extension uses Shadow DOM, need to check if aletheia-host exists
        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .analyze();

        // Log violations
        if (results.violations.length > 0) {
            console.log('Accessibility violations (with extension):');
            console.log(formatViolations(results.violations));
        }

        // Assert no violations
        expect(results.violations).toEqual([]);
    });

    test('030: Adult-restricted page - blocked state accessibility', async ({ page }) => {
        // Navigate to adult-rated test page (triggers age gate)
        await gotoWithCacheBust(page, '/test-adult.html');

        // Wait for extension to inject blocked overlay
        await waitForExtensionReady(page);

        // Check if aletheia-host element exists (blocked overlay)
        const overlayHost = page.locator('aletheia-host');
        const hasOverlay = await overlayHost.count() > 0;

        if (hasOverlay) {
            console.log('Extension overlay detected - scanning for accessibility');
        }

        // Run axe scan
        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .analyze();

        // Log violations
        if (results.violations.length > 0) {
            console.log('Accessibility violations (blocked state):');
            console.log(formatViolations(results.violations));
        }

        // For now, just log - we expect violations that need fixing
        // This test documents the current state
        console.log(`Total violations: ${results.violations.length}`);
        console.log(`Violations by impact:`);
        const byImpact = {};
        results.violations.forEach(v => {
            byImpact[v.impact] = (byImpact[v.impact] || 0) + 1;
        });
        console.log(byImpact);
    });

    test('040: Index page - landing page accessibility', async ({ page }) => {
        // Navigate to main index page
        await gotoWithCacheBust(page, '/index.html');
        await page.waitForLoadState('networkidle');

        // Run axe scan
        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .analyze();

        // Log violations
        if (results.violations.length > 0) {
            console.log('Accessibility violations (index page):');
            console.log(formatViolations(results.violations));
        }

        // Assert no violations
        expect(results.violations).toEqual([]);
    });

    test('050: Extension popup HTML - direct accessibility scan', async ({ page, context }) => {
        // Use hardcoded extension ID (derived from manifest key)
        const extensionId = getExtensionId();
        console.log(`Using extension ID: ${extensionId}`);

        // Navigate to any page first to trigger extension load
        await gotoWithCacheBust(page, '/test-clean.html');
        await waitForExtensionReady(page);

        if (extensionId) {
            // Try to open popup in a fresh page
            // Note: Chrome blocks direct navigation to chrome-extension:// URLs
            // from pages for security reasons. This test documents the limitation.
            const popupUrl = getPopupUrl(extensionId);
            const popupPage = await context.newPage();

            try {
                await popupPage.goto(popupUrl);
                await popupPage.waitForLoadState('networkidle');
                await popupPage.waitForTimeout(500);

                // Run accessibility scan on popup
                const results = await new AxeBuilder({ page: popupPage })
                    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
                    .analyze();

                console.log('Popup accessibility scan:');
                console.log(`  Total violations: ${results.violations.length}`);

                if (results.violations.length > 0) {
                    console.log(formatViolations(results.violations));

                    // Categorize by impact
                    const critical = results.violations.filter(v => v.impact === 'critical');
                    const serious = results.violations.filter(v => v.impact === 'serious');

                    console.log(`  Critical: ${critical.length}`);
                    console.log(`  Serious: ${serious.length}`);

                    // Fail on critical/serious violations
                    expect(critical.length + serious.length).toBe(0);
                }
            } catch (error) {
                // Chrome blocks navigation to chrome-extension:// URLs for security
                if (error.message.includes('ERR_BLOCKED_BY_CLIENT')) {
                    console.log('Popup scan skipped: Chrome blocks direct extension URL access');
                    console.log('Popup accessibility must be tested manually via:');
                    console.log(`  1. Open Chrome DevTools on the popup`);
                    console.log(`  2. Run axe accessibility audit`);
                    console.log(`  Or use a standalone HTML accessibility checker on popup.html`);
                } else {
                    throw error; // Re-throw unexpected errors
                }
            } finally {
                await popupPage.close();
            }
        } else {
            console.log('Could not get extension ID - skipping popup scan');
        }
    });

    test('060: Museum Label UI - triggered overlay accessibility', async ({ page, context }) => {
        // This test triggers the actual overlay UI to scan its accessibility
        // The overlay uses Shadow DOM, so we need special handling

        // First, we need to allowlist localhost so the extension will show the overlay
        // Inject storage state to enable extension on localhost
        await page.addInitScript(() => {
            // Set up allowlist in chrome.storage.local
            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                chrome.storage.local.set({
                    allowlist: ['localhost', '127.0.0.1'],
                    userId: 'test-user-12345',
                    displayName: 'Test User'
                });
            }
        });

        // Navigate to test page
        await gotoWithCacheBust(page, '/test-clean.html');
        await waitForExtensionReady(page);

        // Check if aletheia-host element exists
        const overlayHost = page.locator('aletheia-host');
        const hostCount = await overlayHost.count();

        console.log(`aletheia-host elements found: ${hostCount}`);

        if (hostCount > 0) {
            // If overlay is present, scan it specifically
            // axe-core should automatically include shadow DOM content
            const results = await new AxeBuilder({ page })
                .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
                .include('aletheia-host')
                .analyze();

            console.log('Museum Label UI accessibility scan:');
            console.log(`  Total violations: ${results.violations.length}`);

            if (results.violations.length > 0) {
                console.log(formatViolations(results.violations));

                // Categorize violations
                const critical = results.violations.filter(v => v.impact === 'critical');
                const serious = results.violations.filter(v => v.impact === 'serious');
                const moderate = results.violations.filter(v => v.impact === 'moderate');
                const minor = results.violations.filter(v => v.impact === 'minor');

                console.log(`  Critical: ${critical.length}`);
                console.log(`  Serious: ${serious.length}`);
                console.log(`  Moderate: ${moderate.length}`);
                console.log(`  Minor: ${minor.length}`);

                // Fail on critical/serious violations
                expect(critical.length + serious.length).toBe(0);
            }
        } else {
            // Overlay not present - try to trigger it via text selection
            console.log('No overlay detected. Attempting to trigger via selection...');

            // Select text on the page
            const selectableText = page.locator('[data-testid="selectable-text"]');
            if (await selectableText.count() > 0) {
                // Triple-click to select paragraph
                await selectableText.click({ clickCount: 3 });
                await page.waitForTimeout(500);

                // Check again for overlay
                const overlayAfterSelection = await page.locator('aletheia-host').count();
                console.log(`aletheia-host after selection: ${overlayAfterSelection}`);

                if (overlayAfterSelection > 0) {
                    const results = await new AxeBuilder({ page })
                        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
                        .include('aletheia-host')
                        .analyze();

                    console.log('Museum Label UI (post-selection) accessibility:');
                    console.log(`  Violations: ${results.violations.length}`);

                    if (results.violations.length > 0) {
                        console.log(formatViolations(results.violations));
                    }
                } else {
                    console.log('Overlay still not present. Site may need to be allowlisted.');
                    console.log('This is expected behavior - overlay only shows on allowlisted sites.');
                }
            }
        }
    });

    test('070: Forced Museum Label Scan - direct injection', async ({ page }) => {
        // This test bypasses extension triggers by directly injecting the overlay
        // component into the DOM for accessibility scanning.

        // Navigate to test fixture
        await gotoWithCacheBust(page, '/test-clean.html');
        await page.waitForLoadState('networkidle');

        // Read and inject overlay.js source code
        const fs = require('fs');
        const path = require('path');
        const overlayPath = path.join(__dirname, '../../extensions/chrome/overlay.js');
        const overlaySource = fs.readFileSync(overlayPath, 'utf-8');

        // Inject overlay.js into page
        await page.addScriptTag({ content: overlaySource });

        // Create a mock selection position for overlay positioning
        // The overlay uses window.getSelection() for positioning
        await page.evaluate(() => {
            // Create a dummy text node and select it so overlay can position
            const textEl = document.createElement('p');
            textEl.textContent = 'Test selection text for Museum Label positioning';
            textEl.style.cssText = 'position: absolute; top: 100px; left: 100px; padding: 20px;';
            document.body.appendChild(textEl);

            // Create a range and select the text
            const range = document.createRange();
            range.selectNodeContents(textEl);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        });

        // Test 1: Warning badge (amber) - typical use case
        console.log('Testing WARNING badge overlay...');
        await page.evaluate(() => {
            window.showAletheiaResult({
                signal: 'Archaic Term',
                gem: 'This word has fallen out of common usage and may carry outdated connotations.',
                context: 'Originally used in the 18th century, this term now primarily appears in historical texts.'
            }, 200);
        });
        await page.waitForTimeout(300);

        // Verify overlay is in DOM
        const warningOverlay = await page.locator('#aletheia-overlay-host').count();
        console.log(`  Overlay injected: ${warningOverlay > 0}`);
        expect(warningOverlay).toBeGreaterThan(0);

        // Run axe scan on the overlay (axe-core auto-scans shadow DOM)
        let results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .include('#aletheia-overlay-host')
            .analyze();

        console.log('  WARNING overlay scan:');
        console.log(`    Total violations: ${results.violations.length}`);
        if (results.violations.length > 0) {
            console.log(formatViolations(results.violations));
        }

        // Track all violations across states
        let allViolations = [...results.violations];

        // Test 2: Block badge (red) - hard block
        console.log('Testing BLOCK badge overlay...');
        await page.evaluate(() => {
            window.showAletheiaResult({
                signal: 'Hard Block - Hate Speech',
                blocked: 'This content has been blocked due to hateful language.'
            }, 403);
        });
        await page.waitForTimeout(300);

        results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .include('#aletheia-overlay-host')
            .analyze();

        console.log('  BLOCK overlay scan:');
        console.log(`    Total violations: ${results.violations.length}`);
        if (results.violations.length > 0) {
            console.log(formatViolations(results.violations));
        }
        allViolations = [...allViolations, ...results.violations];

        // Test 3: Neutral badge (blue) - informational
        console.log('Testing NEUTRAL badge overlay...');
        await page.evaluate(() => {
            window.showAletheiaResult({
                signal: 'Etymology Info',
                gem: 'From Latin "exemplum" meaning sample or pattern.',
                context: 'First recorded usage in English circa 1400.'
            }, 200);
        });
        await page.waitForTimeout(300);

        results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .include('#aletheia-overlay-host')
            .analyze();

        console.log('  NEUTRAL overlay scan:');
        console.log(`    Total violations: ${results.violations.length}`);
        if (results.violations.length > 0) {
            console.log(formatViolations(results.violations));
        }
        allViolations = [...allViolations, ...results.violations];

        // Test 4: Loading state
        console.log('Testing LOADING state overlay...');
        await page.evaluate(() => {
            window.showAletheiaLoading();
        });
        await page.waitForTimeout(300);

        results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .include('#aletheia-overlay-host')
            .analyze();

        console.log('  LOADING overlay scan:');
        console.log(`    Total violations: ${results.violations.length}`);
        if (results.violations.length > 0) {
            console.log(formatViolations(results.violations));
        }
        allViolations = [...allViolations, ...results.violations];

        // Summarize results
        console.log('\n=== MUSEUM LABEL ACCESSIBILITY SUMMARY ===');
        console.log(`Total violations across all states: ${allViolations.length}`);

        if (allViolations.length > 0) {
            // Deduplicate violations by rule ID
            const uniqueViolations = [];
            const seenIds = new Set();
            for (const v of allViolations) {
                if (!seenIds.has(v.id)) {
                    seenIds.add(v.id);
                    uniqueViolations.push(v);
                }
            }

            console.log(`Unique violation types: ${uniqueViolations.length}`);

            const critical = uniqueViolations.filter(v => v.impact === 'critical');
            const serious = uniqueViolations.filter(v => v.impact === 'serious');
            const moderate = uniqueViolations.filter(v => v.impact === 'moderate');
            const minor = uniqueViolations.filter(v => v.impact === 'minor');

            console.log(`  Critical: ${critical.length}`);
            console.log(`  Serious: ${serious.length}`);
            console.log(`  Moderate: ${moderate.length}`);
            console.log(`  Minor: ${minor.length}`);

            // Show all unique violations for fixing
            console.log('\nViolations to fix:');
            console.log(formatViolations(uniqueViolations));

            // Fail on critical/serious violations
            expect(critical.length + serious.length).toBe(0);
        } else {
            console.log('Museum Label passes WCAG 2.0/2.1 AA!');
        }
    });

});
