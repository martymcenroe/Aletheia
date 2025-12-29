#!/bin/bash
# AWS Account Inventory Check
# Run this to see what resources exist

echo "=== AWS Account Inventory ==="
echo ""

echo "--- IAM Users ---"
aws iam list-users --query 'Users[*].[UserName,CreateDate]' --output table

echo ""
echo "--- IAM Roles ---"
aws iam list-roles --query 'Roles[*].[RoleName,CreateDate]' --output table | head -20

echo ""
echo "--- Access Keys ---"
aws iam list-access-keys --query 'AccessKeyMetadata[*].[AccessKeyId,Status,CreateDate]' --output table

echo ""
echo "--- Lambda Functions ---"
aws lambda list-functions --query 'Functions[*].[FunctionName,Runtime,LastModified]' --output table

echo ""
echo "--- DynamoDB Tables ---"
aws dynamodb list-tables --query 'TableNames' --output table

echo ""
echo "--- S3 Buckets ---"
aws s3 ls

echo ""
echo "--- CloudWatch Log Groups ---"
aws logs describe-log-groups --query 'logGroups[*].[logGroupName,storedBytes]' --output table

echo ""
echo "--- API Gateway APIs ---"
aws apigateway get-rest-apis --query 'items[*].[name,id,createdDate]' --output table

echo ""
echo "--- Bedrock Access ---"
aws bedrock list-foundation-models --query 'modelSummaries[0:5].[modelId,modelName]' --output table 2>/dev/null || echo "Bedrock: No access or not enabled"

echo ""
echo "=== Cost & Billing ==="
echo "Current month charges (approximate):"
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d 'month start' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
  --output text 2>/dev/null || echo "Cost Explorer: Not enabled or no access"

echo ""
echo "=== Inventory Complete ==="
