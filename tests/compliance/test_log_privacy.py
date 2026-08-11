"""Verify no logger call interpolates exception text.

Issue #835. Umbrella #637 fixed 14 enumerated line numbers; the same pattern
later reappeared in the very files it had covered, and 34 further surfaces sat
in files it never scoped at all. Enumerating locations does not hold. This scans
the source so the defect class cannot return unnoticed.

Protects the public commitment in `docs/observability.html`:

    "NEVER log prompt text, user input, completion text, URLs, or user IDs."

Exception messages are unbounded third-party text. `botocore.exceptions.
ClientError` in particular can echo request field values back, and several call
sites wrap DynamoDB operations keyed on user_id.

SCOPE — logs only.
    Response payloads deliberately keep `str(e)`. Issue #668 reverted an
    over-scrub that reached returned fields; the operator caught the regression
    in production, and the reasoning is that the response goes back to the user
    who made the request and who already knows their own input. This module must
    never be extended to flag a returned field.
"""

from __future__ import annotations

import re
from pathlib import Path

SRC_DIR = Path(__file__).parent.parent.parent / "src"

_LOG_CALL = re.compile(
    r"logger\.(?:debug|info|warning|error|critical|exception)\s*\("
)

# Exception text reaching the message: f-string `{e}` or an interpolated str(e).
_LEAK = re.compile(
    r"\{(?:e|err|ex|exc)\}"
    r"|str\((?:e|err|ex|exc)\)"
    r"|repr\((?:e|err|ex|exc)\)"
    r"|(?:e|err|ex|exc)\.args"
)

# Sanctioned alternatives.
#   - class name only: the established pattern from #636/#619
#   - a specific, audited attribute (e.g. e.response['Error']['Code']), which is
#     the documented way to keep more signal than a bare class name
_SANCTIONED = re.compile(
    r"__class__\.__name__"
    r"|type\((?:e|err|ex|exc)\)\.__name__"
    r"|(?:e|err|ex|exc)\.response\["
)


def _python_sources() -> list[Path]:
    return [
        f
        for f in sorted(SRC_DIR.rglob("*.py"))
        if "__pycache__" not in str(f)
    ]


def _find_leaks() -> list[tuple[str, int, str]]:
    leaks: list[tuple[str, int, str]] = []
    for path in _python_sources():
        rel = path.relative_to(SRC_DIR.parent).as_posix()
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if line.strip().startswith("#"):
                continue
            if not _LOG_CALL.search(line):
                continue
            if _SANCTIONED.search(line):
                continue
            if _LEAK.search(line):
                leaks.append((rel, lineno, line.strip()))
    return leaks


class TestLogPrivacy:
    """No exception text may reach a log message."""

    def test_no_logger_call_interpolates_exception_text(self) -> None:
        leaks = _find_leaks()

        assert not leaks, (
            "EXCEPTION TEXT IN LOGS — violates docs/observability.html:\n"
            + "\n".join(f"  {f}:{n}  {line}" for f, n, line in leaks)
            + "\n\nUse `e.__class__.__name__`, or extract one specific audited "
            "attribute (e.g. e.response['Error']['Code']).\n"
            "Do NOT change response-payload fields — those keep str(e) per #668."
        )

    def test_the_scan_actually_inspects_source(self) -> None:
        """Guard against the check passing because it found nothing to read.

        A scan that silently walks an empty tree reports success forever. That
        is the failure mode this whole issue is about.
        """
        sources = _python_sources()
        assert len(sources) >= 10, (
            f"Only {len(sources)} source files scanned; the scan is not "
            "reaching src/ and its green result is meaningless."
        )

        joined = "\n".join(p.read_text(encoding="utf-8") for p in sources)
        assert "logger." in joined, "No logger calls found — scan is not working."

    def test_sanctioned_patterns_are_not_flagged(self) -> None:
        """The class-name and audited-attribute forms must remain usable."""
        for safe in (
            'logger.error(f"OP_FAILED: {e.__class__.__name__}")',
            'logger.error(f"OP_FAILED: {type(e).__name__}")',
            "logger.error(f\"DynamoDB error: {e.response['Error']['Code']}\")",
            'logger.error("Failed: %s", e.__class__.__name__)',
        ):
            assert _LOG_CALL.search(safe)
            assert _SANCTIONED.search(safe), f"wrongly flagged: {safe}"

    def test_response_payload_assignments_are_out_of_scope(self) -> None:
        """#668: returned fields keep str(e) and must never be flagged here.

        Re-scrubbing them reintroduces a regression the operator caught in
        production, so this is asserted rather than left to convention.
        """
        for payload_line in (
            '            "gem": str(e),',
            '                "error": str(e),',
            '        original_result["metadata"]["opus_verifier_error"] = str(e)',
            '                "message": str(e),',
        ):
            assert not _LOG_CALL.search(payload_line), (
                f"response-payload line matched the log-call pattern: {payload_line}"
            )
