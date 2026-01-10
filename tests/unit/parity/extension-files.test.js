/**
 * Extension File Parity Tests
 *
 * Ensures Firefox extension has all required files from Chrome extension.
 * Added after 2026-01-09 incident where Firefox was missing:
 * - 178 lines of popup.css
 * - content-check.js (entire file)
 * - content-safety.js (entire file)
 *
 * See: docs/0826-audit-cross-browser-testing.md
 */

import { describe, test, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

const CHROME_DIR = path.resolve(__dirname, '../../../extensions/chrome');
const FIREFOX_DIR = path.resolve(__dirname, '../../../extensions/firefox');

/**
 * Files that MUST exist in both extensions (identical content expected)
 */
const SHARED_FILES = [
  'popup.css',
  'content-check.js',
  'content-safety.js',
  'icons/icon16.png',
  'icons/icon32.png',
  'icons/icon48.png',
  'icons/icon128.png',
];

/**
 * Files that exist in both but have browser-specific differences
 */
const BROWSER_SPECIFIC_FILES = [
  'manifest.json',    // Different manifest format
  'service-worker.js', // browser.* vs chrome.* namespace
  'auth.js',          // Different OAuth implementation
  'popup.js',         // browser.* vs chrome.* namespace
  'popup.html',       // Different issue references in comments
  'overlay.js',       // Different file path in header comment
];

/**
 * Files that should NOT exist in Firefox (Chrome-only)
 */
const CHROME_ONLY_FILES = [
  // Add any Chrome-only files here
];

describe('Extension File Parity', () => {

  describe('Shared files exist in both extensions', () => {
    for (const file of SHARED_FILES) {
      test(`${file} exists in Firefox`, () => {
        const firefoxPath = path.join(FIREFOX_DIR, file);
        expect(
          fs.existsSync(firefoxPath),
          `Firefox missing file: ${file}`
        ).toBe(true);
      });

      test(`${file} exists in Chrome`, () => {
        const chromePath = path.join(CHROME_DIR, file);
        expect(
          fs.existsSync(chromePath),
          `Chrome missing file: ${file}`
        ).toBe(true);
      });
    }
  });

  describe('Shared files have identical content', () => {
    for (const file of SHARED_FILES) {
      // Skip binary files (icons)
      if (file.endsWith('.png')) continue;

      test(`${file} is identical in both extensions`, () => {
        const chromePath = path.join(CHROME_DIR, file);
        const firefoxPath = path.join(FIREFOX_DIR, file);

        // Skip if either doesn't exist (caught by previous test)
        if (!fs.existsSync(chromePath) || !fs.existsSync(firefoxPath)) {
          return;
        }

        const chromeContent = fs.readFileSync(chromePath, 'utf-8');
        const firefoxContent = fs.readFileSync(firefoxPath, 'utf-8');

        expect(
          firefoxContent,
          `${file} differs between Chrome and Firefox. Run: diff extensions/chrome/${file} extensions/firefox/${file}`
        ).toEqual(chromeContent);
      });
    }
  });

  describe('Browser-specific files exist', () => {
    for (const file of BROWSER_SPECIFIC_FILES) {
      test(`${file} exists in Chrome`, () => {
        const chromePath = path.join(CHROME_DIR, file);
        expect(fs.existsSync(chromePath)).toBe(true);
      });

      test(`${file} exists in Firefox`, () => {
        const firefoxPath = path.join(FIREFOX_DIR, file);
        expect(fs.existsSync(firefoxPath)).toBe(true);
      });
    }
  });

  describe('No unexpected files in Firefox', () => {
    test('Firefox has no files Chrome lacks (except manifest differences)', () => {
      const getFiles = (dir) => {
        const files = [];
        const items = fs.readdirSync(dir, { withFileTypes: true });
        for (const item of items) {
          if (item.isDirectory()) {
            files.push(...getFiles(path.join(dir, item.name)).map(f => `${item.name}/${f}`));
          } else {
            files.push(item.name);
          }
        }
        return files;
      };

      const chromeFiles = new Set(getFiles(CHROME_DIR));
      const firefoxFiles = getFiles(FIREFOX_DIR);

      const unexpectedFiles = firefoxFiles.filter(f => !chromeFiles.has(f));

      expect(
        unexpectedFiles,
        `Firefox has unexpected files not in Chrome: ${unexpectedFiles.join(', ')}`
      ).toEqual([]);
    });
  });

  describe('Chrome-only files do not exist in Firefox', () => {
    if (CHROME_ONLY_FILES.length === 0) {
      test('no Chrome-only files defined (placeholder)', () => {
        expect(true).toBe(true);
      });
    } else {
      for (const file of CHROME_ONLY_FILES) {
        test(`${file} does not exist in Firefox`, () => {
          const firefoxPath = path.join(FIREFOX_DIR, file);
          expect(fs.existsSync(firefoxPath)).toBe(false);
        });
      }
    }
  });

});
