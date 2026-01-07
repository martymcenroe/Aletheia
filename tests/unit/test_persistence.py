"""
Unit tests for Data Persistence (Issues #177 & #178).

Tests verify:
- domContext is stored in DynamoDB (#177)
- AI response (signal, gem, context) is stored (#178)
- save_state is called even on generation failure (#178 resilience)

See: docs/1177-store-domcontext.md, docs/1178-store-ai-response.md
"""
import json
from unittest.mock import MagicMock, patch

from src.lambda_function import lambda_handler, save_state

# Safe mock denylist - NO real slurs (Willison Protocol)
MOCK_DENYLIST = {"test_block_term", "forbidden_fruit", "blocked_word"}


class TestDomContextPersistence:
    """
    Tests for Issue #177: Store domContext in DynamoDB.

    See: docs/1177-store-domcontext.md Section 11.1
    """

    def test_010_domcontext_stored(self):
        """Scenario 010: domContext in input event is saved to DynamoDB."""
        event = {
            "text": "apple",
            "domContext": "The apple fell from the tree in Newton's garden.",
            "url": "https://example.com/article",
        }

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, \
             patch("src.lambda_function.get_dynamodb_client") as mock_dynamo, \
             patch("src.lambda_function.get_bedrock_client") as mock_bedrock:

            # Mock semantic to pass
            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "is_safe": True,
                "reason": "None",
                "scores": {},
            }
            mock_semantic.return_value = mock_guard

            # Mock DynamoDB
            mock_client = MagicMock()
            mock_dynamo.return_value = mock_client

            # Mock Bedrock response
            mock_response = {
                "body": MagicMock(
                    read=MagicMock(
                        return_value=json.dumps({
                            "content": [{
                                "type": "text",
                                "text": '{"signal": "green", "gem": "A fruit.", "context": "Newton apple."}',
                            }]
                        }).encode()
                    )
                )
            }
            mock_bedrock.return_value.invoke_model.return_value = mock_response

            result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

            assert result["statusCode"] == 200

            # Verify DynamoDB put_item was called with domContext
            mock_client.put_item.assert_called_once()
            call_args = mock_client.put_item.call_args
            item = call_args.kwargs.get("Item") or call_args[1].get("Item")

            assert "domContext" in item, "Item should have domContext field"
            assert item["domContext"]["S"] == "The apple fell from the tree in Newton's garden."

    def test_020_missing_domcontext_defaults_empty(self):
        """Scenario 020: Missing domContext defaults to empty string (no error)."""
        event = {
            "text": "apple",
            "url": "https://example.com/article",
            # Note: no domContext field
        }

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, \
             patch("src.lambda_function.get_dynamodb_client") as mock_dynamo, \
             patch("src.lambda_function.get_bedrock_client") as mock_bedrock:

            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "is_safe": True,
                "reason": "None",
                "scores": {},
            }
            mock_semantic.return_value = mock_guard

            mock_client = MagicMock()
            mock_dynamo.return_value = mock_client

            mock_response = {
                "body": MagicMock(
                    read=MagicMock(
                        return_value=json.dumps({
                            "content": [{
                                "type": "text",
                                "text": '{"signal": "green", "gem": "A fruit.", "context": "Common noun."}',
                            }]
                        }).encode()
                    )
                )
            }
            mock_bedrock.return_value.invoke_model.return_value = mock_response

            result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

            assert result["statusCode"] == 200

            # Verify domContext is empty string, not missing or None
            call_args = mock_dynamo.return_value.put_item.call_args
            item = call_args.kwargs.get("Item") or call_args[1].get("Item")

            assert "domContext" in item, "Item should have domContext field even when missing from input"
            assert item["domContext"]["S"] == ""

    def test_030_large_domcontext_truncated(self):
        """Scenario 030: Large domContext (>100KB) is truncated for DynamoDB safety."""
        large_context = "x" * 150000  # 150KB - exceeds 100KB cap
        event = {
            "text": "apple",
            "domContext": large_context,
        }

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, \
             patch("src.lambda_function.get_dynamodb_client") as mock_dynamo, \
             patch("src.lambda_function.get_bedrock_client") as mock_bedrock:

            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "is_safe": True,
                "reason": "None",
                "scores": {},
            }
            mock_semantic.return_value = mock_guard

            mock_client = MagicMock()
            mock_dynamo.return_value = mock_client

            mock_response = {
                "body": MagicMock(
                    read=MagicMock(
                        return_value=json.dumps({
                            "content": [{
                                "type": "text",
                                "text": '{"signal": "green", "gem": "A fruit.", "context": "Test."}',
                            }]
                        }).encode()
                    )
                )
            }
            mock_bedrock.return_value.invoke_model.return_value = mock_response

            result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

            assert result["statusCode"] == 200

            # Verify domContext is truncated to 100KB
            call_args = mock_dynamo.return_value.put_item.call_args
            item = call_args.kwargs.get("Item") or call_args[1].get("Item")

            stored_context = item["domContext"]["S"]
            assert len(stored_context) == 100000, f"Expected 100KB, got {len(stored_context)}"


class TestAIResponsePersistence:
    """
    Tests for Issue #178: Store AI response in DynamoDB.

    See: docs/1178-store-ai-response.md Section 11.1
    """

    def test_010_response_stored(self):
        """Scenario 010: AI response (signal, gem, context) is saved to DynamoDB."""
        event = {"text": "apple"}

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, \
             patch("src.lambda_function.get_dynamodb_client") as mock_dynamo, \
             patch("src.lambda_function.get_bedrock_client") as mock_bedrock:

            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "is_safe": True,
                "reason": "None",
                "scores": {},
            }
            mock_semantic.return_value = mock_guard

            mock_client = MagicMock()
            mock_dynamo.return_value = mock_client

            # Mock specific response to verify it's stored
            mock_response = {
                "body": MagicMock(
                    read=MagicMock(
                        return_value=json.dumps({
                            "content": [{
                                "type": "text",
                                "text": '{"signal": "green", "gem": "From Old English æppel.", "context": "Common fruit name."}',
                            }]
                        }).encode()
                    )
                )
            }
            mock_bedrock.return_value.invoke_model.return_value = mock_response

            result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

            assert result["statusCode"] == 200

            # Verify response fields are stored
            call_args = mock_dynamo.return_value.put_item.call_args
            item = call_args.kwargs.get("Item") or call_args[1].get("Item")

            assert "response" in item, "Item should have response field"
            # Response is stored as JSON string in DynamoDB
            response_data = json.loads(item["response"]["S"])
            assert response_data["signal"] == "green"
            assert response_data["gem"] == "From Old English æppel."
            assert response_data["context"] == "Common fruit name."

    def test_020_generation_failure_still_saves(self):
        """Scenario 020: Generation failure still saves input to DynamoDB (resilience)."""
        event = {
            "text": "problematic_term",
            "domContext": "Some context here.",
            "url": "https://example.com",
        }

        with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, \
             patch("src.lambda_function.get_dynamodb_client") as mock_dynamo, \
             patch("src.lambda_function.generate_etymology") as mock_etymology:

            mock_guard = MagicMock()
            mock_guard.check_safety.return_value = {
                "is_safe": True,
                "reason": "None",
                "scores": {},
            }
            mock_semantic.return_value = mock_guard

            mock_client = MagicMock()
            mock_dynamo.return_value = mock_client

            # Mock etymology to RAISE an exception
            mock_etymology.side_effect = Exception("Bedrock timeout")

            # Call handler - should return 500 but still save
            result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

            assert result["statusCode"] == 500

            # CRITICAL: save_state MUST still be called even on failure
            mock_client.put_item.assert_called_once()

            call_args = mock_client.put_item.call_args
            item = call_args.kwargs.get("Item") or call_args[1].get("Item")

            # Verify input data was saved
            assert item["input"]["S"] == "problematic_term"
            assert item["domContext"]["S"] == "Some context here."
            assert item["url"]["S"] == "https://example.com"

            # Verify error response was captured
            assert "response" in item
            response_data = json.loads(item["response"]["S"])
            assert response_data["signal"] == "error"
            assert "Bedrock timeout" in response_data["gem"]

    def test_030_signal_values_stored_correctly(self):
        """Scenario 030: Signal color values are stored correctly."""
        test_cases = [
            ("green", "Common Noun"),
            ("yellow", "Archaic Term"),
            ("orange", "Potential Issue"),
            ("red", "Warning"),
        ]

        for expected_signal, signal_label in test_cases:
            event = {"text": f"test_{expected_signal}"}

            with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, \
                 patch("src.lambda_function.get_dynamodb_client") as mock_dynamo, \
                 patch("src.lambda_function.get_bedrock_client") as mock_bedrock:

                mock_guard = MagicMock()
                mock_guard.check_safety.return_value = {
                    "is_safe": True,
                    "reason": "None",
                    "scores": {},
                }
                mock_semantic.return_value = mock_guard

                mock_client = MagicMock()
                mock_dynamo.return_value = mock_client

                mock_response = {
                    "body": MagicMock(
                        read=MagicMock(
                            return_value=json.dumps({
                                "content": [{
                                    "type": "text",
                                    "text": f'{{"signal": "{expected_signal}", "gem": "{signal_label}", "context": "Test."}}',
                                }]
                            }).encode()
                        )
                    )
                }
                mock_bedrock.return_value.invoke_model.return_value = mock_response

                result = lambda_handler(event, None, denylist=MOCK_DENYLIST)

                assert result["statusCode"] == 200

                call_args = mock_dynamo.return_value.put_item.call_args
                item = call_args.kwargs.get("Item") or call_args[1].get("Item")

                response_data = json.loads(item["response"]["S"])
                assert response_data["signal"] == expected_signal, \
                    f"Expected signal '{expected_signal}', got '{response_data['signal']}'"


class TestSaveStateDirectUnit:
    """
    Direct unit tests for save_state function with new fields.

    Tests the function signature update for domContext and response.
    """

    def test_save_state_includes_domcontext(self):
        """save_state correctly persists domContext field."""
        with patch("src.lambda_function.get_dynamodb_client") as mock_dynamo:
            mock_client = MagicMock()
            mock_dynamo.return_value = mock_client

            save_state(
                "test_thread_id",
                {
                    "text": "apple",
                    "domContext": "The apple tree context.",
                    "url": "https://example.com",
                    "safety_score": {},
                },
            )

            call_args = mock_client.put_item.call_args
            item = call_args.kwargs.get("Item") or call_args[1].get("Item")

            assert "domContext" in item
            assert item["domContext"]["S"] == "The apple tree context."

    def test_save_state_includes_response(self):
        """save_state correctly persists response field."""
        with patch("src.lambda_function.get_dynamodb_client") as mock_dynamo:
            mock_client = MagicMock()
            mock_dynamo.return_value = mock_client

            save_state(
                "test_thread_id",
                {
                    "text": "apple",
                    "domContext": "",
                    "url": "https://example.com",
                    "safety_score": {},
                    "response": {
                        "signal": "green",
                        "gem": "Etymology here.",
                        "context": "Analysis context.",
                    },
                },
            )

            call_args = mock_client.put_item.call_args
            item = call_args.kwargs.get("Item") or call_args[1].get("Item")

            assert "response" in item
            response_data = json.loads(item["response"]["S"])
            assert response_data["signal"] == "green"
            assert response_data["gem"] == "Etymology here."

    def test_save_state_handles_none_response(self):
        """save_state handles None response gracefully (pre-generation save)."""
        with patch("src.lambda_function.get_dynamodb_client") as mock_dynamo:
            mock_client = MagicMock()
            mock_dynamo.return_value = mock_client

            save_state(
                "test_thread_id",
                {
                    "text": "apple",
                    "domContext": "",
                    "url": "https://example.com",
                    "safety_score": {},
                    "response": None,
                },
            )

            call_args = mock_client.put_item.call_args
            item = call_args.kwargs.get("Item") or call_args[1].get("Item")

            # response field should still exist with null/empty marker
            assert "response" in item
            assert item["response"]["S"] == "null" or item["response"]["S"] == "{}"
