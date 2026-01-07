# Test Report: #53 - Store Assets Build Script

## Test Environment

- **OS:** Windows 11 (MINGW64/Git Bash)
- **Python:** 3.x via Poetry
- **Date:** 2026-01-06

## Test Execution

### Test 1: Full Build Run

**Command:**
```bash
poetry run python tools/build_release.py
```

**Result:** PASS

**Output:**
```
==================================================
Building Aletheia release artifacts
==================================================

Step 1: Verifying icons...
  [OK] Chrome: All 4 icons present and non-empty
  [OK] Firefox: All 4 icons present and non-empty

Step 2: Validating manifest parity...
  [OK] Manifest parity verified (4 keys)

Step 3: Reading version...
  [OK] Version: 1.0

Step 4: Creating dist directory...
  [OK] C:\Users\mcwiz\Projects\Aletheia-53\dist

Step 5: Building Chrome artifact...
  [OK] Chrome: aletheia-chrome-v1.0.zip (13 files)

Step 6: Building Firefox artifact...
  [OK] Firefox: aletheia-firefox-v1.0.zip (10 files)

==================================================
Build complete!
==================================================
  Chrome:  C:\Users\mcwiz\Projects\Aletheia-53\dist\aletheia-chrome-v1.0.zip
  Firefox: C:\Users\mcwiz\Projects\Aletheia-53\dist\aletheia-firefox-v1.0.zip

Next steps:
  1. Unzip and test locally in each browser
  2. Upload to Chrome Web Store / Firefox Add-ons
```

### Test 2: Chrome Zip Contents

**Command:**
```bash
unzip -l dist/aletheia-chrome-v1.0.zip
```

**Result:** PASS - 13 files including manifest.json

**Contents:**
```
  Length      Date    Time    Name
---------  ---------- -----   ----
    11589  2026-01-06 18:40   auth.js
     2148  2026-01-06 18:40   content-check.js
     2203  2026-01-06 18:40   content-safety.js
     1152  2026-01-06 18:40   manifest.json
    21371  2026-01-06 18:40   overlay.js
    10929  2026-01-06 18:40   popup.css
     4558  2026-01-06 18:40   popup.html
    14511  2026-01-06 18:40   popup.js
    13662  2026-01-06 18:40   service-worker.js
     6318  2026-01-06 18:40   icons/icon128.png
      432  2026-01-06 18:40   icons/icon16.png
     1035  2026-01-06 18:40   icons/icon32.png
     1669  2026-01-06 18:40   icons/icon48.png
---------                     -------
    91577                     13 files
```

### Test 3: Chrome Manifest Verification

**Command:**
```bash
unzip -p dist/aletheia-chrome-v1.0.zip manifest.json | head -20
```

**Result:** PASS - MV3 manifest with `service_worker`

**Key fields verified:**
- `manifest_version: 3`
- `background.service_worker: "service-worker.js"`
- `permissions: ["activeTab", "tabs", "scripting", "contextMenus", "storage", "identity"]`

### Test 4: Firefox Zip Contents

**Command:**
```bash
unzip -l dist/aletheia-firefox-v1.0.zip
```

**Result:** PASS - 10 files including manifest.json

**Contents:**
```
  Length      Date    Time    Name
---------  ---------- -----   ----
      827  2026-01-06 18:40   manifest.json
    21227  2026-01-06 18:40   overlay.js
     7584  2026-01-06 18:40   popup.css
     2660  2026-01-06 18:40   popup.html
     9113  2026-01-06 18:40   popup.js
    13662  2026-01-06 18:40   service-worker.js
     6318  2026-01-06 18:40   icons/icon128.png
      432  2026-01-06 18:40   icons/icon16.png
     1035  2026-01-06 18:40   icons/icon32.png
     1669  2026-01-06 18:40   icons/icon48.png
---------                     -------
    64527                     10 files
```

### Test 5: Firefox Manifest Verification

**Command:**
```bash
unzip -p dist/aletheia-firefox-v1.0.zip manifest.json | head -20
```

**Result:** PASS - MV2 manifest with `scripts` array and `gecko.id`

**Key fields verified:**
- `manifest_version: 2`
- `background.scripts: ["service-worker.js"]`
- `browser_specific_settings.gecko.id: "extension@aletheia.study"`
- `permissions: ["activeTab", "tabs", "contextMenus", "storage"]`

### Test 6: Manifest Parity Check

**Verification:** Both manifests have identical values for:
- `name: "Aletheia"`
- `version: "1.0"`
- `description: "AI-Powered Context Analysis"`
- `icons: {"16": "icons/icon16.png", ...}`

**Result:** PASS

## Test Summary

| Test | Description | Result |
|------|-------------|--------|
| 1 | Full build run | PASS |
| 2 | Chrome zip contents (13 files) | PASS |
| 3 | Chrome manifest is MV3 | PASS |
| 4 | Firefox zip contents (10 files) | PASS |
| 5 | Firefox manifest is MV2 with gecko.id | PASS |
| 6 | Parity keys match between manifests | PASS |

## Manual Testing Required

The following tests require human verification:

- [ ] Load Chrome zip in `chrome://extensions/` (Developer mode)
- [ ] Load Firefox zip in `about:debugging` (This Firefox)
- [ ] Verify extension functionality in both browsers

## Notes

- Chrome has 3 more files than Firefox (auth.js, content-check.js, content-safety.js) due to MV3-specific features
- Icon size validation confirmed all icons are >100 bytes (smallest: icon16.png at 432 bytes)
