# Test Report: Issue #535

## Unit Tests

```
974 passed, 2 skipped, 13 warnings in 17.72s
```

## New Tests Added

| Test Class | Tests | Description |
|------------|-------|-------------|
| `TestIsNovaModel` | 6 | Raw Nova ID, AIP ARN with nova, Haiku ID, Opus ID, AIP ARN without nova |

## Modified Tests

| Test | Change |
|------|--------|
| `TestModelConstants::test_haiku_model_id` | Updated assertion from `claude-3-haiku-20240307` to `claude-haiku-4-5-20251001` |
| `TestValidateModelId::test_similar_but_wrong_model_is_invalid` | Removed stale `claude-3-haiku-20240307-v2:0` assertion |

## Existing Tests Verified

All existing tests pass with new model defaults:
- `TestExtractResponseText` — Nova/Haiku response parsing still works
- `TestExtractTokenUsage` — Nova/Haiku token extraction still works
- `TestBuildNovaPrompt` / `TestBuildHaikuPrompt` — prompt building unchanged
- `TestGetModelId` — env var handling still works (constants are now env-backed)
- `TestAnalyzeTerm` — full pipeline still works with mock client

## Post-Deploy Verification (manual)

```bash
# Health check
curl -s https://api.aletheia.study/health
# Analysis test
curl -s -X POST https://api.aletheia.study/ \
  -H "Content-Type: application/json" \
  -H "X-Aletheia-Client-Version: 1.0" \
  -d '{"text":"eschews"}'
```
