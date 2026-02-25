/**
 * Unit Tests for Firefox content-check.js
 * Issue #104 - Age-Restricted Content Detection
 * Issue #162 - NoArchive Transform Layer
 *
 * Firefox mirror of chrome/content-check.test.js.
 * Source files are functionally identical across browsers.
 */

import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const extensionDir = path.resolve(__dirname, '../../../extensions/firefox');

const contentCheckSource = fs.readFileSync(path.join(extensionDir, 'content-check.js'), 'utf-8');

describe('Content Check File (Firefox)', () => {
  it('content-check.js file exists and is non-empty', () => {
    expect(contentCheckSource.length).toBeGreaterThan(0);
  });
});

describe('checkPageRating function (Firefox)', () => {
  it('source contains checkPageRating function', () => {
    expect(contentCheckSource).toContain('function checkPageRating()');
  });

  it('queries for rating meta tag', () => {
    expect(contentCheckSource).toContain('meta[name="rating"]');
  });

  it('returns RATING_CHECK type', () => {
    expect(contentCheckSource).toContain("type: 'RATING_CHECK'");
  });

  it('returns isRestricted and ratingValue fields', () => {
    expect(contentCheckSource).toContain('isRestricted:');
    expect(contentCheckSource).toContain('ratingValue:');
  });
});

describe('isAgeRestrictedInline function (Firefox)', () => {
  it('source contains inline age restriction check', () => {
    expect(contentCheckSource).toContain('function isAgeRestrictedInline(ratingContent)');
  });

  it('checks for adult rating', () => {
    expect(contentCheckSource).toContain("ADULT_RATING = 'adult'");
  });

  it('checks for RTA label pattern', () => {
    expect(contentCheckSource).toContain("RTA_LABEL_PATTERN = 'rta-5042-1996-1400-1577-rta'");
  });

  it('normalizes input with toLowerCase and trim', () => {
    expect(contentCheckSource).toContain('.toLowerCase()');
    expect(contentCheckSource).toContain('.trim()');
  });

  it('validates string type before checking', () => {
    expect(contentCheckSource).toContain("typeof ratingContent !== 'string'");
  });
});

describe('checkNoArchive function (Firefox)', () => {
  it('source contains checkNoArchive function', () => {
    expect(contentCheckSource).toContain('function checkNoArchive()');
  });

  it('queries both robots and googlebot meta tags', () => {
    expect(contentCheckSource).toContain('meta[name="robots"]');
    expect(contentCheckSource).toContain('meta[name="googlebot"]');
  });

  it('checks for noarchive directive', () => {
    expect(contentCheckSource).toContain("'noarchive'");
  });
});

describe('checkPageSignals function (Firefox)', () => {
  it('source contains checkPageSignals entry point', () => {
    expect(contentCheckSource).toContain('function checkPageSignals()');
  });

  it('returns PAGE_SIGNALS type', () => {
    expect(contentCheckSource).toContain("type: 'PAGE_SIGNALS'");
  });

  it('includes noarchive in result', () => {
    expect(contentCheckSource).toContain('noarchive: checkNoArchive()');
  });

  it('script auto-executes at end for injection', () => {
    expect(contentCheckSource).toContain('checkPageSignals();');
  });
});
