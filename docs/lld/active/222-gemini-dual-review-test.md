# LLD: Gemini Dual-Review Test

**Issue:** #222
**Author:** Claude Sonnet 4.5
**Date:** 2026-01-10
**Status:** Draft

## Objective

Test the Gemini 3 Pro review automation by submitting this LLD for review.

## Background

This is a test LLD to verify that:
1. The Gemini CLI can be invoked with the correct model (gemini-3-pro-preview)
2. Model downgrade detection works
3. The review feedback can be parsed correctly
4. The three-tier priority system ([BLOCKING], [HIGH], [SUGGESTION]) is understood

## Approach

### Components

**File:** `tools/gemini-model-check.sh`
- Bash wrapper for Gemini CLI
- Detects model downgrades via JSON output parsing
- Exit codes: 0 (success), 1 (CLI failure), 2 (quota exhausted), 3 (downgrade)

**File:** `gemini-prompts/lld-review.txt`
- Prompt template for LLD reviews
- Uses placeholder syntax: `{{LLD_PATH}}`, `{{LLD_CONTENT}}`
- Enforces output format with priority markers

### Workflow

```
1. Write LLD → docs/lld/active/222-feature.md
2. Load prompt: gemini-prompts/lld-review.txt
3. Replace placeholders with actual LLD path and content
4. Invoke: tools/gemini-model-check.sh <prompt> gemini-3-pro-preview
5. Parse response for [BLOCKING], [HIGH], [SUGGESTION]
6. Update LLD with feedback
7. Wait for user approval to implement
```

### Error Handling

| Error Type | Detection | Response |
|------------|-----------|----------|
| Model downgrade | JSON shows unexpected model | Abort + notify user |
| Quota exhausted | 429 error or "Resource exhausted" | Abort + log event |
| Network timeout | Exit code 1 | Retry once, then abort |

## Security Considerations

- Model detection prevents using wrong model tier
- Quota logs stored locally (no PII)
- Prompt library versioned in git for audit trail

## Testing Strategy

1. **Unit Test:** Invoke script with simple prompt, verify exit code 0
2. **Model Detection Test:** Force downgrade (if possible), verify exit code 3
3. **Integration Test:** Submit this LLD for Gemini review, verify feedback parsing

## Success Criteria

- [ ] Gemini 3 Pro successfully invoked
- [ ] Feedback received in expected format
- [ ] [BLOCKING], [HIGH], [SUGGESTION] markers parsed correctly
- [ ] No model downgrades detected

## Known Limitations

- Gemini may offer to implement code (ignore these offers)
- "Loaded cached credentials" line breaks JSON parsing (fixed with sed)
- Trailing whitespace in model names requires trimming

## Future Enhancements

- Quota pre-checking (warn before exhaustion)
- Automated LLD trigger detection (file save event)
- Session state tracking for multi-phase reviews
