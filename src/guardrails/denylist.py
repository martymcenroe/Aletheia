"""
Deterministic Hate Speech Filter (Denylist).

Blocks hate speech using a known denylist before engaging the LLM.
See: docs/1045-deterministic-hate-filter.md

O(1) lookup per token using HashSet. Fails open on errors.
"""
import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)

# Singleton: loaded once on cold start
_denylist: set[str] | None = None


class DenylistResult(TypedDict):
    """Result of denylist check."""
    blocked: bool
    term: str | None  # Redacted if blocked
    reason: str  # "denylist" or "clean"


def load_denylist(path: str | None = None) -> set[str]:
    """
    Load denylist from JSON file into memory.
    Called once on cold start.

    Args:
        path: Path to denylist JSON file. Defaults to resources/denylist.json.

    Returns:
        Set of lowercase terms from the denylist.

    Raises:
        No exceptions - fails open with empty set on error.
    """
    global _denylist

    if path is None:
        path = str(Path(__file__).parent / "resources" / "denylist.json")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        terms = data.get("terms", [])
        _denylist = {term.lower() for term in terms}
        logger.info(f"Loaded denylist: {len(_denylist)} terms from {path}")
        return _denylist
    except FileNotFoundError:
        logger.warning(f"Denylist file not found: {path}. Failing open.")
        _denylist = set()
        return _denylist
    except json.JSONDecodeError as e:
        logger.warning(f"Malformed denylist JSON: {e}. Failing open.")
        _denylist = set()
        return _denylist
    except Exception as e:
        logger.warning(f"Error loading denylist: {e}. Failing open.")
        _denylist = set()
        return _denylist


def normalize_text(text: str) -> str:
    """
    Normalize input for consistent matching.

    - NFKC unicode normalization (handles unicode bypass)
    - Lowercase
    - Strip whitespace

    Args:
        text: Raw input text.

    Returns:
        Normalized text.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.lower().strip()
    return text


def check_denylist(text: str, denylist: set[str] | None = None) -> DenylistResult:
    """
    Check if any token in text matches the denylist.

    O(1) lookup per token using HashSet.

    Args:
        text: Input text to check.
        denylist: Set of blocked terms. If None, uses global singleton.

    Returns:
        DenylistResult with blocked status, redacted term (if blocked), and reason.
    """
    global _denylist

    # Use provided denylist or load global singleton
    if denylist is None:
        if _denylist is None:
            load_denylist()
        denylist = _denylist

    # Handle empty/None denylist (fail open)
    if not denylist:
        return DenylistResult(blocked=False, term=None, reason="clean")

    # Normalize and tokenize
    normalized = normalize_text(text)
    # Use re.findall to handle punctuation (e.g., "badword!" -> "badword")
    tokens = set(re.findall(r"\w+", normalized))

    # O(1) lookup for each token
    for token in tokens:
        if token in denylist:
            # Redact the matched term for security
            return DenylistResult(blocked=True, term="[REDACTED]", reason="denylist")

    return DenylistResult(blocked=False, term=None, reason="clean")
