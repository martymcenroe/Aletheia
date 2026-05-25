"""Tests for Signal Inspector.

See docs/1084-signal-inspector.md Section 11.1 for test scenarios.
"""

import json
import sys
from pathlib import Path

import pytest
import responses

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from signal_inspector import (  # noqa: E402
    AletheiaAction,
    FetchStatus,
    SignalResult,
    derive_action,
    merge_signals,
    parse_meta_tags,
    parse_rating_tag,
    parse_robots_txt,
    parse_x_robots_tag,
)
from signal_inspector.models import HeaderResult, MergedSignals, MetaTagResult, RatingResult  # noqa: E402

# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "signal_inspector"


def load_fixture(name: str) -> str:
    """Load fixture file content."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class TestParseMetaTags:
    """Test 010-030: Meta tag parsing."""

    def test_010_clean_page(self):
        """Test 010: Clean page with no signals."""
        html = load_fixture("clean.html")
        result = parse_meta_tags(html)

        assert result.noindex is False
        assert result.noarchive is False
        assert result.nosnippet is False
        assert result.noai is False
        assert result.noimageai is False

    def test_020_noarchive_meta_tag(self):
        """Test 020: noarchive meta tag detection."""
        html = load_fixture("noarchive.html")
        result = parse_meta_tags(html)

        assert result.noarchive is True
        assert result.noindex is False

    def test_030_noai_meta_tag(self):
        """Test 030: noai meta tag detection (should be detected but ignored in action)."""
        html = load_fixture("noai.html")
        result = parse_meta_tags(html)

        assert result.noai is True
        assert result.noarchive is False

    def test_multiple_directives(self):
        """Test parsing multiple comma-separated directives."""
        html = load_fixture("multiple_signals.html")
        result = parse_meta_tags(html)

        assert result.noindex is True
        assert result.noarchive is True
        assert result.nosnippet is True


class TestParseXRobotsTag:
    """Test 040-050: X-Robots-Tag header parsing."""

    def test_040_x_robots_tag_header(self):
        """Test 040: X-Robots-Tag header detection."""
        headers = {"X-Robots-Tag": "noarchive, nosnippet"}
        result = parse_x_robots_tag(headers)

        assert result.x_robots_tag_present is True
        assert "noarchive" in result.x_robots_tag_values
        assert "nosnippet" in result.x_robots_tag_values

    def test_no_header(self):
        """Test when X-Robots-Tag header is absent."""
        headers = {"Content-Type": "text/html"}
        result = parse_x_robots_tag(headers)

        assert result.x_robots_tag_present is False
        assert result.x_robots_tag_values == []

    def test_user_agent_prefix_stripped(self):
        """Test that user-agent prefix is stripped from directives."""
        headers = {"X-Robots-Tag": "googlebot: noindex"}
        result = parse_x_robots_tag(headers)

        assert "noindex" in result.x_robots_tag_values
        assert "googlebot" not in result.x_robots_tag_values


class TestMergeSignals:
    """Test 050: Merging meta tags and headers with OR logic."""

    def test_050_merge_or_logic(self):
        """Test 050: OR logic for merging signals."""
        meta = MetaTagResult(noarchive=True)
        headers = HeaderResult(x_robots_tag_present=True, x_robots_tag_values=["nosnippet"])
        rating = RatingResult()

        merged = merge_signals(meta, headers, rating)

        # Both should be True (OR logic)
        assert merged.noarchive is True
        assert merged.nosnippet is True
        assert merged.noindex is False

    def test_merge_header_only(self):
        """Test merging when only header has directive."""
        meta = MetaTagResult()
        headers = HeaderResult(x_robots_tag_present=True, x_robots_tag_values=["noarchive"])
        rating = RatingResult()

        merged = merge_signals(meta, headers, rating)

        assert merged.noarchive is True


class TestParseRatingTag:
    """Test 060-070: Rating tag detection."""

    def test_060_adult_rating(self):
        """Test 060: Adult rating meta tag detection."""
        html = load_fixture("adult_rated.html")
        result = parse_rating_tag(html)

        assert result.adult_rated is True
        assert result.raw_value == "adult"

    def test_070_rta_label(self):
        """Test 070: RTA label pattern detection."""
        html = load_fixture("rta_label.html")
        result = parse_rating_tag(html)

        assert result.adult_rated is True
        assert "RTA-5042" in result.raw_value

    def test_no_rating(self):
        """Test when no rating tag is present."""
        html = load_fixture("clean.html")
        result = parse_rating_tag(html)

        assert result.adult_rated is False
        assert result.raw_value is None


class TestParseRobotsTxt:
    """Test 080, 085, 120: robots.txt parsing."""

    def test_080_robots_disallow(self):
        """Test 080: robots.txt with Disallow directive."""
        content = load_fixture("robots_disallow.txt")
        result = parse_robots_txt(content, "https://example.com/page")

        assert result.can_fetch_wildcard is False
        assert len(result.raw_directives) > 0

    def test_robots_allow(self):
        """Test robots.txt with Allow directive."""
        content = load_fixture("robots_allow.txt")
        result = parse_robots_txt(content, "https://example.com/page")

        assert result.can_fetch_wildcard is True

    def test_120_robots_missing(self):
        """Test 120: Missing robots.txt (permissive)."""
        result = parse_robots_txt(None, "https://example.com/page")

        assert result.can_fetch_wildcard is True
        assert result.can_fetch_aletheia is True


class TestDeriveAction:
    """Test action derivation per docs/0007 policy."""

    def test_action_allow(self):
        """Test ALLOW action for clean signals."""
        merged = MergedSignals()
        action = derive_action(merged)

        assert action == AletheiaAction.ALLOW

    def test_action_transform_noarchive(self):
        """Test TRANSFORM action for noarchive signal."""
        merged = MergedSignals(noarchive=True)
        action = derive_action(merged)

        assert action == AletheiaAction.TRANSFORM

    def test_action_block_adult(self):
        """Test BLOCK action for adult content."""
        merged = MergedSignals(adult_blocked=True)
        action = derive_action(merged)

        assert action == AletheiaAction.BLOCK

    def test_action_block_robots(self):
        """Test BLOCK action for robots.txt block."""
        merged = MergedSignals()
        action = derive_action(merged, robots_blocked=True)

        assert action == AletheiaAction.BLOCK

    def test_noai_ignored_in_action(self):
        """Test 030: noai is detected but ignored in action (per 0007)."""
        merged = MergedSignals(noai=True)
        action = derive_action(merged)

        # noai should NOT cause BLOCK or TRANSFORM
        assert action == AletheiaAction.ALLOW


class TestInspectUrlIntegration:
    """Integration tests using responses mock library."""

    @responses.activate
    def test_full_inspection_clean(self):
        """Test full inspection of clean page."""
        # Import here to avoid import issues
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
        from inspect_signals import inspect_url

        # Mock robots.txt (not found)
        responses.add(
            responses.GET,
            "https://example.com/robots.txt",
            status=404,
        )

        # Mock page
        responses.add(
            responses.GET,
            "https://example.com/page",
            body=load_fixture("clean.html"),
            status=200,
            headers={"Content-Type": "text/html"},
        )

        result = inspect_url(
            url="https://example.com/page",
            user_agent="TestBot",
            timeout=10,
            force=False,
        )

        assert result.fetch_status == FetchStatus.SUCCESS
        assert result.aletheia_action == AletheiaAction.ALLOW

    @responses.activate
    def test_full_inspection_noarchive(self):
        """Test full inspection with noarchive."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
        from inspect_signals import inspect_url

        responses.add(responses.GET, "https://example.com/robots.txt", status=404)
        responses.add(
            responses.GET,
            "https://example.com/page",
            body=load_fixture("noarchive.html"),
            status=200,
        )

        result = inspect_url("https://example.com/page", "TestBot", 10, False)

        assert result.fetch_status == FetchStatus.SUCCESS
        assert result.merged.noarchive is True
        assert result.aletheia_action == AletheiaAction.TRANSFORM

    @responses.activate
    def test_gatekeeper_robots_blocked(self):
        """Test 080: Gatekeeper blocks when robots.txt disallows."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
        from inspect_signals import inspect_url

        responses.add(
            responses.GET,
            "https://example.com/robots.txt",
            body=load_fixture("robots_disallow.txt"),
            status=200,
        )

        result = inspect_url("https://example.com/page", "TestBot", 10, force=False)

        assert result.fetch_status == FetchStatus.ROBOTS_BLOCKED
        assert result.aletheia_action == AletheiaAction.BLOCK
        # Page should NOT have been fetched
        assert len(responses.calls) == 1  # Only robots.txt

    @responses.activate
    def test_085_force_bypasses_gatekeeper(self):
        """Test 085: --force flag bypasses robots.txt gatekeeper."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
        from inspect_signals import inspect_url

        responses.add(
            responses.GET,
            "https://example.com/robots.txt",
            body=load_fixture("robots_disallow.txt"),
            status=200,
        )
        responses.add(
            responses.GET,
            "https://example.com/page",
            body=load_fixture("clean.html"),
            status=200,
        )

        result = inspect_url("https://example.com/page", "TestBot", 10, force=True)

        assert result.fetch_status == FetchStatus.SUCCESS
        assert len(responses.calls) == 2  # Both robots.txt and page fetched

    @responses.activate
    def test_090_timeout_handling(self):
        """Test 090: Timeout handling."""
        import requests

        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
        from inspect_signals import inspect_url

        responses.add(responses.GET, "https://example.com/robots.txt", status=404)
        responses.add(
            responses.GET,
            "https://example.com/page",
            body=requests.exceptions.Timeout(),
        )

        result = inspect_url("https://example.com/page", "TestBot", 10, False)

        assert result.fetch_status == FetchStatus.TIMEOUT

    @responses.activate
    def test_x_robots_tag_in_response(self):
        """Test X-Robots-Tag header is parsed from response."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
        from inspect_signals import inspect_url

        responses.add(responses.GET, "https://example.com/robots.txt", status=404)
        responses.add(
            responses.GET,
            "https://example.com/page",
            body=load_fixture("clean.html"),
            status=200,
            headers={"X-Robots-Tag": "noarchive"},
        )

        result = inspect_url("https://example.com/page", "TestBot", 10, False)

        assert result.headers.x_robots_tag_present is True
        assert "noarchive" in result.headers.x_robots_tag_values
        assert result.merged.noarchive is True
        assert result.aletheia_action == AletheiaAction.TRANSFORM


class TestSignalResultSerialization:
    """Test JSONL output format."""

    def test_to_dict_format(self):
        """Test SignalResult.to_dict() output matches schema."""
        from datetime import datetime, timezone

        result = SignalResult(
            timestamp=datetime(2024, 12, 22, 14, 30, 0, tzinfo=timezone.utc),
            url="https://example.com/page",
            fetch_status=FetchStatus.SUCCESS,
            http_status=200,
        )
        result.merged.noarchive = True
        result.aletheia_action = AletheiaAction.TRANSFORM

        data = result.to_dict()

        assert data["timestamp"] == "2024-12-22T14:30:00+00:00Z"
        assert data["url"] == "https://example.com/page"
        assert data["fetch_status"] == "success"
        assert data["signals"]["merged"]["noarchive"] is True
        assert data["aletheia_action"] == "TRANSFORM"

        # Should be valid JSON
        json_str = json.dumps(data)
        assert json_str is not None


@pytest.mark.live
class TestLiveWebsites:
    """Live integration tests against real websites.

    These tests hit actual URLs and verify the tool works end-to-end.
    Run with: poetry run pytest -v -m live

    Note: These tests may be slower and can fail if sites change or are unavailable.
    """

    def test_wikipedia_allows(self):
        """Test Wikipedia returns ALLOW (permissive, no restrictive signals)."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
        from inspect_signals import inspect_url

        result = inspect_url(
            url="https://en.wikipedia.org/wiki/Main_Page",
            user_agent="AletheiaBot/1.0 (Compliance Auditor)",
            timeout=15,
            force=False,
        )

        assert result.fetch_status == FetchStatus.SUCCESS
        assert result.http_status == 200
        assert result.aletheia_action == AletheiaAction.ALLOW
        # Wikipedia should not have noarchive
        assert result.merged.noarchive is False

    def test_bbc_transforms_via_header(self):
        """Test BBC returns TRANSFORM (has X-Robots-Tag: noarchive header)."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
        from inspect_signals import inspect_url

        result = inspect_url(
            url="https://www.bbc.com",
            user_agent="AletheiaBot/1.0 (Compliance Auditor)",
            timeout=15,
            force=False,
        )

        assert result.fetch_status == FetchStatus.SUCCESS
        assert result.http_status == 200
        # BBC sends X-Robots-Tag: noarchive header
        assert result.headers.x_robots_tag_present is True
        assert "noarchive" in result.headers.x_robots_tag_values
        assert result.merged.noarchive is True
        assert result.aletheia_action == AletheiaAction.TRANSFORM

    def test_noarchive_net_with_force(self):
        """Test noarchive.net has noarchive meta tag (requires --force due to robots.txt)."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
        from inspect_signals import inspect_url

        result = inspect_url(
            url="https://noarchive.net",
            user_agent="AletheiaBot/1.0 (Compliance Auditor)",
            timeout=15,
            force=True,  # Site blocks via robots.txt
        )

        assert result.fetch_status == FetchStatus.SUCCESS
        assert result.http_status == 200
        # noarchive.net has <meta name="robots" content="noarchive">
        assert result.meta_tags.noarchive is True
        assert result.merged.noarchive is True
        assert result.aletheia_action == AletheiaAction.TRANSFORM

    def test_noarchive_net_blocked_without_force(self):
        """Test noarchive.net is blocked by robots.txt without --force."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
        from inspect_signals import inspect_url

        result = inspect_url(
            url="https://noarchive.net",
            user_agent="AletheiaBot/1.0 (Compliance Auditor)",
            timeout=15,
            force=False,
        )

        assert result.fetch_status == FetchStatus.ROBOTS_BLOCKED
        assert result.aletheia_action == AletheiaAction.BLOCK


class TestFetcherExceptionTextDoesNotLeak:
    """Issue #644 (audit umbrella #637):

    Per docs/observability.html: "NEVER log prompt text, user input, completion
    text, URLs, or user IDs." The fetcher's exception handlers must not log
    the URL or the exception text — only the exception class name.
    """

    CANARY_URL = "https://CANARY-LEAK-fetcher-5e2d4f.example.com/secret-path"

    @responses.activate
    def test_request_exception_does_not_leak_url_or_message_into_log(self, caplog):
        """Issue #644: RequestException handler must not log url or str(e)."""
        import logging
        from signal_inspector.fetcher import fetch_page

        # responses lib raises ConnectionError if no matcher registered for
        # the URL — perfect for triggering the exception path.
        with caplog.at_level(logging.WARNING, logger="signal_inspector.fetcher"):
            html, headers, status, error = fetch_page(self.CANARY_URL, "TestBot/1.0", timeout=5)

        log_text = "\n".join(r.getMessage() for r in caplog.records)
        assert self.CANARY_URL not in log_text, f"URL leaked into log: {log_text!r}"
        assert "CANARY-LEAK" not in log_text
        # Class name should be present for diagnostic value
        assert any(token in log_text for token in (
            "FETCH_CONNECTION_ERROR", "FETCH_REQUEST_ERROR", "FETCH_TIMEOUT"
        ))

    @responses.activate
    def test_request_exception_does_not_leak_message_into_return_tuple(self):
        """Issue #644: 4th element of return tuple must be a fixed token or class
        name, never str(e) with embedded URL/content."""
        from signal_inspector.fetcher import fetch_page

        html, headers, status, error = fetch_page(self.CANARY_URL, "TestBot/1.0", timeout=5)

        assert html is None
        assert self.CANARY_URL not in (error or "")
        assert "CANARY-LEAK" not in (error or "")
