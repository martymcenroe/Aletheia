#!/bin/bash
# tools/aws/waf-setup.sh
# Creates CloudFront distribution + WAF Web ACL for Aletheia
#
# Usage:
#   ./waf-setup.sh              # Production: 100 req/5min
#   ./waf-setup.sh --env dev    # Development: 10 req/10min
#   ./waf-setup.sh --env prod   # Production (explicit)
#   ./waf-setup.sh --teardown   # Remove CloudFront + WAF
#
# Prerequisites:
#   - AWS CLI v2 configured with appropriate permissions
#   - Lambda function URL must already exist
#
# LLD: docs/1095-security-hardening.md

set -e

# Use portable temp directory (works on Windows Git Bash)
# Force $HOME/tmp instead of system TMPDIR which may not work on Windows
SCRIPT_TMPDIR="$HOME/tmp/aletheia-waf"
mkdir -p "$SCRIPT_TMPDIR"

# Convert to Windows path for AWS CLI (required on Git Bash)
if command -v cygpath &> /dev/null; then
    SCRIPT_TMPDIR_WIN=$(cygpath -w "$SCRIPT_TMPDIR")
else
    SCRIPT_TMPDIR_WIN="$SCRIPT_TMPDIR"
fi

# Configuration
LAMBDA_URL="sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws"
WAF_NAME="AletheiaWebACL"
CF_COMMENT="Aletheia API Gateway"
REGION="us-east-1"  # WAF for CloudFront must be in us-east-1

# Parse arguments
ENV="prod"
TEARDOWN=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --env) ENV="$2"; shift 2 ;;
        --teardown) TEARDOWN=true; shift ;;
        --help|-h)
            echo "Usage: $0 [--env dev|prod] [--teardown]"
            echo ""
            echo "Options:"
            echo "  --env dev   Development mode: 10 requests per 10 minutes"
            echo "  --env prod  Production mode: 100 requests per 5 minutes (default)"
            echo "  --teardown  Remove CloudFront distribution and WAF Web ACL"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Environment-specific rate limits
if [ "$ENV" == "dev" ]; then
    RATE_LIMIT=10
    RATE_WINDOW=600  # 10 minutes (WAF minimum is 5 min, we use 10 for stricter dev testing)
    echo "=== Development Mode: 10 req/10min ==="
else
    RATE_LIMIT=100
    RATE_WINDOW=300  # 5 minutes
    echo "=== Production Mode: 100 req/5min ==="
fi

# ============================================================
# TEARDOWN MODE
# ============================================================
if [ "$TEARDOWN" == "true" ]; then
    echo "=== Teardown Mode ==="

    # Find CloudFront distribution
    CF_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='$CF_COMMENT'].Id" --output text 2>/dev/null || echo "")

    if [ -n "$CF_ID" ] && [ "$CF_ID" != "None" ]; then
        echo "Found CloudFront distribution: $CF_ID"

        # Disable distribution first (required before deletion)
        echo "-> Disabling distribution..."
        ETAG=$(aws cloudfront get-distribution-config --id "$CF_ID" --query 'ETag' --output text)
        aws cloudfront get-distribution-config --id "$CF_ID" --query 'DistributionConfig' --output json | \
            jq '.Enabled = false' > "$SCRIPT_TMPDIR/cf-config.json"
        aws cloudfront update-distribution --id "$CF_ID" --if-match "$ETAG" --distribution-config "file://$SCRIPT_TMPDIR_WIN/cf-config.json" > /dev/null

        echo "-> Waiting for distribution to deploy (this takes 5-10 minutes)..."
        aws cloudfront wait distribution-deployed --id "$CF_ID"

        echo "-> Deleting distribution..."
        ETAG=$(aws cloudfront get-distribution --id "$CF_ID" --query 'ETag' --output text)
        aws cloudfront delete-distribution --id "$CF_ID" --if-match "$ETAG"
        echo "✓ CloudFront distribution deleted"
    else
        echo "No CloudFront distribution found with comment: $CF_COMMENT"
    fi

    # Find and delete WAF Web ACL
    WAF_ARN=$(aws wafv2 list-web-acls --scope CLOUDFRONT --region "$REGION" --query "WebACLs[?Name=='$WAF_NAME'].ARN" --output text 2>/dev/null || echo "")

    if [ -n "$WAF_ARN" ] && [ "$WAF_ARN" != "None" ]; then
        echo "Found WAF Web ACL: $WAF_ARN"
        LOCK_TOKEN=$(aws wafv2 get-web-acl --name "$WAF_NAME" --scope CLOUDFRONT --id "${WAF_ARN##*/}" --region "$REGION" --query 'LockToken' --output text)
        aws wafv2 delete-web-acl --name "$WAF_NAME" --scope CLOUDFRONT --id "${WAF_ARN##*/}" --lock-token "$LOCK_TOKEN" --region "$REGION"
        echo "✓ WAF Web ACL deleted"
    else
        echo "No WAF Web ACL found with name: $WAF_NAME"
    fi

    echo "=== Teardown Complete ==="
    exit 0
fi

# ============================================================
# CREATE MODE
# ============================================================
echo "=== Creating WAF + CloudFront Infrastructure ==="

# Step 1: Create WAF Web ACL
echo ""
echo "Step 1: Creating WAF Web ACL..."

# Check if WAF already exists
EXISTING_WAF=$(aws wafv2 list-web-acls --scope CLOUDFRONT --region "$REGION" --query "WebACLs[?Name=='$WAF_NAME'].ARN" --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_WAF" ] && [ "$EXISTING_WAF" != "None" ]; then
    echo "-> WAF Web ACL already exists: $EXISTING_WAF"
    WAF_ARN="$EXISTING_WAF"
else
    # Create WAF Web ACL with rules
    # Note: OPTIONS requests are allowed through for CORS preflight (browsers send preflight
    # before POST with custom headers). The rule blocks if: NOT OPTIONS AND NOT header "1.*"
    cat > "$SCRIPT_TMPDIR/waf-rules.json" << 'WAFRULES'
{
  "Name": "AletheiaWebACL",
  "Scope": "CLOUDFRONT",
  "DefaultAction": { "Allow": {} },
  "Description": "Aletheia API protection: header validation + rate limiting",
  "Rules": [
    {
      "Name": "RequireClientVersionExceptOptions",
      "Priority": 1,
      "Action": { "Block": {} },
      "Statement": {
        "AndStatement": {
          "Statements": [
            {
              "NotStatement": {
                "Statement": {
                  "ByteMatchStatement": {
                    "FieldToMatch": { "Method": {} },
                    "PositionalConstraint": "EXACTLY",
                    "SearchString": "T1BUSU9OUw==",
                    "TextTransformations": [{ "Priority": 0, "Type": "NONE" }]
                  }
                }
              }
            },
            {
              "NotStatement": {
                "Statement": {
                  "ByteMatchStatement": {
                    "FieldToMatch": { "SingleHeader": { "Name": "x-aletheia-client-version" } },
                    "PositionalConstraint": "STARTS_WITH",
                    "SearchString": "MS4=",
                    "TextTransformations": [{ "Priority": 0, "Type": "NONE" }]
                  }
                }
              }
            }
          ]
        }
      },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RequireClientVersionExceptOptions"
      }
    },
    {
      "Name": "RateLimitPerIP",
      "Priority": 2,
      "Action": {
        "Block": {
          "CustomResponse": {
            "ResponseCode": 429,
            "CustomResponseBodyKey": "rate-limited"
          }
        }
      },
      "Statement": {
        "RateBasedStatement": {
          "Limit": RATE_LIMIT_PLACEHOLDER,
          "EvaluationWindowSec": RATE_WINDOW_PLACEHOLDER,
          "AggregateKeyType": "IP"
        }
      },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimitPerIP"
      }
    }
  ],
  "VisibilityConfig": {
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "AletheiaWebACL"
  },
  "CustomResponseBodies": {
    "rate-limited": {
      "ContentType": "APPLICATION_JSON",
      "Content": "{\"error\": \"rate_limited\", \"message\": \"Too many requests. Please try again later.\"}"
    }
  }
}
WAFRULES

    # Replace placeholders with actual values
    sed -i "s/RATE_LIMIT_PLACEHOLDER/$RATE_LIMIT/g" "$SCRIPT_TMPDIR/waf-rules.json"
    sed -i "s/RATE_WINDOW_PLACEHOLDER/$RATE_WINDOW/g" "$SCRIPT_TMPDIR/waf-rules.json"

    # Note: ByteMatchStatement with BASE64_DECODE looks for "1." which is "MS4" in base64
    # This allows matching "1.0", "1.1", etc.

    WAF_ARN=$(aws wafv2 create-web-acl \
        --cli-input-json "file://$SCRIPT_TMPDIR_WIN/waf-rules.json" \
        --region "$REGION" \
        --query 'Summary.ARN' \
        --output text)

    echo "-> Created WAF Web ACL: $WAF_ARN"
fi

# Step 2: Create CloudFront Distribution
echo ""
echo "Step 2: Creating CloudFront Distribution..."

# Check if distribution already exists
EXISTING_CF=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='$CF_COMMENT'].Id" --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_CF" ] && [ "$EXISTING_CF" != "None" ]; then
    echo "-> CloudFront distribution already exists: $EXISTING_CF"
    CF_ID="$EXISTING_CF"
    CF_DOMAIN=$(aws cloudfront get-distribution --id "$CF_ID" --query 'Distribution.DomainName' --output text)
else
    # Create distribution config
    cat > "$SCRIPT_TMPDIR/cf-config.json" << CFCONFIG
{
  "CallerReference": "aletheia-$(date +%s)",
  "Comment": "$CF_COMMENT",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "lambda-origin",
        "DomainName": "$LAMBDA_URL",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "https-only",
          "OriginSslProtocols": { "Quantity": 1, "Items": ["TLSv1.2"] },
          "OriginReadTimeout": 60,
          "OriginKeepaliveTimeout": 5
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "lambda-origin",
    "ViewerProtocolPolicy": "https-only",
    "AllowedMethods": {
      "Quantity": 7,
      "Items": ["HEAD", "DELETE", "POST", "GET", "OPTIONS", "PUT", "PATCH"],
      "CachedMethods": { "Quantity": 2, "Items": ["GET", "HEAD"] }
    },
    "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
    "OriginRequestPolicyId": "b689b0a8-53d0-40ab-baf2-68738e2966ac",
    "Compress": true
  },
  "PriceClass": "PriceClass_100",
  "WebACLId": "$WAF_ARN",
  "HttpVersion": "http2"
}
CFCONFIG

    # Note: CachePolicyId "4135ea2d-..." is AWS managed "CachingDisabled"
    # Note: OriginRequestPolicyId "b689b0a8-..." is AWS managed "AllViewerExceptHostHeader"

    CF_RESULT=$(aws cloudfront create-distribution \
        --distribution-config "file://$SCRIPT_TMPDIR_WIN/cf-config.json" \
        --output json)

    CF_ID=$(echo "$CF_RESULT" | jq -r '.Distribution.Id')
    CF_DOMAIN=$(echo "$CF_RESULT" | jq -r '.Distribution.DomainName')

    echo "-> Created CloudFront distribution: $CF_ID"
    echo "-> Waiting for deployment (this takes 5-10 minutes)..."
    aws cloudfront wait distribution-deployed --id "$CF_ID"
    echo "-> Distribution deployed!"
fi

# Step 3: Update Lambda CORS
echo ""
echo "Step 3: Updating Lambda CORS configuration..."

aws lambda update-function-url-config \
    --function-name AletheiaAgent \
    --cors '{
        "AllowOrigins": ["*"],
        "AllowMethods": ["POST"],
        "AllowHeaders": ["content-type", "x-aletheia-client-version"],
        "MaxAge": 86400
    }' \
    --region "$REGION" > /dev/null

echo "-> Lambda CORS updated to allow x-aletheia-client-version header"

# Step 4: Output Summary
echo ""
echo "============================================================"
echo "=== WAF + CloudFront Setup Complete ==="
echo "============================================================"
echo ""
echo "CloudFront URL: https://$CF_DOMAIN"
echo "CloudFront ID:  $CF_ID"
echo "WAF ARN:        $WAF_ARN"
echo "Rate Limit:     $RATE_LIMIT requests per $((RATE_WINDOW / 60)) minutes"
echo ""
echo "Next Steps:"
echo "1. Update extension/service-worker.js:"
echo "   const API_ENDPOINT = \"https://$CF_DOMAIN/\";"
echo ""
echo "2. Add header to fetch request:"
echo "   headers: {"
echo "       'Content-Type': 'application/json',"
echo "       'X-Aletheia-Client-Version': '1.0'"
echo "   }"
echo ""
echo "3. Run verification:"
echo "   CLOUDFRONT_URL=\"https://$CF_DOMAIN\" ./tests/infra/verify_waf.sh"
echo ""

# Save config for other scripts
echo "CLOUDFRONT_URL=https://$CF_DOMAIN" > "$SCRIPT_TMPDIR/aletheia-waf-config.env"
echo "CLOUDFRONT_ID=$CF_ID" >> "$SCRIPT_TMPDIR/aletheia-waf-config.env"
echo "WAF_ARN=$WAF_ARN" >> "$SCRIPT_TMPDIR/aletheia-waf-config.env"
echo "-> Config saved to $SCRIPT_TMPDIR/aletheia-waf-config.env"
