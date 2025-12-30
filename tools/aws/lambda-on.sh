#!/bin/bash
# Enable Lambda by removing concurrency restriction
# Usage: ./lambda-on.sh [function-name]

FUNCTION_NAME="${1:-aletheia-harvester}"

aws lambda delete-function-concurrency --function-name "$FUNCTION_NAME" 2>/dev/null
echo "✓ Lambda ON (unrestricted)"
