# Implementation Report — Issue #619

## Scope

Fix the silent exception swallowing in `src/guardrails/semantic.py` while honoring Aletheia's absolute privacy commitment in `docs/observability.html`: *"NEVER log prompt text, user input, completion text, URLs, or user IDs."*

## Changes

### `src/guardrails/semantic.py:160-173`

Before:
```python
except Exception as e:
    timings["total_ms"] = int((time.time() - start) * 1000)
    logger.info(f"SEMANTIC_GUARDRAIL_TIMING (error): {json.dumps(timings)}")
    return {
        ...
        "reason": f"Guardrail Error: {str(e)}",
        ...
    }
```

After:
```python
except Exception as e:
    timings["total_ms"] = int((time.time() - start) * 1000)
    # Privacy: log exception class name only, never str(e) or repr(e).
    # Exception messages from this path can carry user-derived content
    # (json.JSONDecodeError, botocore ClientError) — see issue #619.
    error_class = e.__class__.__name__
    logger.error(
        f"SEMANTIC_GUARDRAIL_ERROR: {error_class} | {json.dumps(timings)}"
    )
    return {
        ...
        "reason": f"Guardrail Error: {error_class}",
        ...
    }
```

Three behavioral changes:

1. **Log level promoted from `info` to `error`** — this is an actual failure condition, not normal flow. Better for CloudWatch filtering and alarming.
2. **Diagnostic signal added** — log line now includes `SEMANTIC_GUARDRAIL_ERROR: <ClassName>` so future occurrences are attributable to a specific exception class.
3. **Privacy hardening** — `str(e)` removed from both the log message AND the `reason` field of the returned dict. The `reason` field went over the wire to the client; cleaning it up closes a pre-existing leak.

## Privacy Rationale

The semantic guardrail processes user-selected text. Exceptions raised from that processing path can carry user-derived content:

- `botocore.exceptions.ClientError` — Bedrock validation error messages can echo field values from the request payload (including the user text wrapped in the prompt).
- `json.JSONDecodeError` — `str(e)` is safe, but `e.doc` holds the full malformed document (LLM output, which often paraphrases user input). Logging `str(e)` today is a foot-gun for any future code that touches `e.doc`.
- Custom exceptions from transitively-imported libraries — unbounded; the catch-all `except Exception` can receive anything.

Only the exception class name is bounded by a code-readable enumeration, so it's the only safe thing to surface.

## What This Fix Does NOT Cover

The audit performed in service of this issue identified **13 other distinct exception-text leak surfaces** across `src/lambda_function.py`, `src/lambda_auth_function.py`, `src/etymologist.py`, `src/poetic_analyzer.py`, and `src/signal_inspector/fetcher.py` — all introduced before the Mar 12 build. Per "One Issue Per Concern," each will be filed as its own follow-up issue rather than bundled into this PR.

## Closes

- #619

## Blast Radius

- Code change is in `src/guardrails/semantic.py` only — code-only deploy, no dependency layer rebuild
- Deploy via `provision.sh` repackages the Agent Lambda zip; only `AletheiaAgent` swaps; other 3 Lambdas untouched
- Rollback: `aws lambda update-function-code --function-name AletheiaAgent --zip-file fileb://<previous>.zip` (or revert + redeploy)

## Verification (post-deploy)

1. Smoke test: `curl https://api.aletheia.study/health` + `curl -X POST https://api.aletheia.study/ ...`
2. Trigger a deliberate semantic guardrail failure (e.g. via test endpoint or by sending a request known to provoke a `JSONDecodeError` on the model output) and verify CloudWatch `/aws/lambda/AletheiaAgent` shows `SEMANTIC_GUARDRAIL_ERROR: <ClassName>` and nothing else
