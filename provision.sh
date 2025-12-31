#!/bin/bash
set -e

APP_NAME="Aletheia"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TABLE_NAME="${APP_NAME}AgentState"
ROLE_NAME="${APP_NAME}LambdaRole"
FUNC_NAME="${APP_NAME}Agent"

echo "=== Provisioning Infrastructure for $APP_NAME ($REGION) ==="

# 1. DynamoDB Table
echo "[1/4] Checking DynamoDB Table..."
if ! aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" >/dev/null 2>&1; then
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions AttributeName=thread_id,AttributeType=S AttributeName=checkpoint_id,AttributeType=S \
        --key-schema AttributeName=thread_id,KeyType=HASH AttributeName=checkpoint_id,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
fi

# 2. IAM Role
echo "[2/4] Checking IAM Role..."
TRUST_POLICY='{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": { "Service": "lambda.amazonaws.com" },"Action": "sts:AssumeRole"}]}'

if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "$TRUST_POLICY"
fi

aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name "${APP_NAME}Access" --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Allow","Action": ["dynamodb:PutItem","dynamodb:GetItem","dynamodb:UpdateItem","dynamodb:DeleteItem","dynamodb:Query","dynamodb:Scan"],"Resource": "arn:aws:dynamodb:*:*:table/'"$TABLE_NAME"'"},
        {"Effect": "Allow","Action": ["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],"Resource": "*"}
    ]
}'
sleep 5

# 3. Lambda Function (x86_64 Enforced)
echo "[3/4] Creating Lambda Function..."
echo "def lambda_handler(event, context): return 'Init'" > lambda_function.py
cat << 'PY_SCRIPT' > zipper.py
import zipfile
with zipfile.ZipFile('init.zip', 'w') as z:
    z.write('lambda_function.py')
PY_SCRIPT
python zipper.py

if ! aws lambda get-function --function-name "$FUNC_NAME" --region "$REGION" >/dev/null 2>&1; then
    aws lambda create-function \
        --function-name "$FUNC_NAME" \
        --runtime python3.12 \
        --role "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}" \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://init.zip \
        --architectures x86_64 \
        --timeout 60 \
        --environment "Variables={ALETHEIA_ENV=dev}" \
        --region "$REGION"
fi
rm init.zip lambda_function.py zipper.py

# 4. Function URL
echo "[4/4] Configuring URL..."
aws lambda create-function-url-config --function-name "$FUNC_NAME" --auth-type NONE --cors "AllowOrigins=['*'],AllowMethods=['POST'],AllowHeaders=['Content-Type']" --region "$REGION" 2>/dev/null || true
aws lambda add-permission --function-name "$FUNC_NAME" --action lambda:InvokeFunctionUrl --statement-id FunctionURLAllowPublicAccess --principal "*" --function-url-auth-type NONE --region "$REGION" 2>/dev/null || true

FUNC_URL=$(aws lambda get-function-url-config --function-name "$FUNC_NAME" --region "$REGION" --query 'FunctionUrl' --output text)
echo "=== Provisioning Complete ==="
echo "NEW FUNCTION URL: $FUNC_URL"
