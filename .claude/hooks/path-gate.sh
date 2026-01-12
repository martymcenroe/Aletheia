#!/bin/bash
# Path Gate Hook
#
# BLOCK: Glob/Read/Write/Edit calls with paths containing tilde (~)
# The tilde character is not supported on Windows and triggers permission prompts.
#
# Environment variables (varies by tool):
#   Glob: $CLAUDE_TOOL_INPUT_PATH
#   Read: $CLAUDE_TOOL_INPUT_FILE_PATH
#   Write: $CLAUDE_TOOL_INPUT_FILE_PATH
#   Edit: $CLAUDE_TOOL_INPUT_FILE_PATH

set -e

# Get the path from whichever variable is set
path="${CLAUDE_TOOL_INPUT_PATH:-$CLAUDE_TOOL_INPUT_FILE_PATH}"

# Debug: write ALL env vars to file to find the right one
debug_file="/c/Users/mcwiz/Projects/Aletheia/tmp/path-gate-debug.log"
echo "$(date): === ALL ENVIRONMENT VARIABLES ===" >> "$debug_file"
env >> "$debug_file"
echo "=== END ENV ===" >> "$debug_file"
echo "---" >> "$debug_file"

# Skip if no path
if [ -z "$path" ]; then
    echo "PATH-GATE DEBUG: empty path, allowing" >&2
    exit 0
fi

# Check for tilde ANYWHERE in the path (not just start)
if [[ "$path" == *"~"* ]]; then
    echo "" >&2
    echo "========================================" >&2
    echo "BLOCKED: Path Gate Violation" >&2
    echo "========================================" >&2
    echo "" >&2
    echo "REJECTED PATH: $path" >&2
    echo "" >&2
    echo "Violation:" >&2
    echo "  - Path starts with ~ (tilde)" >&2
    echo "  - Tilde is NOT supported on Windows" >&2
    echo "  - This WILL trigger permission prompts" >&2
    echo "" >&2
    echo "----------------------------------------" >&2
    echo "CORRECT FORMAT:" >&2
    echo "" >&2

    # Try to construct the correct path
    # Replace ~ with C:\Users\mcwiz and fix slashes
    if [[ "$path" == "~\\"* ]] || [[ "$path" == "~/"* ]]; then
        suffix="${path:2}"  # Remove ~\ or ~/
        # Convert forward slashes to backslashes for Windows
        suffix="${suffix//\//\\}"
        corrected="C:\\Users\\mcwiz\\$suffix"
        echo "  USE: $corrected" >&2
    elif [[ "$path" == "~"* ]]; then
        suffix="${path:1}"  # Remove ~
        suffix="${suffix//\//\\}"
        corrected="C:\\Users\\mcwiz$suffix"
        echo "  USE: $corrected" >&2
    else
        echo "  USE: C:\\Users\\mcwiz\\Projects\\Aletheia\\..." >&2
    fi

    echo "" >&2
    echo "----------------------------------------" >&2
    echo "" >&2
    echo "ACTION REQUIRED: Rewrite path and retry." >&2
    echo "DO NOT STOP. Fix the path and try again." >&2
    echo "" >&2
    exit 1
fi

# No violations, allow
exit 0
