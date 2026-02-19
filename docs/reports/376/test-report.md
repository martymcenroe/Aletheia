# Test Report: #376 Admin ID Resolution CLI

## Results
```
8 passed in 0.36s
975 passed, 2 skipped (full regression)
mypy: Success, no issues found
ruff: All checks passed
```

## Test Coverage
| Test | What it verifies |
|------|-----------------|
| `test_returns_user_id_and_hash` | Forward resolve returns correct hash |
| `test_hash_is_12_chars` | Hash length is 12 characters |
| `test_deterministic` | Same input = same output |
| `test_dry_run_refuses_without_confirm` | PII guard blocks without --confirm |
| `test_finds_matching_user` | Reverse resolve finds correct user (mocked DynamoDB) |
| `test_not_found` | Returns not_found when no match |
| `test_empty_table` | Handles empty users table gracefully |
| `test_dynamo_error` | Returns error status on DynamoDB failure |
