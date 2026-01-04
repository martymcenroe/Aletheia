import json
from unittest.mock import Mock, patch
from src.guardrails.semantic import SemanticGuardrail

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
