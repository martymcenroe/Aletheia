"""URL fetching with User-Agent handling.

See docs/1084-signal-inspector.md Section 4.4 for User-Agent strategy.
"""

import logging
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# User-Agent strings per LLD Section 4.4
USER_AGENTS = {
    "aletheia": "AletheiaBot/1.0 (Compliance Auditor; +https://github.com/martymcenroe/aletheia)",
    "chrome": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Default timeout in seconds
DEFAULT_TIMEOUT = 10

# Maximum redirects to follow
MAX_REDIRECTS = 5


def get_user_agent(mode: str, custom_string: Optional[str] = None) -> str:
    """Get User-Agent string based on mode.

    Args:
        mode: One of 'aletheia', 'chrome', or 'custom'
        custom_string: Custom User-Agent string (required if mode is 'custom')

    Returns:
        User-Agent string to use in requests
    """
    if mode == "custom":
        if not custom_string:
            raise ValueError("Custom User-Agent string required when mode is 'custom'")
        return custom_string
    return USER_AGENTS.get(mode, USER_AGENTS["aletheia"])


def fetch_robots_txt(
    url: str,
    user_agent: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Optional[str]:
    """Fetch robots.txt from domain root.

    Args:
        url: Any URL on the target domain
        user_agent: User-Agent string to use
        timeout: Request timeout in seconds

    Returns:
        robots.txt content as string, or None if not found/error
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    logger.debug(f"Fetching robots.txt from {robots_url}")

    try:
        response = requests.get(
            robots_url,
            headers={"User-Agent": user_agent},
            timeout=timeout,
            allow_redirects=True,
        )

        if response.status_code == 200:
            return response.text
        elif response.status_code == 404:
            logger.debug(f"No robots.txt found at {robots_url}")
            return None
        else:
            logger.warning(
                f"Unexpected status {response.status_code} fetching robots.txt"
            )
            return None

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching robots.txt from {robots_url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching robots.txt: {e}")
        return None


def fetch_page(
    url: str,
    user_agent: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[Optional[str], dict, Optional[int], Optional[str]]:
    """Fetch page content with headers.

    Args:
        url: URL to fetch
        user_agent: User-Agent string to use
        timeout: Request timeout in seconds

    Returns:
        Tuple of (html_content, headers_dict, status_code, error_message)
        - html_content: Page HTML or None on error
        - headers_dict: Response headers (case-insensitive dict)
        - status_code: HTTP status code or None on connection error
        - error_message: Error description or None on success
    """
    logger.debug(f"Fetching page {url}")

    try:
        response = requests.get(
            url,
            headers={"User-Agent": user_agent},
            timeout=timeout,
            allow_redirects=True,
        )

        # Convert headers to regular dict for easier handling
        headers = dict(response.headers)

        if response.status_code == 200:
            return response.text, headers, response.status_code, None
        else:
            return None, headers, response.status_code, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching {url}")
        return None, {}, None, "timeout"
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"Connection error fetching {url}: {e}")
        return None, {}, None, "dns_error"
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None, {}, None, str(e)
