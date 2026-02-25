/**
 * Unit Tests for Firefox overlay.js
 *
 * Issue #391 Phase 3: Overlay error rendering tests.
 * Firefox mirror of chrome/overlay.test.js.
 * Source files are functionally identical across browsers.
 */

import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const extensionDir = path.resolve(__dirname, '../../../extensions/firefox');

const overlaySource = fs.readFileSync(path.join(extensionDir, 'overlay.js'), 'utf-8');

describe('Overlay File (Firefox)', () => {
  it('overlay.js file exists and is non-empty', () => {
    expect(overlaySource.length).toBeGreaterThan(0);
  });
});

describe('isHardBlock behavior (Firefox)', () => {
  it('403 is rendered as hard block', () => {
    expect(overlaySource).toContain('if (httpStatus === 403) return true');
  });

  it('source contains isHardBlock function', () => {
    expect(overlaySource).toContain('function isHardBlock(response, httpStatus)');
  });
});

describe('Unexpected response handling (Firefox)', () => {
  it('overlay uses fallback signal when response.signal is missing', () => {
    expect(overlaySource).toContain("response?.signal || 'Analysis'");
  });

  it('overlay uses fallback gem when response.gem is missing', () => {
    expect(overlaySource).toContain("response?.gem || ''");
  });
});
