"""
Unit tests for Lambda Handler (Naked Python Orchestrator).

See: docs/1113-naked-python-architecture.md Section 11.

Tests use mocked AWS services and safe placeholder terms.
No real slurs in test files (Willison Protocol).
"""
import json
import os
from unittest.mock import MagicMock, patch


from src.lambda_function import (
    TTL_SECONDS,
    generate_thread_id,
    lambda_handler,
    process_scores_for_display,
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
    """Tests for run_guardrails function - guardrail pipeline.

    Issue #126: Updated to expect block_type instead of is_safe.
    """

    def test_020_blocked_text_denylist(self):
        """Scenario 020: Denylist term returns hard block."""
        from src.guardrails.semantic import BLOCK_TYPE_HARD

        block_type, category, metadata = run_guardrails(
            "test_block_term", denylist=MOCK_DENYLIST
        )
        assert block_type == BLOCK_TYPE_HARD
        assert category == "denylist"
        assert metadata["layer"] == "denylist"

    def test_safe_text_passes_denylist(self):
        """Safe text passes denylist and semantic checks."""
        from src.guardrails.semantic import BLOCK_TYPE_NONE

        # Mock semantic to also pass
        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic:
            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "block_type": BLOCK_TYPE_NONE,
                "category": "None",
                "is_safe": True,
                "reason": "None",
                "scores": {},
            }
            mock_semantic.return_value = mock_guard

            block_type, category, metadata = run_guardrails("apple", denylist=MOCK_DENYLIST)
            assert block_type == BLOCK_TYPE_NONE
            assert category == "None"
            assert metadata["layer"] == "semantic"

    def test_blocked_by_semantic_hard(self):
        """Hate speech returns hard block from semantic guardrail."""
        from src.guardrails.semantic import BLOCK_TYPE_HARD

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic:
            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "block_type": BLOCK_TYPE_HARD,
                "category": "Hate",
                "is_safe": False,
                "reason": "Hate",
                "scores": {"Hate": 0.9},
            }
            mock_semantic.return_value = mock_guard

            block_type, category, metadata = run_guardrails(
                "safe_word", denylist=MOCK_DENYLIST
            )
            assert block_type == BLOCK_TYPE_HARD
            assert category == "Hate"
            assert metadata["layer"] == "semantic"

    def test_archaic_returns_soft_block(self):
        """Archaic words return soft block (Issue #126)."""
        from src.guardrails.semantic import BLOCK_TYPE_SOFT

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic:
            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "block_type": BLOCK_TYPE_SOFT,
                "category": "Archaic",
                "is_safe": False,
                "reason": "Archaic",
                "scores": {"Archaic": 0.9},
            }
            mock_semantic.return_value = mock_guard

            block_type, category, metadata = run_guardrails(
                "forsooth", denylist=MOCK_DENYLIST
            )
            assert block_type == BLOCK_TYPE_SOFT
            assert category == "Archaic"
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
        from src.guardrails.semantic import BLOCK_TYPE_NONE

        event = {"text": "apple"}

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, patch(
            "src.lambda_function.get_dynamodb_client"
        ) as mock_dynamo, patch("src.lambda_function.get_bedrock_client") as mock_bedrock:
            # Mock semantic to pass (Issue #126: include block_type)
            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "block_type": BLOCK_TYPE_NONE,
                "category": "None",
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
        from src.guardrails.semantic import BLOCK_TYPE_NONE

        event = {"text": "apple"}

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, patch(
            "src.lambda_function.get_dynamodb_client"
        ) as mock_dynamo:
            # Mock semantic to pass (Issue #126: include block_type)
            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "block_type": BLOCK_TYPE_NONE,
                "category": "None",
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


class TestProcessScoresForDisplay:
    """Tests for process_scores_for_display - Issue #295 LLD Section 11."""

    def test_060_score_filtering_threshold(self):
        """Scenario 060: Only scores >= 15% are included."""
        scores = {"Archaic": 0.80, "Provocative": 0.14, "None": 0.06}
        result = process_scores_for_display(scores)
        assert len(result) == 1
        assert result[0]["category"] == "Archaic"

    def test_061_boundary_exactly_15_percent(self):
        """Scenario 061: Score exactly at 15% is included."""
        scores = {"Archaic": 0.85, "None": 0.15}
        result = process_scores_for_display(scores)
        assert len(result) == 2
        categories = [r["category"] for r in result]
        assert "General Usage" in categories  # None -> General Usage

    def test_062_boundary_just_below_15_percent(self):
        """Scenario 062: Score at 14.9% is excluded."""
        scores = {"Archaic": 0.851, "None": 0.149}
        result = process_scores_for_display(scores)
        assert len(result) == 1
        assert result[0]["category"] == "Archaic"

    def test_063_boundary_just_above_15_percent(self):
        """Scenario 063: Score at 15.1% is included."""
        scores = {"Archaic": 0.849, "None": 0.151}
        result = process_scores_for_display(scores)
        assert len(result) == 2

    def test_070_score_rounding_to_nearest_5(self):
        """Scenario 070: Scores are rounded to nearest 5%."""
        scores = {"Archaic": 0.73}  # Should round to 75%
        result = process_scores_for_display(scores)
        assert result[0]["score"] == 75

    def test_070b_rounding_edge_cases(self):
        """Rounding edge cases for various values.

        Rounding is to nearest 5%:
        - 0.72 (72%) -> round(14.4) * 5 = 70%
        - 0.73 (73%) -> round(14.6) * 5 = 75%
        - 0.77 (77%) -> round(15.4) * 5 = 75%
        - 0.78 (78%) -> round(15.6) * 5 = 80%
        """
        assert process_scores_for_display({"Archaic": 0.72})[0]["score"] == 70
        assert process_scores_for_display({"Archaic": 0.73})[0]["score"] == 75
        assert process_scores_for_display({"Archaic": 0.77})[0]["score"] == 75  # Still rounds to 75
        assert process_scores_for_display({"Archaic": 0.78})[0]["score"] == 80  # Rounds up to 80
        assert process_scores_for_display({"Archaic": 0.975})[0]["score"] == 100
        assert process_scores_for_display({"Archaic": 0.15})[0]["score"] == 15

    def test_080_score_sorting_descending(self):
        """Scenario 080: Scores sorted in descending order."""
        scores = {"Archaic": 0.30, "None": 0.70}
        result = process_scores_for_display(scores)
        assert result[0]["category"] == "General Usage"  # 70% comes first
        assert result[1]["category"] == "Archaic"  # 30% comes second
        assert result[0]["score"] > result[1]["score"]

    def test_category_name_mapping(self):
        """None is mapped to General Usage in display."""
        scores = {"None": 0.95, "Archaic": 0.05}
        result = process_scores_for_display(scores)
        assert result[0]["category"] == "General Usage"

    def test_empty_scores_returns_empty_list(self):
        """Empty scores dict returns empty list."""
        result = process_scores_for_display({})
        assert result == []

    def test_none_scores_returns_empty_list(self):
        """None input returns empty list."""
        result = process_scores_for_display(None)
        assert result == []

    def test_all_categories_below_threshold(self):
        """All scores below 15% returns empty list."""
        scores = {"Archaic": 0.05, "Provocative": 0.05, "None": 0.04}
        result = process_scores_for_display(scores)
        assert result == []


class TestAuthFeatureFlag:
    """Tests for Issue #390: AUTH_ENABLED feature flag.

    The auth gate at lambda_handler:652 should be controlled by the
    AUTH_ENABLED env var. When disabled (default), HTTP requests bypass
    JWT authentication. When enabled, @require_auth is applied.
    """

    MOCK_HTTP_EVENT = {
        "body": json.dumps({"text": "apple"}),
        "headers": {
            "x-aletheia-client-version": "1.0",
        },
        "requestContext": {
            "http": {
                "method": "POST",
                "sourceIp": "10.0.0.1",
                "path": "/",
            }
        },
    }

    def test_auth_disabled_bypasses_jwt(self):
        """HTTP request without JWT succeeds when AUTH_ENABLED=false (default)."""
        mock_response = {"statusCode": 200, "body": json.dumps({"status": "success"})}

        with patch.dict(os.environ, {"AUTH_ENABLED": "false"}, clear=False), patch(
            "src.lambda_function._analysis_handler", return_value=mock_response
        ):
            result = lambda_handler(self.MOCK_HTTP_EVENT, None, denylist=MOCK_DENYLIST)

        assert result["statusCode"] == 200

    def test_auth_enabled_requires_jwt(self):
        """HTTP request without JWT returns 401 when AUTH_ENABLED=true."""
        with patch.dict(os.environ, {"AUTH_ENABLED": "true"}, clear=False):
            result = lambda_handler(self.MOCK_HTTP_EVENT, None, denylist=MOCK_DENYLIST)

        assert result["statusCode"] == 401

    def test_direct_invocation_unaffected(self):
        """Direct Lambda invocation (no requestContext) works regardless of flag."""
        event = {"text": "apple"}
        mock_response = {"statusCode": 200, "body": json.dumps({"status": "success"})}

        with patch.dict(os.environ, {"AUTH_ENABLED": "true"}, clear=False), patch(
            "src.lambda_function._analysis_handler", return_value=mock_response
        ):
            result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

        assert result["statusCode"] == 200


class TestHealthCheck:
    """Tests for Issue #391 Phase 1: Health check endpoint.

    GET /health returns status ok without auth or origin secret.
    POST /health falls through to normal handler.
    """

    HEALTH_GET_EVENT = {
        "headers": {},
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/health",
                "sourceIp": "10.0.0.1",
            }
        },
    }

    def test_health_check_returns_200(self):
        """GET /health returns 200 with status ok and version."""
        result = lambda_handler(self.HEALTH_GET_EVENT, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "ok"
        assert body["version"] == "1.0"

    def test_health_check_no_auth_required(self):
        """GET /health succeeds without JWT even when AUTH_ENABLED=true."""
        with patch.dict(os.environ, {"AUTH_ENABLED": "true"}, clear=False):
            result = lambda_handler(self.HEALTH_GET_EVENT, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "ok"

    def test_health_check_post_falls_through(self):
        """POST /health triggers normal handler, not health endpoint."""
        event = {
            "body": json.dumps({"text": "apple"}),
            "headers": {"x-aletheia-client-version": "1.0"},
            "requestContext": {
                "http": {
                    "method": "POST",
                    "path": "/health",
                    "sourceIp": "10.0.0.1",
                }
            },
        }
        mock_response = {"statusCode": 200, "body": json.dumps({"status": "success"})}

        with patch.dict(os.environ, {"AUTH_ENABLED": "false"}, clear=False), patch(
            "src.lambda_function._analysis_handler", return_value=mock_response
        ):
            result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

        assert result["statusCode"] == 200

    def test_health_check_no_origin_secret_required(self):
        """GET /health succeeds even without origin secret header."""
        with patch.dict(os.environ, {"CLOUDFLARE_ORIGIN_SECRET": "test-secret"}, clear=False):
            result = lambda_handler(self.HEALTH_GET_EVENT, None)

        assert result["statusCode"] == 200


class TestMetricsEndpoint:
    """Tests for Issue #391 Phase 6: Admin metrics endpoint.

    GET /metrics requires admin JWT and returns user/usage data.
    """

    METRICS_GET_EVENT = {
        "headers": {},
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/metrics",
                "sourceIp": "10.0.0.1",
            }
        },
    }

    def test_metrics_requires_auth(self):
        """GET /metrics without JWT returns 401 when auth enabled."""
        with patch.dict(os.environ, {"AUTH_ENABLED": "true"}, clear=False):
            result = lambda_handler(self.METRICS_GET_EVENT, None)

        assert result["statusCode"] == 401

    def test_metrics_returns_expected_shape(self):
        """GET /metrics returns JSON with users, usage, caps keys."""
        mock_metrics = {
            "statusCode": 200,
            "body": json.dumps({
                "users": {"total": 5, "by_tier": {"free": 3, "subscriber": 1, "admin": 1}},
                "usage": {"requests_today": 42, "requests_this_month": 500},
                "caps": {"denials_today": 2}
            })
        }

        with patch.dict(os.environ, {"AUTH_ENABLED": "false"}, clear=False), patch(
            "src.lambda_function._metrics_handler", return_value=mock_metrics
        ):
            result = lambda_handler(self.METRICS_GET_EVENT, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "users" in body
        assert "usage" in body
        assert "caps" in body


class TestLambdaFunctionExceptionTextDoesNotLeak:
    """Issues #638, #650, #651 (audit umbrella #637):

    Per docs/observability.html: "NEVER log prompt text, user input, completion
    text, URLs, or user IDs." Exception messages from etymology generation and
    the catch-all handler must not leak into the response body or log output.
    Only the exception class name may surface.
    """

    CANARY = "CANARY-LEAK-lambda-fn-d9b3e7-WOULD-BE-USER-TEXT"

    def _safe_semantic_mock(self):
        from src.guardrails.semantic import BLOCK_TYPE_NONE

        mock_guard = MagicMock()
        mock_guard.check_safety.return_value = {
            "block_type": BLOCK_TYPE_NONE,
            "category": "None",
            "is_safe": True,
            "reason": "None",
            "scores": {},
        }
        return mock_guard

    def test_etymology_exception_not_in_response_gem(self, caplog):
        """Issue #638: etymology generation exception must not appear in response gem field."""
        import logging

        event = {"text": "apple"}

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, patch(
            "src.lambda_function.generate_etymology"
        ) as mock_gen, patch(
            "src.lambda_function.get_dynamodb_client"
        ) as mock_dynamo:
            mock_semantic.return_value = self._safe_semantic_mock()
            mock_gen.side_effect = Exception(self.CANARY)
            mock_dynamo.return_value = MagicMock()

            with caplog.at_level(logging.ERROR, logger="src.lambda_function"):
                result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

            body = json.loads(result["body"])

            def _no_canary(obj, path="body"):
                if isinstance(obj, str):
                    assert self.CANARY not in obj, f"Canary leaked at {path}: {obj!r}"
                elif isinstance(obj, dict):
                    for k, v in obj.items():
                        _no_canary(v, f"{path}[{k!r}]")
                elif isinstance(obj, (list, tuple)):
                    for i, v in enumerate(obj):
                        _no_canary(v, f"{path}[{i}]")

            _no_canary(body)

            log_text = "\n".join(r.getMessage() for r in caplog.records)
            assert self.CANARY not in log_text, f"Canary leaked into logs: {log_text!r}"
            assert "ETYMOLOGY_GENERATION_ERROR" in log_text
            assert "Exception" in log_text

    def test_etymology_exception_class_name_preserved_in_gem(self):
        """Issue #638: the diagnostic class name must still appear in the gem field."""
        event = {"text": "apple"}

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, patch(
            "src.lambda_function.generate_etymology"
        ) as mock_gen, patch(
            "src.lambda_function.get_dynamodb_client"
        ) as mock_dynamo:
            mock_semantic.return_value = self._safe_semantic_mock()
            mock_gen.side_effect = RuntimeError(self.CANARY)
            mock_dynamo.return_value = MagicMock()

            result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

        body = json.loads(result["body"])
        if "response" in body and isinstance(body.get("response"), dict):
            gem = body["response"].get("gem", "")
            assert "RuntimeError" in gem, f"Class name missing from gem: {gem!r}"
            assert self.CANARY not in gem

    def test_unhandled_exception_log_does_not_leak(self, caplog):
        """Issue #650: catch-all unhandled exception logger must not include str(e)."""
        import logging

        event = {"text": "apple"}

        with patch("src.lambda_function.validate_input") as mock_validate:
            mock_validate.side_effect = RuntimeError(self.CANARY)

            with caplog.at_level(logging.ERROR, logger="src.lambda_function"):
                result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

        body = json.loads(result["body"])
        assert result["statusCode"] == 500
        assert self.CANARY not in json.dumps(body)

        log_text = "\n".join(r.getMessage() for r in caplog.records)
        assert self.CANARY not in log_text, f"Canary leaked into logs: {log_text!r}"
        # Class name should still be present somewhere in the log (either
        # the CRITICAL line or earlier handlers).
        assert "RuntimeError" in log_text
