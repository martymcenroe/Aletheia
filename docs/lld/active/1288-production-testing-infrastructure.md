# LLD 1288: Production Lambda Testing Infrastructure

**Issue:** #288
**Status:** Draft
**Author:** Claude Opus 4.5
**Created:** 2026-01-10

---

## 1. Overview

### 1.1 Problem Statement
Lambda returns "Analysis Failed - Could not parse response" when Bedrock outputs Unicode curly quotes in JSON string values. The current fix only handles 4 quote characters (U+201C, U+201D, U+2018, U+2019), but many more Unicode quote variants exist. Additionally, agents cannot debug these issues autonomously - the debug cycle requires human involvement.

### 1.2 Solution Summary
Three components:
1. **Comprehensive quote normalization** - Expand from 4 to 22+ Unicode quote variants
2. **Unicode diagnostic logging** - Log exact codepoints when JSON parsing fails
3. **Direct Lambda testing tool** - `tools/test_lambda.py` for autonomous agent debugging

---

## 2. Technical Design

### 2.1 Component 1: Comprehensive Quote Normalization

**File:** `src/etymologist.py`

#### 2.1.1 Quote Normalization Map

```python
# Comprehensive Unicode quote normalization map
QUOTE_NORMALIZATION_MAP = {
    # Double quote variants -> single quote (to avoid breaking JSON structure)
    '\u201C': "'",  # LEFT DOUBLE QUOTATION MARK "
    '\u201D': "'",  # RIGHT DOUBLE QUOTATION MARK "
    '\u201E': "'",  # DOUBLE LOW-9 QUOTATION MARK „
    '\u201F': "'",  # DOUBLE HIGH-REVERSED-9 QUOTATION MARK ‟
    '\u2033': "'",  # DOUBLE PRIME ″
    '\u2036': "'",  # REVERSED DOUBLE PRIME ‶
    '\u00AB': "'",  # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK «
    '\u00BB': "'",  # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK »

    # Single quote variants -> straight single quote
    '\u2018': "'",  # LEFT SINGLE QUOTATION MARK '
    '\u2019': "'",  # RIGHT SINGLE QUOTATION MARK '
    '\u201A': "'",  # SINGLE LOW-9 QUOTATION MARK ‚
    '\u201B': "'",  # SINGLE HIGH-REVERSED-9 QUOTATION MARK ‛
    '\u2032': "'",  # PRIME ′
    '\u2035': "'",  # REVERSED PRIME ‵
    '\u2039': "'",  # SINGLE LEFT-POINTING ANGLE QUOTATION MARK ‹
    '\u203A': "'",  # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK ›

    # Fullwidth variants -> ASCII equivalents
    '\uFF02': '"',  # FULLWIDTH QUOTATION MARK ＂
    '\uFF07': "'",  # FULLWIDTH APOSTROPHE ＇

    # CJK brackets (rare but possible from multilingual models)
    '\u300C': "'",  # LEFT CORNER BRACKET 「
    '\u300D': "'",  # RIGHT CORNER BRACKET 」
    '\u300E': "'",  # LEFT WHITE CORNER BRACKET 『
    '\u300F': "'",  # RIGHT WHITE CORNER BRACKET 』
}
```

#### 2.1.2 Normalization Function

```python
def normalize_unicode_quotes(text: str) -> str:
    """Normalize all Unicode quotation marks to ASCII equivalents.

    Critical for JSON parsing: Bedrock may return curly quotes inside
    string values (e.g., 'the term "waypoint" originated...').

    Strategy:
    - Double quote variants -> single quote (to avoid breaking JSON)
    - Single quote variants -> straight single quote
    - Fullwidth variants -> ASCII equivalents

    See Issue #288 for background.
    """
    for unicode_char, replacement in QUOTE_NORMALIZATION_MAP.items():
        text = text.replace(unicode_char, replacement)
    return text
```

#### 2.1.3 Integration Point

Update `extract_json()` to use the new function:

```python
def extract_json(raw_response: str) -> dict | None:
    # ... existing code ...

    text = raw_response.strip()

    # Step 0: Comprehensive quote normalization (Issue #288)
    text = normalize_unicode_quotes(text)

    # ... rest of existing code ...
```

### 2.2 Component 2: Unicode Diagnostic Logging

**File:** `src/etymologist.py`

#### 2.2.1 Diagnostic Function

```python
import unicodedata

def _log_unicode_diagnostics(text: str, context: str) -> None:
    """Log Unicode codepoints for debugging JSON parse failures.

    Only logs non-ASCII characters that might be causing issues.
    Limited to first 500 chars and first 10 problematic characters.
    """
    non_ascii_chars = []
    for i, char in enumerate(text[:500]):
        codepoint = ord(char)
        if codepoint > 127:
            try:
                name = unicodedata.name(char)
            except ValueError:
                name = "UNKNOWN"
            non_ascii_chars.append({
                "pos": i,
                "char": char,
                "codepoint": f"U+{codepoint:04X}",
                "name": name
            })

    if non_ascii_chars:
        logger.warning(f"UNICODE_DIAGNOSTIC [{context}]: Found {len(non_ascii_chars)} non-ASCII chars")
        for entry in non_ascii_chars[:10]:
            logger.warning(
                f"  Position {entry['pos']}: {entry['codepoint']} ({entry['name']}) = '{entry['char']}'"
            )
    else:
        logger.warning(f"UNICODE_DIAGNOSTIC [{context}]: No non-ASCII characters found")
```

#### 2.2.2 Integration Points

Call diagnostics on failure in `extract_json()`:

```python
except json.JSONDecodeError as e:
    logger.warning(f"JSON decode failed: {e}")
    logger.warning(f"JSON string (first 200 chars): {json_str[:200]}")
    _log_unicode_diagnostics(json_str, f"JSONDecodeError at position {e.pos}")
    return None
```

### 2.3 Component 3: Direct Lambda Testing Tool

**File:** `tools/test_lambda.py` (NEW)

#### 2.3.1 Core Invocation Function

```python
#!/usr/bin/env python3
"""
Direct Lambda SDK Invocation Tool for Agent Testing.

Bypasses Function URL to invoke Lambda directly, providing:
- Full response including debug timings
- Raw bytes/Unicode codepoint inspection
- noarchive flag to prevent test data pollution

Usage:
    poetry run python tools/test_lambda.py --term "hello"
    poetry run python tools/test_lambda.py --term "cryptocurrency" --noarchive
    poetry run python tools/test_lambda.py --term "test" --show-codepoints --json
"""

import argparse
import json
import sys
import time
import unicodedata

import boto3


LAMBDA_FUNCTION_NAME = "AletheiaAgent"
REGION = "us-east-1"


def invoke_lambda(term: str, context: str = "", noarchive: bool = False) -> dict:
    """Invoke Lambda directly via boto3 SDK.

    Returns dict with:
    - status_code: HTTP status from Lambda
    - body: Parsed response body
    - raw_payload: Raw Lambda response as string
    - latency_ms: Invocation latency
    - request_id: AWS Request ID for CloudWatch correlation
    """
    client = boto3.client("lambda", region_name=REGION)

    # Build payload matching extension format
    payload = {
        "text": term,
        "domContext": context,
        "url": "https://test.aletheia.local/agent-test",
        "signals": {"noarchive": noarchive}
    }

    lambda_event = {"body": json.dumps(payload)}

    start = time.time()
    response = client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        Payload=json.dumps(lambda_event)
    )
    latency = int((time.time() - start) * 1000)

    raw_payload = response["Payload"].read().decode("utf-8")
    parsed = json.loads(raw_payload)

    # Extract body (may be string or dict)
    body = parsed.get("body", {})
    if isinstance(body, str):
        body = json.loads(body)

    return {
        "status_code": parsed.get("statusCode"),
        "body": body,
        "raw_payload": raw_payload,
        "latency_ms": latency,
        "request_id": response.get("ResponseMetadata", {}).get("RequestId", "unknown")
    }


def show_unicode_codepoints(text: str, label: str = "Text") -> None:
    """Display Unicode codepoints for non-ASCII characters."""
    print(f"\n{label} - Unicode Analysis:")
    print("-" * 60)

    non_ascii = []
    for i, char in enumerate(text):
        codepoint = ord(char)
        if codepoint > 127:
            try:
                name = unicodedata.name(char)
            except ValueError:
                name = "UNKNOWN"
            non_ascii.append((i, codepoint, name, char))

    if non_ascii:
        print(f"Found {len(non_ascii)} non-ASCII characters:")
        for pos, cp, name, char in non_ascii[:20]:
            print(f"  [{pos:4d}] U+{cp:04X} {name:40s} '{char}'")
        if len(non_ascii) > 20:
            print(f"  ... and {len(non_ascii) - 20} more")
    else:
        print("No non-ASCII characters found.")


def main():
    parser = argparse.ArgumentParser(
        description="Direct Lambda SDK invocation for agent testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  poetry run python tools/test_lambda.py --term "hello"
  poetry run python tools/test_lambda.py --term "cryptocurrency" --noarchive
  poetry run python tools/test_lambda.py --term "test" --show-codepoints
  poetry run python tools/test_lambda.py --term "test" --json
        """
    )
    parser.add_argument("--term", required=True, help="Term to analyze")
    parser.add_argument("--context", default="", help="Page context for disambiguation")
    parser.add_argument("--noarchive", action="store_true", help="Skip DynamoDB persistence")
    parser.add_argument("--show-codepoints", action="store_true", help="Show Unicode codepoints in response")
    parser.add_argument("--json", action="store_true", help="Output as JSON (for scripting)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        result = invoke_lambda(args.term, args.context, args.noarchive)
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        # Machine-readable output
        output = {
            "status_code": result["status_code"],
            "body": result["body"],
            "latency_ms": result["latency_ms"],
            "request_id": result["request_id"]
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(f"\n{'='*60}")
        print(f"Term: {args.term}")
        print(f"Request ID: {result['request_id']}")
        print(f"Latency: {result['latency_ms']}ms")
        print(f"Status: {result['status_code']}")
        print(f"{'='*60}")

        body = result["body"]
        print(f"\nStatus: {body.get('status', 'unknown')}")
        print(f"Signal: {body.get('signal', 'N/A')}")
        print(f"Gem: {body.get('gem', 'N/A')}")
        print(f"Context: {body.get('context', 'N/A')}")

        if args.verbose and "_debug_timings" in body:
            print(f"\nDebug Timings:")
            print(json.dumps(body["_debug_timings"], indent=2))

        # Check for failure indicators
        if body.get("status") == "fallback":
            print("\n*** WARNING: Response is FALLBACK - JSON parsing likely failed ***")
        if body.get("signal") == "Analysis Failed":
            print("\n*** WARNING: Analysis failed - check CloudWatch logs ***")
            print(f"    Use: aws logs tail /aws/lambda/AletheiaAgent --since 5m")

    if args.show_codepoints:
        # Show codepoints in relevant fields
        for field in ["signal", "gem", "context"]:
            if field in result["body"]:
                show_unicode_codepoints(result["body"][field], field)

    # Exit with appropriate code
    if result["status_code"] != 200:
        sys.exit(1)
    if result["body"].get("status") == "fallback":
        sys.exit(2)


if __name__ == "__main__":
    main()
```

---

## 3. File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `src/etymologist.py` | MODIFY | Add `QUOTE_NORMALIZATION_MAP`, `normalize_unicode_quotes()`, `_log_unicode_diagnostics()` |
| `tools/test_lambda.py` | CREATE | Direct Lambda SDK invocation tool |
| `tests/unit/test_etymologist.py` | MODIFY | Add parametrized tests for 22 quote characters |
| `tests/tools/test_tools_smoke.py` | MODIFY | Add smoke test for test_lambda.py |

---

## 4. Testing Strategy

### 4.1 Unit Tests

Add parametrized tests covering each quote character:

```python
@pytest.mark.parametrize("input_char,expected", [
    ('\u201C', "'"),  # LEFT DOUBLE QUOTATION MARK
    ('\u201D', "'"),  # RIGHT DOUBLE QUOTATION MARK
    ('\u00AB', "'"),  # LEFT GUILLEMET
    ('\u00BB', "'"),  # RIGHT GUILLEMET
    # ... all 22 characters
])
def test_quote_normalization(input_char, expected):
    from src.etymologist import normalize_unicode_quotes
    assert normalize_unicode_quotes(input_char) == expected
```

### 4.2 Integration Test

```python
def test_guillemets_in_json_value():
    """French guillemets should not break JSON parsing."""
    raw = '{"signal": "Test", "gem": "French uses «guillemets».", "context": "Context."}'
    result = extract_json(raw)
    assert result is not None
    assert result["gem"] == "French uses 'guillemets'."
```

### 4.3 End-to-End Verification

```bash
# 1. Deploy updated Lambda
bash deploy.sh

# 2. Test with tool
poetry run python tools/test_lambda.py --term "cryptocurrency" --noarchive

# 3. Verify success (not fallback)
# Expected: status=success, signal != "Analysis Failed"
```

---

## 5. Rollback Plan

If issues occur:
1. Revert `src/etymologist.py` changes
2. Redeploy Lambda: `bash deploy.sh`
3. Tool can remain (read-only, no impact)

---

## 6. Security Considerations

- **No PII in logs**: Only codepoints and positions logged, not user input
- **Test tool is read-only**: Cannot modify Lambda or DynamoDB schema
- **noarchive flag**: Prevents test pollution in production data
- **Existing IAM**: Uses existing AWS credentials, no new permissions needed

---

## 7. Gemini Review Clarifications

**Gemini 3 Pro Review:** 2026-01-10

Gemini raised two concerns that have been addressed:

### 7.1 Quote Normalization Target (Resolved)

**Concern:** "Mapping double quote variants to single quotes will break JSON"

**Clarification:** The normalization targets curly quotes **inside string values**, NOT JSON delimiters. Example:

```
Input:  {"context": "The word "cryptocurrency" was coined"}
                           ↑                ↑
                     U+201C             U+201D (inside string value)

Output: {"context": "The word 'cryptocurrency' was coined"}
                           ↑                ↑
                     ASCII apostrophe   (valid JSON)
```

The outer JSON delimiters (U+0022) are **never modified**. Only U+201C/U+201D inside values become single quotes.

### 7.2 noarchive Backend Support (Already Exists)

**Concern:** "Backend logic for noarchive flag appears missing"

**Clarification:** Already implemented in Issue #162:
- `src/lambda_function.py` lines 359-395
- Logs: `NOARCHIVE: Skipping persistence for thread_id=...`

No changes needed to Lambda for this feature.

---

## 8. Open Questions

None - design is straightforward.

---

## 9. References

- Issue #288: Production Lambda Testing Infrastructure
- Issue #259: Original curly quote fix (partial)
- ADR 0202: Shadow DOM isolation (context for extension error handling)
- [Unicode Quotation Marks](https://www.cl.cam.ac.uk/~mgk25/ucs/quotes.html)
