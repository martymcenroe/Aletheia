#!/bin/bash
# Show Lambda concurrency status with clear ON/OFF indication
# Usage: ./lambda-status.sh [function-name]

FUNCTION_NAME="${1:-AletheiaAgent}"

result=$(aws lambda get-function-concurrency --function-name "$FUNCTION_NAME" 2>/dev/null)

if [ -z "$result" ]; then
    echo "✓ Lambda ON (unrestricted concurrency)"
else
    concurrency=$(echo "$result" | grep -o '"ReservedConcurrentExecutions": [0-9]*' | grep -o '[0-9]*')
    if [ "$concurrency" = "0" ]; then
        echo "✗ Lambda OFF (concurrency=0)"
    else
        echo "⚡ Lambda ON (reserved=$concurrency)"
    fi
fi
