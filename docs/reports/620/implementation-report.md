# Implementation Report — Issue #620

**Title:** chore: remove dead ETYMOLOGIST_MODEL routing — consolidate etymologist model selection
**Date:** 2026-05-23
**Status:** Complete (pending review + merge + deploy)
**Branch:** `620-remove-etymologist-model-routing`

## Summary

Removed dead code paths in `src/etymologist.py` that read the `ETYMOLOGIST_MODEL` environment variable. The Lambda's production code path goes through `BEDROCK_MODEL_ID` (in `lambda_function.py:50`) which is wired correctly; the parallel `ETYMOLOGIST_MODEL` path was specified in LLD #294 but never reached during a real request.

## Files Changed

| File | Change |
|------|--------|
| `src/etymologist.py` | Deleted `DEFAULT_MODEL_ID` constant (line 35) |
| `src/etymologist.py` | Deleted `get_model_id()` function (lines 206-216) |
| `src/etymologist.py` | Changed `build_etymologist_prompt()` fallback: `model_id is None` now defaults to `HAIKU_MODEL_ID` (was: `get_model_id()`) |
| `src/etymologist.py` | Changed `analyze_term()` fallback: same |
| `src/etymologist.py` | Updated docstrings on `build_etymologist_prompt()` and `analyze_term()` to reflect new behavior |
| `tests/unit/test_etymologist.py` | Removed imports of `DEFAULT_MODEL_ID` and `get_model_id` |
| `tests/unit/test_etymologist.py` | Deleted `test_default_model_is_nova` (asserts a deleted constant) |
| `tests/unit/test_etymologist.py` | Deleted `TestGetModelId` class (5 tests, all exercised dead code) |
| `tests/unit/test_etymologist.py` | Restructured `TestAnalyzeTermModelSelection`: replaced env-var/default-Nova tests with single `test_defaults_to_haiku_when_model_id_none` test |
| `docs/lld/active/LLD-620.md` | New LLD documenting the decision and scope |

## Files Intentionally NOT Changed

- `src/lambda_function.py` — `BEDROCK_MODEL_ID` is the correct prod path; no change needed.
- `src/guardrails/semantic.py` — uses `ALETHEIA_AIP_HAIKU` directly; unaffected.
- `docs/lld/done/10294-nova-micro-switch.md` — historical, immutable per project rule.
- `docs/reports/done/1294-implementation-report.md` — same.
- `docs/audits/10827-audit-infrastructure-integration.md` — already references the correct env var (`BEDROCK_MODEL_ID`).
- `NOVA_MICRO_MODEL_ID`, `ALLOWED_MODELS`, `is_nova_model()`, `validate_model_id()`, `build_nova_prompt()` — all retained. Nova prompt format remains supported even though no production route currently selects it.

## Lambda Behavior After Deploy

- `BEDROCK_MODEL_ID` env var: unset (no change)
- `lambda_function.py:50` `BEDROCK_MODEL_ID` constant: falls back to `HAIKU_MODEL_ID` (no change)
- `HAIKU_MODEL_ID` reads `ALETHEIA_AIP_HAIKU` env var → `arn:aws:bedrock:us-east-1:383687041805:application-inference-profile/hbcetfkyu7ft` (no change)
- Production etymology requests continue to use Haiku 4.5 (no change in user-visible behavior)

The cleanup is non-functional from a runtime perspective — it removes dead code that was confusing the model-selection picture (per #618 investigation) but does not change which model serves traffic.

## Deploy

1. Merge PR → main.
2. `provision.sh` deploys Lambda.
3. Smoke test:
   - `curl https://api.aletheia.study/health` → 200 OK
   - `curl -X POST https://api.aletheia.study/ -H "Content-Type: application/json" -H "X-Aletheia-Client-Version: 1.0" -d '{"text":"test"}'` → response with `signal` and `gem`
4. Confirm `ETYMOLOGIST_MODEL` env var still absent: `aws lambda get-function-configuration --function-name AletheiaAgent --region us-east-1 --query 'Environment.Variables.ETYMOLOGIST_MODEL'` → `null`.

## Rollback

`git revert <commit-sha>` + `provision.sh`. No data migration. No external systems affected.

## Related

- #618 — discovery (gedenken misclassification, includes empirical model probe)
- #294 — original Nova Micro switch (LLD documented `ETYMOLOGIST_MODEL` as the deploy variable; that env var was never wired into the Lambda code path)
- #535 — Bedrock AIPs (introduced `ALETHEIA_AIP_*` env vars; orthogonal to this cleanup)
- #621 — separate pre-existing issue: `httpx` missing from `pyproject.toml` and `provision.sh` (discovered while running tests for this issue)
