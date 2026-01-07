"""
Unit tests for NoArchive Transform Layer (Issue #162).

See: docs/1162-noarchive-transform.md

Tests verify that the noarchive signal correctly skips DynamoDB persistence
while still returning the etymology analysis to the user.
"""
import json
from unittest.mock import MagicMock, patch


from src.lambda_function import lambda_handler


# Safe mock denylist - NO real slurs
MOCK_DENYLIST = {"test_block_term"}


def make_mock_context():
    """Create a mock Lambda context object."""
    ctx = MagicMock()
    ctx.function_name = "test-lambda"
    ctx.memory_limit_in_mb = 128
    ctx.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789:function:test"
    ctx.aws_request_id = "test-request-id"
    return ctx


def make_event(text: str, signals: dict | None = None) -> dict:
    """Create a Lambda event with optional signals."""
    body: dict[str, str | dict] = {
        "text": text,
        "url": "https://example.com/test",
        "title": "Test Page",
        "domContext": "Some context text",
    }
    if signals is not None:
        body["signals"] = signals

    return {"body": json.dumps(body)}


class TestNoArchiveSkipsPersistence:
    """Tests for Issue #162: NoArchive signal skips DynamoDB persistence."""

    @patch("src.lambda_function.get_dynamodb_client")
    @patch("src.lambda_function.get_semantic_guardrail")
    @patch("src.lambda_function.analyze_term")
    def test_noarchive_true_skips_save_state(
        self, mock_analyze, mock_semantic, mock_dynamodb
    ):
        """When signals.noarchive=True, save_state is NOT called."""
        # Setup mocks
        mock_semantic_guard = MagicMock()
        mock_semantic_guard.check_safety.return_value = {
            "is_safe": True,
            "reason": "None",
            "scores": {},
        }
        mock_semantic.return_value = mock_semantic_guard

        mock_analyze.return_value = {
            "status": "success",
            "response": {
                "signal": "Test Signal",
                "gem": "Test etymology",
                "context": "Test context",
            },
            "metadata": {"latency_ms": 100},
        }

        mock_db_client = MagicMock()
        mock_dynamodb.return_value = mock_db_client

        # Call with noarchive=True
        event = make_event("apple", signals={"noarchive": True})
        response = lambda_handler(event, make_mock_context(), denylist=MOCK_DENYLIST)

        # Verify response is still returned
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["signal"] == "Test Signal"
        assert body["gem"] == "Test etymology"

        # Verify DynamoDB put_item was NOT called
        mock_db_client.put_item.assert_not_called()

    @patch("src.lambda_function.get_dynamodb_client")
    @patch("src.lambda_function.get_semantic_guardrail")
    @patch("src.lambda_function.analyze_term")
    def test_no_signals_persists_to_dynamodb(
        self, mock_analyze, mock_semantic, mock_dynamodb
    ):
        """When no signals provided, save_state IS called."""
        # Setup mocks
        mock_semantic_guard = MagicMock()
        mock_semantic_guard.check_safety.return_value = {
            "is_safe": True,
            "reason": "None",
            "scores": {},
        }
        mock_semantic.return_value = mock_semantic_guard

        mock_analyze.return_value = {
            "status": "success",
            "response": {
                "signal": "Test Signal",
                "gem": "Test etymology",
                "context": "Test context",
            },
            "metadata": {"latency_ms": 100},
        }

        mock_db_client = MagicMock()
        mock_dynamodb.return_value = mock_db_client

        # Call without signals
        event = make_event("apple")
        response = lambda_handler(event, make_mock_context(), denylist=MOCK_DENYLIST)

        # Verify response is returned
        assert response["statusCode"] == 200

        # Verify DynamoDB put_item WAS called
        mock_db_client.put_item.assert_called_once()

    @patch("src.lambda_function.get_dynamodb_client")
    @patch("src.lambda_function.get_semantic_guardrail")
    @patch("src.lambda_function.analyze_term")
    def test_noarchive_false_persists_to_dynamodb(
        self, mock_analyze, mock_semantic, mock_dynamodb
    ):
        """When signals.noarchive=False, save_state IS called."""
        # Setup mocks
        mock_semantic_guard = MagicMock()
        mock_semantic_guard.check_safety.return_value = {
            "is_safe": True,
            "reason": "None",
            "scores": {},
        }
        mock_semantic.return_value = mock_semantic_guard

        mock_analyze.return_value = {
            "status": "success",
            "response": {
                "signal": "Test Signal",
                "gem": "Test etymology",
                "context": "Test context",
            },
            "metadata": {"latency_ms": 100},
        }

        mock_db_client = MagicMock()
        mock_dynamodb.return_value = mock_db_client

        # Call with noarchive=False (explicit)
        event = make_event("apple", signals={"noarchive": False})
        response = lambda_handler(event, make_mock_context(), denylist=MOCK_DENYLIST)

        # Verify response is returned
        assert response["statusCode"] == 200

        # Verify DynamoDB put_item WAS called
        mock_db_client.put_item.assert_called_once()

    @patch("src.lambda_function.get_dynamodb_client")
    @patch("src.lambda_function.get_semantic_guardrail")
    @patch("src.lambda_function.analyze_term")
    def test_noarchive_empty_signals_persists(
        self, mock_analyze, mock_semantic, mock_dynamodb
    ):
        """When signals={} (empty), save_state IS called."""
        # Setup mocks
        mock_semantic_guard = MagicMock()
        mock_semantic_guard.check_safety.return_value = {
            "is_safe": True,
            "reason": "None",
            "scores": {},
        }
        mock_semantic.return_value = mock_semantic_guard

        mock_analyze.return_value = {
            "status": "success",
            "response": {
                "signal": "Test Signal",
                "gem": "Test etymology",
                "context": "Test context",
            },
            "metadata": {"latency_ms": 100},
        }

        mock_db_client = MagicMock()
        mock_dynamodb.return_value = mock_db_client

        # Call with empty signals
        event = make_event("apple", signals={})
        response = lambda_handler(event, make_mock_context(), denylist=MOCK_DENYLIST)

        # Verify response is returned
        assert response["statusCode"] == 200

        # Verify DynamoDB put_item WAS called
        mock_db_client.put_item.assert_called_once()

    @patch("src.lambda_function.get_dynamodb_client")
    @patch("src.lambda_function.get_semantic_guardrail")
    @patch("src.lambda_function.analyze_term")
    def test_response_structure_same_regardless_of_noarchive(
        self, mock_analyze, mock_semantic, mock_dynamodb
    ):
        """Response structure is identical whether noarchive is True or False."""
        # Setup mocks
        mock_semantic_guard = MagicMock()
        mock_semantic_guard.check_safety.return_value = {
            "is_safe": True,
            "reason": "None",
            "scores": {},
        }
        mock_semantic.return_value = mock_semantic_guard

        mock_analyze.return_value = {
            "status": "success",
            "response": {
                "signal": "Test Signal",
                "gem": "Test etymology",
                "context": "Test context",
            },
            "metadata": {"latency_ms": 100},
        }

        mock_db_client = MagicMock()
        mock_dynamodb.return_value = mock_db_client

        # Call with noarchive=True
        event_noarchive = make_event("apple", signals={"noarchive": True})
        response_noarchive = lambda_handler(
            event_noarchive, make_mock_context(), denylist=MOCK_DENYLIST
        )

        # Reset mock for second call
        mock_db_client.reset_mock()

        # Call without noarchive
        event_normal = make_event("apple")
        response_normal = lambda_handler(
            event_normal, make_mock_context(), denylist=MOCK_DENYLIST
        )

        # Both should return 200
        assert response_noarchive["statusCode"] == 200
        assert response_normal["statusCode"] == 200

        # Both should have same response structure
        body_noarchive = json.loads(response_noarchive["body"])
        body_normal = json.loads(response_normal["body"])

        assert "signal" in body_noarchive
        assert "gem" in body_noarchive
        assert "context" in body_noarchive
        assert "thread_id" in body_noarchive

        assert "signal" in body_normal
        assert "gem" in body_normal
        assert "context" in body_normal
        assert "thread_id" in body_normal
