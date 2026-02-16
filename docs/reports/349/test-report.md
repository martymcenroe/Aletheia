# Test Report: Issue #349 — CloudFlare Migration

**Date:** 2026-02-16
**Tester:** Claude Opus 4.6
**Branch:** `349-cloudflare-migration`

## Unit Tests

| Suite | Pass | Fail | Notes |
|-------|------|------|-------|
| `test_lambda_handler.py` | 37 | 0 | All passing including header check scenarios |
| `test_etymologist.py` | All | 0 | Unaffected |
| `test_verify_audits.py` | N/A | 3 | Pre-existing failures, unrelated |
| All other unit tests | All | 0 | Unaffected |
| **Total** | **389** | **3** | 3 failures pre-existing |

## Live Integration Tests

### Test 1: CloudFlare Worker Proxy

```
curl -s -X POST https://api.aletheia.study/ \
  -H "Content-Type: application/json" \
  -H "X-Aletheia-Client-Version: 1.0" \
  -d '{"text":"The unprecedented restructuring of democratic norms..."}'
```

**Result:** 200 OK — full analysis response with signal, scores, gem, context, timings.
Latency: ~3.6s (comparable to CloudFront route).

### Test 2: CloudFlare Headers Present

```
curl -sI https://api.aletheia.study/
```

**Result:** Response includes `Server: cloudflare`, `CF-RAY` header — confirms CloudFlare proxy active.

### Test 3: Direct Lambda (baseline comparison)

```
curl -s -X POST https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -H "X-Aletheia-Client-Version: 1.0" \
  -d '{"text":"test"}'
```

**Result:** 200 OK — confirms Lambda Function URL still works directly.

### Test 4: Host Header Rejection (before Worker)

```
curl -s -X POST https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/ \
  -H "Host: api.aletheia.study" \
  -d '{"text":"test"}'
```

**Result:** 403 AccessDeniedException — Lambda Function URL rejects mismatched Host header. This is why the Worker was needed.

## Benchmark Tests

All benchmark tests pass with performance within expected ranges:

| Benchmark | Median |
|-----------|--------|
| `test_validate_input_benchmark` | 169ns |
| `test_denylist_check_benchmark` | 900ns |
| `test_lambda_handler_warm_invocation` | 269μs |

## Conclusion

All code changes verified. CloudFlare proxy operational. No regressions introduced.
