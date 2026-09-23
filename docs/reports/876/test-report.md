# Test Report — Issue #876

```
pytest tests/integration/test_dynamodb_ops.py            →  15 passed
pytest tests/unit/test_operator_retention.py tests/unit/test_lambda_auth.py
                                                         →  65 passed
bash -n provision.sh                                     →  ok
```

Running the three files together in one process, unit files first, fails 040, 041 and 042 in `TestSaveState`. **That failure also occurs on unchanged main** and is pre-existing: `DYNAMODB_TABLE` is fixed when `src/lambda_function.py` is first imported. It is filed as #877. The full suite passes in its normal order because `tests/integration/` is collected before `tests/unit/`.
