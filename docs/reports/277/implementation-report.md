# Implementation Report: #277 Fix npx subprocess on Windows

## Summary

One-line fix to use full path for npx in subprocess call.

## Change

**File:** `tools/build_release.py` line 112

**Before:**
```python
result = subprocess.run(
    ["npx", "web-ext", "lint", ...],
```

**After:**
```python
result = subprocess.run(
    [npx, "web-ext", "lint", ...],
```

## Root Cause

`shutil.which("npx")` returns the full path (e.g., `C:/Program Files/nodejs/npx`), but the subprocess call used the bare string `"npx"` instead of the `npx` variable. On Windows, subprocess cannot resolve bare command names without the full path.

## Testing

- `poetry run python tools/build_release.py` - PASS (build completes successfully)
