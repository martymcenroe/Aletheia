# Test Report — Issue #620

**Title:** chore: remove dead ETYMOLOGIST_MODEL routing
**Date:** 2026-05-23
**Branch:** `620-remove-etymologist-model-routing`

## Lint

```
$ poetry run ruff check src/etymologist.py tests/unit/test_etymologist.py
All checks passed!
```

## Unit Tests (etymologist module — the changed module)

```
$ poetry run pytest tests/unit/test_etymologist.py -v
...
============================= 157 passed in 0.19s =============================
```

All 157 tests pass. Net change from this issue:

| Action | Tests removed | Tests added | Tests modified |
|---|---|---|---|
| Removed `TestGetModelId` class | 5 (covered dead `get_model_id`) | 0 | 0 |
| Removed `test_default_model_is_nova` | 1 (asserted deleted `DEFAULT_MODEL_ID`) | 0 | 0 |
| Restructured `TestAnalyzeTermModelSelection` | 2 (env-var read; default-Nova) | 1 (`test_defaults_to_haiku_when_model_id_none`) | 0 |

Net: -7 dead tests, +1 new test reflecting new contract. Total test count before: ~163. After: 157.

## Broader Unit Test Suite (pre-existing breakage, NOT introduced by #620)

```
$ poetry run pytest tests/unit/ -q
ERROR ... ModuleNotFoundError: No module named 'httpx'
ERROR ... ModuleNotFoundError: No module named 'jwt'  (resolved after `poetry install --with dev`)
!!! Interrupted: 23 errors during collection !!!
```

23 unit test modules fail to collect due to missing dependencies:

- `httpx` is imported by `src/auth/linkedin_oauth.py:32`, `src/auth/token_manager.py:26`, `tests/unit/test_linkedin_oauth.py:19`, `tests/unit/test_token_manager.py:18` — but is not declared in `pyproject.toml` and not installed by `provision.sh`. Filed as #621.

These failures are **pre-existing** on `main` (verified by running the same command against the main worktree's venv). The #620 change does not introduce them and does not change them. The etymologist module — the only module modified by #620 — has full test coverage that passes.

## Smoke Test (post-deploy — to be executed after merge + provision)

```bash
# Health
curl -s https://api.aletheia.study/health
# Expected: {"status":"ok",...} (200)

# Analysis (Haiku path)
curl -s -X POST https://api.aletheia.study/ \
  -H "Content-Type: application/json" \
  -H "X-Aletheia-Client-Version: 1.0" \
  -d '{"text":"zeitgeist"}'
# Expected: {"signal":"...","gem":"...","context":"..."} (200) — Haiku continues to serve

# Verify env state unchanged
aws lambda get-function-configuration \
  --function-name AletheiaAgent --region us-east-1 \
  --query 'Environment.Variables.ETYMOLOGIST_MODEL'
# Expected: null

aws lambda get-function-configuration \
  --function-name AletheiaAgent --region us-east-1 \
  --query 'Environment.Variables.BEDROCK_MODEL_ID'
# Expected: null
```

## Regression Risk Assessment

**None for production traffic.** The Lambda's call path uses `BEDROCK_MODEL_ID` (line 50 in `lambda_function.py`), which is unchanged. The deleted code was on a `model_id is None` branch that the Lambda never takes (the Lambda always passes an explicit `model_id`).

The `model_id is None` branch is exercised by:
- Direct test callers in `test_etymologist.py` (covered by `test_defaults_to_haiku_when_model_id_none`)
- Direct script callers (e.g., `data/probe_models.py` and similar — all pass explicit `model_id`)

No production caller relies on the `None` default.
