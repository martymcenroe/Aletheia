"""Signal extraction from HTML, headers, and robots.txt.

See docs/1084-signal-inspector.md for parsing rules:
- Section 4.1: Signal precedence (robots.txt gatekeeper)
- Section 4.3: X-Robots-Tag header handling
- Appendix A: Standards references
"""

import logging
import re
from typing import Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

from .models import (
    AletheiaAction,
    HeaderResult,
    MergedSignals,
    MetaTagResult,
    RatingResult,
    RobotsTxtResult,
)

logger = logging.getLogger(__name__)

# RTA label pattern per Google SafeSearch docs
RTA_PATTERN = re.compile(r"RTA-5042-1996-1400-1577-RTA", re.IGNORECASE)


def parse_robots_txt(
    content: Optional[str],
    url: str,
    user_agent: str = "AletheiaBot",
) -> RobotsTxtResult:
    """Parse robots.txt and check permissions for URL.

    Args:
        content: robots.txt content (None if not found)
        url: Target URL to check permissions for
        user_agent: Bot name to check (default: AletheiaBot)

    Returns:
        RobotsTxtResult with fetch permissions
    """
    result = RobotsTxtResult()

    if content is None:
        # No robots.txt = permissive (can fetch everything)
        result.can_fetch_wildcard = True
        result.can_fetch_aletheia = True
        return result

    # Extract raw directives for debugging
    result.raw_directives = [
        line.strip()
        for line in content.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]

    # Parse using stdlib RobotFileParser
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    # Check for wildcard user-agent
    rp_wildcard = RobotFileParser()
    rp_wildcard.set_url(robots_url)
    rp_wildcard.parse(content.split("\n"))
    result.can_fetch_wildcard = rp_wildcard.can_fetch("*", url)

    # Check for specific Aletheia user-agent
    # If not explicitly defined, inherit from wildcard
    rp_aletheia = RobotFileParser()
    rp_aletheia.set_url(robots_url)
    rp_aletheia.parse(content.split("\n"))
    result.can_fetch_aletheia = rp_aletheia.can_fetch(user_agent, url)

    logger.debug(
        f"robots.txt check: wildcard={result.can_fetch_wildcard}, "
        f"aletheia={result.can_fetch_aletheia}"
    )

    return result


def parse_meta_tags(html: str) -> MetaTagResult:
    """Extract robots-related meta tags from HTML.

    Looks for:
    - <meta name="robots" content="...">
    - <meta name="googlebot" content="..."> (also checked)

    Args:
        html: HTML content to parse

    Returns:
        MetaTagResult with detected directives
    """
    result = MetaTagResult()
    soup = BeautifulSoup(html, "html.parser")

    # Find all robots meta tags
    for meta in soup.find_all("meta", attrs={"name": re.compile(r"robots|googlebot", re.I)}):
        raw_content = meta.get("content", "")
        content = str(raw_content).lower() if raw_content else ""
        directives = [d.strip() for d in content.split(",")]

        for directive in directives:
            if directive == "noindex":
                result.noindex = True
            elif directive == "noarchive":
                result.noarchive = True
            elif directive == "nosnippet":
                result.nosnippet = True
            elif directive == "noai":
                result.noai = True
            elif directive == "noimageai":
                result.noimageai = True

    logger.debug(f"Meta tags parsed: {result}")
    return result


def parse_x_robots_tag(headers: dict) -> HeaderResult:
    """Parse X-Robots-Tag header value(s).

    Per LLD Section 4.3:
    - Header may appear multiple times
    - Values are comma-separated
    - User-agent prefix is stripped

    Args:
        headers: Response headers dict

    Returns:
        HeaderResult with parsed directives
    """
    result = HeaderResult()

    # Get X-Robots-Tag header (case-insensitive)
    header_value = None
    for key, value in headers.items():
        if key.lower() == "x-robots-tag":
            header_value = value
            break

    if not header_value:
        return result

    result.x_robots_tag_present = True

    # Handle multiple values (could be list or comma-separated string)
    values = header_value if isinstance(header_value, list) else [header_value]

    directives = set()
    for value in values:
        # Split on comma and process each directive
        for part in value.split(","):
            part = part.strip().lower()
            # Strip user-agent prefix if present (e.g., "googlebot: noindex")
            if ":" in part:
                part = part.split(":", 1)[1].strip()
            if part:
                directives.add(part)

    result.x_robots_tag_values = sorted(directives)
    logger.debug(f"X-Robots-Tag parsed: {result.x_robots_tag_values}")
    return result


def parse_rating_tag(html: str) -> RatingResult:
    """Detect adult/RTA rating meta tags.

    Looks for:
    - <meta name="rating" content="adult">
    - <meta name="rating" content="RTA-5042-1996-1400-1577-RTA">

    Args:
        html: HTML content to parse

    Returns:
        RatingResult with adult rating status
    """
    result = RatingResult()
    soup = BeautifulSoup(html, "html.parser")

    # Find rating meta tag
    rating_meta = soup.find("meta", attrs={"name": re.compile(r"^rating$", re.I)})
    if not rating_meta:
        return result

    raw_content = rating_meta.get("content", "")
    content = str(raw_content) if raw_content else ""
    result.raw_value = content

    # Check for adult rating
    content_lower = content.lower()
    if content_lower == "adult":
        result.adult_rated = True
    elif content and RTA_PATTERN.search(content):
        result.adult_rated = True

    logger.debug(f"Rating tag: adult_rated={result.adult_rated}, raw={result.raw_value}")
    return result


def merge_signals(
    meta: MetaTagResult,
    headers: HeaderResult,
    rating: RatingResult,
) -> MergedSignals:
    """Combine meta tags and headers into unified signal set.

    Per LLD Section 4.1: Uses OR logic (most restrictive interpretation).
    "No" trumps "Yes" - if either source has the directive, it's present.

    Args:
        meta: Parsed meta tag results
        headers: Parsed X-Robots-Tag header results
        rating: Parsed rating tag results

    Returns:
        MergedSignals with combined results
    """
    header_directives = set(headers.x_robots_tag_values)

    return MergedSignals(
        noindex=meta.noindex or "noindex" in header_directives,
        noarchive=meta.noarchive or "noarchive" in header_directives,
        nosnippet=meta.nosnippet or "nosnippet" in header_directives,
        noai=meta.noai or "noai" in header_directives,
        adult_blocked=rating.adult_rated,
    )


def derive_action(
    merged: MergedSignals,
    robots_blocked: bool = False,
) -> AletheiaAction:
    """Determine Aletheia action per docs/0007 policy.

    Priority order:
    1. robots.txt block (gatekeeper) -> BLOCK
    2. Adult content -> BLOCK
    3. noarchive -> TRANSFORM
    4. Otherwise -> ALLOW

    Note: noai is IGNORED per 0007 (we do inference, not training)

    Args:
        merged: Combined signals from meta and headers
        robots_blocked: True if robots.txt disallows access

    Returns:
        AletheiaAction to take
    """
    if robots_blocked:
        return AletheiaAction.BLOCK

    if merged.adult_blocked:
        return AletheiaAction.BLOCK

    if merged.noarchive:
        return AletheiaAction.TRANSFORM

    return AletheiaAction.ALLOW
