# Test Report: Issue #161 - CI Performance Benchmarks

## Test Execution Summary

### Benchmark Tests (5 tests)

```
poetry run pytest tests/benchmark/ --benchmark-only -v
```

| Test | Median | Min | Max | Status |
|------|--------|-----|-----|--------|
| test_validate_input_benchmark | 177 ns | 168 ns | 2,616 ns | PASS |
| test_denylist_check_benchmark | 900 ns | 800 ns | 160,400 ns | PASS |
| test_denylist_check_blocked_benchmark | 900 ns | 800 ns | 113,300 ns | PASS |
| test_lambda_handler_with_denylist_block | 3.7 us | 3.4 us | 156 us | PASS |
| test_lambda_handler_warm_invocation | 236 us | 200 us | 8,710 us | PASS |

All benchmarks pass with excellent performance:
- Input validation: ~177 nanoseconds (target < 1ms) - 5600x better than target
- Denylist lookup: ~900 nanoseconds (target < 1ms) - meets target
- Lambda handler (mocked): ~236 microseconds (target < 100ms) - 423x better than target

### Regression Testing (246 tests)

```
poetry run pytest tests/unit tests/tools -v -m "not audit"
```

Result: **246 passed** in 10.03s

No regressions introduced.

## Benchmark Analysis

### Lambda Handler Performance

The mocked Lambda handler benchmark shows:
- **Median**: 236 microseconds (0.236ms)
- **P99** (approx max): 8.7ms

This is well under the 100ms warm invocation target from 0812-audit-performance.md.

Note: Real production latency is higher due to actual network I/O to Bedrock and DynamoDB. These benchmarks test pure Python execution time with mocked AWS services.

### Denylist Block Fast Path

The denylist block path shows:
- **Median**: 3.7 microseconds
- **P99**: 156 microseconds

This validates that blocked terms skip expensive Bedrock calls.

## CI Integration

The benchmark workflow will:
1. Run on every PR to catch performance regressions
2. Run weekly to establish baseline trends
3. Output JSON results to GitHub artifacts
4. Start in "warn only" mode per LLD recommendation

## Baseline Establishment

Next steps (per LLD 1161):
1. Run benchmarks in CI for 2-3 weeks
2. Analyze results to establish reliable baseline
3. Tighten threshold from 50% to 20% when baseline is stable
4. Document baseline metrics in 0812-audit-performance.md
