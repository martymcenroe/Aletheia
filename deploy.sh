#!/bin/bash
set -e

# Naked Python Architecture Deployment
# See: docs/1113-naked-python-architecture.md

FUNC_NAME="AletheiaAgent"
ZIP_FILE="function.zip"
HANDLER_NAME="src.lambda_function.lambda_handler"
REGION="us-east-1"

echo "=== Deploying Naked Python Orchestrator ==="

# 0. Ensure denylist is fresh
DENYLIST_PATH="src/guardrails/resources/denylist.json"
if [ ! -f "$DENYLIST_PATH" ]; then
    echo "-> Denylist not found. Fetching from Wikipedia..."
    python tools/fetch_denylist.py
    if [ ! -f "$DENYLIST_PATH" ]; then
        echo "ERROR: Failed to create denylist.json"
        exit 1
    fi
else
    echo "-> Denylist exists: $DENYLIST_PATH"
    # Show age of denylist
    DENYLIST_AGE=$(python -c "import json; d=json.load(open('$DENYLIST_PATH')); print(d.get('updated', 'unknown'))")
    echo "   Last updated: $DENYLIST_AGE"
fi

# Verify denylist has content
TERM_COUNT=$(python -c "import json; d=json.load(open('$DENYLIST_PATH')); print(len(d.get('terms', [])))")
if [ "$TERM_COUNT" -lt 500 ]; then
    echo "WARNING: Denylist has only $TERM_COUNT terms (expected 500+)"
    echo "         Consider running: python tools/fetch_denylist.py"
fi
echo "   Term count: $TERM_COUNT"

# 1. Create deployment package
# MUST include lambda_function.py AND src/ directory
rm -f "$ZIP_FILE"

cat << 'PY_SCRIPT' > zipper.py
import zipfile
import os

with zipfile.ZipFile('function.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    # Recursively add src/ directory (includes lambda_function.py and all modules)
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py') or file.endswith('.json'):
                filepath = os.path.join(root, file)
                z.write(filepath)
                print(f"  Added: {filepath}")

print(f"Created: function.zip")
PY_SCRIPT

echo "-> Building deployment package..."
python zipper.py
rm zipper.py

# 2. Verify package contents
echo "-> Verifying package structure..."
python -c "
import zipfile
with zipfile.ZipFile('function.zip', 'r') as z:
    files = z.namelist()
    assert 'src/lambda_function.py' in files, 'Missing src/lambda_function.py!'
    assert any('src/guardrails' in f for f in files), 'Missing src/guardrails!'
    assert 'src/guardrails/resources/denylist.json' in files, 'Missing denylist.json!'
    print(f'  Package contains {len(files)} files')
    print('  ✓ src/lambda_function.py')
    print('  ✓ src/guardrails/')
    print('  ✓ denylist.json')
"

# 3. Update Configuration (Handler)
echo "-> Updating Handler to: $HANDLER_NAME"
aws lambda update-function-configuration \
    --function-name "$FUNC_NAME" \
    --handler "$HANDLER_NAME" \
    --timeout 60 \
    --memory-size 256 \
    --environment "Variables={ALETHEIA_ENV=dev,DYNAMODB_TABLE=AletheiaAgentState}" \
    --region "$REGION" >/dev/null

# Wait for config update to complete
echo "-> Waiting for configuration update..."
aws lambda wait function-updated --function-name "$FUNC_NAME" --region "$REGION"

# 4. Update Code
echo "-> Uploading Code..."
aws lambda update-function-code \
    --function-name "$FUNC_NAME" \
    --zip-file fileb://"$ZIP_FILE" \
    --region "$REGION" \
    --publish >/dev/null

# Wait for code update to complete
echo "-> Waiting for deployment..."
aws lambda wait function-updated --function-name "$FUNC_NAME" --region "$REGION"

# 5. Get Function URL for verification
FUNC_URL=$(aws lambda get-function-url-config --function-name "$FUNC_NAME" --region "$REGION" --query 'FunctionUrl' --output text 2>/dev/null || echo "NOT_CONFIGURED")

echo "=== Deployment Complete ==="
echo "Function: $FUNC_NAME"
echo "Handler:  $HANDLER_NAME"
echo "URL:      $FUNC_URL"

rm -f "$ZIP_FILE"
