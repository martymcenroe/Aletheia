# Implementation Report: Issue #362

## Summary

Update provision.sh, CI pipeline, and token_cap_service.py to support JWT auth deployment (Issue #341).

## Changes

### provision.sh (108 insertions, 49 deletions)

| Change | Description |
|--------|-------------|
| Step 3 (new) | `aletheia-token-cap` DynamoDB table with PK/SK composite key, PAY_PER_REQUEST, TTL on `ttl` attribute |
| Step 4 (IAM) | Added `aletheia-token-cap` to DynamoDB resource list; added `aletheia/jwt-signing-key` to Secrets Manager resource list |
| Step 5 (Layer) | Added `PyJWT` to pip install for Lambda dependency layer |
| Step 7 (Auth Lambda) | Changed from flat file packaging (`cp lambda_auth_function.py`) to `src/` directory packaging (`zip -rq auth_lambda.zip src/`); updated handler to `src.lambda_auth_function.lambda_handler` |
| Steps 6+7 (env vars) | Added `TOKEN_CAP_TABLE` and `JWT_SECRET_NAME` to both Lambda environment configurations |
| Step 10 (secrets) | Validates both LinkedIn OAuth and JWT signing secrets |
| Renumbered | Steps 0-9 → 0-10 to accommodate new token cap table step |

### .github/workflows/ci.yml (1 line)

- `deploy-infra` now requires `integration-tests` job in addition to `test` and `policy-check`

### src/auth/token_cap_service.py (1 line)

- `DYNAMODB_ENDPOINT_URL` → `DYNAMODB_ENDPOINT` to align with existing codebase convention

## Risk Assessment

- **Auth Lambda packaging fix is a deployment blocker** — without it, the Auth Lambda would crash on `from auth.jwt_service import ...` because the `auth/` package wouldn't be in the zip
- All other changes are additive (new table, new env vars, new secret validation)
- IAM policy is idempotent — `put-role-policy` replaces the existing inline policy
