"""
Unit tests for the Guardrails feature.
"""
import pytest
from src.guardrails.engine import GuardrailsEngine

@pytest.fixture
def engine():
    return GuardrailsEngine()

def test_valid_input(engine):
    """Test a standard, valid word."""
    result = engine.validate_input("enthalpy")
    assert result.is_valid is True
    assert result.reason == "Valid"

@pytest.mark.parametrize("invalid_word, expected_reason_part", [
    ("a", "Input length"),
    ("a" * 51, "Input length"),
    ("bbbbbbbbbb", "low entropy"),
    ("1212121212", "low entropy"),
])
def test_invalid_inputs(engine, invalid_word, expected_reason_part):
    """Test various invalid inputs."""
    result = engine.validate_input(invalid_word)
    assert result.is_valid is False
    assert expected_reason_part in result.reason

def test_empty_input(engine):
    """Test that empty string is caught by the length validator."""
    result = engine.validate_input("")
    assert result.is_valid is False
    # The length validator runs first (performance optimization), so we expect a length error.
    assert "Input length" in result.reason
