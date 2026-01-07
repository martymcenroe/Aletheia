/**
 * content-check.js - DOM wrapper for page signal detection
 * Issue #104 - Age-Restricted Blocking
 * Issue #162 - NoArchive Transform Layer
 *
 * This script is injected into web pages to check for meta tags:
 * - Age restriction (rating meta tag)
 * - NoArchive signal (robots/googlebot meta tags)
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
 * Keep in sync with extensions/chrome/content-safety.js
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

/**
 * Check if the page has a noarchive signal in robots or googlebot meta tags.
 * Issue #162 - NoArchive Transform Layer
 *
 * Checks both:
 * - <meta name="robots" content="noarchive">
 * - <meta name="googlebot" content="noarchive">
 *
 * The noarchive directive can appear alone or with other directives (comma-separated).
 *
 * @returns {boolean} True if noarchive signal is present
 */
function checkNoArchive() {
    // Query for both robots and googlebot meta tags
    const metas = document.querySelectorAll('meta[name="robots"], meta[name="googlebot"]');

    for (const meta of metas) {
        const content = meta.getAttribute('content') || '';
        // noarchive can appear alone or comma-separated with other directives
        if (content.toLowerCase().includes('noarchive')) {
            return true;
        }
    }

    return false;
}

/**
 * Check all page signals and return combined result.
 * This is the main entry point when the script is injected.
 *
 * @returns {Object} Result object with all signal checks
 */
function checkPageSignals() {
    const ratingResult = checkPageRating();

    return {
        type: 'PAGE_SIGNALS',
        isRestricted: ratingResult.isRestricted,
        ratingValue: ratingResult.ratingValue,
        noarchive: checkNoArchive()
    };
}

// Execute and return result when script is injected
checkPageSignals();
