"""Tests for admin ID resolution CLI.

Issue #376: Admin ID Resolution CLI.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from src.auth.anonymize import anonymize_user_id
from tools.admin_id_resolve import forward_resolve, reverse_resolve


class TestForwardResolve:
    """Forward resolution: user_id -> anonymized hash."""

    def test_returns_user_id_and_hash(self):
        """Forward resolve returns both the input and its hash."""
        result = forward_resolve("user123")
        assert result["user_id"] == "user123"
        assert result["anonymized_hash"] == anonymize_user_id("user123")

    def test_hash_is_12_chars(self):
        """Hash output is 12 characters."""
        result = forward_resolve("test@example.com")
        assert len(result["anonymized_hash"]) == 12

    def test_deterministic(self):
        """Same input always produces same output."""
        r1 = forward_resolve("user_abc")
        r2 = forward_resolve("user_abc")
        assert r1 == r2


class TestReverseResolve:
    """Reverse resolution: anonymized hash -> user_id (with PII guard)."""

    def test_dry_run_refuses_without_confirm(self):
        """Without --confirm, reverse lookup returns dry_run status."""
        result = reverse_resolve("abcdef123456", dry_run=True)
        assert result["status"] == "dry_run"
        assert "PII" in result["message"]

    @patch("tools.admin_id_resolve.get_dynamodb_client")
    def test_finds_matching_user(self, mock_get_client):
        """Reverse resolve finds the user whose hash matches."""
        target_user = "linkedin|abc123"
        target_hash = anonymize_user_id(target_user)

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Items": [
                    {"user_id": {"S": "other_user"}},
                    {"user_id": {"S": target_user}},
                    {"user_id": {"S": "another_user"}},
                ]
            }
        ]

        result = reverse_resolve(target_hash, dry_run=False)
        assert result["status"] == "found"
        assert result["user_id"] == target_user
        assert result["anonymized_hash"] == target_hash
        assert result["users_scanned"] == 2

    @patch("tools.admin_id_resolve.get_dynamodb_client")
    def test_not_found(self, mock_get_client):
        """Reverse resolve returns not_found when no user matches."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Items": [
                    {"user_id": {"S": "user_a"}},
                    {"user_id": {"S": "user_b"}},
                ]
            }
        ]

        result = reverse_resolve("000000000000", dry_run=False)
        assert result["status"] == "not_found"
        assert result["users_scanned"] == 2

    @patch("tools.admin_id_resolve.get_dynamodb_client")
    def test_empty_table(self, mock_get_client):
        """Reverse resolve handles empty users table."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Items": []}]

        result = reverse_resolve("abcdef123456", dry_run=False)
        assert result["status"] == "not_found"
        assert result["users_scanned"] == 0

    @patch("tools.admin_id_resolve.get_dynamodb_client")
    def test_dynamo_error(self, mock_get_client):
        """Reverse resolve returns error on DynamoDB failure."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
            "Scan",
        )

        result = reverse_resolve("abcdef123456", dry_run=False)
        assert result["status"] == "error"
