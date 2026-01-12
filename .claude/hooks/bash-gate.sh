#!/bin/bash
# Bash Command Gate Hook
#
# BLOCK: Bash commands containing banned patterns (&&, |, ;)
# These patterns trigger permission approval dialogs.
#
# Environment: $CLAUDE_TOOL_INPUT_COMMAND contains the bash command

set -e

command="$CLAUDE_TOOL_INPUT_COMMAND"

# Skip empty commands
if [ -z "$command" ]; then
    exit 0
fi

violations=""

# Check for && (chain operator)
if [[ "$command" == *"&&"* ]]; then
    violations="${violations}
  - Found: &&
    Issue: Chain operator triggers permission dialogs
    Fix: Split into separate Bash calls or use git -C /path"
fi

# Check for | (pipe)
if [[ "$command" == *"|"* ]]; then
    violations="${violations}
  - Found: |
    Issue: Pipe operator triggers permission dialogs
    Fix: Use dedicated tools (Read, Grep, Glob) instead of piping"
fi

# Check for ; (command separator)
if [[ "$command" == *";"* ]]; then
    violations="${violations}
  - Found: ;
    Issue: Command separator triggers permission dialogs
    Fix: Split into separate parallel Bash calls"
fi

# Check for cd at start (should use absolute paths)
if [[ "$command" =~ ^cd[[:space:]] ]]; then
    violations="${violations}
  - Found: cd at start
    Issue: Directory change followed by command should use absolute paths
    Fix: Use 'git -C /path' or absolute paths directly"
fi

# If violations found, block the command
if [ -n "$violations" ]; then
    echo "" >&2
    echo "========================================" >&2
    echo "BLOCKED: Bash Command Gate Violation" >&2
    echo "========================================" >&2
    echo "" >&2
    echo "Command: $command" >&2
    echo "" >&2
    echo "Violations:$violations" >&2
    echo "" >&2
    echo "REQUIRED PATTERN:" >&2
    echo "  - One command per Bash tool call" >&2
    echo "  - Use absolute paths (e.g., /c/Users/mcwiz/Projects/...)" >&2
    echo "  - Use 'git -C /path' instead of 'cd /path && git'" >&2
    echo "  - Multiple independent commands? Use parallel Bash calls" >&2
    echo "" >&2
    echo "See CLAUDE.md 'BASH COMMAND GATE' section." >&2
    echo "" >&2
    exit 1
fi

# No violations, allow command
exit 0
