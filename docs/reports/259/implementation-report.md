# Implementation Report: Fix Curly Quotes in JSON Extraction

**Issue:** #259
**Branch:** `259-fix-curly-quotes`
**Date:** 2026-01-10

## Summary

Fixed JSON parsing failures in the Digital Etymologist caused by Bedrock returning curly/smart quotes instead of straight quotes.

## Problem

The `extract_json()` function in `etymologist.py` was failing to parse valid-looking JSON responses from Bedrock. Investigation revealed that Bedrock sometimes returns Unicode curly quotes (U+201C `"` and U+201D `"`) instead of ASCII straight quotes (U+0022 `"`).

Example raw response that caused failure:
```
{"signal": "Formal Academic Term", "gem": "The term "ultimate" derives..."}
```

The curly quotes around "ultimate" broke JSON parsing because the parser interpreted them as string terminators.

## Solution

Added quote normalization as the first step in `extract_json()`:

```python
# Step 0: Normalize curly/smart quotes to straight quotes (Issue #259)
text = text.replace('"', '"').replace('"', '"')  # Curly double quotes to straight
text = text.replace(''', "'").replace(''', "'")  # Curly single quotes to straight
```

Also added debug logging for future parsing failures:
- Log raw response when extraction fails
- Log JSON decode errors with the attempted JSON string

## Files Changed

| File | Changes |
|------|---------|
| `src/etymologist.py` | Quote normalization + debug logging |

## Testing

- Lambda invocation with "ultimate" term: SUCCESS
- Response parsed correctly with signal, gem, and context fields
