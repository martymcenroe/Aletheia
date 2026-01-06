#!/bin/bash
set -e

APP_NAME="Aletheia"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TABLE_NAME="${APP_NAME}AgentState"
USERS_TABLE="aletheia-users"
ROLE_NAME="${APP_NAME}LambdaRole"
FUNC_NAME="${APP_NAME}Agent"
AUTH_FUNC_NAME="${APP_NAME}Auth"
LINKEDIN_SECRET_NAME="aletheia/linkedin-oauth"

echo "=== Provisioning Infrastructure for $APP_NAME ($REGION) ==="

# 1. DynamoDB Table
echo "[1/5] Checking DynamoDB Table..."
if ! aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" >/dev/null 2>&1; then
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions AttributeName=thread_id,AttributeType=S AttributeName=checkpoint_id,AttributeType=S \
        --key-schema AttributeName=thread_id,KeyType=HASH AttributeName=checkpoint_id,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
fi

# 1.5. DynamoDB TTL (Issue #145: 30-day auto-expiry)
echo "[1.5/5] Checking DynamoDB TTL..."
TTL_STATUS=$(aws dynamodb describe-time-to-live \
    --table-name "$TABLE_NAME" \
    --region "$REGION" \
    --query 'TimeToLiveDescription.TimeToLiveStatus' \
    --output text 2>/dev/null || echo "DISABLED")

if [ "$TTL_STATUS" != "ENABLED" ]; then
    echo "Enabling TTL on $TABLE_NAME..."
    aws dynamodb update-time-to-live \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --time-to-live-specification "Enabled=true,AttributeName=ttl"
else
    echo "TTL already enabled on $TABLE_NAME"
fi

# 1.6. Users DynamoDB Table (Issue #116: LinkedIn OAuth)
echo "[1.6/7] Checking Users DynamoDB Table..."
if ! aws dynamodb describe-table --table-name "$USERS_TABLE" --region "$REGION" >/dev/null 2>&1; then
    echo "Creating users table: $USERS_TABLE"
    aws dynamodb create-table \
        --table-name "$USERS_TABLE" \
        --attribute-definitions AttributeName=user_id,AttributeType=S \
        --key-schema AttributeName=user_id,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    aws dynamodb wait table-exists --table-name "$USERS_TABLE" --region "$REGION"
else
    echo "Users table already exists: $USERS_TABLE"
fi

# 2. IAM Role
echo "[2/5] Checking IAM Role..."
TRUST_POLICY='{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": { "Service": "lambda.amazonaws.com" },"Action": "sts:AssumeRole"}]}'

if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "$TRUST_POLICY"
fi

aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name "${APP_NAME}Access" --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Allow","Action": ["dynamodb:PutItem","dynamodb:GetItem","dynamodb:UpdateItem","dynamodb:DeleteItem","dynamodb:Query","dynamodb:Scan"],"Resource": ["arn:aws:dynamodb:*:*:table/'"$TABLE_NAME"'", "arn:aws:dynamodb:*:*:table/'"$USERS_TABLE"'"]},
        {"Effect": "Allow","Action": ["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],"Resource": "*"},
        {"Effect": "Allow","Action": ["secretsmanager:GetSecretValue"],"Resource": "arn:aws:secretsmanager:*:*:secret:'"$LINKEDIN_SECRET_NAME"'*"}
    ]
}'
sleep 5

# 3. Lambda Function (x86_64 Enforced)
echo "[3/5] Creating Lambda Function..."
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
echo "[4/5] Configuring URL..."
aws lambda create-function-url-config --function-name "$FUNC_NAME" --auth-type NONE --cors "AllowOrigins=['*'],AllowMethods=['POST'],AllowHeaders=['Content-Type']" --region "$REGION" 2>/dev/null || true
aws lambda add-permission --function-name "$FUNC_NAME" --action lambda:InvokeFunctionUrl --statement-id FunctionURLAllowPublicAccess --principal "*" --function-url-auth-type NONE --region "$REGION" 2>/dev/null || true

FUNC_URL=$(aws lambda get-function-url-config --function-name "$FUNC_NAME" --region "$REGION" --query 'FunctionUrl' --output text)

# 5. Auth Lambda Function (Issue #116: LinkedIn OAuth)
echo "[5/7] Creating Auth Lambda Function..."
echo "def lambda_handler(event, context): return 'Init'" > lambda_auth_function.py
cat << 'PY_SCRIPT' > zipper_auth.py
import zipfile
with zipfile.ZipFile('init_auth.zip', 'w') as z:
    z.write('lambda_auth_function.py')
PY_SCRIPT
python zipper_auth.py

if ! aws lambda get-function --function-name "$AUTH_FUNC_NAME" --region "$REGION" >/dev/null 2>&1; then
    aws lambda create-function \
        --function-name "$AUTH_FUNC_NAME" \
        --runtime python3.12 \
        --role "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}" \
        --handler lambda_auth_function.lambda_handler \
        --zip-file fileb://init_auth.zip \
        --architectures x86_64 \
        --timeout 30 \
        --environment "Variables={USERS_TABLE=$USERS_TABLE,LINKEDIN_SECRET_NAME=$LINKEDIN_SECRET_NAME}" \
        --region "$REGION"
fi
rm init_auth.zip lambda_auth_function.py zipper_auth.py

# 6. Auth Function URL
echo "[6/7] Configuring Auth URL..."
aws lambda create-function-url-config --function-name "$AUTH_FUNC_NAME" --auth-type NONE --cors "AllowOrigins=['*'],AllowMethods=['POST','GET'],AllowHeaders=['Content-Type','Authorization']" --region "$REGION" 2>/dev/null || true
aws lambda add-permission --function-name "$AUTH_FUNC_NAME" --action lambda:InvokeFunctionUrl --statement-id FunctionURLAllowPublicAccess --principal "*" --function-url-auth-type NONE --region "$REGION" 2>/dev/null || true

AUTH_FUNC_URL=$(aws lambda get-function-url-config --function-name "$AUTH_FUNC_NAME" --region "$REGION" --query 'FunctionUrl' --output text)

# 7. LinkedIn Secret reminder
echo "[7/7] LinkedIn OAuth Secret..."
if ! aws secretsmanager describe-secret --secret-id "$LINKEDIN_SECRET_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "WARNING: LinkedIn OAuth secret '$LINKEDIN_SECRET_NAME' not found!"
    echo "Create it manually with:"
    echo "  aws secretsmanager create-secret --name $LINKEDIN_SECRET_NAME --secret-string '{\"client_id\":\"YOUR_ID\",\"client_secret\":\"YOUR_SECRET\"}'"
else
    echo "LinkedIn secret exists: $LINKEDIN_SECRET_NAME"
fi

echo "=== Provisioning Complete ==="
echo "Agent Function URL: $FUNC_URL"
echo "Auth Function URL:  $AUTH_FUNC_URL"
