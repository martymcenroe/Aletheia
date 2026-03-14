# Implementation Report — Issue #556

**Issue:** fix: EULA Section 7 stale claims contradict updated privacy policy
**Date:** 2026-03-13

## Changes

### `docs/legal/eula.md` — Section 7
- "We only process text you explicitly select" → includes full page analysis
- "Amazon Nova AI" → names all three models (Nova Micro, Claude Haiku 4.5, Claude Opus 4.6)
- "Data is retained for 30 days" → scoped to analysis data; account data until deletion
- Added LinkedIn PII disclosure bullet
- Added DELETE /my-data endpoint reference

### `docs/legal/eula.html` — Section 7
- Same changes as eula.md, rendered as HTML list
