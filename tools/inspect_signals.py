#!/usr/bin/env python3
"""Signal Inspector CLI - Audit compliance signals from target URLs.

See docs/1084-signal-inspector.md for full design documentation.

Usage:
    python tools/inspect_signals.py -u https://example.com
    python tools/inspect_signals.py -f urls.txt --ua chrome
    python tools/inspect_signals.py -u https://example.com --force
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from signal_inspector import (
    AletheiaAction,
    FetchStatus,
    SignalResult,
    append_jsonl,
    derive_action,
    fetch_page,
    fetch_robots_txt,
    merge_signals,
    parse_meta_tags,
    parse_rating_tag,
    parse_robots_txt,
    parse_x_robots_tag,
    print_console_report,
)
from signal_inspector.fetcher import get_user_agent

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT = Path("data/signal_audit.jsonl")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Audit compliance signals from target URLs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -u https://example.com
  %(prog)s -f urls.txt --ua chrome -o data/batch_audit.jsonl
  %(prog)s -u https://example.com --force
        """,
    )

    # Input (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-u", "--url",
        help="Single URL to inspect",
    )
    input_group.add_argument(
        "-f", "--file",
        type=Path,
        help="File containing URLs (one per line)",
    )

    # Output
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"JSONL output path (default: {DEFAULT_OUTPUT})",
    )

    # User-Agent
    parser.add_argument(
        "--ua",
        choices=["chrome", "aletheia", "custom"],
        default="aletheia",
        help="User-Agent mode (default: aletheia)",
    )
    parser.add_argument(
        "--ua-string",
        help="Custom User-Agent string (requires --ua custom)",
    )

    # Behavior
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0,
        help="Delay between requests in batch mode (default: 0)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass robots.txt gatekeeper (fetch even if disallowed)",
    )

    # Logging
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    parsed = parser.parse_args(args)

    # Validate custom UA requires string
    if parsed.ua == "custom" and not parsed.ua_string:
        parser.error("--ua-string required when --ua is 'custom'")

    return parsed


def get_urls(args: argparse.Namespace) -> list[str]:
    """Get list of URLs to inspect from args."""
    if args.url:
        return [args.url]

    # Read from file
    urls = []
    with open(args.file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def inspect_url(
    url: str,
    user_agent: str,
    timeout: int,
    force: bool,
) -> SignalResult:
    """Inspect a single URL and return SignalResult.

    Implements the gatekeeper pattern from LLD Section 4.1:
    1. Fetch robots.txt
    2. Check permissions (block if disallowed unless --force)
    3. Fetch page and parse signals
    """
    result = SignalResult(
        timestamp=datetime.now(timezone.utc),
        url=url,
        fetch_status=FetchStatus.SUCCESS,
    )

    # Step 1: Fetch robots.txt
    robots_content = fetch_robots_txt(url, user_agent, timeout)

    # Step 2: Parse robots.txt and check permissions
    result.robots_txt = parse_robots_txt(robots_content, url, "AletheiaBot")

    # Determine if blocked by robots.txt
    # Use Aletheia-specific permission if defined, otherwise fall back to wildcard
    can_fetch = result.robots_txt.can_fetch_aletheia
    if can_fetch is None:
        can_fetch = result.robots_txt.can_fetch_wildcard

    robots_blocked = can_fetch is False

    # Gatekeeper check
    if robots_blocked and not force:
        result.fetch_status = FetchStatus.ROBOTS_BLOCKED
        result.aletheia_action = AletheiaAction.BLOCK
        return result

    # Step 3: Fetch page
    html, headers, status_code, error = fetch_page(url, user_agent, timeout)
    result.http_status = status_code

    if error:
        # Map error to FetchStatus
        if error == "timeout":
            result.fetch_status = FetchStatus.TIMEOUT
        elif error == "dns_error":
            result.fetch_status = FetchStatus.DNS_ERROR
        else:
            result.fetch_status = FetchStatus.HTTP_ERROR
        result.errors.append(error)
        result.aletheia_action = derive_action(result.merged, robots_blocked=False)
        return result

    if not html:
        result.fetch_status = FetchStatus.HTTP_ERROR
        result.errors.append(f"Empty response from {url}")
        return result

    # Step 4: Parse signals
    try:
        result.meta_tags = parse_meta_tags(html)
        result.headers = parse_x_robots_tag(headers)
        result.rating = parse_rating_tag(html)
    except Exception as e:
        result.fetch_status = FetchStatus.PARSE_ERROR
        result.errors.append(f"Parse error: {e}")
        return result

    # Step 5: Merge and derive action
    result.merged = merge_signals(result.meta_tags, result.headers, result.rating)
    result.aletheia_action = derive_action(result.merged, robots_blocked=False)

    return result


def main(args: list[str] | None = None) -> int:
    """CLI entry point."""
    parsed = parse_args(args)

    # Configure logging
    log_level = logging.DEBUG if parsed.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Get User-Agent
    user_agent = get_user_agent(parsed.ua, parsed.ua_string)
    logger.info(f"Using User-Agent: {user_agent[:50]}...")

    # Get URLs
    try:
        urls = get_urls(parsed)
    except FileNotFoundError:
        print(f"Error: File not found: {parsed.file}", file=sys.stderr)
        return 1

    if not urls:
        print("Error: No URLs to inspect", file=sys.stderr)
        return 1

    logger.info(f"Inspecting {len(urls)} URL(s)")

    # Process each URL
    errors = 0
    for i, url in enumerate(urls):
        if i > 0 and parsed.delay > 0:
            time.sleep(parsed.delay)

        try:
            result = inspect_url(
                url=url,
                user_agent=user_agent,
                timeout=parsed.timeout,
                force=parsed.force,
            )

            # Output
            print_console_report(result)
            append_jsonl(result, parsed.output)

            if result.fetch_status != FetchStatus.SUCCESS:
                errors += 1

        except Exception as e:
            logger.exception(f"Unexpected error inspecting {url}")
            errors += 1

    # Summary
    print(f"\nProcessed {len(urls)} URL(s), {errors} error(s)")
    print(f"Results saved to: {parsed.output}")

    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
