#!/bin/bash
set -e

# Configuration
APP_NAME="Aletheia"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TABLE_NAME="${APP_NAME}AgentState"
ROLE_NAME="${APP_NAME}LambdaRole"
FUNC_NAME="${APP_NAME}Agent"

echo "=== Provisioning Infrastructure for $APP_NAME ($REGION) ==="

# 1. DynamoDB Table
echo "[1/3] Checking DynamoDB Table: $TABLE_NAME..."
if aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "  -> Table exists."
else
    echo "  -> Creating table..."
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions AttributeName=thread_id,AttributeType=S AttributeName=checkpoint_id,AttributeType=S \
        --key-schema AttributeName=thread_id,KeyType=HASH AttributeName=checkpoint_id,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    
    echo "  -> Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
fi

# 2. IAM Role
echo "[2/3] Checking IAM Role: $ROLE_NAME..."
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}'

if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    echo "  -> Role exists."
else
    echo "  -> Creating role..."
    aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "$TRUST_POLICY"
fi

echo "  -> Attaching policies..."
aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

# Inline Policy for DynamoDB + Bedrock
aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name "${APP_NAME}Access" --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/'"$TABLE_NAME"'"
        },
        {
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": "*"
        }
    ]
}'
sleep 5 # Propagate

# 3. Lambda Function
echo "[3/3] Checking Lambda Function: $FUNC_NAME..."
if aws lambda get-function --function-name "$FUNC_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "  -> Function exists."
else
    echo "  -> Creating placeholder function..."
    echo "def lambda_handler(event, context): return 'Init'" > lambda_function_init.py
    
    # FIX: Create a temporary python script for zipping
    cat << 'PY_SCRIPT' > zipper.py
import zipfile
with zipfile.ZipFile('init.zip', 'w') as z:
    z.write('lambda_function_init.py')
PY_SCRIPT
    
    python zipper.py
    
    aws lambda create-function \
        --function-name "$FUNC_NAME" \
        --runtime python3.12 \
        --role "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}" \
        --handler lambda_function_init.lambda_handler \
        --zip-file fileb://init.zip \
        --architectures arm64 \
        --timeout 60 \
        --region "$REGION"
        
    rm init.zip lambda_function_init.py zipper.py
fi

echo "=== Provisioning Complete ==="
