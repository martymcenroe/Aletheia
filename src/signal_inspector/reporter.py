"""Console and JSONL output reporting.

See docs/1084-signal-inspector.md Section 13 for console format.
"""

import json
import logging
from pathlib import Path

from colorama import Fore, Style, init as colorama_init

from .models import AletheiaAction, FetchStatus, SignalResult

logger = logging.getLogger(__name__)

# Initialize colorama for cross-platform support
colorama_init()


def _color_bool(value: bool, inverted: bool = False) -> str:
    """Format boolean with color (green=good, red=bad).

    Args:
        value: Boolean value to format
        inverted: If True, True is bad (red) and False is good (green)

    Returns:
        Colored string representation
    """
    if inverted:
        color = Fore.RED if value else Fore.GREEN
    else:
        color = Fore.GREEN if value else Fore.RED
    return f"{color}{str(value).upper()}{Style.RESET_ALL}"


def _color_action(action: AletheiaAction) -> str:
    """Format action with appropriate color."""
    colors = {
        AletheiaAction.ALLOW: Fore.GREEN,
        AletheiaAction.TRANSFORM: Fore.YELLOW,
        AletheiaAction.BLOCK: Fore.RED,
    }
    color = colors.get(action, Fore.WHITE)
    return f"{color}{action.value}{Style.RESET_ALL}"


def _color_status(status: FetchStatus) -> str:
    """Format fetch status with color."""
    if status == FetchStatus.SUCCESS:
        return f"{Fore.GREEN}{status.value}{Style.RESET_ALL}"
    else:
        return f"{Fore.RED}{status.value}{Style.RESET_ALL}"


def print_console_report(result: SignalResult) -> None:
    """Print color-coded report to stdout.

    See LLD Section 13 for format specification.
    """
    width = 64
    divider = "=" * width
    thin_divider = "-" * width

    print(f"\n{divider}")
    print(f"URL: {result.url}")
    print(f"Status: {_color_status(result.fetch_status)}")
    if result.http_status:
        print(f"HTTP: {result.http_status}")
    print(divider)

    # Robots.txt section
    print("\nROBOTS.TXT")
    if result.robots_txt.can_fetch_wildcard is not None:
        allowed = "Allowed" if result.robots_txt.can_fetch_wildcard else "BLOCKED"
        color = Fore.GREEN if result.robots_txt.can_fetch_wildcard else Fore.RED
        print(f"  User-agent: *        -> {color}{allowed}{Style.RESET_ALL}")
    else:
        print(f"  User-agent: *        -> {Fore.CYAN}(not found){Style.RESET_ALL}")

    if result.robots_txt.can_fetch_aletheia is not None:
        allowed = "Allowed" if result.robots_txt.can_fetch_aletheia else "BLOCKED"
        color = Fore.GREEN if result.robots_txt.can_fetch_aletheia else Fore.RED
        print(f"  User-agent: Aletheia -> {color}{allowed}{Style.RESET_ALL}")
    else:
        print(f"  User-agent: Aletheia -> {Fore.CYAN}(not defined){Style.RESET_ALL}")

    # Only show meta/header details if we fetched the page
    if result.fetch_status == FetchStatus.SUCCESS:
        # Meta tags section
        print("\nMETA TAGS")
        print(f"  noindex              -> {_color_bool(result.meta_tags.noindex, inverted=True)}")
        print(f"  noarchive            -> {_color_bool(result.meta_tags.noarchive, inverted=True)}")
        print(f"  nosnippet            -> {_color_bool(result.meta_tags.nosnippet, inverted=True)}")
        print(f"  noai                 -> {_color_bool(result.meta_tags.noai, inverted=True)}")

        # HTTP headers section
        print("\nHTTP HEADERS")
        if result.headers.x_robots_tag_present:
            values = ", ".join(result.headers.x_robots_tag_values) or "(empty)"
            print(f"  X-Robots-Tag         -> {Fore.YELLOW}{values}{Style.RESET_ALL}")
        else:
            print(f"  X-Robots-Tag         -> {Fore.CYAN}(not present){Style.RESET_ALL}")

        # Content rating section
        print("\nCONTENT RATING")
        if result.rating.raw_value:
            color = Fore.RED if result.rating.adult_rated else Fore.GREEN
            print(f"  rating               -> {color}{result.rating.raw_value}{Style.RESET_ALL}")
        else:
            print(f"  rating               -> {Fore.CYAN}(not present){Style.RESET_ALL}")

        # Merged results
        print(f"\n{thin_divider}")
        merged_parts = []
        if result.merged.noindex:
            merged_parts.append(f"{Fore.YELLOW}noindex{Style.RESET_ALL}")
        if result.merged.noarchive:
            merged_parts.append(f"{Fore.YELLOW}noarchive{Style.RESET_ALL}")
        if result.merged.nosnippet:
            merged_parts.append(f"{Fore.YELLOW}nosnippet{Style.RESET_ALL}")
        if result.merged.adult_blocked:
            merged_parts.append(f"{Fore.RED}adult_blocked{Style.RESET_ALL}")

        if merged_parts:
            print(f"MERGED RESULT:      {', '.join(merged_parts)}")
        else:
            print(f"MERGED RESULT:      {Fore.GREEN}(none){Style.RESET_ALL}")

    elif result.fetch_status == FetchStatus.ROBOTS_BLOCKED:
        print(f"\n{Fore.RED}PAGE NOT FETCHED - Blocked by robots.txt{Style.RESET_ALL}")

    # Aletheia action
    print(f"ALETHEIA ACTION:    {_color_action(result.aletheia_action)} (per docs/0007)")
    print(thin_divider)

    # Errors if any
    if result.errors:
        print(f"\n{Fore.RED}ERRORS:{Style.RESET_ALL}")
        for error in result.errors:
            print(f"  - {error}")


def append_jsonl(result: SignalResult, output_path: Path) -> None:
    """Append result as JSON line to output file.

    Args:
        result: SignalResult to serialize
        output_path: Path to JSONL output file

    Creates parent directories if needed.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Append as single line
    with open(output_path, "a", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False)
        f.write("\n")

    logger.debug(f"Appended result to {output_path}")
