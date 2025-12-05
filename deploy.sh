#!/bin/bash
set -e

FUNC_NAME="AletheiaAgent"
ZIP_FILE="function.zip"
TARGET_FILE="lambda_harvester_function.py"
HANDLER_NAME="lambda_harvester_function.lambda_handler"
REGION="us-east-1"

echo "=== Deploying Harvester ($TARGET_FILE) ==="

# 1. Zip ONLY the specific harvester file
rm -f "$ZIP_FILE"
cat << PY_SCRIPT > zipper.py
import zipfile
with zipfile.ZipFile('$ZIP_FILE', 'w', zipfile.ZIP_DEFLATED) as z:
    z.write('$TARGET_FILE')
PY_SCRIPT
python zipper.py
rm zipper.py

# 2. Update Configuration (Tell AWS to use the new filename)
# We do this first to ensure the runtime knows where to look
echo "-> Updating Handler to: $HANDLER_NAME"
aws lambda update-function-configuration \
    --function-name "$FUNC_NAME" \
    --handler "$HANDLER_NAME" \
    --region "$REGION" >/dev/null

# 3. Update Code
echo "-> Uploading Code..."
aws lambda update-function-code \
    --function-name "$FUNC_NAME" \
    --zip-file fileb://"$ZIP_FILE" \
    --region "$REGION" \
    --publish >/dev/null

echo "=== Deployment Success ==="
rm -f "$ZIP_FILE"
