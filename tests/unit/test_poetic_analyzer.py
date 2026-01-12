"""
Unit tests for Poetic Resonance Analyzer module.

Issue #310: Tests for the Opus-powered deep meaning extraction.
See: docs/lld/active/1310-poetic-resonance.md Section 11
"""

import json
from unittest.mock import MagicMock, Mock


from src.poetic_analyzer import (
    FALLBACK_RESULT,
    OPUS_MODEL_ID,
    POETIC_SYSTEM_PROMPT,
    VALID_DIMENSIONS,
    analyze_poetic_resonance,
    build_poetic_prompt,
    _extract_json_from_response,
    _validate_poetic_result,
)


class TestBuildPoeticPrompt:
    """Tests for prompt construction."""

    def test_basic_prompt_structure(self):
        """Test that prompt contains required Bedrock fields."""
        result = build_poetic_prompt(
            word="ascension",
            etymology={"signal": "Religious Term", "gem": "Rising upward", "context": "From Latin"},
            page_context="Article about elderly care",
            dimensions=["religious"],
        )

        assert "anthropic_version" in result
        assert result["max_tokens"] == 1000
        assert result["system"] == POETIC_SYSTEM_PROMPT
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"

    def test_word_included_in_message(self):
        """Test that the word is included in the user message."""
        result = build_poetic_prompt(
            word="ascension",
            etymology={},
            page_context="",
            dimensions=[],
        )

        message_text = result["messages"][0]["content"][0]["text"]
        assert "<word>ascension</word>" in message_text

    def test_etymology_fields_included(self):
        """Test that etymology data is included."""
        result = build_poetic_prompt(
            word="test",
            etymology={"signal": "TestSignal", "gem": "TestGem", "context": "TestContext"},
            page_context="",
            dimensions=[],
        )

        message_text = result["messages"][0]["content"][0]["text"]
        assert "Signal: TestSignal" in message_text
        assert "Summary: TestGem" in message_text
        assert "History: TestContext" in message_text

    def test_page_context_truncated(self):
        """Test that page context is truncated to 5000 chars."""
        marker = "QQQ"  # Unique marker not in template
        long_context = marker * 4000  # 12000 chars, should truncate to 5000
        result = build_poetic_prompt(
            word="test",
            etymology={},
            page_context=long_context,
            dimensions=[],
        )

        message_text = result["messages"][0]["content"][0]["text"]
        # Count marker occurrences (5000 chars / 3 chars per marker = 1666 markers)
        marker_count = message_text.count(marker)
        # 5000 chars means 1666 complete markers (5000 // 3 = 1666 with 2 chars left over)
        assert marker_count == 1666

    def test_dimensions_formatted(self):
        """Test that dimensions are comma-separated."""
        result = build_poetic_prompt(
            word="test",
            etymology={},
            page_context="",
            dimensions=["religious", "literary", "artistic"],
        )

        message_text = result["messages"][0]["content"][0]["text"]
        assert "religious, literary, artistic" in message_text

    def test_empty_dimensions(self):
        """Test handling of empty dimensions list."""
        result = build_poetic_prompt(
            word="test",
            etymology={},
            page_context="",
            dimensions=[],
        )

        message_text = result["messages"][0]["content"][0]["text"]
        assert "None detected" in message_text


class TestExtractJsonFromResponse:
    """Tests for JSON extraction from Opus response."""

    def test_extract_clean_json(self):
        """Test extraction of clean JSON."""
        raw = '{"synthesis": "test", "dimensions": [], "resonance_strength": 0.5}'
        result = _extract_json_from_response(raw)
        assert result == {"synthesis": "test", "dimensions": [], "resonance_strength": 0.5}

    def test_extract_json_with_whitespace(self):
        """Test extraction with leading/trailing whitespace."""
        raw = '  \n  {"synthesis": "test", "dimensions": [], "resonance_strength": 0.5}  \n  '
        result = _extract_json_from_response(raw)
        assert result is not None
        assert result["synthesis"] == "test"

    def test_extract_json_from_markdown_fence(self):
        """Test extraction from markdown code fence."""
        raw = '```json\n{"synthesis": "test", "dimensions": [], "resonance_strength": 0.5}\n```'
        result = _extract_json_from_response(raw)
        assert result is not None
        assert result["synthesis"] == "test"

    def test_extract_json_with_text_before(self):
        """Test extraction when there's preamble text."""
        raw = 'Here is the analysis:\n{"synthesis": "test", "dimensions": [], "resonance_strength": 0.5}'
        result = _extract_json_from_response(raw)
        assert result is not None
        assert result["synthesis"] == "test"

    def test_returns_none_for_empty_input(self):
        """Test returns None for empty input."""
        assert _extract_json_from_response("") is None
        assert _extract_json_from_response(None) is None

    def test_returns_none_for_invalid_json(self):
        """Test returns None for invalid JSON."""
        assert _extract_json_from_response("not json at all") is None
        assert _extract_json_from_response('{"broken": }') is None

    def test_returns_none_for_no_braces(self):
        """Test returns None when no JSON object found."""
        assert _extract_json_from_response("just plain text") is None


class TestValidatePoeticResult:
    """Tests for result validation."""

    def test_valid_result_passes(self):
        """Test that a valid result passes validation."""
        result = {
            "synthesis": "The word carries meaning...",
            "dimensions": [{"dimension": "religious", "explanation": "Echoes spiritual themes"}],
            "resonance_strength": 0.75,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert is_valid
        assert len(errors) == 0

    def test_missing_synthesis_fails(self):
        """Test that missing synthesis field fails."""
        result = {
            "dimensions": [],
            "resonance_strength": 0.5,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert not is_valid
        assert "Missing field: synthesis" in errors

    def test_missing_dimensions_fails(self):
        """Test that missing dimensions field fails."""
        result = {
            "synthesis": "test",
            "resonance_strength": 0.5,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert not is_valid
        assert "Missing field: dimensions" in errors

    def test_missing_resonance_strength_fails(self):
        """Test that missing resonance_strength field fails."""
        result = {
            "synthesis": "test",
            "dimensions": [],
        }
        is_valid, errors = _validate_poetic_result(result)
        assert not is_valid
        assert "Missing field: resonance_strength" in errors

    def test_invalid_synthesis_type_fails(self):
        """Test that non-string synthesis fails."""
        result = {
            "synthesis": 123,
            "dimensions": [],
            "resonance_strength": 0.5,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert not is_valid
        assert "Field 'synthesis' must be string" in errors

    def test_invalid_dimensions_type_fails(self):
        """Test that non-list dimensions fails."""
        result = {
            "synthesis": "test",
            "dimensions": "not a list",
            "resonance_strength": 0.5,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert not is_valid
        assert "Field 'dimensions' must be list" in errors

    def test_invalid_resonance_range_fails(self):
        """Test that resonance_strength outside 0-1 fails."""
        result = {
            "synthesis": "test",
            "dimensions": [],
            "resonance_strength": 1.5,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert not is_valid
        assert any("0.0-1.0" in e for e in errors)

    def test_invalid_resonance_negative_fails(self):
        """Test that negative resonance_strength fails."""
        result = {
            "synthesis": "test",
            "dimensions": [],
            "resonance_strength": -0.1,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert not is_valid
        assert any("0.0-1.0" in e for e in errors)

    def test_dimension_missing_fields_fails(self):
        """Test that dimension without required fields fails."""
        result = {
            "synthesis": "test",
            "dimensions": [{"dimension": "religious"}],  # missing explanation
            "resonance_strength": 0.5,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert not is_valid
        assert any("dimension or explanation" in e for e in errors)


class TestAnalyzePoeticResonance:
    """Tests for the main analysis function."""

    def test_returns_error_when_no_client(self):
        """Test that missing client returns error status."""
        result = analyze_poetic_resonance(
            word="test",
            etymology={},
            page_context="",
            dimensions=[],
            bedrock_client=None,
        )

        assert result["status"] == "error"
        assert result["synthesis"] == ""
        assert result["dimensions"] == []
        assert result["resonance_strength"] == 0.0

    def test_returns_error_for_empty_word(self):
        """Test that empty word returns error status."""
        mock_client = MagicMock()
        result = analyze_poetic_resonance(
            word="",
            etymology={},
            page_context="",
            dimensions=[],
            bedrock_client=mock_client,
        )

        assert result["status"] == "error"

    def test_returns_error_for_whitespace_word(self):
        """Test that whitespace-only word returns error status."""
        mock_client = MagicMock()
        result = analyze_poetic_resonance(
            word="   ",
            etymology={},
            page_context="",
            dimensions=[],
            bedrock_client=mock_client,
        )

        assert result["status"] == "error"

    def test_successful_analysis(self):
        """Test successful Opus analysis flow."""
        mock_client = MagicMock()

        # Mock successful response
        mock_response = {
            "body": Mock(
                read=Mock(
                    return_value=json.dumps({
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({
                                    "synthesis": "The word carries profound meaning...",
                                    "dimensions": [
                                        {"dimension": "religious", "explanation": "Echoes ascent to heaven"}
                                    ],
                                    "resonance_strength": 0.82,
                                }),
                            }
                        ]
                    }).encode()
                )
            )
        }
        mock_client.invoke_model.return_value = mock_response

        result = analyze_poetic_resonance(
            word="ascension",
            etymology={"signal": "Religious", "gem": "Rising", "context": "Latin"},
            page_context="Article about elderly care",
            dimensions=["religious"],
            bedrock_client=mock_client,
        )

        assert result["status"] == "success"
        assert "profound meaning" in result["synthesis"]
        assert len(result["dimensions"]) == 1
        assert result["dimensions"][0]["dimension"] == "religious"
        assert result["resonance_strength"] == 0.82
        assert result["latency_ms"] >= 0

    def test_handles_bedrock_exception(self):
        """Test that Bedrock exceptions are caught and return error."""
        mock_client = MagicMock()
        mock_client.invoke_model.side_effect = Exception("Bedrock error")

        result = analyze_poetic_resonance(
            word="test",
            etymology={},
            page_context="",
            dimensions=[],
            bedrock_client=mock_client,
        )

        assert result["status"] == "error"
        assert result["latency_ms"] >= 0

    def test_handles_malformed_response(self):
        """Test handling of malformed Opus response."""
        mock_client = MagicMock()

        # Mock response with invalid JSON
        mock_response = {
            "body": Mock(
                read=Mock(
                    return_value=json.dumps({
                        "content": [{"type": "text", "text": "Not valid JSON"}]
                    }).encode()
                )
            )
        }
        mock_client.invoke_model.return_value = mock_response

        result = analyze_poetic_resonance(
            word="test",
            etymology={},
            page_context="",
            dimensions=[],
            bedrock_client=mock_client,
        )

        assert result["status"] == "error"

    def test_handles_validation_failure(self):
        """Test handling when response fails validation."""
        mock_client = MagicMock()

        # Mock response with invalid resonance_strength
        mock_response = {
            "body": Mock(
                read=Mock(
                    return_value=json.dumps({
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({
                                    "synthesis": "test",
                                    "dimensions": [],
                                    "resonance_strength": 5.0,  # Invalid
                                }),
                            }
                        ]
                    }).encode()
                )
            )
        }
        mock_client.invoke_model.return_value = mock_response

        result = analyze_poetic_resonance(
            word="test",
            etymology={},
            page_context="",
            dimensions=[],
            bedrock_client=mock_client,
        )

        assert result["status"] == "error"


class TestConstants:
    """Tests for module constants."""

    def test_opus_model_id_valid(self):
        """Test Opus model ID is valid."""
        assert "opus" in OPUS_MODEL_ID.lower()

    def test_valid_dimensions_frozenset(self):
        """Test valid dimensions is a frozenset."""
        assert isinstance(VALID_DIMENSIONS, frozenset)
        assert "religious" in VALID_DIMENSIONS
        assert "literary" in VALID_DIMENSIONS
        assert "architectural" in VALID_DIMENSIONS
        assert "artistic" in VALID_DIMENSIONS
        assert "political" in VALID_DIMENSIONS
        assert "scientific" in VALID_DIMENSIONS

    def test_fallback_result_structure(self):
        """Test fallback result has required fields."""
        assert FALLBACK_RESULT["status"] == "error"
        assert FALLBACK_RESULT["synthesis"] == ""
        assert FALLBACK_RESULT["dimensions"] == []
        assert FALLBACK_RESULT["resonance_strength"] == 0.0
        assert FALLBACK_RESULT["latency_ms"] == 0


class TestBoundaryConditions:
    """Tests for boundary conditions per LLD test scenarios."""

    def test_resonance_at_zero(self):
        """Test handling of 0.0 resonance (valid minimum)."""
        result = {
            "synthesis": "No resonance detected.",
            "dimensions": [],
            "resonance_strength": 0.0,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert is_valid

    def test_resonance_at_one(self):
        """Test handling of 1.0 resonance (valid maximum)."""
        result = {
            "synthesis": "Maximum resonance.",
            "dimensions": [],
            "resonance_strength": 1.0,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert is_valid

    def test_empty_synthesis_allowed(self):
        """Test that empty synthesis is technically valid (just not useful)."""
        result = {
            "synthesis": "",
            "dimensions": [],
            "resonance_strength": 0.0,
        }
        is_valid, errors = _validate_poetic_result(result)
        # Empty string is still a string, so validation passes
        assert is_valid

    def test_multiple_dimensions(self):
        """Test handling of multiple dimensions."""
        result = {
            "synthesis": "Multiple dimensions resonate.",
            "dimensions": [
                {"dimension": "religious", "explanation": "Spiritual ascent"},
                {"dimension": "architectural", "explanation": "Rising structure"},
                {"dimension": "literary", "explanation": "Metaphorical rise"},
            ],
            "resonance_strength": 0.9,
        }
        is_valid, errors = _validate_poetic_result(result)
        assert is_valid
