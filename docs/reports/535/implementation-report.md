# Implementation Report: Issue #535

## Summary

Aletheia/Hermes cost separation via Application Inference Profiles, model upgrade, role migration, and budget restructure.

## Changes

### Code Changes

| File | Change |
|------|--------|
| `src/etymologist.py` | Added `is_nova_model()` helper; model IDs from env vars (`ALETHEIA_AIP_NOVA_MICRO`, `ALETHEIA_AIP_HAIKU`); expanded `ALLOWED_MODELS` for AIP ARNs; replaced 3x `startswith("amazon.nova")` with `is_nova_model()` |
| `src/poetic_analyzer.py` | `OPUS_MODEL_ID` from env var `ALETHEIA_AIP_OPUS` (default: `anthropic.claude-opus-4-6-v1`); added `import os` |
| `src/guardrails/semantic.py` | Default `model_id` from env var `ALETHEIA_AIP_HAIKU` (default: `anthropic.claude-haiku-4-5-20251001-v1:0`); `model_id` parameter now `str | None` |
| `src/lambda_function.py` | No changes needed — already reads `BEDROCK_MODEL_ID` from env, imports `HAIKU_MODEL_ID` which is now env-var-backed |

### Infrastructure Changes (provision.sh)

| Section | Change |
|---------|--------|
| IAM policy | New model ARNs (Haiku 4.5, Opus 4.6) + AIP wildcard (`aletheia-*`) |
| Step 4b | AIP creation (idempotent) for nova-micro, haiku, opus |
| Lambda env vars | Added `ALETHEIA_AIP_NOVA_MICRO`, `ALETHEIA_AIP_HAIKU`, `ALETHEIA_AIP_OPUS` |
| Step 10b | Lambda tagging (`Project:Aletheia` / `Project:Hermes`) |
| Step 10c | `HermesPollerRole` creation + migration of `AletheiaHermesPoller` |
| Step 10d | Cost allocation tag activation |

### Documentation

| File | Change |
|------|--------|
| `docs/runbooks/10902-runbook-cost-incident-response.md` | Updated budget structure (Account-Monthly-Canary + Aletheia-Monthly-25USD) |
| `AssemblyZero/docs/adrs/0213-aws-multi-app-cost-separation.md` | New ADR: multi-app cost separation pattern |

### Test Changes

| File | Change |
|------|--------|
| `tests/unit/test_etymologist.py` | Added `is_nova_model` import + `TestIsNovaModel` class (6 tests); updated `test_haiku_model_id` expectation to Haiku 4.5 |

## Model Upgrade

| Role | Old | New |
|------|-----|-----|
| Etymologist (main) | `anthropic.claude-3-haiku-20240307-v1:0` | `anthropic.claude-haiku-4-5-20251001-v1:0` |
| Semantic guardrail | `anthropic.claude-3-haiku-20240307-v1:0` | `anthropic.claude-haiku-4-5-20251001-v1:0` |
| Poetic analysis | `anthropic.claude-3-opus-20240229-v1:0` | `anthropic.claude-opus-4-6-v1` |
| Cost-efficient default | `amazon.nova-micro-v1:0` | stays |

## Risk Assessment

- Same Messages API across Claude 3/4 — no prompt or parsing changes needed
- `is_nova_model()` uses defensive check: `startswith("amazon.nova") or "nova" in model_id.lower()`
- AIP ARNs don't start with `amazon.nova` — the helper prevents misrouting
- Budget action targets only `AletheiaLambdaRole` — Hermes unaffected
