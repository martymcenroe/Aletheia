# Implementation Report: Issue #343, #344, #345 - Audit Cleanup

## Issue References

- [#343](https://github.com/martymcenroe/Aletheia/issues/343) - Remove stale TODO comments referencing closed Issue #116
- [#344](https://github.com/martymcenroe/Aletheia/issues/344) - Fix skipped popup.test.js test for null domain handling
- [#345](https://github.com/martymcenroe/Aletheia/issues/345) - Remove stale skipif reason referencing closed Issue #150

## Files Changed

| File | Change |
|------|--------|
| `src/lambda_function.py` | Removed 3 stale TODO comments referencing closed Issue #116 |
| `tests/unit/chrome/popup.test.js` | Fixed skipped test by resetting mock after DOMContentLoaded init |
| `tests/tools/test_tools_regression.py` | Removed stale skipif, added proper boto3 availability check |

## Design Decisions

1. **#343 (Stale TODOs)**: Removed specific issue references but preserved the intent in comments where the work is still relevant (e.g., "Future: Use authenticated user ID when available")

2. **#344 (Skipped test)**: Fixed by calling `mockReset()` on `chrome.tabs.query` after DOMContentLoaded fires, then setting up the null URL mock before calling `renderMainView()`

3. **#345 (Stale skipif)**: Removed the stale reference to closed Issue #150. Also added proper boto3 availability check for both `TestLogViewer` and `TestDataHygiene` since both tools require AWS SDK

## Known Limitations

- Tests requiring boto3 will be skipped in environments where boto3 is not installed (e.g., minimal CI environments)
