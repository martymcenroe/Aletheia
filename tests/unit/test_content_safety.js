/**
 * Unit tests for content-safety.js
 * Issue #104 - Age-Restricted Blocking
 *
 * TDD: These tests are written BEFORE the implementation.
 * Run: npm test
 */

const { isAgeRestricted, RTA_LABEL_PATTERN } = require('../../extension/content-safety.js');

describe('isAgeRestricted', () => {
    // =========================================================================
    // BLOCKED CASES - Should return true
    // =========================================================================

    describe('blocks adult content', () => {
        test('blocks "adult"', () => {
            expect(isAgeRestricted('adult')).toBe(true);
        });

        test('blocks "ADULT" (case insensitive)', () => {
            expect(isAgeRestricted('ADULT')).toBe(true);
        });

        test('blocks "Adult" (mixed case)', () => {
            expect(isAgeRestricted('Adult')).toBe(true);
        });

        test('blocks " adult " (whitespace trimmed)', () => {
            expect(isAgeRestricted(' adult ')).toBe(true);
        });

        test('blocks "\\tadult\\n" (various whitespace)', () => {
            expect(isAgeRestricted('\tadult\n')).toBe(true);
        });
    });

    describe('blocks RTA label pattern', () => {
        test('blocks full RTA pattern uppercase', () => {
            expect(isAgeRestricted('RTA-5042-1996-1400-1577-RTA')).toBe(true);
        });

        test('blocks full RTA pattern lowercase', () => {
            expect(isAgeRestricted('rta-5042-1996-1400-1577-rta')).toBe(true);
        });

        test('blocks RTA pattern mixed case', () => {
            expect(isAgeRestricted('Rta-5042-1996-1400-1577-Rta')).toBe(true);
        });

        test('blocks RTA pattern embedded in string', () => {
            expect(isAgeRestricted('prefix-RTA-5042-1996-1400-1577-RTA-suffix')).toBe(true);
        });

        test('blocks RTA pattern with leading text', () => {
            expect(isAgeRestricted('some-text-RTA-5042-1996-1400-1577-RTA')).toBe(true);
        });

        test('blocks RTA pattern with trailing text', () => {
            expect(isAgeRestricted('RTA-5042-1996-1400-1577-RTA-more')).toBe(true);
        });
    });

    // =========================================================================
    // ALLOWED CASES - Should return false (fail open)
    // =========================================================================

    describe('allows mature rating (NOT adult)', () => {
        test('allows "mature"', () => {
            expect(isAgeRestricted('mature')).toBe(false);
        });

        test('allows "MATURE" (case insensitive)', () => {
            expect(isAgeRestricted('MATURE')).toBe(false);
        });

        test('allows " mature " (whitespace)', () => {
            expect(isAgeRestricted(' mature ')).toBe(false);
        });
    });

    describe('allows safe/general ratings', () => {
        test('allows "general"', () => {
            expect(isAgeRestricted('general')).toBe(false);
        });

        test('allows "safe"', () => {
            expect(isAgeRestricted('safe')).toBe(false);
        });

        test('allows "everyone"', () => {
            expect(isAgeRestricted('everyone')).toBe(false);
        });

        test('allows "PG-13"', () => {
            expect(isAgeRestricted('PG-13')).toBe(false);
        });
    });

    describe('allows missing/empty values (fail open)', () => {
        test('allows empty string', () => {
            expect(isAgeRestricted('')).toBe(false);
        });

        test('allows null', () => {
            expect(isAgeRestricted(null)).toBe(false);
        });

        test('allows undefined', () => {
            expect(isAgeRestricted(undefined)).toBe(false);
        });
    });

    describe('does NOT match partial RTA pattern (regex precision)', () => {
        test('allows partial RTA "RTA-5042"', () => {
            expect(isAgeRestricted('RTA-5042')).toBe(false);
        });

        test('allows partial RTA "RTA-5042-1996"', () => {
            expect(isAgeRestricted('RTA-5042-1996')).toBe(false);
        });

        test('allows partial RTA "RTA-5042-1996-1400"', () => {
            expect(isAgeRestricted('RTA-5042-1996-1400')).toBe(false);
        });

        test('allows partial RTA "RTA-5042-1996-1400-1577"', () => {
            expect(isAgeRestricted('RTA-5042-1996-1400-1577')).toBe(false);
        });

        test('allows "RTA" alone (might appear in article text)', () => {
            expect(isAgeRestricted('RTA')).toBe(false);
        });

        test('allows text mentioning RTA casually', () => {
            expect(isAgeRestricted('RTA label is used for age rating')).toBe(false);
        });
    });

    describe('handles edge cases gracefully (fail open)', () => {
        test('allows number input', () => {
            expect(isAgeRestricted(123)).toBe(false);
        });

        test('allows boolean input', () => {
            expect(isAgeRestricted(true)).toBe(false);
        });

        test('allows object input', () => {
            expect(isAgeRestricted({})).toBe(false);
        });

        test('allows array input', () => {
            expect(isAgeRestricted(['adult'])).toBe(false);
        });
    });
});

describe('RTA_LABEL_PATTERN constant', () => {
    test('is the correct lowercase pattern', () => {
        expect(RTA_LABEL_PATTERN).toBe('rta-5042-1996-1400-1577-rta');
    });

    test('is lowercase (for case-insensitive matching)', () => {
        expect(RTA_LABEL_PATTERN).toBe(RTA_LABEL_PATTERN.toLowerCase());
    });
});
