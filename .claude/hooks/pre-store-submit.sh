#!/bin/bash
# Pre-Store Submit Hook: Build Freshness Gate
#
# BLOCK: Store submission commands if artifacts are stale
# Enforces 0828-audit-build-artifact-freshness.md automatically.
#
# Environment: $CLAUDE_TOOL_INPUT_COMMAND contains the bash command

set -e

command="$CLAUDE_TOOL_INPUT_COMMAND"

# Detect store submission commands
is_store_command=false

# Chrome Web Store
if [[ "$command" =~ chrome-webstore-upload|webstore|"Chrome Web Store" ]]; then
    is_store_command=true
fi

# Firefox Add-ons
if [[ "$command" =~ web-ext\ sign|addons\.mozilla|"Firefox Add-ons"|amo-upload ]]; then
    is_store_command=true
fi

# GitHub Release with extension artifacts
if [[ "$command" =~ gh\ release.*aletheia.*\.zip ]]; then
    is_store_command=true
fi

# Generic upload patterns
if [[ "$command" =~ upload.*extension|submit.*extension|publish.*extension ]]; then
    is_store_command=true
fi

# If not a store command, allow
if [ "$is_store_command" = false ]; then
    exit 0
fi

# Run freshness check
echo "[Hook] Checking build artifact freshness..." >&2

# Get the project root (where this hook lives)
project_root="/c/Users/mcwiz/Projects/Aletheia"

# Run the check
result=$(poetry run python "$project_root/tools/check_artifact_freshness.py" 2>&1) || true

if [[ "$result" == *"STALE"* ]] || [[ "$result" == *"MISSING"* ]]; then
    echo "" >&2
    echo "========================================" >&2
    echo "BLOCKED: Stale Build Artifacts" >&2
    echo "========================================" >&2
    echo "" >&2
    echo "$result" >&2
    echo "" >&2
    echo "----------------------------------------" >&2
    echo "FIX: Rebuild artifacts before submission" >&2
    echo "" >&2
    echo "  poetry run python tools/build_release.py" >&2
    echo "" >&2
    echo "Then retry the store submission." >&2
    echo "----------------------------------------" >&2
    echo "" >&2
    exit 1
fi

echo "[Hook] Artifacts are FRESH. Proceeding with submission." >&2
exit 0
