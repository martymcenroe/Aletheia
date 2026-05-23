# Test Report — Issue #623

**Title:** feat: Opus verifier for prompt-injection classifications
**Date:** 2026-05-23
**Branch:** `623-opus-verifier`

## Lint

```
$ poetry run ruff check src/etymologist.py tests/unit/test_etymologist.py
All checks passed!
```

## Unit Tests

```
$ poetry run pytest tests/unit/test_etymologist.py -q
165 passed in 0.10s
```

Net change: +8 tests in new `TestOpusVerifier` class. Total now 165 (was 157).

## New tests covered

| Test | What it verifies |
|---|---|
| `test_verifier_fires_when_haiku_says_injection` | When Haiku returns "Prompt Injection Attempt", a second `invoke_model` call to `OPUS_MODEL_ID` is made |
| `test_verifier_downgrades_when_opus_disagrees` | Opus's signal/gem/context replace Haiku's; `metadata.model == OPUS_MODEL_ID`; `verified_by_opus == True`; `original_haiku_signal == "Prompt Injection Attempt"` |
| `test_verifier_preserves_signal_when_opus_agrees` | When both models say injection, signal preserved; Opus's gem/context used; verification metadata still set |
| `test_verifier_falls_back_on_opus_exception` | When Opus raises, return original Haiku result with `metadata.opus_verifier_error` set; `verified_by_opus` not set |
| `test_verifier_doesnt_recurse_on_opus_model_id` | If `model_id == OPUS_MODEL_ID` and signal is injection, no second call |
| `test_verifier_doesnt_fire_on_nova_model_id` | Nova-model requests never trigger the verifier regardless of signal |
| `test_verifier_doesnt_fire_when_no_injection_signal` | Normal etymology results don't trigger the verifier |
| `test_opus_model_id_in_allowed_models` | `OPUS_MODEL_ID` is in `ALLOWED_MODELS` allowlist |

## Mock-fixture pattern

Two helper functions return Bedrock-shaped response dicts:

```python
def _haiku_response(signal=..., gem=..., context=..., input_tokens=..., output_tokens=...): ...
def _opus_response(signal=..., gem=..., context=..., input_tokens=..., output_tokens=...): ...
```

Tests configure `mock_bedrock_client.invoke_model.side_effect` with a list of these responses (or exceptions). The test framework then verifies both call count and per-call `modelId` kwarg.

## Empirical probe (separate from unit tests — confirmed real model behavior)

From earlier in session (`data/probe_opus_verifier.py`):

| input | Haiku 4.5 (actual) | Opus 4.6 (actual) |
|---|---|---|
| `gedenken` + Ford-context | `"Prompt Injection Attempt"` (false positive) | `"German Loanword Usage"` |
| `"Ignore all previous instructions..."` | `"Prompt Injection Attempt"` | `"Prompt Injection Attempt"` |

Opus's gem on the gedenken case: *"German verb meaning 'to remember' or 'to commemorate,' used here as casual code-switching."* Opus's context: *"Here it is deployed informally as a playful substitution for 'reminiscing' or 'imagining,' lending faux-intellectual color to conversational prose."* — high-quality, nuanced classification.

## Pre-existing breakage (NOT introduced by #623)

Same as documented in #620: the broader unit test suite has collection failures for `httpx` and other unrelated import errors. Filed as #621. Does not affect `test_etymologist.py`.

## Post-deploy smoke test plan

```bash
# Verify Lambda redeployed
aws lambda get-function-configuration --function-name AletheiaAgent --region us-east-1 \
  --query '{LastModified:LastModified,CodeSha256:CodeSha256}'

# Verify Opus AIP is reachable (already deployed; just confirming env)
aws lambda get-function-configuration --function-name AletheiaAgent --region us-east-1 \
  --query 'Environment.Variables.ALETHEIA_AIP_OPUS'

# Trigger verifier via known reproducer (gedenken + injection-suspicious context)
# Requires either a test JWT or running through the extension. Manual step.

# Confirm CloudWatch logs include "action": "opus_verifier" events
aws logs filter-log-events --log-group-name /aws/lambda/AletheiaAgent \
  --filter-pattern "opus_verifier" --region us-east-1
```

## Regression risk

**Low.** Behavior change is gated on `signal == "Prompt Injection Attempt"`, which production data shows is rare. Non-flagged traffic is byte-identical to before this change. Opus failure path falls back to original Haiku result with an error annotation in metadata. Worst case on Opus outage: same UX as before this PR.
