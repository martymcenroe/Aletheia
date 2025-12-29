#!/bin/bash
# AWS Cleanup Script - Chore #21
# Deletes old certification resources, keeps Aletheia production

set -e  # Exit on any error

echo "=========================================="
echo "AWS CLEANUP - OLD CERTIFICATION RESOURCES"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will DELETE the following:"
echo ""
echo "❌ DynamoDB Table: VocabularyLog (us-east-2)"
echo "❌ Lambda Function: processVocabularyRequest (us-east-2)"
echo "❌ IAM Role: processVocabularyRequest-role-b6wce27j"
echo "❌ IAM Policy: AWSLambdaBasicExecutionRole-11024561-..."
echo "❌ KMS Key: d592b89f-d400-4e61-9982-1d3d9d64be5b (us-east-2) - if unused"
echo ""
echo "✅ KEEPING (Aletheia Production):"
echo "✅ DynamoDB Table: AletheiaAgentState (us-east-1)"
echo "✅ Lambda Function: AletheiaAgent (us-east-1)"
echo "✅ IAM Role: AletheiaLambdaRole"
echo "✅ IAM User: aletheia-developer (YOU - currently logged in)"
echo "✅ IAM User: IAM-martymcenroe (for future certifications)"
echo "✅ KMS Key: 93147945-... (us-east-1) - probably Aletheia"
echo ""
echo "=========================================="
echo ""

# Function to check if we're logged in as aletheia-developer
check_identity() {
    echo "Verifying identity..."
    CURRENT_USER=$(aws sts get-caller-identity --query 'Arn' --output text)
    if [[ ! "$CURRENT_USER" == *"aletheia-developer"* ]]; then
        echo "❌ ERROR: You must be logged in as 'aletheia-developer'"
        echo "Current identity: $CURRENT_USER"
        exit 1
    fi
    echo "✅ Logged in as: aletheia-developer"
    echo ""
}

# Safety check
safety_check() {
    echo "=========================================="
    echo "SAFETY CHECK"
    echo "=========================================="
    echo ""

    # Check if Aletheia resources exist
    echo "Checking Aletheia production resources..."

    ALETHEIA_TABLE=$(aws dynamodb list-tables --region us-east-1 --query 'TableNames[?contains(@, `AletheiaAgentState`)]' --output text)
    ALETHEIA_LAMBDA=$(aws lambda list-functions --region us-east-1 --query 'Functions[?FunctionName==`AletheiaAgent`].FunctionName' --output text)

    if [[ -z "$ALETHEIA_TABLE" ]] || [[ -z "$ALETHEIA_LAMBDA" ]]; then
        echo "⚠️  WARNING: Aletheia resources not found!"
        echo "   DynamoDB: $ALETHEIA_TABLE"
        echo "   Lambda: $ALETHEIA_LAMBDA"
        echo ""
        read -p "Continue anyway? (yes/no): " CONTINUE
        if [[ "$CONTINUE" != "yes" ]]; then
            echo "Aborted."
            exit 1
        fi
    else
        echo "✅ AletheiaAgentState table exists (us-east-1)"
        echo "✅ AletheiaAgent lambda exists (us-east-1)"
    fi
    echo ""
}

# Confirm deletion
confirm_deletion() {
    echo "=========================================="
    read -p "Type 'DELETE' to proceed with deletion: " CONFIRM
    echo "=========================================="
    if [[ "$CONFIRM" != "DELETE" ]]; then
        echo "Aborted. No resources were deleted."
        exit 0
    fi
    echo ""
}

# Delete old Lambda function
delete_old_lambda() {
    echo "🗑️  Deleting Lambda: processVocabularyRequest (us-east-2)..."
    aws lambda delete-function \
        --function-name processVocabularyRequest \
        --region us-east-2 2>/dev/null && echo "✅ Deleted" || echo "⚠️  Not found or already deleted"
    echo ""
}

# Delete old DynamoDB table
delete_old_dynamodb() {
    echo "🗑️  Deleting DynamoDB: VocabularyLog (us-east-2)..."
    aws dynamodb delete-table \
        --table-name VocabularyLog \
        --region us-east-2 2>/dev/null && echo "✅ Deletion initiated (takes ~1 minute)" || echo "⚠️  Not found or already deleted"
    echo ""
}

# Delete old IAM role
delete_old_iam_role() {
    echo "🗑️  Deleting IAM Role: processVocabularyRequest-role-b6wce27j..."

    # First, detach all policies
    echo "   Detaching policies..."
    ATTACHED_POLICIES=$(aws iam list-attached-role-policies \
        --role-name processVocabularyRequest-role-b6wce27j \
        --query 'AttachedPolicies[*].PolicyArn' \
        --output text 2>/dev/null)

    for POLICY_ARN in $ATTACHED_POLICIES; do
        echo "   - Detaching: $POLICY_ARN"
        aws iam detach-role-policy \
            --role-name processVocabularyRequest-role-b6wce27j \
            --policy-arn "$POLICY_ARN" 2>/dev/null
    done

    # Delete the role
    aws iam delete-role \
        --role-name processVocabularyRequest-role-b6wce27j 2>/dev/null && echo "✅ Deleted" || echo "⚠️  Not found or already deleted"
    echo ""
}

# Delete old IAM policy
delete_old_iam_policy() {
    echo "🗑️  Deleting IAM Policy: AWSLambdaBasicExecutionRole-11024561-..."
    POLICY_ARN="arn:aws:iam::383687041805:policy/service-role/AWSLambdaBasicExecutionRole-11024561-7297-4e69-8bee-f01049fdef14"

    aws iam delete-policy \
        --policy-arn "$POLICY_ARN" 2>/dev/null && echo "✅ Deleted" || echo "⚠️  Not found or already deleted"
    echo ""
}

# Delete old IAM user (NOT CALLED - kept for reference)
# User decided to preserve IAM-martymcenroe for future certifications
delete_old_iam_user() {
    echo "🗑️  Deleting IAM User: IAM-martymcenroe..."

    # Delete access keys first
    echo "   Deleting access keys..."
    ACCESS_KEYS=$(aws iam list-access-keys \
        --user-name IAM-martymcenroe \
        --query 'AccessKeyMetadata[*].AccessKeyId' \
        --output text 2>/dev/null)

    for KEY in $ACCESS_KEYS; do
        echo "   - Deleting key: $KEY"
        aws iam delete-access-key \
            --user-name IAM-martymcenroe \
            --access-key-id "$KEY" 2>/dev/null
    done

    # Deactivate MFA device
    echo "   Deactivating MFA device..."
    MFA_DEVICE=$(aws iam list-mfa-devices \
        --user-name IAM-martymcenroe \
        --query 'MFADevices[0].SerialNumber' \
        --output text 2>/dev/null)

    if [[ "$MFA_DEVICE" != "None" ]] && [[ ! -z "$MFA_DEVICE" ]]; then
        echo "   - Deactivating: $MFA_DEVICE"
        aws iam deactivate-mfa-device \
            --user-name IAM-martymcenroe \
            --serial-number "$MFA_DEVICE" 2>/dev/null

        echo "   - Deleting virtual MFA device..."
        aws iam delete-virtual-mfa-device \
            --serial-number "$MFA_DEVICE" 2>/dev/null
    fi

    # Detach all policies
    echo "   Detaching policies..."
    ATTACHED_POLICIES=$(aws iam list-attached-user-policies \
        --user-name IAM-martymcenroe \
        --query 'AttachedPolicies[*].PolicyArn' \
        --output text 2>/dev/null)

    for POLICY_ARN in $ATTACHED_POLICIES; do
        echo "   - Detaching: $POLICY_ARN"
        aws iam detach-user-policy \
            --user-name IAM-martymcenroe \
            --policy-arn "$POLICY_ARN" 2>/dev/null
    done

    # Delete the user
    aws iam delete-user \
        --user-name IAM-martymcenroe 2>/dev/null && echo "✅ Deleted" || echo "⚠️  Not found or already deleted"
    echo ""
}

# Check KMS key usage
check_kms_key() {
    echo "🔍 Checking KMS Key: d592b89f-d400-4e61-9982-1d3d9d64be5b (us-east-2)..."

    KEY_ID="d592b89f-d400-4e61-9982-1d3d9d64be5b"
    KEY_STATE=$(aws kms describe-key \
        --key-id "$KEY_ID" \
        --region us-east-2 \
        --query 'KeyMetadata.KeyState' \
        --output text 2>/dev/null)

    if [[ -z "$KEY_STATE" ]]; then
        echo "⚠️  Key not found or already deleted"
    else
        echo "   Key State: $KEY_STATE"
        echo ""
        echo "⚠️  KMS keys cannot be immediately deleted (AWS requires 7-30 day waiting period)"
        echo "   To schedule deletion:"
        echo "   aws kms schedule-key-deletion --key-id $KEY_ID --region us-east-2 --pending-window-in-days 7"
        echo ""
        read -p "Schedule this KMS key for deletion in 7 days? (yes/no): " DELETE_KMS
        if [[ "$DELETE_KMS" == "yes" ]]; then
            aws kms schedule-key-deletion \
                --key-id "$KEY_ID" \
                --region us-east-2 \
                --pending-window-in-days 7 2>/dev/null && echo "✅ Scheduled for deletion in 7 days" || echo "❌ Failed to schedule"
        else
            echo "⏭️  Skipped KMS key deletion"
        fi
    fi
    echo ""
}

# Main execution
main() {
    check_identity
    safety_check
    confirm_deletion

    echo "=========================================="
    echo "STARTING DELETION"
    echo "=========================================="
    echo ""

    delete_old_lambda
    delete_old_dynamodb
    delete_old_iam_role
    delete_old_iam_policy
    check_kms_key

    echo "=========================================="
    echo "CLEANUP COMPLETE"
    echo "=========================================="
    echo ""
    echo "✅ Old certification resources deleted"
    echo "✅ Aletheia production resources preserved"
    echo "✅ IAM-martymcenroe user preserved (for future certifications)"
    echo ""
    echo "Verify cleanup:"
    echo "  aws dynamodb list-tables --region us-east-2"
    echo "  aws lambda list-functions --region us-east-2"
    echo "  aws iam list-users"
    echo ""
    echo "Chore #21 complete! 🎉"
}

# Run it
main
