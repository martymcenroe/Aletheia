#!/usr/bin/env python3
"""
RSDB Download Utility - Fetches racial slur data and formats for denylist.

See: docs/1119-rsdb-download-utility.md

Usage:
    poetry run python tools/rsdb_download.py           # Download to .rsdb/
    poetry run python tools/rsdb_download.py --dry-run # Stats only, no save
    poetry run python tools/rsdb_download.py --output-dir /path/to/dir
"""
import argparse
import json
import logging
import sys
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Source URL for RSDB data (GitHub Gist with pre-structured JSON)
RSDB_GIST_URL = (
    "https://gist.githubusercontent.com/Vizdun/"
    "0e9d76834d609dde09842be9bab53db7/raw/rsdb.json"
)

# Default output directory (relative to repo root)
DEFAULT_OUTPUT_DIR = ".rsdb"


def fetch_rsdb_json(url: str = RSDB_GIST_URL) -> list[dict]:
    """
    Fetch RSDB data from GitHub Gist.

    Args:
        url: URL to fetch JSON from.

    Returns:
        List of dictionaries with slur data.

    Raises:
        urllib.error.URLError: On network failure.
        json.JSONDecodeError: On invalid JSON.
    """
    logger.info(f"Fetching data from: {url}")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Aletheia-RSDB-Downloader/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)


def extract_terms(rsdb_data: list[dict]) -> set[str]:
    """
    Extract and normalize slur terms from RSDB data.

    Args:
        rsdb_data: List of dicts with 'slur' field.

    Returns:
        Set of unique, lowercase terms.
    """
    terms = set()
    missing_field_count = 0

    for entry in rsdb_data:
        if "slur" in entry and entry["slur"]:
            term = entry["slur"].lower().strip()
            if term:
                terms.add(term)
        else:
            missing_field_count += 1

    if missing_field_count > 0:
        logger.warning(f"Skipped {missing_field_count} entries without 'slur' field")

    return terms


def format_denylist(terms: set[str], source_url: str) -> dict:
    """
    Format terms into denylist.json schema.

    Args:
        terms: Set of normalized terms.
        source_url: URL where data was fetched from.

    Returns:
        Dictionary matching denylist.json schema.
    """
    sorted_terms = sorted(terms)
    return {
        "version": "1.0",
        "source": "rsdb.org",
        "source_url": source_url,
        "updated": date.today().isoformat(),
        "term_count": len(sorted_terms),
        "terms": sorted_terms
    }


def save_json(data: dict, path: Path) -> None:
    """Save data as formatted JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download RSDB data and format for denylist"
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
        "--url",
        default=RSDB_GIST_URL,
        help="Source URL (default: GitHub Gist)"
    )

    args = parser.parse_args()

    try:
        # Fetch data
        rsdb_data = fetch_rsdb_json(args.url)
        logger.info(f"Fetched {len(rsdb_data)} entries")

        # Save raw backup (unless dry run)
        if not args.dry_run:
            raw_path = args.output_dir / "rsdb-raw.json"
            save_json(rsdb_data, raw_path)

        # Extract and normalize terms
        terms = extract_terms(rsdb_data)
        logger.info(f"Extracted {len(terms)} unique terms")
        logger.info(f"Removed {len(rsdb_data) - len(terms)} duplicates")

        # Format for denylist
        denylist = format_denylist(terms, args.url)

        # Save or report
        if args.dry_run:
            logger.info("Dry run - not saving files")
            logger.info(f"Would save {denylist['term_count']} terms")
        else:
            denylist_path = args.output_dir / "denylist.json"
            save_json(denylist, denylist_path)
            logger.info(f"Success! {denylist['term_count']} terms saved")
            logger.info(f"Copy to src/guardrails/resources/denylist.json before deploy")

    except urllib.error.URLError as e:
        logger.error(f"Network error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
