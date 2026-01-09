#!/bin/bash
# tools/report_gate.sh - PRE-MERGE GATE Enforcement
#
# Blocks commits on issue branches that don't include implementation reports.
# This is a technical backstop for the PRE-MERGE GATE documented in CLAUDE.md.
#
# Reference: docs/9000-lessons-learned.md (2026-01-09 entry)
# "The gate is advisory, not blocking. Documentation doesn't change behavior."
#
# Logic:
# 1. If on issue branch (starts with number, e.g., "126-feature-name")
# 2. AND staging implementation files (*.py in src/)
# 3. THEN require docs/reports/{N}/implementation-report.md AND test-report.md
#    to either exist on disk OR be staged in this commit

set -e

# Get current branch
BRANCH=$(git branch --show-current 2>/dev/null || echo "")

# If no branch (detached HEAD) or on main, allow
if [ -z "$BRANCH" ] || [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    exit 0
fi

# Extract issue number from start of branch name (e.g., "126-feature" -> "126")
ISSUE_NUM=$(echo "$BRANCH" | grep -oE '^[0-9]+' | head -1)

# If branch doesn't start with a number, allow (not an issue branch)
if [ -z "$ISSUE_NUM" ]; then
    exit 0
fi

# Check if we're staging implementation files (src/*.py)
STAGED_IMPL=$(git diff --cached --name-only | grep -E '^src/.*\.py$' || true)

# If no implementation files staged, allow (just docs/config changes)
if [ -z "$STAGED_IMPL" ]; then
    exit 0
fi

# We're on an issue branch AND staging implementation files
# Now check for reports

IMPL_REPORT="docs/reports/$ISSUE_NUM/implementation-report.md"
TEST_REPORT="docs/reports/$ISSUE_NUM/test-report.md"

# Check if reports exist on disk OR are being staged
IMPL_EXISTS=false
TEST_EXISTS=false

# Check disk
if [ -f "$IMPL_REPORT" ]; then
    IMPL_EXISTS=true
fi
if [ -f "$TEST_REPORT" ]; then
    TEST_EXISTS=true
fi

# Check staged files (in case reports are being added in this commit)
if git diff --cached --name-only | grep -q "^$IMPL_REPORT$"; then
    IMPL_EXISTS=true
fi
if git diff --cached --name-only | grep -q "^$TEST_REPORT$"; then
    TEST_EXISTS=true
fi

# Report results
ERRORS=0

echo "=== PRE-MERGE GATE CHECK ==="
echo "Branch: $BRANCH (Issue #$ISSUE_NUM)"
echo "Implementation files staged: $(echo "$STAGED_IMPL" | wc -l | tr -d ' ') file(s)"
echo ""

echo -n "Checking $IMPL_REPORT... "
if [ "$IMPL_EXISTS" = true ]; then
    echo "OK"
else
    echo "MISSING"
    ERRORS=$((ERRORS + 1))
fi

echo -n "Checking $TEST_REPORT... "
if [ "$TEST_EXISTS" = true ]; then
    echo "OK"
else
    echo "MISSING"
    ERRORS=$((ERRORS + 1))
fi

echo ""

if [ $ERRORS -gt 0 ]; then
    echo "=== PRE-MERGE GATE FAILED ==="
    echo ""
    echo "You are committing implementation code without reports."
    echo ""
    echo "Required before commit:"
    echo "  1. Create $IMPL_REPORT"
    echo "  2. Create $TEST_REPORT"
    echo "  3. Stage reports: git add docs/reports/$ISSUE_NUM/"
    echo "  4. Present for Gemini review"
    echo "  5. After approval: commit"
    echo ""
    echo "See CLAUDE.md 'PRE-MERGE REVIEW GATE' for full protocol."
    exit 1
else
    echo "=== PRE-MERGE GATE PASSED ==="
    exit 0
fi
