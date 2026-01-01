"""
Unit tests for tools/fetch_denylist.py

All tests use mocked fixtures - no network calls (Willison Protocol).
See: docs/1121-wikipedia-denylist.md Section 11
"""
import sys
from pathlib import Path

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

import pytest
from fetch_denylist import (
    parse_wikitables,
    parse_definition_lists,
    parse_bulleted_bold,
    parse_ethnic_slurs_wikitext,
    extract_terms_from_title,
    split_compound_terms,
    merge_and_normalize,
    check_safety_stop_list,
    check_minimum_threshold,
    check_canary_terms,
    run_safety_checks,
    SAFETY_STOP_LIST,
    MINIMUM_TERM_COUNT,
    CANARY_TERMS,
    SEED_TERMS,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_wikitext():
    """Load sample wikitext from fixture file."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_wikitext.txt"
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def valid_term_set():
    """A valid term set that passes all safety checks."""
    # Start with seed terms (includes canaries)
    terms = set(SEED_TERMS)
    # Add enough terms to meet threshold
    for i in range(600):
        terms.add(f"testterm{i}")
    return terms


# =============================================================================
# TEST: Multi-Pass Parsing (050-060)
# =============================================================================

class TestWikitableParsing:
    """Test ID 050: Wikitable parsing."""

    def test_extracts_table_cells(self, sample_wikitext):
        """Pass 1 should extract terms from wikitable cells."""
        terms = parse_wikitables(sample_wikitext)
        assert "Beaner" in terms
        assert "Gringo" in terms

    def test_extracts_bold_in_tables(self, sample_wikitext):
        """Pass 1 should extract bold terms in table cells."""
        terms = parse_wikitables(sample_wikitext)
        # Bold terms in tables should also be captured
        assert len(terms) >= 2


class TestDefinitionListParsing:
    """Test ID 055: Definition list parsing."""

    def test_extracts_definition_terms(self, sample_wikitext):
        """Pass 2 should extract terms from ;Term: format."""
        terms = parse_definition_lists(sample_wikitext)
        assert "Honky" in terms or "Spic" in terms

    def test_extracts_bold_definition_terms(self, sample_wikitext):
        """Pass 2 should extract bold terms in definitions."""
        terms = parse_definition_lists(sample_wikitext)
        assert len(terms) >= 1


class TestBulletedBoldParsing:
    """Test ID 058: Bulleted bold parsing."""

    def test_extracts_bulleted_bold(self, sample_wikitext):
        """Pass 3 should extract * '''term''' format."""
        terms = parse_bulleted_bold(sample_wikitext)
        assert "Wetback" in terms
        assert "Chink" in terms

    def test_ignores_non_bold_bullets(self, sample_wikitext):
        """Pass 3 should ignore bullets without bold."""
        terms = parse_bulleted_bold(sample_wikitext)
        assert "Regular text without bold" not in terms


class TestMultiPassAggregation:
    """Test ID 060: Multi-pass aggregation."""

    def test_aggregates_all_passes(self, sample_wikitext):
        """All passes should be combined into a single set."""
        terms = parse_ethnic_slurs_wikitext(sample_wikitext)
        # Should have terms from multiple passes
        assert len(terms) >= 5


# =============================================================================
# TEST: Normalization (070-090)
# =============================================================================

class TestTitleExtraction:
    """Test ID 070: Category member extraction."""

    def test_extracts_simple_title(self):
        """Simple titles should be extracted."""
        assert extract_terms_from_title("Fuck") == ["Fuck"]

    def test_removes_disambiguation(self):
        """Disambiguation suffixes should be removed."""
        assert extract_terms_from_title("Fuck (word)") == ["Fuck"]

    def test_filters_list_articles(self):
        """'List of...' articles should be filtered."""
        assert extract_terms_from_title("List of profane words") == []

    def test_filters_category_articles(self):
        """Category articles should be filtered."""
        assert extract_terms_from_title("Category:Profanity") == []

    def test_filters_long_titles(self):
        """Titles with >4 words should be filtered."""
        assert extract_terms_from_title("This is a very long article title") == []


class TestCompoundTermSplitting:
    """Test ID 080: Compound term splitting."""

    def test_splits_slash_separated(self):
        """'abo / abbo' should split to ['abo', 'abbo']."""
        result = split_compound_terms("abo / abbo")
        assert "abo" in result
        assert "abbo" in result

    def test_splits_comma_separated(self):
        """'beaner, beaney' should split."""
        result = split_compound_terms("beaner, beaney")
        assert "beaner" in result
        assert "beaney" in result

    def test_keeps_single_term(self):
        """Single terms should not be split."""
        result = split_compound_terms("slur")
        assert result == ["slur"]


class TestInvalidTitleFiltering:
    """Test ID 090: Invalid title filtering."""

    def test_filters_list_of(self):
        """'List of profane words' should return empty."""
        assert extract_terms_from_title("List of profane words") == []


# =============================================================================
# TEST: Safety Checks (110-140)
# =============================================================================

class TestSafetyStopList:
    """Test ID 110: Stop-list blocks common words."""

    def test_detects_common_words(self):
        """Terms containing 'the' should fail."""
        terms = {"slur1", "slur2", "the"}
        violations = check_safety_stop_list(terms)
        assert "the" in violations

    def test_passes_clean_terms(self):
        """Clean terms should pass."""
        terms = {"slur1", "slur2", "slur3"}
        violations = check_safety_stop_list(terms)
        assert violations == []


class TestMinimumThreshold:
    """Test ID 120: Threshold catches empty result."""

    def test_fails_below_threshold(self):
        """<500 terms should fail."""
        terms = set(f"term{i}" for i in range(100))
        assert not check_minimum_threshold(terms)

    def test_passes_above_threshold(self):
        """≥500 terms should pass."""
        terms = set(f"term{i}" for i in range(600))
        assert check_minimum_threshold(terms)


class TestCanaryTerms:
    """Test ID 130: Canary catches missing terms."""

    def test_detects_missing_canaries(self):
        """Missing canary terms should be detected."""
        terms = {"slur1", "slur2"}  # Missing all canaries
        missing = check_canary_terms(terms)
        assert len(missing) == len(CANARY_TERMS)

    def test_passes_with_all_canaries(self):
        """All canaries present should pass."""
        terms = CANARY_TERMS.copy()
        missing = check_canary_terms(terms)
        assert missing == []


class TestSafetyChecksIntegration:
    """Test ID 140: All safety checks pass."""

    def test_valid_set_passes(self, valid_term_set):
        """Valid term set should pass all checks."""
        passed, message = run_safety_checks(valid_term_set)
        assert passed
        assert "PASSED" in message

    def test_poisoned_set_fails(self, valid_term_set):
        """Set with common words should fail."""
        poisoned = valid_term_set | {"the", "hello"}
        passed, message = run_safety_checks(poisoned)
        assert not passed
        assert "STOP-LIST" in message


# =============================================================================
# TEST: Schema Validation (100)
# =============================================================================

class TestSchemaValidation:
    """Test ID 100: Schema validation."""

    def test_merge_includes_seed_terms(self):
        """Merge should include all seed terms."""
        sources = {"test": {"term1", "term2"}}
        merged = merge_and_normalize(sources)
        for seed in SEED_TERMS:
            assert seed in merged

    def test_merge_normalizes_case(self):
        """Merge should lowercase all terms."""
        sources = {"test": {"UPPER", "MiXeD"}}
        merged = merge_and_normalize(sources)
        assert "upper" in merged
        assert "mixed" in merged
        assert "UPPER" not in merged


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
