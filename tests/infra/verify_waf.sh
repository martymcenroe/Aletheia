#!/bin/bash
# tests/infra/verify_waf.sh
# Automated WAF verification - NO VIBES TESTING
#
# Usage:
#   CLOUDFRONT_URL=https://d123.cloudfront.net ./verify_waf.sh
#   ./verify_waf.sh --test-rate-limit    # Also test rate limiting (slow)
#   ./verify_waf.sh --help
#
# Exit codes:
#   0 = all tests pass
#   1 = test failure
#
# LLD: docs/1095-security-hardening.md

set -e

# Configuration
CLOUDFRONT_URL="${CLOUDFRONT_URL:-}"
RATE_LIMIT="${RATE_LIMIT:-100}"
VERBOSE="${VERBOSE:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
TEST_RATE_LIMIT=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --test-rate-limit) TEST_RATE_LIMIT=true; shift ;;
        --verbose|-v) VERBOSE=true; shift ;;
        --help|-h)
            echo "Usage: CLOUDFRONT_URL=https://... $0 [options]"
            echo ""
            echo "Options:"
            echo "  --test-rate-limit  Also test rate limiting (sends many requests)"
            echo "  --verbose, -v      Show full response bodies"
            echo ""
            echo "Environment:"
            echo "  CLOUDFRONT_URL     CloudFront distribution URL (required)"
            echo "  RATE_LIMIT         Expected rate limit (default: 100)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Validate configuration
if [ -z "$CLOUDFRONT_URL" ]; then
    # Try to load from config file (portable temp directory)
    SCRIPT_TMPDIR="$HOME/tmp/aletheia-waf"
    if [ -f "$SCRIPT_TMPDIR/aletheia-waf-config.env" ]; then
        # shellcheck disable=SC1091 # Config file is generated at runtime
        source "$SCRIPT_TMPDIR/aletheia-waf-config.env"
    fi
fi

if [ -z "$CLOUDFRONT_URL" ]; then
    echo -e "${RED}ERROR: CLOUDFRONT_URL not set${NC}"
    echo ""
    echo "Set it via:"
    echo "  export CLOUDFRONT_URL=https://d123456789.cloudfront.net"
    echo ""
    echo "Or run waf-setup.sh first (saves config to /tmp/aletheia-waf-config.env)"
    exit 1
fi

echo "=============================================="
echo "WAF Verification Suite"
echo "=============================================="
echo "Target: $CLOUDFRONT_URL"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0

# Helper function for test results
pass() {
    echo -e "${GREEN}PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
    echo -e "${RED}FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

warn() {
    echo -e "${YELLOW}WARN${NC}: $1"
}

# Valid test payload (Lambda expects "text" field, not "word")
VALID_PAYLOAD='{"text":"test","url":"https://example.com","title":"Test Page","context":"This is test context for verification."}'

# ============================================
# Test 010: Missing header should return 403
# ============================================
echo -n "Test 010: Request without header... "

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$VALID_PAYLOAD" \
    "$CLOUDFRONT_URL" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" -eq 403 ]; then
    pass "Got 403 Forbidden (WAF blocked missing header)"
else
    fail "Expected 403, got $HTTP_CODE"
    if [ "$VERBOSE" == "true" ]; then
        echo "  Response body: $BODY"
    fi
fi

# ============================================
# Test 020: Valid header should return 200
# ============================================
echo -n "Test 020: Request with valid header... "

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -H "X-Aletheia-Client-Version: 1.0" \
    -d "$VALID_PAYLOAD" \
    "$CLOUDFRONT_URL" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" -eq 200 ]; then
    pass "Got 200 OK (request processed)"
else
    fail "Expected 200, got $HTTP_CODE"
    if [ "$VERBOSE" == "true" ]; then
        echo "  Response body: $BODY"
    fi
fi

# ============================================
# Test 050: Invalid version format should return 403
# ============================================
echo -n "Test 050: Invalid version (0.9)... "

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -H "X-Aletheia-Client-Version: 0.9" \
    -d "$VALID_PAYLOAD" \
    "$CLOUDFRONT_URL" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" -eq 403 ]; then
    pass "Got 403 Forbidden (WAF blocked invalid version)"
else
    fail "Expected 403, got $HTTP_CODE"
fi

# ============================================
# Test 051: Future version should pass
# ============================================
echo -n "Test 051: Future version (1.99)... "

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -H "X-Aletheia-Client-Version: 1.99" \
    -d "$VALID_PAYLOAD" \
    "$CLOUDFRONT_URL" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" -eq 200 ]; then
    pass "Got 200 OK (future versions allowed)"
else
    fail "Expected 200, got $HTTP_CODE"
fi

# ============================================
# Test 030: Rate limit (optional, slow)
# ============================================
if [ "$TEST_RATE_LIMIT" == "true" ]; then
    echo ""
    echo "Test 030: Rate limit enforcement..."
    echo "  Sending $((RATE_LIMIT + 5)) requests to trigger limit..."
    echo "  (This may take a minute)"

    BLOCKED=false
    for i in $(seq 1 $((RATE_LIMIT + 5))); do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -H "X-Aletheia-Client-Version: 1.0" \
            -d "$VALID_PAYLOAD" \
            "$CLOUDFRONT_URL")

        # Progress indicator
        if [ $((i % 10)) -eq 0 ]; then
            echo -n "  Sent $i requests..."
            if [ "$HTTP_CODE" -eq 429 ]; then
                echo " Rate limited at request $i"
                BLOCKED=true
                break
            else
                echo " (HTTP $HTTP_CODE)"
            fi
        fi

        if [ "$HTTP_CODE" -eq 429 ]; then
            echo "  Rate limited at request $i"
            BLOCKED=true
            break
        fi

        # Small delay to avoid overwhelming
        sleep 0.1
    done

    if [ "$BLOCKED" == "true" ]; then
        pass "Rate limiting enforced"
    else
        fail "Rate limiting NOT enforced after $((RATE_LIMIT + 5)) requests"
        warn "Note: WAF rate limits have a 30-second aggregation window"
    fi
fi

# ============================================
# Summary
# ============================================
echo ""
echo "=============================================="
echo "Summary"
echo "=============================================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ "$TESTS_FAILED" -gt 0 ]; then
    echo -e "${RED}=== VERIFICATION FAILED ===${NC}"
    exit 1
else
    echo -e "${GREEN}=== ALL TESTS PASSED ===${NC}"
    exit 0
fi
