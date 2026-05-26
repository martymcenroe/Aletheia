import json
from pathlib import Path
from unittest.mock import Mock, patch
from src.guardrails.semantic import (
    SemanticGuardrail,
    BLOCK_TYPE_HARD,
    BLOCK_TYPE_SOFT,
    BLOCK_TYPE_NONE,
)

TAXONOMY_PATH = Path(__file__).parent.parent.parent / "src" / "guardrails" / "resources" / "taxonomy.json"


class TestTaxonomyArchaicDefinition:
    """Tests for Issue #199: Refined Archaic definition in taxonomy.json."""

    def test_taxonomy_archaic_definition_includes_1950_cutoff(self):
        """Verify Archaic definition specifies the 1950 chronological cutoff."""
        with open(TAXONOMY_PATH) as f:
            taxonomy = json.load(f)
        archaic_def = taxonomy["taxonomy"]["Archaic"]
        assert "1950" in archaic_def or "BEFORE 1950" in archaic_def

    def test_taxonomy_archaic_definition_excludes_formal_words(self):
        """Verify Archaic definition clarifies that formal words are NOT archaic."""
        with open(TAXONOMY_PATH) as f:
            taxonomy = json.load(f)
        archaic_def = taxonomy["taxonomy"]["Archaic"]
        # Should mention that formal/academic words are NOT archaic
        assert "formal" in archaic_def.lower() or "academic" in archaic_def.lower()

    def test_taxonomy_none_category_includes_formal_words(self):
        """Verify None category mentions formal/academic terms are safe."""
        with open(TAXONOMY_PATH) as f:
            taxonomy = json.load(f)
        none_def = taxonomy["taxonomy"]["None"]
        assert "formal" in none_def.lower() or "academic" in none_def.lower()

    def test_taxonomy_has_formal_word_examples_as_safe(self):
        """Verify few-shot examples include formal words classified as None (safe)."""
        with open(TAXONOMY_PATH) as f:
            taxonomy = json.load(f)

        examples = taxonomy["few_shot_examples"]

        # Find examples containing formal words
        formal_words = ["immiserate", "ameliorate"]
        found_formal_safe = False

        for example in examples:
            text_lower = example["text"].lower()
            if any(word in text_lower for word in formal_words):
                # This formal word should be classified as "None" (safe)
                assert example["category"] == "None", (
                    f"Formal word in '{example['text']}' should be category 'None', "
                    f"got '{example['category']}'"
                )
                found_formal_safe = True

        assert found_formal_safe, "No formal word examples found in taxonomy few-shot examples"

    def test_taxonomy_has_true_archaic_examples(self):
        """Verify few-shot examples include true archaic words classified as Archaic."""
        with open(TAXONOMY_PATH) as f:
            taxonomy = json.load(f)

        examples = taxonomy["few_shot_examples"]

        # Find examples classified as Archaic
        archaic_examples = [ex for ex in examples if ex["category"] == "Archaic"]
        assert len(archaic_examples) >= 1, "Should have at least one Archaic example"

        # True archaic words should include things like "thou", "forsooth", etc.
        archaic_words = ["thou", "forsooth", "betwixt", "blackguard", "knave"]
        found_archaic = False
        for example in archaic_examples:
            text_lower = example["text"].lower()
            if any(word in text_lower for word in archaic_words):
                found_archaic = True
                break

        assert found_archaic, "No true archaic word examples found"


@patch("src.guardrails.semantic.boto3.client")
def test_semantic_safe(mock_boto_client):
    """Test that a safe response from LLM is parsed correctly."""
    # Mock the Bedrock response structure
    mock_client_instance = Mock()
    mock_boto_client.return_value = mock_client_instance

    llm_output = json.dumps({"safe": True, "category": "None"})
    bedrock_response_body = json.dumps({
        "content": [{"text": llm_output}]
    }).encode("utf-8")

    mock_body = Mock()
    mock_body.read.return_value = bedrock_response_body
    mock_client_instance.invoke_model.return_value = {"body": mock_body}

    # Execute
    guard = SemanticGuardrail()
    result = guard.check_safety("Hello world")

    # Assert
    assert result["is_safe"] is True
    assert result["reason"] == "None"

@patch("src.guardrails.semantic.boto3.client")
def test_semantic_unsafe(mock_boto_client):
    """Test that an unsafe response properly flags the category."""
    mock_client_instance = Mock()
    mock_boto_client.return_value = mock_client_instance

    llm_output = json.dumps({"safe": False, "category": "Archaic"})
    bedrock_response_body = json.dumps({
        "content": [{"text": llm_output}]
    }).encode("utf-8")

    mock_body = Mock()
    mock_body.read.return_value = bedrock_response_body
    mock_client_instance.invoke_model.return_value = {"body": mock_body}

    # Execute
    guard = SemanticGuardrail()
    result = guard.check_safety("Thou art consumptive")

    # Assert
    assert result["is_safe"] is False
    assert result["reason"] == "Archaic"

@patch("src.guardrails.semantic.boto3.client")
def test_semantic_failure(mock_boto_client):
    """Test that infrastructure failures result in a closed (unsafe) state."""
    mock_client_instance = Mock()
    mock_boto_client.return_value = mock_client_instance

    # Simulate AWS Exception
    mock_client_instance.invoke_model.side_effect = Exception("AWS Throttling")

    guard = SemanticGuardrail()
    result = guard.check_safety("Test input")

    assert result["is_safe"] is False
    assert "Guardrail Error" in result["reason"]


class TestHardSoftBlockingLogic:
    """Tests for Issue #126: Hard vs. Soft Blocking Logic."""

    @patch("src.guardrails.semantic.boto3.client")
    def test_hate_category_returns_hard_block(self, mock_boto_client):
        """Hate speech should return BLOCK_TYPE_HARD."""
        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance

        llm_output = json.dumps({"scores": {"Hate": 0.95}, "category": "Hate"})
        bedrock_response_body = json.dumps({
            "content": [{"text": llm_output}]
        }).encode("utf-8")

        mock_body = Mock()
        mock_body.read.return_value = bedrock_response_body
        mock_client_instance.invoke_model.return_value = {"body": mock_body}

        guard = SemanticGuardrail()
        result = guard.check_safety("offensive content")

        assert result["block_type"] == BLOCK_TYPE_HARD
        assert result["category"] == "Hate"
        assert result["is_safe"] is False

    @patch("src.guardrails.semantic.boto3.client")
    def test_archaic_category_returns_soft_block(self, mock_boto_client):
        """Archaic words should return BLOCK_TYPE_SOFT (educational warning)."""
        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance

        llm_output = json.dumps({"scores": {"Archaic": 0.9}, "category": "Archaic"})
        bedrock_response_body = json.dumps({
            "content": [{"text": llm_output}]
        }).encode("utf-8")

        mock_body = Mock()
        mock_body.read.return_value = bedrock_response_body
        mock_client_instance.invoke_model.return_value = {"body": mock_body}

        guard = SemanticGuardrail()
        result = guard.check_safety("forsooth")

        assert result["block_type"] == BLOCK_TYPE_SOFT
        assert result["category"] == "Archaic"
        assert result["is_safe"] is False  # Backwards compat: soft block is still "not safe"

    @patch("src.guardrails.semantic.boto3.client")
    def test_provocative_category_returns_soft_block(self, mock_boto_client):
        """Provocative content should return BLOCK_TYPE_SOFT."""
        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance

        llm_output = json.dumps({"scores": {"Provocative": 0.85}, "category": "Provocative"})
        bedrock_response_body = json.dumps({
            "content": [{"text": llm_output}]
        }).encode("utf-8")

        mock_body = Mock()
        mock_body.read.return_value = bedrock_response_body
        mock_client_instance.invoke_model.return_value = {"body": mock_body}

        guard = SemanticGuardrail()
        result = guard.check_safety("provocative term")

        assert result["block_type"] == BLOCK_TYPE_SOFT
        assert result["category"] == "Provocative"

    @patch("src.guardrails.semantic.boto3.client")
    def test_none_category_returns_no_block(self, mock_boto_client):
        """Safe content should return BLOCK_TYPE_NONE."""
        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance

        llm_output = json.dumps({"scores": {"None": 1.0}, "category": "None"})
        bedrock_response_body = json.dumps({
            "content": [{"text": llm_output}]
        }).encode("utf-8")

        mock_body = Mock()
        mock_body.read.return_value = bedrock_response_body
        mock_client_instance.invoke_model.return_value = {"body": mock_body}

        guard = SemanticGuardrail()
        result = guard.check_safety("hello world")

        assert result["block_type"] == BLOCK_TYPE_NONE
        assert result["category"] == "None"
        assert result["is_safe"] is True

    @patch("src.guardrails.semantic.boto3.client")
    def test_neologism_category_returns_no_block(self, mock_boto_client):
        """Neologisms should return BLOCK_TYPE_NONE (informational only)."""
        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance

        llm_output = json.dumps({"scores": {"Neologism": 0.9}, "category": "Neologism"})
        bedrock_response_body = json.dumps({
            "content": [{"text": llm_output}]
        }).encode("utf-8")

        mock_body = Mock()
        mock_body.read.return_value = bedrock_response_body
        mock_client_instance.invoke_model.return_value = {"body": mock_body}

        guard = SemanticGuardrail()
        result = guard.check_safety("skibidi")

        assert result["block_type"] == BLOCK_TYPE_NONE
        assert result["category"] == "Neologism"
        assert result["is_safe"] is True

    @patch("src.guardrails.semantic.boto3.client")
    def test_error_returns_soft_block_with_fallback(self, mock_boto_client):
        """Errors should return BLOCK_TYPE_SOFT with fallback flag (fail safe)."""
        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance

        # Simulate AWS Exception
        mock_client_instance.invoke_model.side_effect = Exception("Network Error")

        guard = SemanticGuardrail()
        result = guard.check_safety("test input")

        assert result["block_type"] == BLOCK_TYPE_SOFT
        assert result["is_fallback"] is True
        assert result["is_safe"] is False


class TestDescriptiveTermsClassification:
    """Tests for Issue #339: Descriptive terms should NOT be classified as Hate."""

    def test_taxonomy_has_descriptive_term_examples(self):
        """Verify few-shot examples include descriptive terms classified as None (safe)."""
        with open(TAXONOMY_PATH) as f:
            taxonomy = json.load(f)

        examples = taxonomy["few_shot_examples"]

        # Find examples containing descriptive terms
        descriptive_terms = ["misogyn", "misandr"]
        found_descriptive_safe = False

        for example in examples:
            text_lower = example["text"].lower()
            if any(term in text_lower for term in descriptive_terms):
                # Descriptive terms should be classified as "None" (safe), NOT "Hate"
                assert example["category"] == "None", (
                    f"Descriptive term in '{example['text']}' should be category 'None', "
                    f"got '{example['category']}'"
                )
                found_descriptive_safe = True

        assert found_descriptive_safe, (
            "No descriptive term examples (misogynist/misandrist) found in taxonomy few-shot examples"
        )

    @patch("src.guardrails.semantic.boto3.client")
    def test_misogynist_returns_no_block(self, mock_boto_client):
        """Descriptive term 'misogynist' should return BLOCK_TYPE_NONE, not HATE."""
        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance

        # Mock Bedrock response: LLM correctly classifies as None (after seeing few-shot examples)
        llm_output = json.dumps({"scores": {"None": 1.0}, "category": "None"})
        bedrock_response_body = json.dumps({
            "content": [{"text": llm_output}]
        }).encode("utf-8")

        mock_body = Mock()
        mock_body.read.return_value = bedrock_response_body
        mock_client_instance.invoke_model.return_value = {"body": mock_body}

        guard = SemanticGuardrail()
        result = guard.check_safety("The article discusses misogynists in modern society")

        assert result["block_type"] == BLOCK_TYPE_NONE
        assert result["category"] == "None"
        assert result["is_safe"] is True

    @patch("src.guardrails.semantic.boto3.client")
    def test_misandrist_returns_no_block(self, mock_boto_client):
        """Descriptive term 'misandrist' should return BLOCK_TYPE_NONE, not HATE."""
        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance

        # Mock Bedrock response: LLM correctly classifies as None
        llm_output = json.dumps({"scores": {"None": 1.0}, "category": "None"})
        bedrock_response_body = json.dumps({
            "content": [{"text": llm_output}]
        }).encode("utf-8")

        mock_body = Mock()
        mock_body.read.return_value = bedrock_response_body
        mock_client_instance.invoke_model.return_value = {"body": mock_body}

        guard = SemanticGuardrail()
        result = guard.check_safety("Critics called him a misandrist for his views")

        assert result["block_type"] == BLOCK_TYPE_NONE
        assert result["category"] == "None"
        assert result["is_safe"] is True


class TestRacialVocabularyClassification:
    """Tests for Issue #418: Academic racial vocabulary should NOT be classified as Hate."""

    def test_taxonomy_has_racial_context_examples(self):
        """Verify few-shot examples include racial-vocabulary-in-context classified as None."""
        with open(TAXONOMY_PATH) as f:
            taxonomy = json.load(f)

        examples = taxonomy["few_shot_examples"]

        racial_context_terms = ["pan-white tribalism"]
        found_racial_safe = False

        for example in examples:
            text_lower = example["text"].lower()
            if any(term in text_lower for term in racial_context_terms):
                assert example["category"] == "None", (
                    f"Racial-context term in '{example['text']}' should be category 'None', "
                    f"got '{example['category']}'"
                )
                found_racial_safe = True

        assert found_racial_safe, (
            "No racial-vocabulary-in-context examples found in taxonomy few-shot examples"
        )

    def test_taxonomy_hate_definition_excludes_academic_discussion(self):
        """Verify Hate definition mentions academic/journalistic discussion is NOT hate."""
        with open(TAXONOMY_PATH) as f:
            taxonomy = json.load(f)

        hate_def = taxonomy["taxonomy"]["Hate"]
        assert "academic" in hate_def.lower() or "journalistic" in hate_def.lower(), (
            "Hate definition should mention that academic/journalistic discussion is NOT hate"
        )

    @patch("src.guardrails.semantic.boto3.client")
    def test_pan_white_tribalism_returns_no_block(self, mock_boto_client):
        """'pan-white tribalism' should return BLOCK_TYPE_NONE, not HATE."""
        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance

        llm_output = json.dumps({"scores": {"None": 1.0}, "category": "None"})
        bedrock_response_body = json.dumps({
            "content": [{"text": llm_output}]
        }).encode("utf-8")

        mock_body = Mock()
        mock_body.read.return_value = bedrock_response_body
        mock_client_instance.invoke_model.return_value = {"body": mock_body}

        guard = SemanticGuardrail()
        result = guard.check_safety("The article discusses pan-white tribalism in modern politics")

        assert result["block_type"] == BLOCK_TYPE_NONE
        assert result["category"] == "None"
        assert result["is_safe"] is True


class TestExceptionTextDoesNotLeakIntoLog:
    """Issue #619: exception text must not appear in server-side log output.

    Per docs/observability.html: "NEVER log prompt text, user input, completion
    text, URLs, or user IDs." Exceptions raised from code that processes user
    input can carry user-derived content in their message text. Only the
    exception class name may flow into logger.* calls.

    Response payloads going back to the requesting user are NOT scrubbed —
    the user is the source of their own request and re-receiving their data
    is not a privacy violation. See #668.
    """

    CANARY = "CANARY-LEAK-9d7e3f0a-WOULD-BE-USER-TEXT"

    @patch("src.guardrails.semantic.boto3.client")
    def test_exception_message_not_in_log_output(self, mock_boto_client, caplog):
        import logging

        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance
        mock_client_instance.invoke_model.side_effect = Exception(self.CANARY)

        guard = SemanticGuardrail()
        with caplog.at_level(logging.ERROR, logger="src.guardrails.semantic"):
            guard.check_safety("test input")

        log_text = "\n".join(r.getMessage() for r in caplog.records)
        assert self.CANARY not in log_text, (
            f"Exception text leaked into log output: {log_text!r}"
        )
        assert "SEMANTIC_GUARDRAIL_ERROR" in log_text
        assert "Exception" in log_text, "Exception class name missing from log — lost diagnostic value"
