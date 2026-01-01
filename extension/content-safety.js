/**
 * content-safety.js - Pure logic for age-restricted content detection
 * Issue #104 - Age-Restricted Blocking
 *
 * This module contains ONLY pure functions with no DOM or Chrome API dependencies.
 * This allows for easy unit testing outside the browser context.
 *
 * Design Decisions:
 * - FAIL OPEN: If input is invalid or ambiguous, we allow (return false)
 * - BLOCK ON: "adult" rating OR full RTA-5042-1996-1400-1577-RTA pattern
 * - ALLOW: "mature" rating (legitimate content like movie reviews, medical sites)
 */

// The RTA (Restricted to Adults) label pattern from 1996
// Used by adult content sites to self-label their content
// Must match the FULL pattern - partial matches are ignored (regex precision)
const RTA_LABEL_PATTERN = 'rta-5042-1996-1400-1577-rta';

// Explicit adult rating per Google SafeSearch guidelines
const ADULT_RATING = 'adult';

/**
 * Determines if content is age-restricted based on meta rating value.
 *
 * @param {*} ratingContent - The content attribute from <meta name="rating">
 * @returns {boolean} - true if content is age-restricted, false otherwise
 *
 * FAIL OPEN: Returns false (allowed) for invalid/ambiguous input.
 * This is intentional - we only block on explicit adult signals.
 */
function isAgeRestricted(ratingContent) {
    // FAIL OPEN: Invalid input types are allowed
    if (!ratingContent || typeof ratingContent !== 'string') {
        return false;
    }

    // Normalize: lowercase and trim whitespace
    const normalized = ratingContent.toLowerCase().trim();

    // Check for explicit "adult" rating
    if (normalized === ADULT_RATING) {
        return true;
    }

    // Check for RTA label pattern (full pattern only, anywhere in string)
    if (normalized.includes(RTA_LABEL_PATTERN)) {
        return true;
    }

    // FAIL OPEN: Unknown ratings are allowed (including "mature")
    return false;
}

// Export for both Node.js (testing) and browser (extension) contexts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { isAgeRestricted, RTA_LABEL_PATTERN, ADULT_RATING };
}
