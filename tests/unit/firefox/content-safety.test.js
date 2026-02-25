/**
 * Unit Tests for Firefox content-safety.js
 * Issue #104 - Age-Restricted Content Detection
 *
 * Firefox mirror of chrome/content-safety.test.js.
 * Source files are identical across browsers.
 */

import { describe, it, expect } from 'vitest';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const extensionDir = path.resolve(__dirname, '../../../extensions/firefox');

const { isAgeRestricted, RTA_LABEL_PATTERN, ADULT_RATING } = await import(
  `file://${path.join(extensionDir, 'content-safety.js')}`
    .replace(/\\/g, '/')
).catch(() => {
  return require(path.join(extensionDir, 'content-safety.js'));
});

describe('isAgeRestricted (Firefox)', () => {
  it('returns false for null', () => {
    expect(isAgeRestricted(null)).toBe(false);
  });

  it('returns false for undefined', () => {
    expect(isAgeRestricted(undefined)).toBe(false);
  });

  it('returns false for empty string', () => {
    expect(isAgeRestricted('')).toBe(false);
  });

  it('returns false for non-string input', () => {
    expect(isAgeRestricted(42)).toBe(false);
  });

  it('returns true for "adult"', () => {
    expect(isAgeRestricted('adult')).toBe(true);
  });

  it('returns true for "Adult" (case insensitive)', () => {
    expect(isAgeRestricted('Adult')).toBe(true);
  });

  it('returns true for " adult " (whitespace trimming)', () => {
    expect(isAgeRestricted(' adult ')).toBe(true);
  });

  it('returns false for "mature" (fail open)', () => {
    expect(isAgeRestricted('mature')).toBe(false);
  });

  it('returns true for RTA pattern', () => {
    expect(isAgeRestricted('rta-5042-1996-1400-1577-rta')).toBe(true);
  });

  it('returns false for partial RTA pattern', () => {
    expect(isAgeRestricted('rta-5042')).toBe(false);
  });
});

describe('Constants (Firefox)', () => {
  it('exports RTA_LABEL_PATTERN', () => {
    expect(RTA_LABEL_PATTERN).toBe('rta-5042-1996-1400-1577-rta');
  });

  it('exports ADULT_RATING', () => {
    expect(ADULT_RATING).toBe('adult');
  });
});
