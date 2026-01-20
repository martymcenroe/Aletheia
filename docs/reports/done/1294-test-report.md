# Test Report: Issue #294 - Nova Micro Switch

## Summary

All unit tests pass after implementing Nova Micro integration.

## Test Execution

```bash
poetry run pytest tests/unit/test_etymologist.py -v
```

**Result:** 145 passed in 0.20s

## New Test Classes (Issue #294)

### TestModelConstants (5 tests)
| Test | Status | Description |
|------|--------|-------------|
| `test_nova_micro_model_id` | PASS | Nova Micro model ID is correct |
| `test_haiku_model_id` | PASS | Haiku model ID is correct |
| `test_default_model_is_nova` | PASS | Default model is Nova Micro |
| `test_allowed_models_contains_nova` | PASS | Allowlist contains Nova |
| `test_allowed_models_contains_haiku` | PASS | Allowlist contains Haiku |

### TestValidateModelId (5 tests)
| Test | Status | Description |
|------|--------|-------------|
| `test_nova_micro_is_valid` | PASS | Nova Micro passes validation |
| `test_haiku_is_valid` | PASS | Haiku passes validation |
| `test_unknown_model_is_invalid` | PASS | Unknown model fails |
| `test_empty_string_is_invalid` | PASS | Empty string fails |
| `test_similar_but_wrong_model_is_invalid` | PASS | Similar but wrong IDs fail |

### TestGetModelId (4 tests)
| Test | Status | Description |
|------|--------|-------------|
| `test_returns_default_when_env_not_set` | PASS | Default when no env var |
| `test_returns_nova_when_set_to_nova` | PASS | Nova from env var |
| `test_returns_haiku_when_set_to_haiku` | PASS | Haiku from env var |
| `test_falls_back_to_default_for_invalid_model` | PASS | Fallback for invalid env |

### TestBuildNovaPrompt (7 tests)
| Test | Status | Description |
|------|--------|-------------|
| `test_includes_schema_version` | PASS | Has schemaVersion: messages-v1 |
| `test_system_is_array_of_text_objects` | PASS | system is array format |
| `test_uses_nova_system_prompt` | PASS | Uses SYSTEM_PROMPT_NOVA |
| `test_includes_inference_config` | PASS | Has inferenceConfig.max_new_tokens |
| `test_user_message_content_format` | PASS | Content has text (not type) |
| `test_includes_word_in_user_message` | PASS | Word in user message |
| `test_includes_context_when_provided` | PASS | Context included |

### TestBuildHaikuPrompt (4 tests)
| Test | Status | Description |
|------|--------|-------------|
| `test_includes_anthropic_version` | PASS | Has anthropic_version |
| `test_system_is_string` | PASS | system is string format |
| `test_includes_max_tokens` | PASS | Has max_tokens |
| `test_user_message_content_format` | PASS | Content has type+text |

### TestExtractResponseText (6 tests)
| Test | Status | Description |
|------|--------|-------------|
| `test_extracts_text_from_nova_response` | PASS | Nova format extraction |
| `test_extracts_text_from_haiku_response` | PASS | Haiku format extraction |
| `test_returns_empty_for_missing_nova_content` | PASS | Handles missing Nova content |
| `test_returns_empty_for_missing_haiku_content` | PASS | Handles missing Haiku content |
| `test_handles_empty_nova_response` | PASS | Handles empty Nova response |
| `test_handles_empty_haiku_response` | PASS | Handles empty Haiku response |

### TestExtractTokenUsage (4 tests)
| Test | Status | Description |
|------|--------|-------------|
| `test_extracts_tokens_from_nova_response` | PASS | Nova inputTokens/outputTokens |
| `test_extracts_tokens_from_haiku_response` | PASS | Haiku input_tokens/output_tokens |
| `test_returns_zeros_for_missing_nova_usage` | PASS | Zero for missing Nova usage |
| `test_returns_zeros_for_missing_haiku_usage` | PASS | Zero for missing Haiku usage |

### TestNovaSystemPrompt (7 tests)
| Test | Status | Description |
|------|--------|-------------|
| `test_nova_prompt_contains_taxonomy_section` | PASS | CLASSIFICATION TAXONOMY present |
| `test_nova_prompt_defines_archaic_as_abandoned` | PASS | ABANDONED before 1950 |
| `test_nova_prompt_defines_formal_academic_as_active` | PASS | RARE but ACTIVE |
| `test_nova_prompt_includes_wsj_rule` | PASS | WSJ Rule present |
| `test_nova_prompt_distinguishes_pejorative` | PASS | INSULT definition |
| `test_nova_prompt_has_immiserate_example` | PASS | Immiserate as NOT archaic |
| `test_nova_prompt_has_prompt_injection_example` | PASS | Prompt Injection JSON (G2.1) |

### TestAnalyzeTermModelSelection (4 tests)
| Test | Status | Description |
|------|--------|-------------|
| `test_uses_default_model_when_none_provided` | PASS | Default model used |
| `test_uses_provided_model_id` | PASS | Explicit model respected |
| `test_uses_env_var_model_when_set` | PASS | Env var model used |
| `test_successful_nova_call_with_mock` | PASS | Full Nova flow works |

## Updated Existing Tests

| Test | Change |
|------|--------|
| `TestBuildEtymologistPrompt` | Updated to explicitly pass `model_id=HAIKU_MODEL_ID` |
| `test_successful_call_with_mock` | Added `model_id=HAIKU_MODEL_ID` for mock compatibility |
| `test_includes_latency_metadata` | Added `model_id=HAIKU_MODEL_ID` for mock compatibility |
| `test_system_override_attempt_escaped` | Added `model_id=HAIKU_MODEL_ID` |
| `test_system_override_attempt_escaped_nova` | NEW - Nova format test |

## Coverage Summary

| Module | Tests | Pass | Fail |
|--------|-------|------|------|
| Model Constants | 5 | 5 | 0 |
| Model Validation | 5 | 5 | 0 |
| Model ID Retrieval | 4 | 4 | 0 |
| Nova Prompt Builder | 7 | 7 | 0 |
| Haiku Prompt Builder | 4 | 4 | 0 |
| Response Extraction | 6 | 6 | 0 |
| Token Extraction | 4 | 4 | 0 |
| Nova System Prompt | 7 | 7 | 0 |
| Model Selection | 4 | 4 | 0 |
| **TOTAL NEW** | **46** | **46** | **0** |

## Integration Testing Required

The following tests require live Bedrock access:

1. **Acceptance Criteria Terms**
   - [ ] "immiserate" → Formal Academic Term (NOT Archaic Pejorative)
   - [ ] "serendipity" → Formal/Historical Term
   - [ ] "glamorous" → Contains "Adjective"
   - [ ] "cryptocurrency" → Contains "Technical" or "Modern"
   - [ ] "hello" → Common Greeting

2. **Latency Verification**
   - [ ] Average < 700ms warm start
   - [ ] P95 < 1000ms

3. **Golden Set Regression**
   - [ ] All existing golden set terms produce valid JSON
   - [ ] No classification regressions

## Conclusion

All 145 unit tests pass. Implementation is ready for integration testing with live Nova Micro API.
