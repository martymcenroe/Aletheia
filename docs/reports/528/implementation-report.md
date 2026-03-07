# Implementation Report — Issue #528

## Context-Aware Word Disambiguation in Analysis Pipeline

### Problem
Polysemous words analyzed incorrectly: "crud" → exclamation (not residue), "flannel" → fabric (not evasive talk), "gantlet" → parse failure.

### Root Cause
1. No disambiguation instruction in system prompts
2. Full page DOM (~100KB) sent as context, burying relevant paragraph
3. No context size cap in `build_user_message()` (unlike `poetic_analyzer.py`)

### Changes

| File | Change |
|------|--------|
| `src/etymologist.py` | Added DISAMBIGUATION section to both `SYSTEM_PROMPT` and `SYSTEM_PROMPT_NOVA`; updated context label to be directive; added 2000-char context cap |
| `extensions/chrome/service-worker.js` | Context windowing: extract ~2000 chars around selection instead of full `document.body.innerText` |
| `extensions/firefox/service-worker.js` | Same context windowing |
| `tests/unit/test_etymologist.py` | 5 new tests: disambiguation in both prompts, directive label, context truncation, short context passthrough |

### Design Decisions
- **2000-char window** matches the backend truncation cap, providing defense-in-depth
- **±1000 chars around selection** captures paragraph-level context without noise
- **Fallback**: if selected text not found in `innerText` (edge case), first 2000 chars of page used
- **Disambiguation examples** use the actual failing cases (flannel, crud) to ground the instruction
