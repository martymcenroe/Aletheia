#!/bin/bash
set -e

APP_NAME="Aletheia"
FUNC_NAME="${APP_NAME}Agent"
REGION="us-east-1"
BUILD_DIR="build_package"
ZIP_FILE="function.zip"

echo "=== Deploying $APP_NAME to Lambda ($REGION) ==="

# 1. Cleanup previous build
rm -rf "$BUILD_DIR" "$ZIP_FILE" requirements.txt
mkdir -p "$BUILD_DIR"

# 2. Export Dependencies (Poetry)
echo "-> Exporting dependencies..."
poetry export -f requirements.txt --output requirements.txt --without-hashes

# 3. Install Dependencies
echo "-> Installing dependencies to build dir..."
pip install -r requirements.txt -t "$BUILD_DIR" --upgrade --quiet

# 4. Copy Source Code
echo "-> Copying application files..."
# REMOVED: guardrails.py (Not yet merged to main)
cp lambda_function.py agent.py checkpointer.py compliance.py "$BUILD_DIR/"

# 5. Zip Package
echo "-> Creating Deployment Package..."
cat << 'PY_SCRIPT' > zipper.py
import zipfile
import os

build_dir = "build_package"
zip_name = "function.zip"

with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(build_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, build_dir)
            z.write(file_path, arcname)
PY_SCRIPT

python zipper.py
rm zipper.py

# 6. Deploy to AWS
echo "-> Uploading to AWS Lambda ($FUNC_NAME)..."
aws lambda update-function-code \
    --function-name "$FUNC_NAME" \
    --zip-file fileb://"$ZIP_FILE" \
    --region "$REGION" \
    --publish

# 7. Cleanup
rm -rf "$BUILD_DIR" "$ZIP_FILE" requirements.txt
echo "=== Deployment Success ==="
