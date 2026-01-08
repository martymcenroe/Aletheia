#!/usr/bin/env node
/**
 * Generate Chrome Web Store screenshots using Playwright.
 *
 * Usage:
 *   npx playwright test tools/generate_store_screenshots.js --headed
 *
 * Or run directly:
 *   node tools/generate_store_screenshots.js
 *
 * Output: docs/assets/store/screenshot-*.png (1280x800)
 *
 * Requirements:
 * - Chrome Web Store: 1280x800 or 640x400, PNG or JPEG, no alpha
 * - At least 1 screenshot required, max 5
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// Configuration
const EXTENSION_PATH = path.join(__dirname, '../extensions/chrome');
const OUTPUT_DIR = path.join(__dirname, '../docs/assets/store');
const FIXTURES_DIR = path.join(__dirname, '../tests/fixtures/html');
const VIEWPORT = { width: 1280, height: 800 };

// Mock data for overlay demonstration
const DEMO_DATA = {
    neutral: {
        signal: 'Historical Term',
        gem: 'Originally a medical term from the 19th century, now recognized as culturally biased.',
        context: 'First documented in 1801 by Franz Joseph Gall. The term evolved from clinical usage to everyday language by the mid-20th century. Modern scholars recommend contextual awareness when encountering this word in historical texts.'
    },
    warning: {
        signal: 'Archaic Pejorative',
        gem: 'Once clinical, now outdated and considered offensive in most contexts.',
        context: 'First used in 18th century medicine. Fell out of clinical use by 1950. Now recognized as dehumanizing. Exercise caution when encountering in historical documents.'
    }
};

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
    console.log('='.repeat(50));
    console.log('Generating Chrome Web Store Screenshots');
    console.log('='.repeat(50));

    // Ensure output directory exists
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });

    // Start local server for fixtures
    const { spawn } = require('child_process');
    const server = spawn('npx', ['serve', FIXTURES_DIR, '-p', '3456', '-C'], {
        stdio: 'pipe',
        shell: true
    });

    await sleep(2000); // Wait for server to start

    try {
        // Launch browser with extension
        console.log('\nLaunching browser with extension...');
        const browser = await chromium.launchPersistentContext('', {
            headless: false,
            args: [
                `--disable-extensions-except=${EXTENSION_PATH}`,
                `--load-extension=${EXTENSION_PATH}`,
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled'
            ],
            viewport: VIEWPORT
        });

        const page = await browser.newPage();
        await page.setViewportSize(VIEWPORT);

        // Screenshot 1: Extension overlay on article (Neutral - Glance state)
        console.log('\n[1/4] Capturing overlay in Glance state...');
        await page.goto('http://localhost:3456/store-demo.html');
        await page.waitForLoadState('networkidle');
        await sleep(500);

        // Inject overlay.js
        const overlayPath = path.join(EXTENSION_PATH, 'overlay.js');
        await page.addScriptTag({ path: overlayPath });
        await page.waitForFunction(() => window.showAletheiaResult !== undefined);

        // Select the demo term
        const term = page.locator('[data-testid="demo-term"]');
        await term.click({ clickCount: 3 });
        await sleep(200);

        // Show overlay with neutral data
        await page.evaluate((data) => {
            window.showAletheiaResult(data, 200);
        }, DEMO_DATA.neutral);
        await sleep(500);

        await page.screenshot({
            path: path.join(OUTPUT_DIR, 'screenshot-1-glance.png'),
            type: 'png'
        });
        console.log('   Saved: screenshot-1-glance.png');

        // Screenshot 2: Overlay with Gem visible (hover state)
        console.log('\n[2/4] Capturing overlay in Hover state...');
        await page.evaluate(() => {
            const host = document.getElementById('aletheia-overlay-host');
            if (host && host.shadowRoot) {
                const card = host.shadowRoot.querySelector('.aletheia-card');
                if (card) {
                    card.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                }
            }
        });
        await sleep(300);

        await page.screenshot({
            path: path.join(OUTPUT_DIR, 'screenshot-2-hover.png'),
            type: 'png'
        });
        console.log('   Saved: screenshot-2-hover.png');

        // Screenshot 3: Overlay fully expanded (context visible)
        console.log('\n[3/4] Capturing overlay in Expanded state...');
        await page.evaluate(() => {
            const host = document.getElementById('aletheia-overlay-host');
            if (host && host.shadowRoot) {
                const toggle = host.shadowRoot.querySelector('.aletheia-toggle');
                if (toggle) toggle.click();
            }
        });
        await sleep(2000); // Wait for typewriter animation

        await page.screenshot({
            path: path.join(OUTPUT_DIR, 'screenshot-3-expanded.png'),
            type: 'png'
        });
        console.log('   Saved: screenshot-3-expanded.png');

        // Screenshot 4: Warning state (amber badge)
        console.log('\n[4/4] Capturing warning state...');

        // Reload and show warning
        await page.goto('http://localhost:3456/store-demo.html');
        await page.waitForLoadState('networkidle');
        await sleep(500);

        await page.addScriptTag({ path: overlayPath });
        await page.waitForFunction(() => window.showAletheiaResult !== undefined);

        const term2 = page.locator('[data-testid="demo-term"]');
        await term2.click({ clickCount: 3 });
        await sleep(200);

        await page.evaluate((data) => {
            window.showAletheiaResult(data, 200);
        }, DEMO_DATA.warning);
        await sleep(500);

        // Trigger hover
        await page.evaluate(() => {
            const host = document.getElementById('aletheia-overlay-host');
            if (host && host.shadowRoot) {
                const card = host.shadowRoot.querySelector('.aletheia-card');
                if (card) {
                    card.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                }
            }
        });
        await sleep(300);

        await page.screenshot({
            path: path.join(OUTPUT_DIR, 'screenshot-4-warning.png'),
            type: 'png'
        });
        console.log('   Saved: screenshot-4-warning.png');

        await browser.close();

        console.log('\n' + '='.repeat(50));
        console.log('Screenshots generated successfully!');
        console.log('='.repeat(50));
        console.log(`\nOutput directory: ${OUTPUT_DIR}`);
        console.log('\nFiles:');
        fs.readdirSync(OUTPUT_DIR)
            .filter(f => f.startsWith('screenshot-'))
            .forEach(f => console.log(`  - ${f}`));
        console.log('\nReady to upload to Chrome Web Store.');

    } finally {
        server.kill();
    }
}

main().catch(console.error);
