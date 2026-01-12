/**
 * Unit Tests for Chrome article-extractor.js
 * Issue #106 - Full Article Context Retrieval
 *
 * Test Categories:
 * 1. Text Cleaning - cleanText function
 * 2. PII Scrubbing - scrubPII function
 * 3. Truncation - truncateArticle function
 * 4. Article Extraction - extractArticleContent function
 * 5. Full Pipeline - extractFullArticle function
 */

import { describe, it, expect } from 'vitest';
import { JSDOM } from 'jsdom';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get directory paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const extensionDir = path.resolve(__dirname, '../../../extensions/chrome');

// Read article-extractor.js
const extractorJs = fs.readFileSync(path.join(extensionDir, 'article-extractor.js'), 'utf-8');

/**
 * Creates a fresh DOM environment and evaluates article-extractor.js within it.
 */
function createExtractorEnvironment(htmlContent = '<html><body></body></html>') {
  const dom = new JSDOM(htmlContent, {
    url: 'http://localhost/test.html',
    runScripts: 'dangerously'
  });

  const { window } = dom;

  // Mock console.error for cleaner test output
  window.console = { ...console, error: () => {} };

  // Execute article-extractor.js in the window context
  // We need to wrap it to extract the functions since they don't use window.* prefix
  const wrappedJs = `
    ${extractorJs}

    // Expose functions for testing
    window.cleanText = cleanText;
    window.scrubPII = scrubPII;
    window.truncateArticle = truncateArticle;
    window.extractArticleContent = extractArticleContent;
    window.extractFullArticle = extractFullArticle;
    window.MAX_ARTICLE_CHARS = MAX_ARTICLE_CHARS;
    window.PII_PATTERNS = PII_PATTERNS;
  `;

  window.eval(wrappedJs);

  return { dom, window };
}

// =============================================================================
// TEXT CLEANING TESTS
// =============================================================================

describe('cleanText', () => {
  it('should collapse multiple whitespace to single space', () => {
    const { window } = createExtractorEnvironment();
    const result = window.cleanText('hello    world');
    expect(result).toBe('hello world');
  });

  it('should trim leading and trailing whitespace', () => {
    const { window } = createExtractorEnvironment();
    const result = window.cleanText('  hello world  ');
    expect(result).toBe('hello world');
  });

  it('should normalize newlines and tabs', () => {
    const { window } = createExtractorEnvironment();
    const result = window.cleanText('hello\n\n\nworld\t\tthere');
    expect(result).toBe('hello world there');
  });

  it('should handle empty string', () => {
    const { window } = createExtractorEnvironment();
    const result = window.cleanText('');
    expect(result).toBe('');
  });

  it('should handle null/undefined', () => {
    const { window } = createExtractorEnvironment();
    expect(window.cleanText(null)).toBe('');
    expect(window.cleanText(undefined)).toBe('');
  });
});

// =============================================================================
// PII SCRUBBING TESTS
// =============================================================================

describe('scrubPII', () => {
  describe('email scrubbing', () => {
    it('should redact simple email addresses', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('Contact: john@example.com for info');
      expect(result).toBe('Contact: [email redacted] for info');
    });

    it('should redact multiple email addresses', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('Email john@example.com or jane@test.org');
      expect(result).toBe('Email [email redacted] or [email redacted]');
    });

    it('should redact emails with dots in username', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('john.doe@example.com');
      expect(result).toBe('[email redacted]');
    });

    it('should redact emails with plus sign', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('john+tag@example.com');
      expect(result).toBe('[email redacted]');
    });

    it('should redact emails with subdomains', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('john@mail.example.co.uk');
      expect(result).toBe('[email redacted]');
    });
  });

  describe('phone scrubbing', () => {
    it('should redact US phone with dashes', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('Call 555-123-4567');
      expect(result).toBe('Call [phone redacted]');
    });

    it('should redact US phone with dots', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('Call 555.123.4567');
      expect(result).toBe('Call [phone redacted]');
    });

    it('should redact US phone with parentheses', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('Call (555) 123-4567');
      expect(result).toBe('Call [phone redacted]');
    });

    it('should redact phone with country code', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('Call +1-555-123-4567');
      expect(result).toBe('Call [phone redacted]');
    });

    it('should redact multiple phone numbers', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('Call 555-123-4567 or 555-987-6543');
      expect(result).toBe('Call [phone redacted] or [phone redacted]');
    });
  });

  describe('combined scrubbing', () => {
    it('should redact both email and phone in same text', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('Contact john@example.com or call 555-123-4567');
      expect(result).toBe('Contact [email redacted] or call [phone redacted]');
    });

    it('should preserve non-PII text', () => {
      const { window } = createExtractorEnvironment();
      const result = window.scrubPII('Lorem ipsum dolor sit amet');
      expect(result).toBe('Lorem ipsum dolor sit amet');
    });

    it('should handle empty string', () => {
      const { window } = createExtractorEnvironment();
      expect(window.scrubPII('')).toBe('');
    });

    it('should handle null/undefined', () => {
      const { window } = createExtractorEnvironment();
      expect(window.scrubPII(null)).toBe('');
      expect(window.scrubPII(undefined)).toBe('');
    });
  });
});

// =============================================================================
// TRUNCATION TESTS
// =============================================================================

describe('truncateArticle', () => {
  it('should not truncate text under limit', () => {
    const { window } = createExtractorEnvironment();
    const shortText = 'Hello world';
    const result = window.truncateArticle(shortText);
    expect(result.text).toBe(shortText);
    expect(result.truncated).toBe(false);
  });

  it('should truncate text over limit', () => {
    const { window } = createExtractorEnvironment();
    // Create text longer than MAX_ARTICLE_CHARS (10000)
    const longText = 'a'.repeat(15000);
    const result = window.truncateArticle(longText);
    expect(result.truncated).toBe(true);
    expect(result.text.length).toBeLessThan(longText.length);
    expect(result.text).toContain('...[truncated]');
  });

  it('should truncate to exactly MAX_ARTICLE_CHARS + marker', () => {
    const { window } = createExtractorEnvironment();
    const longText = 'x'.repeat(15000);
    const result = window.truncateArticle(longText);
    // MAX_ARTICLE_CHARS is 10000, plus '\n...[truncated]' marker
    expect(result.text.startsWith('x'.repeat(10000))).toBe(true);
  });

  it('should handle empty string', () => {
    const { window } = createExtractorEnvironment();
    const result = window.truncateArticle('');
    expect(result.text).toBe('');
    expect(result.truncated).toBe(false);
  });

  it('should handle null/undefined', () => {
    const { window } = createExtractorEnvironment();
    const result = window.truncateArticle(null);
    expect(result.text).toBe('');
    expect(result.truncated).toBe(false);
  });

  it('should handle text exactly at limit', () => {
    const { window } = createExtractorEnvironment();
    const exactText = 'a'.repeat(10000);
    const result = window.truncateArticle(exactText);
    expect(result.text).toBe(exactText);
    expect(result.truncated).toBe(false);
  });
});

// =============================================================================
// ARTICLE EXTRACTION TESTS
// Note: JSDOM doesn't support innerText the same way browsers do.
// These tests use textContent-based approaches. Full browser testing
// should be done via E2E tests in tests/e2e/.
// =============================================================================

describe('extractArticleContent', () => {
  // Note: DOM-based extraction tests are skipped in JSDOM because innerText
  // is not supported. The actual extraction logic is tested via E2E tests
  // in tests/e2e/. See: https://github.com/jsdom/jsdom/issues/1245

  it.skip('should return a string type (requires browser innerText)', () => {
    // This test requires real browser innerText support
    // Tested via E2E in tests/e2e/full-article.spec.js
  });

  it('should not throw on empty body', () => {
    const html = '<html><body></body></html>';
    const { window } = createExtractorEnvironment(html);
    // This passes because extractArticleContent returns '' for empty body
    const result = window.extractArticleContent();
    expect(result).toBe('');
  });

  it.skip('should not throw on complex HTML structure (requires browser innerText)', () => {
    // This test requires real browser innerText support
    // Tested via E2E in tests/e2e/full-article.spec.js
  });
});

// =============================================================================
// FULL PIPELINE TESTS
// Note: Full integration with DOM extraction is limited in JSDOM.
// These tests verify the pipeline structure and error handling.
// =============================================================================

describe('extractFullArticle', () => {
  it('should return expected result structure', () => {
    const html = `
      <html>
        <body>
          <article>Some article content</article>
        </body>
      </html>
    `;
    const { window } = createExtractorEnvironment(html);
    const result = window.extractFullArticle();

    // Verify result structure
    expect(result).toHaveProperty('text');
    expect(result).toHaveProperty('truncated');
    expect(result).toHaveProperty('originalLength');
    expect(typeof result.text).toBe('string');
    expect(typeof result.truncated).toBe('boolean');
    expect(typeof result.originalLength).toBe('number');
  });

  it('should not throw on any input', () => {
    const html = '<html><body></body></html>';
    const { window } = createExtractorEnvironment(html);
    expect(() => window.extractFullArticle()).not.toThrow();
  });

  it('should handle complex HTML without throwing', () => {
    const html = `
      <html>
        <body>
          <nav>Nav</nav>
          <article>
            <h1>Title</h1>
            <p>Content with john@test.com and 555-123-4567</p>
          </article>
          <footer>Footer</footer>
        </body>
      </html>
    `;
    const { window } = createExtractorEnvironment(html);
    expect(() => window.extractFullArticle()).not.toThrow();
  });
});

// =============================================================================
// CONSTANTS TESTS
// =============================================================================

describe('Constants', () => {
  it('should have MAX_ARTICLE_CHARS set to 10000', () => {
    const { window } = createExtractorEnvironment();
    expect(window.MAX_ARTICLE_CHARS).toBe(10000);
  });

  it('should have PII_PATTERNS with email and phone', () => {
    const { window } = createExtractorEnvironment();
    expect(window.PII_PATTERNS).toHaveProperty('email');
    expect(window.PII_PATTERNS).toHaveProperty('phone');
    // RegExp cross-realm check (JSDOM creates a separate realm)
    expect(window.PII_PATTERNS.email.constructor.name).toBe('RegExp');
    expect(window.PII_PATTERNS.phone.constructor.name).toBe('RegExp');
  });
});
