"""Data models for Signal Inspector.

See docs/1084-signal-inspector.md Section 7.1 for schema details.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class FetchStatus(Enum):
    """Status of URL fetch operation."""

    SUCCESS = "success"
    ROBOTS_BLOCKED = "robots_blocked"  # Gatekeeper denied access
    TIMEOUT = "timeout"
    DNS_ERROR = "dns_error"
    HTTP_ERROR = "http_error"
    PARSE_ERROR = "parse_error"


class AletheiaAction(Enum):
    """Action Aletheia should take per docs/0007 policy."""

    ALLOW = "ALLOW"
    TRANSFORM = "TRANSFORM"
    BLOCK = "BLOCK"


@dataclass
class RobotsTxtResult:
    """Result of robots.txt parsing."""

    can_fetch_wildcard: Optional[bool] = None
    can_fetch_aletheia: Optional[bool] = None
    raw_directives: list[str] = field(default_factory=list)


@dataclass
class MetaTagResult:
    """Result of HTML meta tag parsing."""

    noindex: bool = False
    noarchive: bool = False
    nosnippet: bool = False
    noai: bool = False
    noimageai: bool = False


@dataclass
class HeaderResult:
    """Result of X-Robots-Tag header parsing."""

    x_robots_tag_present: bool = False
    x_robots_tag_values: list[str] = field(default_factory=list)


@dataclass
class RatingResult:
    """Result of content rating meta tag parsing."""

    adult_rated: bool = False
    raw_value: Optional[str] = None


@dataclass
class MergedSignals:
    """Combined signals from meta tags and headers (OR logic)."""

    noindex: bool = False
    noarchive: bool = False
    nosnippet: bool = False
    noai: bool = False
    adult_blocked: bool = False


@dataclass
class SignalResult:
    """Complete result of URL signal inspection."""

    timestamp: datetime
    url: str
    fetch_status: FetchStatus
    http_status: Optional[int] = None
    robots_txt: RobotsTxtResult = field(default_factory=RobotsTxtResult)
    meta_tags: MetaTagResult = field(default_factory=MetaTagResult)
    headers: HeaderResult = field(default_factory=HeaderResult)
    rating: RatingResult = field(default_factory=RatingResult)
    merged: MergedSignals = field(default_factory=MergedSignals)
    aletheia_action: AletheiaAction = AletheiaAction.ALLOW
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat() + "Z",
            "url": self.url,
            "fetch_status": self.fetch_status.value,
            "http_status": self.http_status,
            "signals": {
                "robots_txt": {
                    "can_fetch_wildcard": self.robots_txt.can_fetch_wildcard,
                    "can_fetch_aletheia": self.robots_txt.can_fetch_aletheia,
                    "raw_directives": self.robots_txt.raw_directives,
                },
                "meta_tags": {
                    "noindex": self.meta_tags.noindex,
                    "noarchive": self.meta_tags.noarchive,
                    "nosnippet": self.meta_tags.nosnippet,
                    "noai": self.meta_tags.noai,
                    "noimageai": self.meta_tags.noimageai,
                },
                "headers": {
                    "x_robots_tag_present": self.headers.x_robots_tag_present,
                    "x_robots_tag_values": self.headers.x_robots_tag_values,
                },
                "rating": {
                    "adult_rated": self.rating.adult_rated,
                    "raw_value": self.rating.raw_value,
                },
                "merged": {
                    "noindex": self.merged.noindex,
                    "noarchive": self.merged.noarchive,
                    "nosnippet": self.merged.nosnippet,
                    "noai": self.merged.noai,
                    "adult_blocked": self.merged.adult_blocked,
                },
            },
            "aletheia_action": self.aletheia_action.value,
            "errors": self.errors,
        }
