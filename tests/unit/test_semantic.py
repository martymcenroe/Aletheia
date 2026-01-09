import json
from pathlib import Path
from unittest.mock import Mock, patch
from src.guardrails.semantic import SemanticGuardrail

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
