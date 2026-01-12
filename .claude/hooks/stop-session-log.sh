#!/bin/bash
# Stop Hook: Session Log Guarantee
#
# Ensures session log is appended when Claude Code session ends.
# This is a STOP hook - runs when the session terminates.
#
# Note: Stop hooks run with limited context. We append a minimal
# entry that can be enriched by /cleanup if run beforehand.

set -e

project_root="/c/Users/mcwiz/Projects/Aletheia"

# Check if session log tool exists
if [ ! -f "$project_root/tools/append_session_log.py" ]; then
    echo "[Stop Hook] Session log tool not found, skipping" >&2
    exit 0
fi

# Check if we're in the Aletheia project
if [ ! -d "$project_root/docs/session-logs" ]; then
    echo "[Stop Hook] Not in Aletheia project, skipping" >&2
    exit 0
fi

# Get today's date for the log file
today=$(powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd'" | tr -d '\r')
log_file="$project_root/docs/session-logs/$today.md"

# Check if there's already a recent entry (within ~2 minutes)
# This prevents duplicate entries if /cleanup was already run
if [ -f "$log_file" ]; then
    last_entry=$(tail -20 "$log_file" | grep -oE "[0-9]{2}:[0-9]{2} CT" | tail -1 || echo "")
    if [ -n "$last_entry" ]; then
        current_time=$(powershell.exe -Command "Get-Date -Format 'HH:mm'" | tr -d '\r')
        # Extract hours and minutes
        last_hour="${last_entry:0:2}"
        last_min="${last_entry:3:2}"
        current_hour="${current_time:0:2}"
        current_min="${current_time:3:2}"
        # Convert to total minutes for comparison
        last_total=$((10#$last_hour * 60 + 10#$last_min))
        current_total=$((10#$current_hour * 60 + 10#$current_min))
        diff=$((current_total - last_total))
        # Handle negative (midnight wrap) by taking absolute value
        if [ $diff -lt 0 ]; then
            diff=$((-diff))
        fi
        # Skip if within 2 minutes
        if [ $diff -le 2 ]; then
            echo "[Stop Hook] Recent session log entry exists ($diff min ago), skipping" >&2
            exit 0
        fi
    fi
fi

# Append minimal session log entry
echo "[Stop Hook] Appending session log entry..." >&2

poetry run python "$project_root/tools/append_session_log.py" \
    --model "Claude Opus 4.5" \
    --summary "Session ended (auto-logged by stop hook)" \
    --created "None" \
    --closed "None" \
    --next "Run /cleanup for detailed summary" \
    2>&1 || echo "[Stop Hook] Failed to append session log" >&2

echo "[Stop Hook] Session log updated" >&2
exit 0
