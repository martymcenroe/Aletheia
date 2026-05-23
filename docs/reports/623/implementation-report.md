# Implementation Report — Issue #623

**Title:** feat: Opus verifier — second-opinion on Haiku 'Prompt Injection Attempt' classifications
**Date:** 2026-05-23
**Status:** Complete (pending review + merge + deploy)
**Branch:** `623-opus-verifier`

## Summary

When the etymologist (Haiku 4.5) classifies an input as `signal: "Prompt Injection Attempt"`, the result is now re-evaluated by Opus 4.6 on the same input. Opus's verdict is canonical. Eliminates Haiku's false-positive confabulation on contextually-incongruous-but-benign inputs (foreign loanwords — see #618) while preserving genuine injection detection.

Empirical probe (2026-05-23) confirmed Opus correctly downgrades the gedenken false positive and correctly confirms a real injection attempt.

## Files Changed

| File | Change |
|------|--------|
| `src/etymologist.py` | Added `OPUS_MODEL_ID` constant (reads `ALETHEIA_AIP_OPUS` env var) |
| `src/etymologist.py` | Added `OPUS_MODEL_ID` and raw `anthropic.claude-opus-4-6-v1:0` to `ALLOWED_MODELS` |
| `src/etymologist.py` | Modified `analyze_term()` — when Haiku returns `"Prompt Injection Attempt"` AND model is not Nova AND model is not already Opus, delegates to `_verify_with_opus()` |
| `src/etymologist.py` | Added `_verify_with_opus()` private function — re-invokes Opus with Haiku-format prompt, falls back to Haiku result on exception, logs an operational metric per verification event |
| `tests/unit/test_etymologist.py` | Added `_haiku_response()` / `_opus_response()` test helpers |
| `tests/unit/test_etymologist.py` | Added `TestOpusVerifier` class — 8 new tests covering all branches |
| `docs/lld/active/LLD-623.md` | New LLD |

## Files Intentionally NOT Changed

- `src/lambda_function.py` — verifier integration happens entirely inside `analyze_term()`; no caller change required.
- `src/guardrails/semantic.py` — orthogonal layer.
- `docs/privacy.html` — operational logging (signal-only, no input text) fits existing "anonymous operational metrics" carve-out.

## Algorithm

```
analyze_term(word, context, model_id):
    result = invoke(model_id, prompt)
    if result.signal == "Prompt Injection Attempt"
       and not is_nova_model(model_id)
       and model_id != OPUS_MODEL_ID:
        return _verify_with_opus(word, context, original_result=result)
    return result

_verify_with_opus(word, context, original_result):
    try:
        opus_result = invoke(OPUS_MODEL_ID, build_haiku_prompt(word, context))
        log_operational_metric(
            haiku_signal=original_result.signal,
            opus_signal=opus_result.signal,
            agreement=original_result.signal == opus_result.signal
        )
        opus_result.metadata["verified_by_opus"] = True
        opus_result.metadata["original_haiku_signal"] = original_result.signal
        return opus_result
    except Exception as e:
        original_result.metadata["opus_verifier_error"] = str(e)
        return original_result  # fall back to Haiku verdict
```

## Production Behavior

**Unchanged for non-injection traffic** — when Haiku returns any signal other than "Prompt Injection Attempt", `analyze_term` returns immediately without the second call. This is >99% of requests based on the gedenken-event being the only one observed in CloudWatch.

**Changed for injection-flagged traffic:**
- Previously: user sees Haiku's flag (often a false positive).
- Now: Opus re-evaluates and the user sees Opus's verdict. False positives downgraded to correct etymology; true positives preserved with Opus's (typically more articulate) explanation.

**Metadata enrichment:**
- `metadata.verified_by_opus = True` when Opus ran
- `metadata.original_haiku_signal = "Prompt Injection Attempt"` retained for observability
- `metadata.opus_verifier_error = "..."` set on Opus failure (visible in logs only — not user-facing)

## Operational Logging

Per verification event:

```json
{
  "action": "opus_verifier",
  "haiku_signal": "Prompt Injection Attempt",
  "opus_signal": "German Loanword Usage",
  "agreement": false
}
```

No content (word, context) retained — compliant with `docs/privacy.html` Section 6.

## Cost & Latency

- **Per Opus call:** ~$0.02 at probe-observed token usage
- **Frequency:** rare — Haiku-flagged requests only
- **Latency:** +2-3s per flagged request
- **Steady-state budget impact:** estimated <$10/month worst case

## Deploy

1. Merge PR → main
2. `provision.sh` redeploys AletheiaAgent Lambda
3. Smoke tests:
   - `GET /health` → 200
   - Lambda CodeSha256 changes
   - Trigger a known-injection via demo or test fixture → verify CloudWatch shows `"action": "opus_verifier"` log line
4. No env var changes required (`ALETHEIA_AIP_OPUS` already set per #535)

## Rollback

`git revert <commit-sha>` + `provision.sh`. Self-contained in `etymologist.py`.

## Related

- #618 — root cause (gedenken misclassification)
- #620 — config hygiene prerequisite (consolidated model selection)
- #535 — Bedrock AIPs (provides `ALETHEIA_AIP_OPUS`)
