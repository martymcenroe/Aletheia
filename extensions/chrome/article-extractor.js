/**
 * article-extractor.js - Full Article Content Extraction
 * Issue #106 - Full Article Context Retrieval
 *
 * Provides Readability-style article extraction, PII scrubbing, and truncation.
 * Designed to be injected into pages and called via chrome.scripting.executeScript.
 *
 * See: docs/lld/active/1106-full-article-context.md
 */

// =============================================================================
// CONSTANTS
// =============================================================================

const MAX_ARTICLE_CHARS = 10000; // ~2500 tokens

// PII patterns for scrubbing
const PII_PATTERNS = {
    // Email: user@domain.tld
    email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
    // Phone: US formats, simplified pattern to avoid ReDoS
    // Matches: 555-123-4567, (555) 123-4567, 555.123.4567, +1-555-123-4567
    // eslint-disable-next-line security/detect-unsafe-regex -- linear alternation, no nested quantifiers
    phone: /(?:\+1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}/g,
};

// =============================================================================
// TEXT CLEANING
// =============================================================================

/**
 * Clean and normalize extracted text.
 * - Collapses multiple whitespace to single space
 * - Trims leading/trailing whitespace
 *
 * @param {string} text - Raw text to clean
 * @returns {string} Cleaned text
 */
function cleanText(text) {
    if (!text) return '';
    return text
        .replace(/\s+/g, ' ')  // Normalize whitespace
        .trim();
}

// =============================================================================
// PII SCRUBBING
// =============================================================================

/**
 * Scrub personally identifiable information from text.
 * Redacts emails and phone numbers.
 *
 * @param {string} text - Text to scrub
 * @returns {string} Text with PII redacted
 */
function scrubPII(text) {
    if (!text) return '';
    let scrubbed = text;
    scrubbed = scrubbed.replace(PII_PATTERNS.email, '[email redacted]');
    scrubbed = scrubbed.replace(PII_PATTERNS.phone, '[phone redacted]');
    return scrubbed;
}

// =============================================================================
// CLIENT-SIDE TRUNCATION
// =============================================================================

/**
 * Truncate text to maximum character limit.
 *
 * @param {string} text - Text to truncate
 * @returns {Object} { text: string, truncated: boolean }
 */
function truncateArticle(text) {
    if (!text) return { text: '', truncated: false };
    if (text.length <= MAX_ARTICLE_CHARS) {
        return { text, truncated: false };
    }
    return {
        text: text.substring(0, MAX_ARTICLE_CHARS) + '\n...[truncated]',
        truncated: true
    };
}

// =============================================================================
// READABILITY-STYLE EXTRACTION
// =============================================================================

/**
 * Extract main article content from the page using a Readability-style approach.
 * Prioritizes semantic HTML elements (article, main) before falling back to heuristics.
 *
 * @returns {string} Extracted article text (cleaned but NOT scrubbed or truncated)
 */
function extractArticleContent() {
    // Priority 1: Look for semantic article containers
    const article = document.querySelector('article');
    if (article && article.innerText.length > 200) {
        return cleanText(article.innerText);
    }

    // Priority 2: Look for main content area
    const main = document.querySelector('main');
    if (main && main.innerText.length > 200) {
        return cleanText(main.innerText);
    }

    // Priority 3: Look for common article class patterns
    const contentSelectors = [
        '[class*="article-content"]',
        '[class*="post-content"]',
        '[class*="entry-content"]',
        '[class*="article-body"]',
        '[class*="post-body"]',
        '[role="article"]',
        '.content',
        '#content',
        '.story-body',
        '.article',
        '.post'
    ];

    for (const selector of contentSelectors) {
        try {
            const el = document.querySelector(selector);
            if (el && el.innerText.length > 500) {
                return cleanText(el.innerText);
            }
        } catch (_e) {
            // Invalid selector or other error - continue to next
        }
    }

    // Fallback: Body minus obvious non-content (LAST RESORT)
    // Clone the body and remove known non-content elements
    const clone = document.body.cloneNode(true);
    const removeSelectors = [
        'script',
        'style',
        'nav',
        'footer',
        'header',
        'aside',
        '[role="navigation"]',
        '[role="banner"]',
        '[role="contentinfo"]',
        '[role="complementary"]',
        '.nav',
        '.navbar',
        '.footer',
        '.header',
        '.sidebar',
        '.advertisement',
        '.ad',
        '.ads',
        '.comments',
        '#comments'
    ];

    for (const selector of removeSelectors) {
        try {
            clone.querySelectorAll(selector).forEach(el => el.remove());
        } catch (_e) {
            // Invalid selector - continue
        }
    }

    return cleanText(clone.innerText);
}

// =============================================================================
// MAIN EXTRACTION PIPELINE
// =============================================================================

/**
 * Extract, scrub, and truncate article content.
 * This is the main entry point called from the popup.
 *
 * @returns {Object} { text: string, truncated: boolean, originalLength: number }
 */
function extractFullArticle() {
    try {
        // Step 1: Extract article content (Readability-style)
        const rawContent = extractArticleContent();
        const originalLength = rawContent.length;

        // Step 2: Scrub PII
        const scrubbed = scrubPII(rawContent);

        // Step 3: Truncate to limit
        const { text, truncated } = truncateArticle(scrubbed);

        return {
            text,
            truncated,
            originalLength
        };
    } catch (error) {
        // Fail gracefully - return empty result
        console.error('[Aletheia] Article extraction failed:', error);
        return {
            text: '',
            truncated: false,
            originalLength: 0,
            error: error.message
        };
    }
}

// Export for testing (if running in Node.js/test environment)
// eslint-disable-next-line no-undef -- module is Node.js global, not browser
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    // eslint-disable-next-line no-undef
    module.exports = {
        cleanText,
        scrubPII,
        truncateArticle,
        extractArticleContent,
        extractFullArticle,
        MAX_ARTICLE_CHARS,
        PII_PATTERNS
    };
}

// Return result when injected via chrome.scripting.executeScript
extractFullArticle();
