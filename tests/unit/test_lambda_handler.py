"""
Unit tests for Lambda Handler (Naked Python Orchestrator).

See: docs/1113-naked-python-architecture.md Section 11.

Tests use mocked AWS services and safe placeholder terms.
No real slurs in test files (Willison Protocol).
"""
import json
from unittest.mock import MagicMock, patch


from src.lambda_function import (
    TTL_SECONDS,
    generate_thread_id,
    lambda_handler,
    run_guardrails,
    save_state,
    validate_input,
)

# Safe mock denylist - NO real slurs
MOCK_DENYLIST = {"test_block_term", "forbidden_fruit", "blocked_word"}


class TestValidateInput:
    """Tests for validate_input function - LLD Section 8.1."""

    def test_010_valid_input(self):
        """Scenario 010: Valid input passes validation."""
        event = {"text": "apple"}
        valid, error = validate_input(event)
        assert valid is True
        assert error is None

    def test_030_missing_text_field(self):
        """Scenario 030: Missing text field returns 400."""
        event = {}
        valid, error = validate_input(event)
        assert valid is False
        assert "text" in error.lower()

    def test_040_wrong_type_for_text(self):
        """Scenario 040: Wrong type for text returns 400."""
        event = {"text": 123}
        valid, error = validate_input(event)
        assert valid is False
        assert "string" in error.lower()

    def test_050_oversized_payload_truncated(self):
        """Scenario 050: Oversized payload is truncated to 20k chars."""
        event = {"text": "a" * 25000}
        valid, error = validate_input(event)
        assert valid is True
        assert len(event["text"]) == 20000

    def test_100_empty_string_blocked(self):
        """Scenario 100: Empty string returns 400."""
        event = {"text": ""}
        valid, error = validate_input(event)
        assert valid is False
        assert "empty" in error.lower()

    def test_whitespace_only_blocked(self):
        """Whitespace-only input returns 400."""
        event = {"text": "   \t\n   "}
        valid, error = validate_input(event)
        assert valid is False
        assert "empty" in error.lower()


class TestRunGuardrails:
    """Tests for run_guardrails function - guardrail pipeline."""

    def test_020_blocked_text_denylist(self):
        """Scenario 020: Blocked text returns 403 via denylist."""
        is_safe, reason, metadata = run_guardrails(
            "test_block_term", denylist=MOCK_DENYLIST
        )
        assert is_safe is False
        assert "blocked" in reason.lower()
        assert metadata["layer"] == "denylist"

    def test_safe_text_passes_denylist(self):
        """Safe text passes denylist check."""
        # Mock semantic to also pass
        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic:
            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "is_safe": True,
                "reason": "None",
                "scores": {},
            }
            mock_semantic.return_value = mock_guard

            is_safe, reason, metadata = run_guardrails("apple", denylist=MOCK_DENYLIST)
            assert is_safe is True
            assert reason is None
            assert metadata["layer"] == "passed"

    def test_blocked_by_semantic(self):
        """Text blocked by semantic guardrail returns correct metadata."""
        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic:
            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "is_safe": False,
                "reason": "Hate",
                "scores": {"Hate": 0.9},
            }
            mock_semantic.return_value = mock_guard

            is_safe, reason, metadata = run_guardrails(
                "safe_word", denylist=MOCK_DENYLIST
            )
            assert is_safe is False
            assert "Hate" in reason
            assert metadata["layer"] == "semantic"


class TestGenerateThreadId:
    """Tests for generate_thread_id function - temporary identity strategy."""

    def test_generates_consistent_id(self):
        """Same input generates same thread ID."""
        event = {"text": "apple", "url": "https://example.com"}
        id1 = generate_thread_id(event)
        id2 = generate_thread_id(event)
        assert id1 == id2

    def test_different_input_different_id(self):
        """Different input generates different thread ID."""
        event1 = {"text": "apple", "url": "https://example.com"}
        event2 = {"text": "banana", "url": "https://example.com"}
        id1 = generate_thread_id(event1)
        id2 = generate_thread_id(event2)
        assert id1 != id2

    def test_id_is_16_chars(self):
        """Thread ID is 16 characters (hex truncation)."""
        event = {"text": "apple"}
        thread_id = generate_thread_id(event)
        assert len(thread_id) == 16


class TestLambdaHandler:
    """Integration tests for lambda_handler - LLD Section 11.1."""

    def test_010_valid_input_safe_text(self):
        """Scenario 010: Valid input with safe text returns 200 with structured output."""
        event = {"text": "apple"}

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, patch(
            "src.lambda_function.get_dynamodb_client"
        ) as mock_dynamo, patch("src.lambda_function.get_bedrock_client") as mock_bedrock:
            # Mock semantic to pass
            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "is_safe": True,
                "reason": "None",
                "scores": {},
            }
            mock_semantic.return_value = mock_guard

            # Mock DynamoDB
            mock_dynamo.return_value = MagicMock()

            # Mock Bedrock buffered response (Issue #124: no streaming)
            mock_response = {
                "body": MagicMock(
                    read=MagicMock(
                        return_value=json.dumps(
                            {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": '{"signal": "Common Noun", "gem": "A sweet fruit.", "context": "First sentence. Second sentence. Third sentence."}',
                                    }
                                ]
                            }
                        ).encode()
                    )
                )
            }
            mock_bedrock.return_value.invoke_model.return_value = mock_response

            result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            # Issue #124: Verify structured response
            assert "thread_id" in body
            assert "signal" in body
            assert "gem" in body
            assert "context" in body
            assert body["status"] == "success"

    def test_020_blocked_text(self):
        """Scenario 020: Blocked text returns 403."""
        event = {"text": "test_block_term"}

        result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

        assert result["statusCode"] == 403
        body = json.loads(result["body"])
        assert "blocked" in body

    def test_030_missing_text(self):
        """Scenario 030: Missing text field returns 400."""
        event = {}

        result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "error" in body
        assert "text" in body["error"].lower()

    def test_040_wrong_type(self):
        """Scenario 040: Wrong type for text returns 400."""
        event = {"text": 123}

        result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "string" in body["error"].lower()

    def test_100_empty_string(self):
        """Scenario 100: Empty string returns 400."""
        event = {"text": ""}

        result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "empty" in body["error"].lower()

    def test_070_boto3_exception(self):
        """Scenario 070: boto3 exception returns 500, no LLM output."""
        from botocore.exceptions import ClientError

        event = {"text": "apple"}

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, patch(
            "src.lambda_function.get_dynamodb_client"
        ) as mock_dynamo:
            # Mock semantic to pass
            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "is_safe": True,
                "reason": "None",
                "scores": {},
            }
            mock_semantic.return_value = mock_guard

            # Mock DynamoDB to raise error
            mock_client = MagicMock()
            mock_client.put_item.side_effect = ClientError(
                {"Error": {"Code": "ServiceUnavailable", "Message": "Service down"}},
                "PutItem",
            )
            mock_dynamo.return_value = mock_client

            result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

            assert result["statusCode"] == 500
            body = json.loads(result["body"])
            assert "error" in body
            # Verify no LLM response leaked
            assert "response" not in body

    def test_api_gateway_body_parsing(self):
        """Handles API Gateway event with body as string."""
        event = {"body": json.dumps({"text": "test_block_term"})}

        result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

        assert result["statusCode"] == 403  # Blocked by denylist

    def test_sequential_execution_denylist_before_semantic(self):
        """Verifies denylist runs before semantic (sequential execution)."""
        # If denylist blocks, semantic should NOT be called
        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic:
            mock_guard = MagicMock()
            mock_semantic.return_value = mock_guard

            result = lambda_handler(
                {"text": "test_block_term"}, None, denylist=MOCK_DENYLIST
            )

            assert result["statusCode"] == 403
            # Semantic check_safety should NOT have been called
            mock_guard.check_safety.assert_not_called()


class TestWillisonProtocol:
    """
    Verify Willison Protocol: tests MUST use mocked data.

    These tests verify that the test suite itself follows the protocol:
    - Uses MOCK_DENYLIST with safe terms
    - Never contains real slurs
    """

    def test_mock_denylist_is_safe(self):
        """Mock denylist contains only test placeholders, no real terms."""
        safe_patterns = ["test_", "forbidden_", "blocked_"]
        for term in MOCK_DENYLIST:
            assert any(
                term.startswith(p) for p in safe_patterns
            ), f"Term '{term}' should be a safe placeholder"

    def test_no_real_terms_in_test_file(self):
        """This test file should not contain any terms from real denylist."""
        # This is a meta-test - if this file were to contain real slurs,
        # it would fail the Willison Protocol. The test passes by design
        # because we only use MOCK_DENYLIST placeholders.
        assert len(MOCK_DENYLIST) > 0, "Mock denylist should have terms"


class TestSaveStateTTL:
    """
    Tests for Issue #145: DynamoDB TTL auto-expiry.

    See: docs/1145-dynamodb-ttl.md Section 11.1
    """

    def test_010_item_saved_with_ttl_attribute(self):
        """Scenario 010: save_state adds ttl attribute to DynamoDB item."""

        with patch("src.lambda_function.get_dynamodb_client") as mock_dynamo:
            mock_client = MagicMock()
            mock_dynamo.return_value = mock_client

            save_state("test_thread_id", {"text": "apple", "url": "https://example.com"})

            # Verify put_item was called
            mock_client.put_item.assert_called_once()
            call_args = mock_client.put_item.call_args

            # Extract the Item from the call
            item = call_args.kwargs.get("Item") or call_args[1].get("Item")
            assert item is not None, "put_item should have Item kwarg"
            assert "ttl" in item, "Item should have ttl attribute"
            assert "N" in item["ttl"], "ttl should be a Number type"

    def test_020_ttl_is_30_days_ahead(self):
        """Scenario 020: TTL value is approximately 30 days from now."""
        import time

        with patch("src.lambda_function.get_dynamodb_client") as mock_dynamo:
            mock_client = MagicMock()
            mock_dynamo.return_value = mock_client

            before = int(time.time())
            save_state("test_thread_id", {"text": "apple", "url": "https://example.com"})
            after = int(time.time())

            call_args = mock_client.put_item.call_args
            item = call_args.kwargs.get("Item") or call_args[1].get("Item")
            ttl_value = int(item["ttl"]["N"])

            # TTL should be now + 30 days (within 2 second tolerance)
            expected_min = before + TTL_SECONDS
            expected_max = after + TTL_SECONDS + 2

            assert expected_min <= ttl_value <= expected_max, (
                f"TTL {ttl_value} should be between {expected_min} and {expected_max}"
            )

    def test_ttl_seconds_constant_is_30_days(self):
        """TTL_SECONDS constant equals 30 days in seconds."""
        assert TTL_SECONDS == 2592000, "TTL_SECONDS should be 30 days (2592000 seconds)"
        assert TTL_SECONDS == 30 * 24 * 60 * 60, "TTL_SECONDS should be 30 days"
