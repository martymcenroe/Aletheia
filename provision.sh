#!/bin/bash
set -e

# =============================================================================
# Aletheia Infrastructure Provisioning Script
# =============================================================================
# This script provisions all AWS infrastructure for Aletheia:
# - DynamoDB tables (agent state, users, token cap)
# - IAM role with appropriate permissions
# - Lambda functions (Agent, Auth) with dependency layers
# - Function URLs with CORS
# - CloudWatch log groups with retention
#
# Prerequisites:
# - AWS CLI configured with appropriate credentials
# - Python 3.x available
# - src/lambda_function.py exists (Agent Lambda)
# - src/lambda_auth_function.py exists (Auth Lambda)
# =============================================================================

APP_NAME="Aletheia"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TABLE_NAME="${APP_NAME}AgentState"
USERS_TABLE="aletheia-users"
TOKEN_CAP_TABLE="aletheia-token-cap"
COUPONS_TABLE="aletheia-coupons"
ROLE_NAME="${APP_NAME}LambdaRole"
FUNC_NAME="${APP_NAME}Agent"
AUTH_FUNC_NAME="${APP_NAME}Auth"
LINKEDIN_SECRET_NAME="aletheia/linkedin-oauth"
JWT_SECRET_NAME="aletheia/jwt-signing-key"
STRIPE_SECRET_NAME="aletheia/stripe-secret-key"
STRIPE_WEBHOOK_SECRET_NAME="aletheia/stripe-webhook-secret"
STRIPE_PRICE_ID="price_1T3sjCARfOsdSf7sfarT8Reo"
GITHUB_SECRET_NAME="aletheia/github-oauth"
LAYER_NAME="${APP_NAME}Dependencies"

# Issue #351: Read CloudFlare origin secret from SSM Parameter Store (never in git)
ORIGIN_SECRET=$(aws ssm get-parameter --name "/aletheia/cloudflare-origin-secret" --with-decryption --query Parameter.Value --output text --region "$REGION" 2>/dev/null || echo "")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Provisioning Infrastructure for $APP_NAME ($REGION) ==="
echo "Account ID: $ACCOUNT_ID"
echo ""

# =============================================================================
# Step 0: Validate Prerequisites
# =============================================================================
echo "[0/10] Validating prerequisites..."

# Check for required Lambda source files
AUTH_LAMBDA_SOURCE="src/lambda_auth_function.py"
AGENT_LAMBDA_SOURCE="src/lambda_function.py"

if [ ! -f "$AUTH_LAMBDA_SOURCE" ]; then
    echo -e "${RED}ERROR: Auth Lambda source not found at $AUTH_LAMBDA_SOURCE${NC}"
    echo "Cannot deploy without real code. Aborting."
    exit 1
fi

if [ ! -f "$AGENT_LAMBDA_SOURCE" ]; then
    echo -e "${RED}ERROR: Agent Lambda source not found at $AGENT_LAMBDA_SOURCE${NC}"
    echo "Cannot deploy without real code. Aborting."
    exit 1
fi

echo -e "${GREEN}Found Lambda source files${NC}"

# =============================================================================
# Step 1: DynamoDB Agent State Table
# =============================================================================
echo ""
echo "[1/10] Checking DynamoDB Agent State Table..."
if ! aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "Creating table: $TABLE_NAME"
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions AttributeName=thread_id,AttributeType=S AttributeName=checkpoint_id,AttributeType=S \
        --key-schema AttributeName=thread_id,KeyType=HASH AttributeName=checkpoint_id,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
    echo -e "${GREEN}Created table: $TABLE_NAME${NC}"
else
    echo "Table already exists: $TABLE_NAME"
fi

# Enable TTL for 30-day auto-expiry (Issue #145)
echo "Checking DynamoDB TTL..."
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
    echo -e "${GREEN}TTL enabled${NC}"
else
    echo "TTL already enabled"
fi

# Issue #147: Add GSI on user_id for GDPR data erasure queries
echo "Checking GSI on user_id..."
GSI_EXISTS=$(aws dynamodb describe-table \
    --table-name "$TABLE_NAME" \
    --region "$REGION" \
    --query "Table.GlobalSecondaryIndexes[?IndexName=='user_id-index'].IndexName" \
    --output text 2>/dev/null || echo "")

if [ -z "$GSI_EXISTS" ]; then
    echo "Creating GSI on user_id for GDPR erasure queries..."
    aws dynamodb update-table \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --attribute-definitions AttributeName=user_id,AttributeType=S \
        --global-secondary-index-updates '[{
            "Create": {
                "IndexName": "user_id-index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "KEYS_ONLY"}
            }
        }]'
    echo "Waiting for GSI to become active..."
    aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
    echo -e "${GREEN}GSI user_id-index created${NC}"
else
    echo "GSI user_id-index already exists"
fi

# =============================================================================
# Step 2: DynamoDB Users Table (Issue #116: LinkedIn OAuth)
# =============================================================================
echo ""
echo "[2/10] Checking DynamoDB Users Table..."
if ! aws dynamodb describe-table --table-name "$USERS_TABLE" --region "$REGION" >/dev/null 2>&1; then
    echo "Creating users table: $USERS_TABLE"
    aws dynamodb create-table \
        --table-name "$USERS_TABLE" \
        --attribute-definitions AttributeName=user_id,AttributeType=S \
        --key-schema AttributeName=user_id,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    aws dynamodb wait table-exists --table-name "$USERS_TABLE" --region "$REGION"
    echo -e "${GREEN}Created users table: $USERS_TABLE${NC}"
else
    echo "Users table already exists: $USERS_TABLE"
fi

# Issue #378: Add GSI on tier for admin metrics queries
echo "Checking GSI on tier..."
TIER_GSI_EXISTS=$(aws dynamodb describe-table \
    --table-name "$USERS_TABLE" \
    --region "$REGION" \
    --query "Table.GlobalSecondaryIndexes[?IndexName=='tier-index'].IndexName" \
    --output text 2>/dev/null || echo "")

if [ -z "$TIER_GSI_EXISTS" ]; then
    echo "Creating GSI on tier for admin metrics queries..."
    aws dynamodb update-table \
        --table-name "$USERS_TABLE" \
        --region "$REGION" \
        --attribute-definitions AttributeName=tier,AttributeType=S \
        --global-secondary-index-updates '[{
            "Create": {
                "IndexName": "tier-index",
                "KeySchema": [{"AttributeName": "tier", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "KEYS_ONLY"}
            }
        }]'
    echo "Waiting for GSI to become active..."
    aws dynamodb wait table-exists --table-name "$USERS_TABLE" --region "$REGION"
    echo -e "${GREEN}GSI tier-index created${NC}"
else
    echo "GSI tier-index already exists"
fi

# =============================================================================
# Step 3: DynamoDB Token Cap Table (Issue #341: JWT Auth + Daily Cap)
# =============================================================================
echo ""
echo "[3/10] Checking DynamoDB Token Cap Table..."
if ! aws dynamodb describe-table --table-name "$TOKEN_CAP_TABLE" --region "$REGION" >/dev/null 2>&1; then
    echo "Creating token cap table: $TOKEN_CAP_TABLE"
    aws dynamodb create-table \
        --table-name "$TOKEN_CAP_TABLE" \
        --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
        --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    aws dynamodb wait table-exists --table-name "$TOKEN_CAP_TABLE" --region "$REGION"
    echo -e "${GREEN}Created token cap table: $TOKEN_CAP_TABLE${NC}"
else
    echo "Token cap table already exists: $TOKEN_CAP_TABLE"
fi

# Enable TTL for 7-day auto-cleanup of daily counters
echo "Checking Token Cap TTL..."
TOKEN_CAP_TTL=$(aws dynamodb describe-time-to-live \
    --table-name "$TOKEN_CAP_TABLE" \
    --region "$REGION" \
    --query 'TimeToLiveDescription.TimeToLiveStatus' \
    --output text 2>/dev/null || echo "DISABLED")

if [ "$TOKEN_CAP_TTL" != "ENABLED" ]; then
    echo "Enabling TTL on $TOKEN_CAP_TABLE..."
    aws dynamodb update-time-to-live \
        --table-name "$TOKEN_CAP_TABLE" \
        --region "$REGION" \
        --time-to-live-specification "Enabled=true,AttributeName=ttl"
    echo -e "${GREEN}TTL enabled on token cap table${NC}"
else
    echo "TTL already enabled on token cap table"
fi

# =============================================================================
# Step 3b: DynamoDB Coupons Table (Issue #367: Manual Subscriptions)
# =============================================================================
echo ""
echo "[3b/10] Checking DynamoDB Coupons Table..."
if ! aws dynamodb describe-table --table-name "$COUPONS_TABLE" --region "$REGION" >/dev/null 2>&1; then
    echo "Creating coupons table: $COUPONS_TABLE"
    aws dynamodb create-table \
        --table-name "$COUPONS_TABLE" \
        --attribute-definitions AttributeName=code,AttributeType=S \
        --key-schema AttributeName=code,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    aws dynamodb wait table-exists --table-name "$COUPONS_TABLE" --region "$REGION"
    echo -e "${GREEN}Created coupons table: $COUPONS_TABLE${NC}"
else
    echo "Coupons table already exists: $COUPONS_TABLE"
fi

# Issue #381: Enable TTL for coupon auto-expiry
echo "Checking Coupons TTL..."
COUPONS_TTL=$(aws dynamodb describe-time-to-live \
    --table-name "$COUPONS_TABLE" \
    --region "$REGION" \
    --query 'TimeToLiveDescription.TimeToLiveStatus' \
    --output text 2>/dev/null || echo "DISABLED")

if [ "$COUPONS_TTL" != "ENABLED" ]; then
    echo "Enabling TTL on $COUPONS_TABLE..."
    aws dynamodb update-time-to-live \
        --table-name "$COUPONS_TABLE" \
        --region "$REGION" \
        --time-to-live-specification "Enabled=true,AttributeName=expiry"
    echo -e "${GREEN}TTL enabled on coupons table${NC}"
else
    echo "TTL already enabled on coupons table"
fi

# =============================================================================
# Step 4: IAM Role with All Required Permissions
# =============================================================================
echo ""
echo "[4/10] Configuring IAM Role..."
TRUST_POLICY='{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": { "Service": "lambda.amazonaws.com" },"Action": "sts:AssumeRole"}]}'

if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    echo "Creating IAM role: $ROLE_NAME"
    aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "$TRUST_POLICY"
    echo -e "${GREEN}Created IAM role${NC}"
else
    echo "IAM role already exists: $ROLE_NAME"
fi

# Attach basic execution role (required for CloudWatch Logs)
echo "Attaching AWSLambdaBasicExecutionRole..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" 2>/dev/null || true

# Issue #7: Attach X-Ray write access for observability tracing
echo "Attaching AWSXRayDaemonWriteAccess..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess" 2>/dev/null || true

# Create inline policy with all required permissions
echo "Configuring inline policy..."
aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "${APP_NAME}Access" \
    --policy-document '{
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
            "Resource": [
                "arn:aws:dynamodb:us-east-1:383687041805:table/'"$TABLE_NAME"'",
                "arn:aws:dynamodb:us-east-1:383687041805:table/'"$TABLE_NAME"'/index/*",
                "arn:aws:dynamodb:us-east-1:383687041805:table/'"$USERS_TABLE"'",
                "arn:aws:dynamodb:us-east-1:383687041805:table/'"$USERS_TABLE"'/index/*",
                "arn:aws:dynamodb:us-east-1:383687041805:table/'"$TOKEN_CAP_TABLE"'",
                "arn:aws:dynamodb:us-east-1:383687041805:table/'"$COUPONS_TABLE"'"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:'"$REGION"':'"$ACCOUNT_ID"':secret:'"$LINKEDIN_SECRET_NAME"'*",
                "arn:aws:secretsmanager:'"$REGION"':'"$ACCOUNT_ID"':secret:'"$JWT_SECRET_NAME"'*",
                "arn:aws:secretsmanager:'"$REGION"':'"$ACCOUNT_ID"':secret:'"$STRIPE_SECRET_NAME"'*",
                "arn:aws:secretsmanager:'"$REGION"':'"$ACCOUNT_ID"':secret:'"$STRIPE_WEBHOOK_SECRET_NAME"'*",
                "arn:aws:secretsmanager:'"$REGION"':'"$ACCOUNT_ID"':secret:'"$GITHUB_SECRET_NAME"'*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:'"$REGION"':'"$ACCOUNT_ID"':log-group:/aws/lambda/*"
        },
        {
            "Sid": "Issue7CloudWatchMetrics",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "cloudwatch:namespace": "Aletheia"
                }
            }
        }
    ]
}'
echo -e "${GREEN}IAM permissions configured${NC}"

# Wait for IAM propagation
echo "Waiting for IAM propagation (10 seconds)..."
sleep 10

# =============================================================================
# Step 5: Lambda Dependency Layer (Cherry-Pick Strategy)
# =============================================================================
echo ""
echo "[5/10] Building Lambda Dependency Layer..."

# Clean up any previous build artifacts
rm -rf build/python 2>/dev/null || true
rm -f dependencies.zip 2>/dev/null || true

# Create build directory
mkdir -p build/python

# Install ONLY the required runtime dependencies (cherry-pick, not full poetry export)
# Issue #7: aws-xray-sdk for observability tracing
# Issue #341: PyJWT for JWT authentication
echo "Installing runtime dependencies: requests, aws-xray-sdk, PyJWT, stripe..."
pip install requests aws-xray-sdk PyJWT stripe -t build/python --no-cache-dir --quiet

# Remove unnecessary files to reduce layer size
echo "Cleaning up unnecessary files..."
find build/python -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find build/python -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find build/python -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find build/python -type f -name "*.pyc" -delete 2>/dev/null || true

# Create the layer zip
echo "Creating dependencies.zip..."
cd build
zip -r ../dependencies.zip python -q
cd ..

LAYER_SIZE=$(du -h dependencies.zip | cut -f1)
echo "Layer size: $LAYER_SIZE"

# Publish the layer
echo "Publishing Lambda Layer: $LAYER_NAME..."
LAYER_VERSION_ARN=$(aws lambda publish-layer-version \
    --layer-name "$LAYER_NAME" \
    --description "Runtime dependencies for Aletheia Lambdas (requests, aws-xray-sdk, PyJWT, stripe)" \
    --zip-file fileb://dependencies.zip \
    --compatible-runtimes python3.12 python3.11 python3.10 \
    --compatible-architectures x86_64 \
    --region "$REGION" \
    --query 'LayerVersionArn' \
    --output text)

echo -e "${GREEN}Published layer: $LAYER_VERSION_ARN${NC}"

# Cleanup build artifacts
rm -rf build dependencies.zip

# =============================================================================
# Step 6: Deploy Agent Lambda (Real Code)
# =============================================================================
echo ""
echo "[6/10] Deploying Agent Lambda..."

# Create deployment package from real source (entire src/ package for relative imports)
echo "Packaging src/ directory..."
zip -rq agent_lambda.zip src/

if ! aws lambda get-function --function-name "$FUNC_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "Creating Lambda function: $FUNC_NAME"
    aws lambda create-function \
        --function-name "$FUNC_NAME" \
        --runtime python3.12 \
        --role "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}" \
        --handler src.lambda_function.lambda_handler \
        --zip-file fileb://agent_lambda.zip \
        --architectures x86_64 \
        --timeout 60 \
        --memory-size 256 \
        --layers "$LAYER_VERSION_ARN" \
        --environment "Variables={ALETHEIA_ENV=dev,DYNAMODB_TABLE=$TABLE_NAME,CLOUDFLARE_ORIGIN_SECRET=$ORIGIN_SECRET,TOKEN_CAP_TABLE=$TOKEN_CAP_TABLE,JWT_SECRET_NAME=$JWT_SECRET_NAME,AUTH_ENABLED=true}" \
        --tracing-config Mode=Active \
        --region "$REGION"
    echo -e "${GREEN}Created Agent Lambda (X-Ray enabled)${NC}"
else
    echo "Updating existing Lambda function: $FUNC_NAME"
    aws lambda update-function-code \
        --function-name "$FUNC_NAME" \
        --zip-file fileb://agent_lambda.zip \
        --region "$REGION" >/dev/null

    # Wait for code update to complete before updating configuration
    aws lambda wait function-updated --function-name "$FUNC_NAME" --region "$REGION"

    # Update configuration including layer, handler, and X-Ray tracing (Issue #7)
    aws lambda update-function-configuration \
        --function-name "$FUNC_NAME" \
        --handler src.lambda_function.lambda_handler \
        --layers "$LAYER_VERSION_ARN" \
        --environment "Variables={ALETHEIA_ENV=dev,DYNAMODB_TABLE=$TABLE_NAME,CLOUDFLARE_ORIGIN_SECRET=$ORIGIN_SECRET,TOKEN_CAP_TABLE=$TOKEN_CAP_TABLE,JWT_SECRET_NAME=$JWT_SECRET_NAME,AUTH_ENABLED=true}" \
        --tracing-config Mode=Active \
        --region "$REGION" >/dev/null

    echo -e "${GREEN}Updated Agent Lambda (X-Ray enabled)${NC}"
fi

rm -f agent_lambda.zip

# =============================================================================
# Step 7: Deploy Auth Lambda (Issue #341: Now uses src/ package imports)
# =============================================================================
echo ""
echo "[7/10] Deploying Auth Lambda..."

# Issue #362: Auth Lambda now imports from auth/ package (jwt_service, token_cap_service).
# Must package entire src/ directory, same as Agent Lambda.
echo "Packaging src/ and static/ directories for Auth Lambda..."
zip -rq auth_lambda.zip src/ static/

# Issue #366: Get existing Auth Function URL for Stripe redirect URLs
AUTH_LAMBDA_URL=$(aws lambda get-function-url-config \
    --function-name "$AUTH_FUNC_NAME" \
    --region "$REGION" \
    --query 'FunctionUrl' \
    --output text 2>/dev/null || echo "")

if ! aws lambda get-function --function-name "$AUTH_FUNC_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "Creating Lambda function: $AUTH_FUNC_NAME"
    aws lambda create-function \
        --function-name "$AUTH_FUNC_NAME" \
        --runtime python3.12 \
        --role "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}" \
        --handler src.lambda_auth_function.lambda_handler \
        --zip-file fileb://auth_lambda.zip \
        --architectures x86_64 \
        --timeout 30 \
        --memory-size 256 \
        --layers "$LAYER_VERSION_ARN" \
        --environment "Variables={USERS_TABLE=$USERS_TABLE,LINKEDIN_SECRET_NAME=$LINKEDIN_SECRET_NAME,AGENT_STATE_TABLE=$TABLE_NAME,TOKEN_CAP_TABLE=$TOKEN_CAP_TABLE,JWT_SECRET_NAME=$JWT_SECRET_NAME,COUPONS_TABLE=$COUPONS_TABLE,STRIPE_SECRET_NAME=$STRIPE_SECRET_NAME,STRIPE_WEBHOOK_SECRET_NAME=$STRIPE_WEBHOOK_SECRET_NAME,STRIPE_PRICE_ID=$STRIPE_PRICE_ID,STRIPE_SUCCESS_URL=${AUTH_LAMBDA_URL}upgrade-success,STRIPE_CANCEL_URL=${AUTH_LAMBDA_URL}upgrade-cancel,GITHUB_SECRET_NAME=$GITHUB_SECRET_NAME}" \
        --tracing-config Mode=Active \
        --region "$REGION"
    echo -e "${GREEN}Created Auth Lambda (X-Ray enabled)${NC}"
else
    echo "Updating existing Lambda function: $AUTH_FUNC_NAME"
    aws lambda update-function-code \
        --function-name "$AUTH_FUNC_NAME" \
        --zip-file fileb://auth_lambda.zip \
        --region "$REGION" >/dev/null

    # Wait for code update to complete before updating configuration
    aws lambda wait function-updated --function-name "$AUTH_FUNC_NAME" --region "$REGION"

    aws lambda update-function-configuration \
        --function-name "$AUTH_FUNC_NAME" \
        --handler src.lambda_auth_function.lambda_handler \
        --layers "$LAYER_VERSION_ARN" \
        --environment "Variables={USERS_TABLE=$USERS_TABLE,LINKEDIN_SECRET_NAME=$LINKEDIN_SECRET_NAME,AGENT_STATE_TABLE=$TABLE_NAME,TOKEN_CAP_TABLE=$TOKEN_CAP_TABLE,JWT_SECRET_NAME=$JWT_SECRET_NAME,COUPONS_TABLE=$COUPONS_TABLE,STRIPE_SECRET_NAME=$STRIPE_SECRET_NAME,STRIPE_WEBHOOK_SECRET_NAME=$STRIPE_WEBHOOK_SECRET_NAME,STRIPE_PRICE_ID=$STRIPE_PRICE_ID,STRIPE_SUCCESS_URL=${AUTH_LAMBDA_URL}upgrade-success,STRIPE_CANCEL_URL=${AUTH_LAMBDA_URL}upgrade-cancel,GITHUB_SECRET_NAME=$GITHUB_SECRET_NAME}" \
        --tracing-config Mode=Active \
        --region "$REGION" >/dev/null

    echo -e "${GREEN}Updated Auth Lambda (X-Ray enabled)${NC}"
fi

rm -f auth_lambda.zip

# =============================================================================
# Step 8: Configure Function URLs
# =============================================================================
echo ""
echo "[8/10] Configuring Function URLs..."

# Agent Function URL
aws lambda create-function-url-config \
    --function-name "$FUNC_NAME" \
    --auth-type NONE \
    --cors "AllowOrigins=['https://api.aletheia.study'],AllowMethods=['POST'],AllowHeaders=['Content-Type']" \
    --region "$REGION" 2>/dev/null || \
aws lambda update-function-url-config \
    --function-name "$FUNC_NAME" \
    --cors "AllowOrigins=['https://api.aletheia.study'],AllowMethods=['POST'],AllowHeaders=['Content-Type']" \
    --region "$REGION" >/dev/null

aws lambda add-permission \
    --function-name "$FUNC_NAME" \
    --action lambda:InvokeFunctionUrl \
    --statement-id FunctionURLAllowPublicAccess \
    --principal "*" \
    --function-url-auth-type NONE \
    --region "$REGION" 2>/dev/null || true

FUNC_URL=$(aws lambda get-function-url-config \
    --function-name "$FUNC_NAME" \
    --region "$REGION" \
    --query 'FunctionUrl' \
    --output text)

# Auth Function URL
aws lambda create-function-url-config \
    --function-name "$AUTH_FUNC_NAME" \
    --auth-type NONE \
    --cors "AllowOrigins=['https://api.aletheia.study'],AllowMethods=['POST','GET'],AllowHeaders=['Content-Type','Authorization']" \
    --region "$REGION" 2>/dev/null || \
aws lambda update-function-url-config \
    --function-name "$AUTH_FUNC_NAME" \
    --cors "AllowOrigins=['https://api.aletheia.study'],AllowMethods=['POST','GET'],AllowHeaders=['Content-Type','Authorization']" \
    --region "$REGION" >/dev/null

aws lambda add-permission \
    --function-name "$AUTH_FUNC_NAME" \
    --action lambda:InvokeFunctionUrl \
    --statement-id FunctionURLAllowPublicAccess \
    --principal "*" \
    --function-url-auth-type NONE \
    --region "$REGION" 2>/dev/null || true

AUTH_FUNC_URL=$(aws lambda get-function-url-config \
    --function-name "$AUTH_FUNC_NAME" \
    --region "$REGION" \
    --query 'FunctionUrl' \
    --output text)

echo -e "${GREEN}Function URLs configured${NC}"

# =============================================================================
# Step 9: CloudWatch Log Groups with Retention
# =============================================================================
echo ""
echo "[9/10] Configuring CloudWatch Logs..."

# Create log groups if they don't exist
# Note: MSYS_NO_PATHCONV=1 prevents Git Bash from converting /aws/lambda to C:/Program Files/Git/aws/lambda
AGENT_LOG_GROUP="/aws/lambda/$FUNC_NAME"
AUTH_LOG_GROUP="/aws/lambda/$AUTH_FUNC_NAME"

for LOG_GROUP in "$AGENT_LOG_GROUP" "$AUTH_LOG_GROUP"; do
    LOG_GROUP_EXISTS=$(MSYS_NO_PATHCONV=1 aws logs describe-log-groups \
        --log-group-name-prefix "$LOG_GROUP" \
        --region "$REGION" \
        --query "logGroups[?logGroupName=='$LOG_GROUP'].logGroupName" \
        --output text 2>/dev/null || echo "")

    if [ -z "$LOG_GROUP_EXISTS" ]; then
        echo "Creating log group: $LOG_GROUP"
        MSYS_NO_PATHCONV=1 aws logs create-log-group --log-group-name "$LOG_GROUP" --region "$REGION" 2>/dev/null || true
    fi

    # Issue #7: Set retention to 14 days (privacy-aligned per LLD)
    echo "Setting 14-day retention on: $LOG_GROUP"
    MSYS_NO_PATHCONV=1 aws logs put-retention-policy \
        --log-group-name "$LOG_GROUP" \
        --retention-in-days 14 \
        --region "$REGION"
done

echo -e "${GREEN}CloudWatch logging configured with 14-day retention (Issue #7)${NC}"

# =============================================================================
# Step 10: Verify Secrets
# =============================================================================
echo ""
echo "[10/10] Checking required secrets..."

SECRETS_OK=true

# LinkedIn OAuth secret
if ! aws secretsmanager describe-secret --secret-id "$LINKEDIN_SECRET_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo -e "${YELLOW}WARNING: LinkedIn OAuth secret '$LINKEDIN_SECRET_NAME' not found!${NC}"
    echo "  Create it with:"
    echo "    aws secretsmanager create-secret \\"
    echo "      --name $LINKEDIN_SECRET_NAME \\"
    echo "      --secret-string '{\"client_id\":\"YOUR_ID\",\"client_secret\":\"YOUR_SECRET\"}' \\"
    echo "      --region $REGION"
    SECRETS_OK=false
else
    echo -e "${GREEN}LinkedIn secret exists: $LINKEDIN_SECRET_NAME${NC}"
fi

# JWT signing secret (Issue #341)
if ! aws secretsmanager describe-secret --secret-id "$JWT_SECRET_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo -e "${YELLOW}WARNING: JWT signing secret '$JWT_SECRET_NAME' not found!${NC}"
    echo "  Create it with:"
    echo "    python -c \"import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(64)).decode())\" | \\"
    echo "      xargs -I{} aws secretsmanager create-secret \\"
    echo "        --name $JWT_SECRET_NAME --secret-string '{}' \\"
    echo "        --region $REGION"
    SECRETS_OK=false
else
    echo -e "${GREEN}JWT signing secret exists: $JWT_SECRET_NAME${NC}"
fi

# GitHub OAuth secret (Issue #433)
if ! aws secretsmanager describe-secret --secret-id "$GITHUB_SECRET_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo -e "${YELLOW}WARNING: GitHub OAuth secret '$GITHUB_SECRET_NAME' not found!${NC}"
    echo "  Create it with:"
    echo "    aws secretsmanager create-secret \\"
    echo "      --name $GITHUB_SECRET_NAME \\"
    echo "      --secret-string '{\"client_id\":\"YOUR_ID\",\"client_secret\":\"YOUR_SECRET\"}' \\"
    echo "      --region $REGION"
    SECRETS_OK=false
else
    echo -e "${GREEN}GitHub OAuth secret exists: $GITHUB_SECRET_NAME${NC}"
fi

# =============================================================================
# Sanity Check: Self-Test the Auth Lambda
# =============================================================================
echo ""
echo "=== Running Sanity Check ==="
echo "Testing Auth Lambda endpoint..."

# Give Lambda a moment to be ready
sleep 2

# Test the auth endpoint with a simple health check
# We expect a JSON response, not "Init" or HTML error page
RESPONSE=$(curl -s -w "\n%{http_code}" --max-time 10 "${AUTH_FUNC_URL}" 2>/dev/null || echo -e "\n000")
HTTP_BODY=$(echo "$RESPONSE" | head -n -1)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)

echo "HTTP Status: $HTTP_CODE"
echo "Response: $HTTP_BODY"

# Check for deployment failures
DEPLOYMENT_OK=true

if [ "$HTTP_CODE" = "000" ]; then
    echo -e "${RED}DEPLOYMENT FAILED: Could not connect to endpoint${NC}"
    DEPLOYMENT_OK=false
elif [ "$HTTP_CODE" = "500" ]; then
    echo -e "${RED}DEPLOYMENT FAILED: Internal Server Error (500)${NC}"
    DEPLOYMENT_OK=false
elif echo "$HTTP_BODY" | grep -q "^Init$"; then
    echo -e "${RED}DEPLOYMENT FAILED: Lambda still returning 'Init' placeholder${NC}"
    DEPLOYMENT_OK=false
elif echo "$HTTP_BODY" | grep -qi "Internal Server Error"; then
    echo -e "${RED}DEPLOYMENT FAILED: Internal Server Error in response${NC}"
    DEPLOYMENT_OK=false
elif ! echo "$HTTP_BODY" | python -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    echo -e "${YELLOW}WARNING: Response is not valid JSON (may be expected for GET without params)${NC}"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "=== Provisioning Complete ==="
echo ""
echo "Resources:"
echo "  DynamoDB Tables:"
echo "    - $TABLE_NAME (TTL enabled)"
echo "    - $USERS_TABLE (tier-index GSI)"
echo "    - $TOKEN_CAP_TABLE (TTL enabled)"
echo "    - $COUPONS_TABLE (TTL enabled)"
echo "  IAM Role: $ROLE_NAME"
echo "  Lambda Layer: $LAYER_NAME"
echo ""
echo "Endpoints:"
echo "  Agent Function URL: $FUNC_URL"
echo "  Auth Function URL:  $AUTH_FUNC_URL"
echo ""

if [ "$SECRETS_OK" = false ]; then
    echo -e "${YELLOW}Action Required: Create missing secrets (see above)${NC}"
    echo ""
fi

if [ "$DEPLOYMENT_OK" = true ]; then
    echo -e "${GREEN}Deployment Status: SUCCESS${NC}"
else
    echo -e "${RED}Deployment Status: FAILED - Check CloudWatch logs for details${NC}"
    echo "  aws logs tail /aws/lambda/$AUTH_FUNC_NAME --region $REGION --follow"
    exit 1
fi
