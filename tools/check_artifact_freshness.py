#!/usr/bin/env python3
"""Check build artifact freshness.

Compares source file modification times against build artifacts to detect
stale builds before store submission.

Usage:
    poetry run python tools/check_artifact_freshness.py           # Check both
    poetry run python tools/check_artifact_freshness.py --firefox # Firefox only
    poetry run python tools/check_artifact_freshness.py --chrome  # Chrome only
    poetry run python tools/check_artifact_freshness.py --quiet   # Exit code only

Exit codes:
    0 - All artifacts fresh (safe to submit)
    1 - One or more artifacts stale (rebuild required)
    2 - Artifact missing (must build first)
    3 - Configuration error (source directory missing)
"""

from datetime import datetime
from pathlib import Path
import argparse
import json
import sys

# Paths - match build_release.py
REPO_ROOT = Path(__file__).parent.parent
CHROME_DIR = REPO_ROOT / "extensions" / "chrome"
FIREFOX_DIR = REPO_ROOT / "extensions" / "firefox"
DIST_DIR = REPO_ROOT / "dist"

# Exclusions - match build_release.py
EXCLUDE_PATTERNS = {".git", "__pycache__", ".DS_Store", ".pyc", "node_modules"}


def should_include(path: Path) -> bool:
    """Filter out excluded patterns."""
    return not any(pattern in path.parts for pattern in EXCLUDE_PATTERNS)


def load_manifest(path: Path) -> dict:
    """Load and parse a manifest JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def format_time(mtime: float) -> str:
    """Format mtime as human-readable string."""
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")


def get_source_files(source_dir: Path) -> list[Path]:
    """Get all source files in directory, filtered by exclusions."""
    return [f for f in source_dir.rglob("*") if f.is_file() and should_include(f)]


def check_freshness(browser: str, version: str) -> tuple[int, str, list[tuple[Path, float]]]:
    """Check artifact freshness for a browser.

    Args:
        browser: "chrome" or "firefox"
        version: Version string from manifest

    Returns:
        (exit_code, message, stale_files)
        exit_code: 0=fresh, 1=stale, 2=missing, 3=error
        message: Human-readable status message
        stale_files: List of (path, mtime) tuples for files newer than artifact
    """
    source_dir = CHROME_DIR if browser == "chrome" else FIREFOX_DIR
    artifact_name = f"aletheia-{browser}-v{version}.zip"
    artifact_path = DIST_DIR / artifact_name

    # Check source directory exists
    if not source_dir.exists():
        return (3, f"Source directory missing: {source_dir}", [])

    # Check artifact exists
    if not artifact_path.exists():
        return (2, f"Artifact missing: {artifact_path}", [])

    artifact_mtime = artifact_path.stat().st_mtime

    # Get all source files
    source_files = get_source_files(source_dir)
    if not source_files:
        return (3, f"No source files found in {source_dir}", [])

    # Find files newer than artifact
    stale_files = []
    for src in source_files:
        src_mtime = src.stat().st_mtime
        if src_mtime > artifact_mtime:
            stale_files.append((src, src_mtime))

    # Build result
    if stale_files:
        newest = max(stale_files, key=lambda x: x[1])
        newest_rel = newest[0].relative_to(source_dir)
        msg = (
            f"STALE: {len(stale_files)} file(s) newer than artifact\n"
            f"  Artifact: {format_time(artifact_mtime)}\n"
            f"  Newest:   {newest_rel} ({format_time(newest[1])})"
        )
        return (1, msg, stale_files)

    msg = f"FRESH: Artifact up-to-date ({len(source_files)} files checked)"
    return (0, msg, [])


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Check build artifact freshness before store submission"
    )
    parser.add_argument("--chrome", action="store_true", help="Check Chrome only")
    parser.add_argument("--firefox", action="store_true", help="Check Firefox only")
    parser.add_argument("--quiet", action="store_true", help="Exit code only, no output")
    args = parser.parse_args()

    # Determine which browsers to check
    if args.chrome:
        browsers = ["chrome"]
    elif args.firefox:
        browsers = ["firefox"]
    else:
        browsers = ["chrome", "firefox"]

    # Get version from Chrome manifest (source of truth)
    try:
        chrome_manifest = load_manifest(CHROME_DIR / "manifest.json")
        version = chrome_manifest["version"]
    except FileNotFoundError:
        if not args.quiet:
            print("ERROR: Chrome manifest not found", file=sys.stderr)
        return 3
    except json.JSONDecodeError as e:
        if not args.quiet:
            print(f"ERROR: Invalid manifest JSON: {e}", file=sys.stderr)
        return 3

    # Check each browser
    worst_exit = 0
    results = []

    for browser in browsers:
        exit_code, message, _ = check_freshness(browser, version)
        results.append((browser, exit_code, message))
        worst_exit = max(worst_exit, exit_code)

    # Output
    if not args.quiet:
        print("=" * 50)
        print("Build Artifact Freshness Check")
        print("=" * 50)
        print(f"Version: {version}")
        print()

        for browser, code, msg in results:
            if code == 0:
                symbol = "[FRESH]"
            elif code == 1:
                symbol = "[STALE]"
            elif code == 2:
                symbol = "[MISSING]"
            else:
                symbol = "[ERROR]"

            print(f"{browser.capitalize()}: {symbol}")
            for line in msg.split("\n"):
                print(f"  {line}")
            print()

        if worst_exit == 0:
            print("All artifacts are fresh. Safe to submit to stores.")
        elif worst_exit == 1:
            print("Action required: poetry run python tools/build_release.py")
        elif worst_exit == 2:
            print("Action required: poetry run python tools/build_release.py")
        else:
            print("Configuration error - check paths above.")

    return worst_exit


if __name__ == "__main__":
    sys.exit(main())
