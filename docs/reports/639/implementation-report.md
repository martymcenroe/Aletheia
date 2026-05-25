# Implementation Report — Issues #639, #640, #646, #647 (audit umbrella #637)

## Scope

PR 2 of 5 in the audit-umbrella #637 arc. Applies the class-name-only pattern to all 4 audit-identified exception-text leak surfaces in `src/etymologist.py`, plus removes two adjacent completion-text leaks in the same JSON decode handler that the original audit did not flag.

## Audit-identified surfaces fixed (4)

| Issue | Line | Pattern before | Pattern after |
|---|---|---|---|
| #639 (H2) | 811 | `"error": str(e)` in metadata | `"error": error_class` |
| #640 (H3) | 882 | `metadata["opus_verifier_error"] = str(e)` | `= error_class` |
| #646 (M9) | 804 | `logger.error(f"... {type(e).__name__}: {e}")` | drop `{e}`, log token + class |
| #647 (M10) | 532 | `logger.warning(f"JSON decode failed: {e}")` | class-name-only log |

## Additional fixes in the same JSON decode handler (NOT in original audit, fixed for completeness)

The `extract_json` JSONDecodeError handler had two adjacent completion-text leaks not flagged by the audit. Fixing them in the same PR because they're literally the next lines of the same `except` branch and leaving them in place would have been worse than incomplete:

1. **Removed** `logger.warning(f"JSON string (first 200 chars): {json_str[:200]}")` — `json_str` is the LLM completion text; logging up to 200 chars of it violates the never-log-completion-text constraint.
2. **Removed** the call to `_log_unicode_diagnostics(json_str, ...)` and the function itself — the helper logged individual non-ASCII characters and their positions from the LLM output, which is a partial information leak about the user-derived content.

Both removals reduce diagnostic richness for a debug scenario (JSON parse failures) but are required by the privacy commitment. If JSON parse failures need investigation in the future, do it with a structured allow-list of safe attributes (e.g. `len(json_str)`, `e.pos`, `e.lineno`) — never raw content.

The `unicodedata` import (top of file) is no longer used and was removed.

## Test Updates

### New: `TestEtymologistExceptionTextDoesNotLeak` (4 tests)

Canary-string assertions for: bedrock exception in metadata, bedrock exception in log, opus verifier exception in metadata, JSON decode handler does not log completion text.

### Updated existing tests

Two existing tests codified the leaky behavior; flipped to assert the fix:
- `tests/unit/test_etymologist.py:665` (`test_bedrock_exception_returns_error`): was `assert "Bedrock error" in metadata["error"]`, now asserts it's NOT present and class name IS.
- `tests/unit/test_etymologist.py:1158` (`test_verifier_falls_back_on_opus_exception`): was `assert "Opus unavailable" in opus_verifier_error`, now asserts it's NOT present and class name IS.

## Resolves

- #639 (H2, HIGH)
- #640 (H3, HIGH)
- #646 (M9, MEDIUM)
- #647 (M10, MEDIUM)

Part of umbrella #637 (8 of 14 surfaces resolved after this PR; 6 remaining across PRs 3-5).

## Blast Radius

Code change in `src/etymologist.py` only. Code-only deploy via `provision.sh`. `AletheiaAgent` Lambda only. Rollback: previous zip.
