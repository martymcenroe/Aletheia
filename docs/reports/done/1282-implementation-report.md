# Implementation Report - Issue #282

**Issue:** fix(firefox): add missing data_collection_permissions to manifest
**PR:** #283
**Merged:** 2026-01-10

## Summary

Added required `data_collection_permissions` to Firefox manifest to comply with Mozilla Add-ons submission requirements.

## Changes Made

| File | Change |
|------|--------|
| `extensions/firefox/manifest.json` | Added `data_collection_permissions` under `browser_specific_settings.gecko` |

## Technical Details

Mozilla requires all new Firefox extensions to declare data collection permissions. Added:

```json
"data_collection_permissions": {
  "required": ["authenticationInfo", "websiteContent"],
  "optional": []
}
```

- `authenticationInfo` - LinkedIn OAuth tokens (for user gating)
- `websiteContent` - Selected text sent to API (for etymology analysis)

## Verification

- `web-ext lint` passes
- `build_release.py` completes successfully
- Manifest JSON valid

## References

- https://mzl.la/firefox-builtin-data-consent
- Mozilla blog: data-collection-consent-changes-for-new-firefox-extensions

---

*Retroactive report created 2026-01-12 during 0802 Reports Completeness Audit.*
