# Implementation Report: #53 - Store Assets Build Script

## Summary

Updated `tools/build_release.py` to work with the new separated extension directory structure introduced in Issue #100.

## What Was Built

### Changes to `tools/build_release.py`

1. **Path Updates** (lines 19-23)
   - Changed from single `extension/` directory to separate `extensions/chrome/` and `extensions/firefox/`
   - Each browser now has its own complete extension with its own `manifest.json`

2. **Parity Key Reduction** (lines 29-37)
   - Reduced `PARITY_KEYS` from 6 keys to 4 keys
   - Removed: `permissions`, `host_permissions` (legitimately differ between MV3/MV2)
   - Kept: `name`, `version`, `description`, `icons` (identity/branding must match)

3. **Icon Validation Enhancement** (lines 40-54)
   - Added file size check per Gemini review
   - Icons must be >100 bytes to catch empty placeholders
   - Separate validation for Chrome and Firefox directories

4. **Improved Error Reporting** (lines 62-91)
   - Manifest drift errors now collect all drifts before reporting
   - Single error message shows all mismatched keys together

5. **Build Function Refactor** (lines 99-119)
   - `build_zip()` now takes `source_dir` parameter instead of manifest name
   - Simpler logic - just packages everything in the source directory

## Why These Decisions

| Decision | Rationale |
|----------|-----------|
| Separate extension directories | Issue #100 established this pattern; MV3 and MV2 are too different for manifest swapping |
| Reduced parity keys | Chrome MV3 uses `identity` permission; Firefox MV2 doesn't. Permissions legitimately differ. |
| Icon size check | Gemini review flagged risk of empty placeholder files being shipped |
| Batch error reporting | Developer experience - see all issues at once, not one at a time |

## Files Modified

| File | Change |
|------|--------|
| `tools/build_release.py` | Updated for new directory structure, reduced parity keys, added icon validation |

## Dependencies

- None new (stdlib only: `pathlib`, `zipfile`, `json`, `sys`)

## Related Issues

- #100 - Firefox Compatibility (established the directory structure)
- #51 - Store Compliance (this script enables store submission)
