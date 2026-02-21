#!/bin/bash
set -e

# =============================================================================
# CloudWatch Dashboard, SNS Topic, and Alarm Provisioning
# Issue #369: CloudWatch Usage Dashboard
# =============================================================================
# Prerequisites:
# - AWS CLI configured
# - provision.sh has been run (Lambda functions deployed)
# =============================================================================

REGION="us-east-1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Provisioning CloudWatch Dashboard & Alarms ==="

# Step 1: Validate JSON files
echo "[1/4] Validating JSON files..."
for f in cloudwatch-dashboard.json sns-alarm.json contributor-insights-top-talkers.json; do
    if ! poetry run python -c "import json; json.load(open('${SCRIPT_DIR}/${f}'))" 2>/dev/null; then
        echo "ERROR: Invalid JSON in $f"
        exit 1
    fi
    echo "  $f - valid"
done

# Step 1b: Pre-flight — check if Bedrock deny policy is attached
echo "[1b/4] Checking for Bedrock deny policy on AletheiaLambdaRole..."
DENY_POLICY=$(MSYS_NO_PATHCONV=1 aws iam list-attached-role-policies \
    --role-name AletheiaLambdaRole --region "$REGION" \
    --query "AttachedPolicies[?PolicyName=='AletheiaDenyBedrock-BudgetBreach'].PolicyName" \
    --output text 2>/dev/null || true)
if [ -n "$DENY_POLICY" ]; then
    echo -e "${YELLOW}WARNING: AletheiaDenyBedrock-BudgetBreach is attached to AletheiaLambdaRole!${NC}"
    echo "  The budget 95% action has fired. Bedrock calls will fail."
    echo "  See runbook 10902 Section 3 to reverse before provisioning."
    echo "  Continuing anyway (alarms/dashboard don't require Bedrock)..."
fi

# Step 2: Create/update CloudWatch dashboard
echo "[2/4] Creating CloudWatch dashboard: Aletheia-Usage..."
DASHBOARD_BODY=$(cat "${SCRIPT_DIR}/cloudwatch-dashboard.json")
MSYS_NO_PATHCONV=1 aws cloudwatch put-dashboard \
    --dashboard-name "Aletheia-Usage" \
    --dashboard-body "$DASHBOARD_BODY" \
    --region "$REGION"
echo -e "${GREEN}Dashboard created: Aletheia-Usage${NC}"

# Step 3: Create SNS topic and alarm
echo "[3/4] Creating SNS topic and alarm..."
SNS_ARN=$(aws sns create-topic \
    --name "Aletheia-CapDenialAlerts" \
    --region "$REGION" \
    --query 'TopicArn' \
    --output text)
echo "  SNS Topic: $SNS_ARN"
echo -e "${YELLOW}NOTE: Subscribe to the SNS topic with your email:${NC}"
echo "  aws sns subscribe --topic-arn $SNS_ARN --protocol email --notification-endpoint YOUR_EMAIL --region $REGION"

# Create alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "Aletheia-CapDenialSpike" \
    --alarm-description "CapDenied > 10 in 1 hour" \
    --namespace "Aletheia/API" \
    --metric-name "CapDenied" \
    --statistic "Sum" \
    --period 3600 \
    --evaluation-periods 1 \
    --threshold 10 \
    --comparison-operator "GreaterThanThreshold" \
    --treat-missing-data "notBreaching" \
    --alarm-actions "$SNS_ARN" \
    --region "$REGION"
echo -e "${GREEN}Alarm created: Aletheia-CapDenialSpike${NC}"

# Issue #391 Phase 5: Create additional alarms
echo "[3b/5] Creating observability alarms..."

# Lambda Errors alarm — fires if any Lambda errors in 5 min
aws cloudwatch put-metric-alarm \
    --alarm-name "Aletheia-LambdaErrors" \
    --alarm-description "Lambda Errors > 0 in 5 minutes" \
    --namespace "AWS/Lambda" \
    --metric-name "Errors" \
    --dimensions Name=FunctionName,Value=AletheiaAgent \
    --statistic "Sum" \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 0 \
    --comparison-operator "GreaterThanThreshold" \
    --treat-missing-data "notBreaching" \
    --alarm-actions "$SNS_ARN" \
    --region "$REGION"
echo -e "${GREEN}Alarm created: Aletheia-LambdaErrors${NC}"

# 4xx Rate alarm — fires if > 50% 4xx in 15 min
aws cloudwatch put-metric-alarm \
    --alarm-name "Aletheia-4xxRate" \
    --alarm-description "4xx Error Rate > 50% in 15 minutes" \
    --namespace "Aletheia/API" \
    --metric-name "ErrorRate" \
    --dimensions Name=StatusClass,Value=4xx \
    --statistic "Average" \
    --period 900 \
    --evaluation-periods 1 \
    --threshold 50 \
    --comparison-operator "GreaterThanThreshold" \
    --treat-missing-data "notBreaching" \
    --alarm-actions "$SNS_ARN" \
    --region "$REGION"
echo -e "${GREEN}Alarm created: Aletheia-4xxRate${NC}"

# 5xx Rate alarm — fires if > 10% 5xx in 15 min
aws cloudwatch put-metric-alarm \
    --alarm-name "Aletheia-5xxRate" \
    --alarm-description "5xx Error Rate > 10% in 15 minutes" \
    --namespace "Aletheia/API" \
    --metric-name "ErrorRate" \
    --dimensions Name=StatusClass,Value=5xx \
    --statistic "Average" \
    --period 900 \
    --evaluation-periods 1 \
    --threshold 10 \
    --comparison-operator "GreaterThanThreshold" \
    --treat-missing-data "notBreaching" \
    --alarm-actions "$SNS_ARN" \
    --region "$REGION"
echo -e "${GREEN}Alarm created: Aletheia-5xxRate${NC}"

# Lambda Throttles alarm — fires if any throttles in 5 min
aws cloudwatch put-metric-alarm \
    --alarm-name "Aletheia-LambdaThrottles" \
    --alarm-description "Lambda Throttles > 0 in 5 minutes" \
    --namespace "AWS/Lambda" \
    --metric-name "Throttles" \
    --dimensions Name=FunctionName,Value=AletheiaAgent \
    --statistic "Sum" \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 0 \
    --comparison-operator "GreaterThanThreshold" \
    --treat-missing-data "notBreaching" \
    --alarm-actions "$SNS_ARN" \
    --region "$REGION"
echo -e "${GREEN}Alarm created: Aletheia-LambdaThrottles${NC}"

# Step 4: Create Contributor Insights rule
echo "[4/4] Creating Contributor Insights rule..."
RULE_DEF=$(poetry run python -c "import json; d=json.load(open('${SCRIPT_DIR}/contributor-insights-top-talkers.json')); print(d['RuleDefinition'])")
MSYS_NO_PATHCONV=1 aws cloudwatch put-insight-rule \
    --rule-name "Aletheia-TopTalkers" \
    --rule-state "ENABLED" \
    --rule-definition "$RULE_DEF" \
    --region "$REGION"
echo -e "${GREEN}Contributor Insights rule created: Aletheia-TopTalkers${NC}"

echo ""
echo "=== CloudWatch Provisioning Complete ==="
echo "  Dashboard: https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards:name=Aletheia-Usage"
echo "  Alarm: Aletheia-CapDenialSpike"
echo "  Insights: Aletheia-TopTalkers"
