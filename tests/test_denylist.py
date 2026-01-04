"""
Unit tests for the Denylist feature.

See: docs/1045-deterministic-hate-filter.md Section 10.

IMPORTANT: Tests mock load_denylist() with safe placeholder terms.
Real denylist validation occurs in manual smoke tests only.
"""
import json
import tempfile
import time
from unittest.mock import patch

import pytest

from src.guardrails.denylist import (
    check_denylist,
    load_denylist,
    normalize_text,
)

# Safe placeholder terms for testing - NO real slurs
MOCK_DENYLIST = {"test_block_term", "forbidden_fruit", "blocked_word"}


@pytest.fixture
def mock_denylist():
    """Provide a mocked denylist with safe placeholder terms."""
    return MOCK_DENYLIST.copy()


@pytest.fixture
def temp_denylist_file():
    """Create a temporary denylist JSON file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(
            {
                "version": "1.0",
                "source": "test",
                "updated": "2025-01-01",
                "terms": list(MOCK_DENYLIST),
            },
            f,
        )
        return f.name


class TestNormalizeText:
    """Tests for normalize_text function."""

    def test_lowercase(self):
        """Text is lowercased."""
        assert normalize_text("HELLO") == "hello"

    def test_strip_whitespace(self):
        """Leading/trailing whitespace is stripped."""
        assert normalize_text("  hello  ") == "hello"

    def test_nfkc_normalization(self):
        """Unicode is normalized to NFKC."""
        # Full-width H -> normal H
        assert normalize_text("\uff28ELLO") == "hello"


class TestLoadDenylist:
    """Tests for load_denylist function."""

    def test_load_from_file(self, temp_denylist_file):
        """Load denylist from a valid JSON file."""
        result = load_denylist(temp_denylist_file)
        assert result == MOCK_DENYLIST

    def test_missing_file_fails_open(self, tmp_path):
        """Missing file returns empty set (fail open)."""
        result = load_denylist(str(tmp_path / "nonexistent.json"))
        assert result == set()

    def test_malformed_json_fails_open(self, tmp_path):
        """Malformed JSON returns empty set (fail open)."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid json }", encoding="utf-8")
        result = load_denylist(str(bad_file))
        assert result == set()

    def test_terms_lowercased(self, tmp_path):
        """Terms are lowercased on load."""
        json_file = tmp_path / "upper.json"
        json_file.write_text(
            json.dumps({"terms": ["UPPER_TERM", "Mixed_Term"]}),
            encoding="utf-8",
        )
        result = load_denylist(str(json_file))
        assert "upper_term" in result
        assert "mixed_term" in result


class TestCheckDenylist:
    """Tests for check_denylist function - covers LLD Section 10.1 scenarios."""

    def test_010_known_term_blocked(self, mock_denylist):
        """Scenario 010: Known term is blocked."""
        result = check_denylist("test_block_term", mock_denylist)
        assert result["blocked"] is True
        assert result["term"] == "[REDACTED]"
        assert result["reason"] == "denylist"

    def test_020_clean_word_passes(self, mock_denylist):
        """Scenario 020: Clean words pass through."""
        result = check_denylist("hello world", mock_denylist)
        assert result["blocked"] is False
        assert result["term"] is None
        assert result["reason"] == "clean"

    def test_030_empty_input(self, mock_denylist):
        """Scenario 030: Empty input does not crash."""
        result = check_denylist("", mock_denylist)
        assert result["blocked"] is False
        assert result["reason"] == "clean"

    def test_040_whitespace_only(self, mock_denylist):
        """Scenario 040: Whitespace-only input does not crash."""
        result = check_denylist("   ", mock_denylist)
        assert result["blocked"] is False
        assert result["reason"] == "clean"

    def test_050_case_insensitive(self, mock_denylist):
        """Scenario 050: Matching is case-insensitive."""
        result = check_denylist("TEST_BLOCK_TERM", mock_denylist)
        assert result["blocked"] is True

    def test_060_mixed_clean_and_blocked(self, mock_denylist):
        """Scenario 060: Blocked term detected in mixed input."""
        result = check_denylist("hello test_block_term world", mock_denylist)
        assert result["blocked"] is True
        assert result["term"] == "[REDACTED]"

    def test_070_performance_benchmark(self, mock_denylist):
        """Scenario 070: 1000 lookups complete in < 5ms."""
        start = time.perf_counter()
        for _ in range(1000):
            check_denylist("hello world", mock_denylist)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 5, f"1000 lookups took {elapsed_ms:.2f}ms (budget: 5ms)"

    def test_punctuation_handling(self, mock_denylist):
        """Blocked term with punctuation is still caught."""
        result = check_denylist("test_block_term!", mock_denylist)
        assert result["blocked"] is True

    def test_embedded_in_sentence(self, mock_denylist):
        """Blocked term embedded in sentence is caught."""
        result = check_denylist("I saw a forbidden_fruit today.", mock_denylist)
        assert result["blocked"] is True

    def test_empty_denylist_passes_all(self):
        """Empty denylist passes all input (fail open behavior)."""
        result = check_denylist("test_block_term", set())
        assert result["blocked"] is False

    def test_none_denylist_uses_global(self, temp_denylist_file):
        """None denylist loads and uses global singleton."""
        # Reset global state
        import src.guardrails.denylist as denylist_module
        denylist_module._denylist = None

        # Patch load_denylist to use our temp file
        with patch.object(
            denylist_module,
            "load_denylist",
            return_value=MOCK_DENYLIST,
        ):
            denylist_module._denylist = MOCK_DENYLIST
            result = check_denylist("test_block_term")
            assert result["blocked"] is True


class TestIntegration:
    """Integration tests using file-based denylist."""

    def test_full_flow(self, temp_denylist_file):
        """Full flow: load from file, check term."""
        denylist = load_denylist(temp_denylist_file)
        result = check_denylist("forbidden_fruit is bad", denylist)
        assert result["blocked"] is True
        assert result["reason"] == "denylist"

    def test_clean_input_full_flow(self, temp_denylist_file):
        """Full flow: clean input passes."""
        denylist = load_denylist(temp_denylist_file)
        result = check_denylist("hello world", denylist)
        assert result["blocked"] is False
        assert result["reason"] == "clean"
