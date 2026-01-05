#!/bin/bash
# tools/policy_check.sh - Project Policy Compliance Check
#
# Enforces PRIMARY DIRECTIVES that are too important for manual review.
# Run as pre-commit hook and in CI.
#
# Reference: docs/9000-lessons-learned.md (2026-01-04 entry)
# "If a policy is important enough to be an ADR, it's important enough to be a CI gate."

set -e

ERRORS=0

echo "=== Aletheia Policy Compliance Check ==="

# -----------------------------------------------------------------------------
# POLICY 1: No <all_urls> in manifest.json (ADR 0201 - Privacy First)
# -----------------------------------------------------------------------------
echo -n "Checking ADR 0201 (<all_urls> forbidden)... "

if grep -q '"<all_urls>"' extensions/chrome/manifest.json 2>/dev/null; then
    echo "FAIL"
    echo "  ERROR: extensions/chrome/manifest.json contains '<all_urls>'"
    echo "  Violation: ADR 0201 - Privacy-First Extension Permissions"
    echo "  Fix: Use activeTab permission instead"
    ERRORS=$((ERRORS + 1))
else
    echo "OK"
fi

if grep -q '"<all_urls>"' extensions/firefox/manifest.json 2>/dev/null; then
    echo "  ERROR: extensions/firefox/manifest.json contains '<all_urls>'"
    echo "  Violation: ADR 0201 - Privacy-First Extension Permissions"
    ERRORS=$((ERRORS + 1))
fi

# -----------------------------------------------------------------------------
# POLICY 2: No pip install in scripts (CLAUDE.md - Use poetry add)
# -----------------------------------------------------------------------------
echo -n "Checking for 'pip install' in scripts... "

PIP_VIOLATIONS=$(grep -rn "pip install" *.sh scripts/ tools/*.sh 2>/dev/null | grep -v "policy_check.sh" || true)
if [ -n "$PIP_VIOLATIONS" ]; then
    echo "FAIL"
    echo "  ERROR: Found 'pip install' in scripts (use 'poetry add' instead):"
    echo "$PIP_VIOLATIONS" | sed 's/^/    /'
    ERRORS=$((ERRORS + 1))
else
    echo "OK"
fi

# -----------------------------------------------------------------------------
# POLICY 3: No git reset in scripts (CLAUDE.md - Use git revert)
# -----------------------------------------------------------------------------
echo -n "Checking for 'git reset' in scripts... "

RESET_VIOLATIONS=$(grep -rn "git reset" *.sh scripts/ tools/*.sh .github/ 2>/dev/null | grep -v "policy_check.sh" || true)
if [ -n "$RESET_VIOLATIONS" ]; then
    echo "FAIL"
    echo "  ERROR: Found 'git reset' in scripts (use 'git revert' instead):"
    echo "$RESET_VIOLATIONS" | sed 's/^/    /'
    ERRORS=$((ERRORS + 1))
else
    echo "OK"
fi

# -----------------------------------------------------------------------------
# POLICY 4: No git push --force in scripts (CLAUDE.md - Destroys collaboration)
# -----------------------------------------------------------------------------
echo -n "Checking for 'git push --force' in scripts... "

FORCE_VIOLATIONS=$(grep -rn "git push.*--force\|git push.*-f" *.sh scripts/ tools/*.sh .github/ 2>/dev/null | grep -v "policy_check.sh" || true)
if [ -n "$FORCE_VIOLATIONS" ]; then
    echo "FAIL"
    echo "  ERROR: Found 'git push --force' in scripts:"
    echo "$FORCE_VIOLATIONS" | sed 's/^/    /'
    ERRORS=$((ERRORS + 1))
else
    echo "OK"
fi

# -----------------------------------------------------------------------------
# POLICY 5: No git clean -fd in scripts (CLAUDE.md - Permanent data loss)
# -----------------------------------------------------------------------------
echo -n "Checking for 'git clean -fd' in scripts... "

CLEAN_VIOLATIONS=$(grep -rn "git clean.*-fd\|git clean.*-f" *.sh scripts/ tools/*.sh .github/ 2>/dev/null | grep -v "policy_check.sh" || true)
if [ -n "$CLEAN_VIOLATIONS" ]; then
    echo "FAIL"
    echo "  ERROR: Found 'git clean -fd' in scripts:"
    echo "$CLEAN_VIOLATIONS" | sed 's/^/    /'
    ERRORS=$((ERRORS + 1))
else
    echo "OK"
fi

# -----------------------------------------------------------------------------
# POLICY 6: No hardcoded AWS credentials (Security)
# -----------------------------------------------------------------------------
echo -n "Checking for hardcoded AWS credentials... "

AWS_VIOLATIONS=$(grep -rn "AKIA[0-9A-Z]\{16\}" src/ tests/ tools/ extensions/ 2>/dev/null || true)
if [ -n "$AWS_VIOLATIONS" ]; then
    echo "FAIL"
    echo "  ERROR: Found potential AWS Access Key ID:"
    echo "$AWS_VIOLATIONS" | sed 's/^/    /'
    ERRORS=$((ERRORS + 1))
else
    echo "OK"
fi

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------
echo ""
if [ $ERRORS -gt 0 ]; then
    echo "=== POLICY CHECK FAILED: $ERRORS violation(s) found ==="
    echo "See docs/0201-ADR-privacy-first-permissions.md and CLAUDE.md for policies."
    exit 1
else
    echo "=== POLICY CHECK PASSED ==="
    exit 0
fi
