"""Tests for user ID anonymization.

Issue #369: CloudWatch Usage Dashboard.
TDD: Tests written before implementation.
"""

import re

from src.auth.anonymize import anonymize_user_id


class TestAnonymizeUserId:
    """T010-T030: Anonymization function tests."""

    def test_returns_12_char_hex(self):
        """T010: Hash output is 12 lowercase hex characters (REQ-14)."""
        result = anonymize_user_id("test@example.com")
        assert len(result) == 12
        assert re.fullmatch(r"[0-9a-f]{12}", result) is not None

    def test_deterministic(self):
        """T020: Same input produces same output (REQ-14)."""
        output1 = anonymize_user_id("user123")
        output2 = anonymize_user_id("user123")
        assert output1 == output2

    def test_no_pii_leakage(self):
        """T030: Output does not contain input email parts (REQ-17)."""
        email = "test@example.com"
        result = anonymize_user_id(email)
        assert "test" not in result
        assert "@" not in result
        assert "example" not in result

    def test_different_inputs_different_outputs(self):
        """Different user IDs produce different hashes."""
        result1 = anonymize_user_id("user_a")
        result2 = anonymize_user_id("user_b")
        assert result1 != result2

    def test_empty_string(self):
        """Empty string is a valid input (edge case)."""
        result = anonymize_user_id("")
        assert len(result) == 12
        assert re.fullmatch(r"[0-9a-f]{12}", result) is not None

    def test_unicode_input(self):
        """Unicode user IDs are handled correctly."""
        result = anonymize_user_id("user_\u00e9\u00e8\u00ea")
        assert len(result) == 12
        assert re.fullmatch(r"[0-9a-f]{12}", result) is not None
