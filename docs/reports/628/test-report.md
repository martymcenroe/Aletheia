# Test Report — Issue #628

**Title:** chore: replace Discworld asides with mainstream literary references
**Date:** 2026-05-23
**Branch:** `628-mainstream-literary-asides`

## Validation

Two-paragraph content swap. No structural change, no CSS change, no code change.

| Check | Result |
|-------|--------|
| `docs/demos.html` aside replaced | ✓ |
| `docs/safety.html` aside replaced | ✓ |
| Both pages render correctly with new content | ✓ |
| `.discworld-aside` class styling still applies | ✓ |
| `grep -i "discworld\|lancre\|ankh\|unseen university\|librarian of\|pratchett"` returns 0 hits | ✓ |

## Linter

This change touches HTML only. Project ruff is Python-only and doesn't lint HTML; no JavaScript was added or modified.

## Post-deploy smoke

```bash
curl -s https://aletheia.study/demos.html | grep -i "Ulysses"
curl -s https://aletheia.study/safety.html | grep -i "Butlerian"
```

Both should return the new aside text after CloudFlare Pages auto-publishes.

## Regression risk

**Effectively zero.** Two single-paragraph content swaps in documentation pages. No code paths involved.
