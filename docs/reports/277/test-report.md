# Test Report: #277 Fix npx subprocess on Windows

## Test Execution

| Test | Result |
|------|--------|
| `poetry run python tools/build_release.py` | PASS |
| Firefox lint step executes | PASS |
| Chrome artifact created | PASS |
| Firefox artifact created | PASS |

## Evidence

```
Step 3: Running Firefox linter...
  [OK] Firefox lint passed

==================================================
Build complete!
==================================================
  Chrome:  aletheia-chrome-v1.0.zip (13 files)
  Firefox: aletheia-firefox-v1.0.zip (13 files)
```

## Regression Risk

Minimal - single-character change using existing variable.
