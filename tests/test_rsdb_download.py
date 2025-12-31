"""
Unit tests for RSDB Download Utility.

See: docs/1119-rsdb-download-utility.md Section 10.

Tests use mocked network responses - no live fetching.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.rsdb_download import (
    extract_terms,
    fetch_rsdb_json,
    format_denylist,
    save_json,
)


# Safe mock data - no real slurs
MOCK_RSDB_DATA = [
    {"slur": "test_term_one", "group": "Test Group A", "desc": "A test term"},
    {"slur": "test_term_two", "group": "Test Group B", "desc": "Another test"},
    {"slur": "TEST_TERM_ONE", "group": "Test Group A", "desc": "Duplicate uppercase"},
    {"slur": "test_term_three", "group": "Test Group C", "desc": "Third term"},
    {"slur": "  whitespace_term  ", "group": "Test", "desc": "Has whitespace"},
]


class TestFetchRsdbJson:
    """Tests for fetch_rsdb_json function."""

    def test_010_successful_fetch(self):
        """Scenario 010: Successful download returns parsed JSON."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(MOCK_RSDB_DATA).encode("utf-8")
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = fetch_rsdb_json("http://test.url")

        assert len(result) == 5
        assert result[0]["slur"] == "test_term_one"

    def test_020_network_error(self):
        """Scenario 020: Network error raises URLError."""
        import urllib.error

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

            with pytest.raises(urllib.error.URLError):
                fetch_rsdb_json("http://unreachable.url")

    def test_030_malformed_json(self):
        """Scenario 030: Invalid JSON raises JSONDecodeError."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"{ invalid json }"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(json.JSONDecodeError):
                fetch_rsdb_json("http://test.url")


class TestExtractTerms:
    """Tests for extract_terms function."""

    def test_extracts_slur_field(self):
        """Extracts 'slur' field from entries."""
        terms = extract_terms(MOCK_RSDB_DATA)
        assert "test_term_one" in terms
        assert "test_term_two" in terms

    def test_050_removes_duplicates(self):
        """Scenario 050: Duplicates are removed (case-insensitive)."""
        terms = extract_terms(MOCK_RSDB_DATA)
        # test_term_one appears twice (different cases)
        assert len([t for t in terms if "test_term_one" in t]) == 1

    def test_normalizes_to_lowercase(self):
        """Terms are normalized to lowercase."""
        terms = extract_terms(MOCK_RSDB_DATA)
        for term in terms:
            assert term == term.lower()

    def test_strips_whitespace(self):
        """Whitespace is stripped from terms."""
        terms = extract_terms(MOCK_RSDB_DATA)
        assert "whitespace_term" in terms
        assert "  whitespace_term  " not in terms

    def test_040_handles_empty_input(self):
        """Scenario 040: Empty input returns empty set."""
        terms = extract_terms([])
        assert terms == set()

    def test_handles_missing_slur_field(self):
        """Entries without 'slur' field are skipped."""
        data = [
            {"group": "Test", "desc": "No slur field"},
            {"slur": "valid_term", "group": "Test", "desc": "Has slur"},
        ]
        terms = extract_terms(data)
        assert len(terms) == 1
        assert "valid_term" in terms


class TestFormatDenylist:
    """Tests for format_denylist function."""

    def test_correct_schema(self):
        """Output matches expected denylist.json schema."""
        terms = {"term_a", "term_b", "term_c"}
        result = format_denylist(terms, "http://source.url")

        assert result["version"] == "1.0"
        assert result["source"] == "rsdb.org"
        assert result["source_url"] == "http://source.url"
        assert "updated" in result  # Date string
        assert result["term_count"] == 3
        assert isinstance(result["terms"], list)

    def test_terms_sorted_alphabetically(self):
        """Terms are sorted alphabetically."""
        terms = {"zebra", "apple", "mango"}
        result = format_denylist(terms, "http://test")

        assert result["terms"] == ["apple", "mango", "zebra"]

    def test_term_count_accurate(self):
        """term_count matches actual number of terms."""
        terms = {"a", "b", "c", "d", "e"}
        result = format_denylist(terms, "http://test")

        assert result["term_count"] == 5
        assert len(result["terms"]) == 5


class TestSaveJson:
    """Tests for save_json function."""

    def test_creates_file(self):
        """Creates JSON file at specified path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            data = {"key": "value"}

            save_json(data, path)

            assert path.exists()
            with open(path) as f:
                loaded = json.load(f)
            assert loaded == data

    def test_creates_parent_directories(self):
        """Creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "dir" / "test.json"
            data = {"key": "value"}

            save_json(data, path)

            assert path.exists()


class TestDryRun:
    """Tests for dry-run mode."""

    def test_060_dry_run_no_file(self):
        """Scenario 060: Dry run does not create files."""
        # This is tested via CLI integration, but we verify the
        # underlying functions don't have side effects when called
        # in a dry-run context (handled in main())
        terms = extract_terms(MOCK_RSDB_DATA)
        denylist = format_denylist(terms, "http://test")

        # Functions return data without file operations
        assert denylist is not None
        assert len(denylist["terms"]) > 0


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline(self):
        """Full pipeline: fetch → extract → format → save."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(MOCK_RSDB_DATA).encode("utf-8")
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            with tempfile.TemporaryDirectory() as tmpdir:
                # Simulate full pipeline
                rsdb_data = fetch_rsdb_json("http://test.url")
                terms = extract_terms(rsdb_data)
                denylist = format_denylist(terms, "http://test.url")

                path = Path(tmpdir) / "denylist.json"
                save_json(denylist, path)

                # Verify result
                assert path.exists()
                with open(path) as f:
                    result = json.load(f)

                assert result["term_count"] == 4  # 5 entries, 1 duplicate
                assert "test_term_one" in result["terms"]
