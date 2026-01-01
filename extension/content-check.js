/**
 * content-check.js - DOM wrapper for age-restricted content detection
 * Issue #104 - Age-Restricted Blocking
 *
 * This script is injected into web pages to check for age-restriction meta tags.
 * It queries the DOM and uses the pure logic from content-safety.js.
 *
 * Execution context: Content script (runs in page context)
 * Returns: Result object sent back to service worker via scripting.executeScript
 */

/**
 * Check the page's rating meta tag and determine if it's age-restricted.
 * This function is executed in the page context via chrome.scripting.executeScript.
 *
 * @returns {Object} Result object with type, isRestricted, and ratingValue
 */
function checkPageRating() {
    // Query for the rating meta tag
    // Format: <meta name="rating" content="adult">
    const ratingMeta = document.querySelector('meta[name="rating"]');

    // Extract the content attribute value (or empty string if not found)
    const ratingValue = ratingMeta?.getAttribute('content') || '';

    // Use the pure detection logic
    // Note: isAgeRestricted is defined inline below since content scripts
    // can't easily import modules in Manifest V3
    const isRestricted = isAgeRestrictedInline(ratingValue);

    return {
        type: 'RATING_CHECK',
        isRestricted: isRestricted,
        ratingValue: ratingValue || null
    };
}

/**
 * Inline copy of isAgeRestricted logic from content-safety.js
 * Required because content scripts can't import ES modules in MV3
 *
 * Keep in sync with extension/content-safety.js
 */
function isAgeRestrictedInline(ratingContent) {
    const RTA_LABEL_PATTERN = 'rta-5042-1996-1400-1577-rta';
    const ADULT_RATING = 'adult';

    if (!ratingContent || typeof ratingContent !== 'string') {
        return false;
    }

    const normalized = ratingContent.toLowerCase().trim();

    if (normalized === ADULT_RATING) {
        return true;
    }

    if (normalized.includes(RTA_LABEL_PATTERN)) {
        return true;
    }

    return false;
}

// Execute and return result when script is injected
checkPageRating();
