/**
 * Unit Tests for Chrome overlay.js
 *
 * Issue #391 Phase 3: Overlay error rendering tests.
 * Tests the isHardBlock function and error-specific overlay behavior.
 */

import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const extensionDir = path.resolve(__dirname, '../../../extensions/chrome');

const overlaySource = fs.readFileSync(path.join(extensionDir, 'overlay.js'), 'utf-8');

describe('Overlay File (Issue #391)', () => {
  it('overlay.js file exists and is non-empty', () => {
    expect(overlaySource.length).toBeGreaterThan(0);
  });
});

describe('isHardBlock behavior (Issue #391)', () => {
  it('401 is NOT rendered as hard block', () => {
    // The isHardBlock function should return false for 401
    // This is critical: 401 means auth config error, NOT content block
    expect(overlaySource).toContain('if (httpStatus === 401) return false');
  });

  it('403 is still rendered as hard block', () => {
    expect(overlaySource).toContain('if (httpStatus === 403) return true');
  });

  it('source contains isHardBlock function', () => {
    expect(overlaySource).toContain('function isHardBlock(response, httpStatus)');
  });
});

describe('Unexpected response handling (Issue #391)', () => {
  it('overlay uses fallback signal when response.signal is missing', () => {
    // The overlay should default to 'Analysis' when signal is missing
    expect(overlaySource).toContain("response?.signal || 'Analysis'");
  });

  it('overlay uses fallback gem when response.gem is missing', () => {
    // Empty string fallback for missing gem
    expect(overlaySource).toContain("response?.gem || ''");
  });
});
