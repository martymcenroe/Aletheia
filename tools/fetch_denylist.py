#!/usr/bin/env python3
"""
Wikipedia Denylist Fetcher - Fetches profanity/slur data from Wikipedia.

See: docs/1121-wikipedia-denylist.md

Sources:
    1. List of ethnic slurs (article) - multi-pass wikitext parsing
    2. Category:Sexual_slang - enumerate category members
    3. Category:Profanity - enumerate category members

Usage:
    poetry run python tools/fetch_denylist.py           # Download to .rsdb/
    poetry run python tools/fetch_denylist.py --dry-run # Stats only, no save
    poetry run python tools/fetch_denylist.py --deploy  # Also copy to src/
"""
import argparse
import json
import logging
import re
import shutil
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
import urllib.request
import urllib.error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Politeness Protocol
USER_AGENT = "Aletheia-Bot/1.0 (+https://github.com/martymcenroe/Aletheia; contact@example.com)"
RATE_LIMIT_SECONDS = 1.0  # MANDATORY: 1 request per second

# Wikipedia API endpoint
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

# Targets
ETHNIC_SLURS_PAGE = "List_of_ethnic_slurs"
CATEGORIES = [
    "Category:Sexual_slang",
    "Category:Profanity",
]

# Output paths
DEFAULT_OUTPUT_DIR = ".rsdb"
DEPLOY_TARGET = "src/guardrails/resources/denylist.json"

# =============================================================================
# SAFETY CHECKS (Section 6.5 of LLD)
# =============================================================================

# 6.5.1 Safety Stop-List - Top 100 common English words
# If Wikipedia is vandalized to include these, build FAILS
SAFETY_STOP_LIST = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    # Additional safety words
    "hello", "world", "cloud", "computer", "phone", "email", "name", "home", "help",
    "is", "are", "was", "were", "been", "being", "has", "had", "does", "did",
}

# 6.5.2 Minimum Threshold - Catches silent parsing failures
MINIMUM_TERM_COUNT = 500

# 6.5.3 Canary Terms - Seven Dirty Words (must be present)
# These are added as seed terms if not found in Wikipedia sources
CANARY_TERMS = {
    "shit", "piss", "fuck", "cunt", "cocksucker", "motherfucker", "tits",
}

# Seed terms - always included regardless of Wikipedia extraction
# These ensure baseline coverage for common profanity not in our Wikipedia sources
# Category:Profanity contains articles ABOUT profanity, not profane words themselves
SEED_TERMS = {
    # Seven Dirty Words (George Carlin)
    "shit", "piss", "fuck", "cunt", "cocksucker", "motherfucker", "tits",
    # Common profanity
    "ass", "asshole", "bastard", "bitch", "damn", "dick", "hell",
    # Common slurs that might be missed
    "fag", "faggot", "dyke", "retard", "retarded",
}

# =============================================================================
# REGEX PATTERNS (Section 6.2 of LLD - Multi-Pass Parsing)
# =============================================================================

# Pass 1: Wikitable cells - first cell often contains the term
PATTERN_TABLE_CELL = re.compile(
    r"^\|\s*(?:''')?([A-Za-z][^|'\n\[\]]{1,40}?)(?:''')?\s*(?:\|\||$)",
    re.MULTILINE
)

# Pass 2: Definition list format (;Term : definition)
PATTERN_DEFINITION_LIST = re.compile(
    r"^;\s*(?:''')?([^':|\n\[\]]+?)(?:''')?(?:\s*:|\s*$)",
    re.MULTILINE
)

# Pass 3: Bulleted bold terms (* '''term''')
PATTERN_BULLETED_BOLD = re.compile(
    r"^\*+\s*'''([^']{2,50})'''",
    re.MULTILINE
)


# =============================================================================
# API LAYER
# =============================================================================

def api_request(params: dict) -> dict:
    """
    Make a request to Wikipedia API with proper User-Agent.

    Includes mandatory time.sleep(1.0) AFTER the request for rate limiting.

    Args:
        params: Dictionary of API parameters.

    Returns:
        Parsed JSON response.

    Raises:
        urllib.error.URLError: On network failure.
    """
    params["format"] = "json"
    url = f"{WIKIPEDIA_API}?{urlencode(params)}"

    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    # MANDATORY rate limiting
    time.sleep(RATE_LIMIT_SECONDS)

    return data


def fetch_page_wikitext(title: str) -> str:
    """
    Fetch raw wikitext content of a Wikipedia article.

    Args:
        title: Page title (underscores or spaces).

    Returns:
        Raw wikitext content.
    """
    logger.info(f"Fetching wikitext: {title}")

    params = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
    }

    data = api_request(params)
    pages = data.get("query", {}).get("pages", {})

    for page_id, page_data in pages.items():
        if page_id == "-1":
            raise ValueError(f"Page not found: {title}")
        revisions = page_data.get("revisions", [])
        if revisions:
            return revisions[0].get("slots", {}).get("main", {}).get("*", "")

    return ""


def fetch_category_members(category: str) -> list[str]:
    """
    Enumerate all page titles in a Wikipedia category.

    Handles continuation to get all members, not just first page.

    Args:
        category: Category name with "Category:" prefix.

    Returns:
        List of page titles in the category.
    """
    logger.info(f"Fetching category members: {category}")

    members = []
    continue_token = None

    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmlimit": "500",  # Max per request
            "cmtype": "page",  # Only pages, not subcategories
        }

        if continue_token:
            params["cmcontinue"] = continue_token

        data = api_request(params)

        # Extract member titles
        for member in data.get("query", {}).get("categorymembers", []):
            members.append(member.get("title", ""))

        # Check for continuation
        if "continue" in data:
            continue_token = data["continue"].get("cmcontinue")
            # Rate limiting handled in api_request
        else:
            break

    return members


# =============================================================================
# MULTI-PASS PARSING (Section 6.2 of LLD)
# =============================================================================

def parse_wikitables(wikitext: str) -> set[str]:
    """
    Pass 1: Extract terms from wikitable cells.

    Args:
        wikitext: Raw wikitext content.

    Returns:
        Set of extracted terms.
    """
    terms = set()
    for match in PATTERN_TABLE_CELL.finditer(wikitext):
        term = match.group(1).strip()
        if term and len(term) >= 2 and len(term) <= 40:
            terms.add(term)
    return terms


def parse_definition_lists(wikitext: str) -> set[str]:
    """
    Pass 2: Extract terms from definition list format (^;Term:).

    Args:
        wikitext: Raw wikitext content.

    Returns:
        Set of extracted terms.
    """
    terms = set()
    for match in PATTERN_DEFINITION_LIST.finditer(wikitext):
        term = match.group(1).strip()
        if term and len(term) >= 2:
            terms.add(term)
    return terms


def parse_bulleted_bold(wikitext: str) -> set[str]:
    """
    Pass 3: Extract terms from bulleted bold format (* '''term''').

    Args:
        wikitext: Raw wikitext content.

    Returns:
        Set of extracted terms.
    """
    terms = set()
    for match in PATTERN_BULLETED_BOLD.finditer(wikitext):
        term = match.group(1).strip()
        if term and len(term) >= 2:
            terms.add(term)
    return terms


def parse_ethnic_slurs_wikitext(wikitext: str) -> set[str]:
    """
    Aggregate all three parsing passes into a single set.

    Args:
        wikitext: Raw wikitext content.

    Returns:
        Set of all extracted terms from all passes.
    """
    terms = set()

    # Pass 1: Wikitables
    table_terms = parse_wikitables(wikitext)
    logger.info(f"  Pass 1 (tables): {len(table_terms)} terms")
    terms.update(table_terms)

    # Pass 2: Definition lists
    def_terms = parse_definition_lists(wikitext)
    logger.info(f"  Pass 2 (definitions): {len(def_terms)} terms")
    terms.update(def_terms)

    # Pass 3: Bulleted bold
    bullet_terms = parse_bulleted_bold(wikitext)
    logger.info(f"  Pass 3 (bullets): {len(bullet_terms)} terms")
    terms.update(bullet_terms)

    return terms


# =============================================================================
# NORMALIZATION
# =============================================================================

def extract_terms_from_title(title: str) -> list[str]:
    """
    Extract usable terms from a Wikipedia article title.

    Filters out non-term articles and handles disambiguation.

    Args:
        title: Wikipedia article title.

    Returns:
        List of cleaned terms (may be empty if title is not a term).
    """
    # Filter out list/category articles - these are not terms themselves
    if title.startswith(("List of", "Lists of", "Category:", "Template:", "Wikipedia:")):
        return []

    # Filter out articles with many words (likely about the topic, not a term)
    word_count = len(title.split())
    if word_count > 4:
        return []

    # Remove disambiguation suffixes: "Fuck (word)" -> "Fuck"
    term = re.sub(r"\s*\([^)]+\)\s*$", "", title).strip()

    if not term or len(term) < 2:
        return []

    return [term]


def split_compound_terms(term: str) -> list[str]:
    """
    Split terms containing multiple variants.

    Handles patterns like:
    - "abo / abbo" -> ["abo", "abbo"]
    - "beaner, beaney" -> ["beaner", "beaney"]

    Args:
        term: A potentially compound term.

    Returns:
        List of individual terms.
    """
    # Split on common separators
    if " / " in term:
        parts = term.split(" / ")
    elif ", " in term:
        parts = term.split(", ")
    elif " or " in term.lower():
        parts = re.split(r"\s+or\s+", term, flags=re.IGNORECASE)
    else:
        return [term]

    # Clean up each part
    cleaned = []
    for part in parts:
        part = part.strip()
        if part and len(part) >= 2:
            cleaned.append(part)

    return cleaned if cleaned else [term]


def merge_and_normalize(sources: dict[str, set[str]]) -> list[str]:
    """
    Merge all sources, normalize to lowercase, deduplicate, sort.

    Also adds SEED_TERMS to ensure baseline coverage.

    Args:
        sources: Dictionary of source -> terms.

    Returns:
        Sorted list of unique lowercase terms.
    """
    all_terms = set()

    for source, terms in sources.items():
        for term in terms:
            # Split compound terms
            for sub_term in split_compound_terms(term):
                normalized = sub_term.lower().strip()
                if normalized and len(normalized) >= 2:
                    all_terms.add(normalized)

    # Add seed terms (ensures baseline coverage)
    all_terms.update(SEED_TERMS)
    logger.info(f"Added {len(SEED_TERMS)} seed terms for baseline coverage")

    # Filter out obvious non-terms
    filtered = {
        t for t in all_terms
        if not t.startswith(("category:", "file:", "template:", "wikipedia:"))
        and "==" not in t
        and len(t) <= 50
    }

    return sorted(filtered)


# =============================================================================
# SAFETY CHECKS (Section 6.5 of LLD - BLOCKING)
# =============================================================================

def check_safety_stop_list(terms: set[str]) -> list[str]:
    """
    Return list of terms that match the stop-list.

    Empty list = pass.

    Args:
        terms: Set of normalized (lowercase) terms.

    Returns:
        List of violating terms.
    """
    violations = []
    for term in terms:
        if term in SAFETY_STOP_LIST:
            violations.append(term)
    return violations


def check_minimum_threshold(terms: set[str]) -> bool:
    """
    Return True if term count >= MINIMUM_TERM_COUNT.

    Args:
        terms: Set of terms.

    Returns:
        True if threshold met.
    """
    return len(terms) >= MINIMUM_TERM_COUNT


def check_canary_terms(terms: set[str]) -> list[str]:
    """
    Return list of missing canary terms.

    Empty list = pass.

    Args:
        terms: Set of normalized (lowercase) terms.

    Returns:
        List of missing canary terms.
    """
    missing = []
    for canary in CANARY_TERMS:
        if canary not in terms:
            missing.append(canary)
    return missing


def run_safety_checks(terms: set[str]) -> tuple[bool, str]:
    """
    Run all safety checks.

    Args:
        terms: Set of normalized (lowercase) terms.

    Returns:
        Tuple of (passed: bool, message: str).
    """
    # Check 1: Stop-list
    stop_list_violations = check_safety_stop_list(terms)
    if stop_list_violations:
        return (False, f"STOP-LIST VIOLATION: Common words found in denylist: {stop_list_violations[:5]}")

    # Check 2: Threshold
    if not check_minimum_threshold(terms):
        return (False, f"THRESHOLD VIOLATION: Only {len(terms)} terms extracted (minimum: {MINIMUM_TERM_COUNT})")

    # Check 3: Canaries
    missing_canaries = check_canary_terms(terms)
    if missing_canaries:
        return (False, f"CANARY VIOLATION: Missing required terms: {missing_canaries}")

    return (True, "All safety checks PASSED")


# =============================================================================
# OUTPUT
# =============================================================================

def format_denylist(terms: list[str], sources: dict[str, set[str]]) -> dict:
    """
    Format terms into denylist.json schema.

    Args:
        terms: Merged and normalized terms list.
        sources: Original sources for metadata.

    Returns:
        Dictionary matching denylist.json schema.
    """
    source_stats = {k: len(v) for k, v in sources.items()}

    return {
        "version": "2.0",
        "source": "wikipedia",
        "generated_by": "tools/fetch_denylist.py",
        "safety_checks": "passed",
        "sources": {
            "ethnic_slurs": "https://en.wikipedia.org/wiki/List_of_ethnic_slurs",
            "sexual-slang": "https://en.wikipedia.org/wiki/Category:Sexual_slang",
            "profanity": "https://en.wikipedia.org/wiki/Category:Profanity",
        },
        "source_stats": source_stats,
        "updated": date.today().isoformat(),
        "term_count": len(terms),
        "terms": terms
    }


def save_json(data: dict, path: Path) -> None:
    """Save data as formatted JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved: {path}")


# =============================================================================
# MAIN
# =============================================================================

def fetch_all_sources() -> dict[str, set[str]]:
    """
    Fetch terms from all sources.

    Returns:
        Dictionary mapping source name to set of terms.
    """
    sources = {}

    # Source 1: Ethnic slurs page (multi-pass wikitext parsing)
    try:
        wikitext = fetch_page_wikitext(ETHNIC_SLURS_PAGE)
        terms = parse_ethnic_slurs_wikitext(wikitext)
        sources["ethnic_slurs"] = terms
        logger.info(f"  → Total from ethnic slurs: {len(terms)} terms")
    except Exception as e:
        logger.error(f"Failed to fetch ethnic slurs: {e}")
        sources["ethnic_slurs"] = set()

    # Source 2 & 3: Categories
    for category in CATEGORIES:
        try:
            members = fetch_category_members(category)
            terms = set()
            for m in members:
                extracted = extract_terms_from_title(m)
                terms.update(extracted)
            # Clean the category name for the key
            key = category.replace("Category:", "").lower().replace("_", "-")
            sources[key] = terms
            logger.info(f"  → Found {len(terms)} terms in {category}")
        except Exception as e:
            logger.error(f"Failed to fetch {category}: {e}")

    return sources


def main():
    """CLI entry point with --dry-run and --deploy options."""
    parser = argparse.ArgumentParser(
        description="Fetch Wikipedia profanity/slur data for denylist"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and report stats without saving files"
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help=f"Also copy to {DEPLOY_TARGET}"
    )

    args = parser.parse_args()

    try:
        logger.info("=" * 60)
        logger.info("Wikipedia Denylist Fetcher")
        logger.info(f"User-Agent: {USER_AGENT}")
        logger.info("=" * 60)

        # Fetch from all sources
        logger.info("")
        logger.info("Fetching from Wikipedia sources...")
        sources = fetch_all_sources()

        # Report per-source stats
        logger.info("")
        logger.info("Source statistics:")
        total_raw = 0
        for source, terms in sources.items():
            logger.info(f"  {source}: {len(terms)} terms")
            total_raw += len(terms)

        # Merge and normalize
        merged_terms = merge_and_normalize(sources)
        logger.info("")
        logger.info(f"Total raw terms: {total_raw}")
        logger.info(f"After merge/dedupe: {len(merged_terms)} unique terms")

        # Run safety checks (BLOCKING)
        logger.info("")
        logger.info("Running safety checks...")
        terms_set = set(merged_terms)
        passed, message = run_safety_checks(terms_set)

        if not passed:
            logger.error("")
            logger.error("=" * 60)
            logger.error("BUILD FAILED - SAFETY CHECK VIOLATION")
            logger.error(message)
            logger.error("=" * 60)
            sys.exit(1)

        logger.info(f"  ✓ {message}")

        # Format for denylist
        denylist = format_denylist(merged_terms, sources)

        # Save or report
        if args.dry_run:
            logger.info("")
            logger.info("Dry run - not saving files")
            logger.info(f"Would save {denylist['term_count']} terms")
            # Print a sample
            logger.info("Sample terms (first 20):")
            for term in merged_terms[:20]:
                logger.info(f"  - {term}")
        else:
            # Save to staging directory
            denylist_path = args.output_dir / "denylist.json"
            save_json(denylist, denylist_path)

            # Optionally deploy
            if args.deploy:
                deploy_path = Path(DEPLOY_TARGET)
                deploy_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(denylist_path, deploy_path)
                logger.info(f"Deployed to: {deploy_path}")

            logger.info("")
            logger.info("=" * 60)
            logger.info(f"SUCCESS: {denylist['term_count']} terms saved")
            logger.info(f"Safety checks: PASSED")
            logger.info("=" * 60)
            if not args.deploy:
                logger.info(f"Run with --deploy to copy to {DEPLOY_TARGET}")

    except urllib.error.URLError as e:
        logger.error(f"Network error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
