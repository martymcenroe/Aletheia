"""
Unit tests for Lambda Auth Function - GDPR Data Erasure.

Issue #213: Mock DynamoDB and verify GDPR erasure logic.

Target: src/lambda_auth_function.py (specifically delete_user_data)
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.lambda_auth_function import (
    delete_user_data,
    handle_delete_my_data,
    AGENT_STATE_TABLE,
)


class TestDeleteUserData:
    """Tests for delete_user_data function - GDPR Article 17 erasure.

    Issue #147: Right to Erasure implementation.
    """

    def test_deletes_single_page_items(self):
        """Deletes all items for user when results fit in single page."""
        mock_client = MagicMock()

        # Single page of results (no LastEvaluatedKey)
        mock_client.query.return_value = {
            "Items": [
                {"thread_id": {"S": "thread-001"}, "checkpoint_id": {"S": "cp-001"}},
                {"thread_id": {"S": "thread-002"}, "checkpoint_id": {"S": "cp-002"}},
            ]
        }

        with patch("src.lambda_auth_function.get_dynamodb_client", return_value=mock_client):
            count = delete_user_data("user-123")

        assert count == 2
        assert mock_client.delete_item.call_count == 2

        # Verify correct keys used for deletion
        mock_client.delete_item.assert_any_call(
            TableName=AGENT_STATE_TABLE,
            Key={
                "thread_id": {"S": "thread-001"},
                "checkpoint_id": {"S": "cp-001"},
            }
        )
        mock_client.delete_item.assert_any_call(
            TableName=AGENT_STATE_TABLE,
            Key={
                "thread_id": {"S": "thread-002"},
                "checkpoint_id": {"S": "cp-002"},
            }
        )

    def test_handles_pagination(self):
        """Handles paginated results for users with many items."""
        mock_client = MagicMock()

        # First page with continuation token
        first_page = {
            "Items": [
                {"thread_id": {"S": "thread-001"}, "checkpoint_id": {"S": "cp-001"}},
            ],
            "LastEvaluatedKey": {"thread_id": {"S": "thread-001"}},
        }

        # Second page (final)
        second_page = {
            "Items": [
                {"thread_id": {"S": "thread-002"}, "checkpoint_id": {"S": "cp-002"}},
            ]
        }

        mock_client.query.side_effect = [first_page, second_page]

        with patch("src.lambda_auth_function.get_dynamodb_client", return_value=mock_client):
            count = delete_user_data("user-123")

        assert count == 2
        assert mock_client.query.call_count == 2
        assert mock_client.delete_item.call_count == 2

    def test_no_items_returns_zero(self):
        """Returns 0 when user has no items to delete."""
        mock_client = MagicMock()
        mock_client.query.return_value = {"Items": []}

        with patch("src.lambda_auth_function.get_dynamodb_client", return_value=mock_client):
            count = delete_user_data("user-with-no-data")

        assert count == 0
        mock_client.delete_item.assert_not_called()

    def test_uses_correct_gsi_index(self):
        """Queries use the user_id-index GSI."""
        mock_client = MagicMock()
        mock_client.query.return_value = {"Items": []}

        with patch("src.lambda_auth_function.get_dynamodb_client", return_value=mock_client):
            delete_user_data("user-123")

        # Verify GSI query parameters
        call_kwargs = mock_client.query.call_args.kwargs
        assert call_kwargs["IndexName"] == "user_id-index"
        assert call_kwargs["KeyConditionExpression"] == "user_id = :uid"
        assert call_kwargs["ExpressionAttributeValues"] == {":uid": {"S": "user-123"}}

    def test_raises_on_dynamodb_error(self):
        """Raises ClientError when DynamoDB fails."""
        mock_client = MagicMock()
        mock_client.query.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "DB error"}},
            "Query"
        )

        with patch("src.lambda_auth_function.get_dynamodb_client", return_value=mock_client):
            with pytest.raises(ClientError):
                delete_user_data("user-123")

    def test_raises_on_delete_error(self):
        """Raises ClientError when delete_item fails."""
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "Items": [
                {"thread_id": {"S": "thread-001"}, "checkpoint_id": {"S": "cp-001"}},
            ]
        }
        mock_client.delete_item.side_effect = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": "Failed"}},
            "DeleteItem"
        )

        with patch("src.lambda_auth_function.get_dynamodb_client", return_value=mock_client):
            with pytest.raises(ClientError):
                delete_user_data("user-123")


class TestHandleDeleteMyData:
    """Tests for handle_delete_my_data endpoint handler.

    Issue #147: GDPR Article 17 data erasure endpoint.
    """

    def test_successful_deletion_returns_200(self):
        """Successful deletion returns 200 with item count."""
        with patch("src.lambda_auth_function.get_linkedin_user_info") as mock_userinfo, \
             patch("src.lambda_auth_function.delete_user_data") as mock_delete:
            mock_userinfo.return_value = {"sub": "linkedin-user-123", "name": "Test User"}
            mock_delete.return_value = 5

            result = handle_delete_my_data({"Authorization": "Bearer valid-token"})

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["success"] is True
        assert body["itemsDeleted"] == 5
        assert "deleted" in body["message"].lower()

    def test_missing_auth_header_returns_401(self):
        """Missing Authorization header returns 401."""
        result = handle_delete_my_data({})

        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert "Authorization" in body["error"]

    def test_invalid_auth_format_returns_401(self):
        """Non-Bearer auth format returns 401."""
        result = handle_delete_my_data({"Authorization": "Basic credentials"})

        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert "Authorization" in body["error"]

    def test_invalid_token_returns_401(self):
        """Invalid token returns 401."""
        with patch("src.lambda_auth_function.get_linkedin_user_info") as mock_userinfo:
            mock_userinfo.return_value = None  # Invalid token

            result = handle_delete_my_data({"Authorization": "Bearer invalid-token"})

        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert "Invalid token" in body["error"]

    def test_dynamodb_error_returns_500(self):
        """DynamoDB error returns 500."""
        with patch("src.lambda_auth_function.get_linkedin_user_info") as mock_userinfo, \
             patch("src.lambda_auth_function.delete_user_data") as mock_delete:
            mock_userinfo.return_value = {"sub": "linkedin-user-123", "name": "Test User"}
            mock_delete.side_effect = ClientError(
                {"Error": {"Code": "InternalServerError", "Message": "DB error"}},
                "Query"
            )

            result = handle_delete_my_data({"Authorization": "Bearer valid-token"})

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "failed" in body["error"].lower()

    def test_lowercase_authorization_header_works(self):
        """Handles lowercase 'authorization' header (HTTP/2 normalization)."""
        with patch("src.lambda_auth_function.get_linkedin_user_info") as mock_userinfo, \
             patch("src.lambda_auth_function.delete_user_data") as mock_delete:
            mock_userinfo.return_value = {"sub": "linkedin-user-123", "name": "Test User"}
            mock_delete.return_value = 2

            result = handle_delete_my_data({"authorization": "Bearer valid-token"})

        assert result["statusCode"] == 200

    def test_extracts_user_id_from_token(self):
        """Extracts LinkedIn 'sub' claim for deletion."""
        with patch("src.lambda_auth_function.get_linkedin_user_info") as mock_userinfo, \
             patch("src.lambda_auth_function.delete_user_data") as mock_delete:
            mock_userinfo.return_value = {"sub": "specific-linkedin-id", "name": "Test User"}
            mock_delete.return_value = 0

            handle_delete_my_data({"Authorization": "Bearer valid-token"})

        # Verify delete_user_data called with correct user_id
        mock_delete.assert_called_once_with("specific-linkedin-id")


class TestGDPRCompliance:
    """Tests verifying GDPR Article 17 compliance requirements."""

    def test_deletion_requires_identity_verification(self):
        """User must prove identity before deletion (OAuth token required)."""
        # No token = no deletion
        result = handle_delete_my_data({})
        assert result["statusCode"] == 401

    def test_all_user_data_queried_for_deletion(self):
        """All user data in agent state table is queried for deletion."""
        mock_client = MagicMock()
        mock_client.query.return_value = {"Items": []}

        with patch("src.lambda_auth_function.get_dynamodb_client", return_value=mock_client):
            delete_user_data("user-123")

        # Verify query targets user's data
        call_kwargs = mock_client.query.call_args.kwargs
        assert "user_id = :uid" in call_kwargs["KeyConditionExpression"]
        assert call_kwargs["ExpressionAttributeValues"][":uid"]["S"] == "user-123"

    def test_deletion_returns_count_for_transparency(self):
        """Response includes count of deleted items for user transparency."""
        with patch("src.lambda_auth_function.get_linkedin_user_info") as mock_userinfo, \
             patch("src.lambda_auth_function.delete_user_data") as mock_delete:
            mock_userinfo.return_value = {"sub": "user-123", "name": "Test User"}
            mock_delete.return_value = 42

            result = handle_delete_my_data({"Authorization": "Bearer valid-token"})

        body = json.loads(result["body"])
        assert body["itemsDeleted"] == 42
