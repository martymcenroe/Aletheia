# Implementation Report: Issue #294 - Nova Micro Switch

## Summary

Implemented Amazon Nova Micro as the default etymology model, replacing Claude Haiku for ~2.76x latency improvement.

## Changes Made

### 1. Core Implementation (`src/etymologist.py`)

#### New Constants
- `NOVA_MICRO_MODEL_ID = "amazon.nova-micro-v1:0"`
- `DEFAULT_MODEL_ID = NOVA_MICRO_MODEL_ID` (changed from Haiku)
- `ALLOWED_MODELS` - Set containing valid model IDs

#### New Functions
| Function | Purpose |
|----------|---------|
| `validate_model_id(model_id)` | Validates model against allowlist (G1.1) |
| `get_model_id()` | Gets model from `ETYMOLOGIST_MODEL` env var with fallback |
| `build_nova_prompt(word, context)` | Builds Nova API schema request |
| `build_haiku_prompt(word, context)` | Builds Haiku API schema request (renamed from original) |
| `extract_response_text(body, model_id)` | Model-agnostic response text extraction |
| `extract_token_usage(body, model_id)` | Model-agnostic token count extraction |

#### Modified Functions
| Function | Change |
|----------|--------|
| `build_etymologist_prompt()` | Now dispatches to Nova or Haiku builder based on model ID prefix |
| `analyze_term()` | Now uses `get_model_id()` when `model_id=None`, uses new extraction helpers |

#### New System Prompt
`SYSTEM_PROMPT_NOVA` - Enhanced prompt with explicit taxonomy rules:
- Defines "Archaic" as words ABANDONED before 1950
- Defines "Formal Academic Term" as RARE but ACTIVE
- Explicit distinction between pejorative (intent to insult) vs descriptive
- Includes "Immiserate" as NOT archaic example
- Includes JSON template for prompt injection (G2.1)

### 2. LLD (`docs/lld/active/1294-nova-micro-switch.md`)

Created comprehensive LLD addressing:
- G1.1: Model ID validation enforcement
- G1.2: Verified `schemaVersion: "messages-v1"` field
- G2.1: Prompt injection JSON compliance
- G2.2: Error handling documentation

### 3. Tests (`tests/unit/test_etymologist.py`)

Added 9 new test classes with 40+ new tests:
- `TestModelConstants` - Model ID constants
- `TestValidateModelId` - Allowlist validation
- `TestGetModelId` - Environment variable handling
- `TestBuildNovaPrompt` - Nova API schema
- `TestBuildHaikuPrompt` - Haiku API schema
- `TestExtractResponseText` - Response parsing
- `TestExtractTokenUsage` - Token extraction
- `TestNovaSystemPrompt` - Taxonomy rules
- `TestAnalyzeTermModelSelection` - Model selection logic

Updated 3 existing tests for Nova-default behavior.

## API Differences Handled

| Aspect | Claude Haiku | Nova Micro |
|--------|--------------|------------|
| Request schema | `anthropic_version`, `max_tokens`, `system: string` | `schemaVersion`, `inferenceConfig.max_new_tokens`, `system: [{text}]` |
| Response format | `{"content": [{type, text}]}` | `{"output": {"message": {"content": [{text}]}}}` |
| Token fields | `input_tokens`, `output_tokens` | `inputTokens`, `outputTokens` |

## Environment Variable

| Variable | Default | Description |
|----------|---------|-------------|
| `ETYMOLOGIST_MODEL` | `amazon.nova-micro-v1:0` | Model ID to use |

## Rollback Procedure

To rollback to Haiku:
```bash
export ETYMOLOGIST_MODEL=anthropic.claude-3-haiku-20240307-v1:0
```

## Files Changed

| File | Lines Added | Lines Removed |
|------|-------------|---------------|
| `src/etymologist.py` | ~120 | ~10 |
| `tests/unit/test_etymologist.py` | ~330 | ~10 |
| `docs/lld/active/1294-nova-micro-switch.md` | ~510 | 0 |

## Test Results

```
145 passed in 0.20s
```

All existing tests updated to work with Nova-default behavior.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Nova misclassifies terms | Enhanced `SYSTEM_PROMPT_NOVA` with explicit taxonomy |
| API format changes | Version-pinned model ID |
| Production issues | Env var rollback to Haiku |

## Acceptance Criteria Status

- [x] R1: Model configurable via environment variable
- [x] R2: Nova Micro as default
- [ ] R3: Classification accuracy parity (requires live testing)
- [x] R4: Backward compatibility with Haiku
- [ ] R5: Latency target < 700ms (requires live testing)
- [x] R6: JSON reliability (code handles both formats)
- [ ] R7: Prompt tuning complete (requires live testing with Nova)
- [x] R8: API schema abstraction
