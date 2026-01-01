# Signal Inspector - Compliance signal auditing tool
# See docs/1084-signal-inspector.md for design details

from .models import (
    FetchStatus,
    AletheiaAction,
    RobotsTxtResult,
    MetaTagResult,
    HeaderResult,
    RatingResult,
    MergedSignals,
    SignalResult,
)
from .fetcher import fetch_robots_txt, fetch_page
from .parser import (
    parse_meta_tags,
    parse_x_robots_tag,
    parse_robots_txt,
    parse_rating_tag,
    merge_signals,
    derive_action,
)
from .reporter import print_console_report, append_jsonl

__all__ = [
    # Models
    "FetchStatus",
    "AletheiaAction",
    "RobotsTxtResult",
    "MetaTagResult",
    "HeaderResult",
    "RatingResult",
    "MergedSignals",
    "SignalResult",
    # Fetcher
    "fetch_robots_txt",
    "fetch_page",
    # Parser
    "parse_meta_tags",
    "parse_x_robots_tag",
    "parse_robots_txt",
    "parse_rating_tag",
    "merge_signals",
    "derive_action",
    # Reporter
    "print_console_report",
    "append_jsonl",
]
