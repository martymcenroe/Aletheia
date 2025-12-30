#!/bin/bash
# Disable Lambda by setting concurrency to 0
# Usage: ./lambda-off.sh [function-name]

FUNCTION_NAME="${1:-aletheia-harvester}"

aws lambda put-function-concurrency --function-name "$FUNCTION_NAME" --reserved-concurrent-executions 0 > /dev/null
echo "✓ Lambda OFF (concurrency=0)"
