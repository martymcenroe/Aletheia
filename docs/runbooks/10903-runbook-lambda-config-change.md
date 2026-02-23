# 10903 - Lambda Configuration Change Runbook

## Purpose

Mandatory checklist for any Lambda environment variable change. Created after the AUTH_ENABLED=true outage on 2026-02-20 (see `docs/retrospectives/2026-02-20-auth-outage.md`).

## Scope

Applies to **all** `aws lambda update-function-configuration` calls targeting:
- `AletheiaAgent`
- `AletheiaAuth`
- `AletheiaKillSwitch`

## Pre-Change

- [ ] **GitHub issue exists** with blast radius and rollback plan documented
- [ ] **Capture current config** (copy-paste the output — this is your rollback source):
  ```bash
  MSYS_NO_PATHCONV=1 aws lambda get-function-configuration \
    --function-name FUNCTION_NAME \
    --query 'Environment.Variables' --output json
  ```
- [ ] **Rollback command prepared** (paste into issue, ready to execute):
  ```bash
  MSYS_NO_PATHCONV=1 aws lambda update-function-configuration \
    --function-name FUNCTION_NAME \
    --environment 'Variables={KEY1=oldval1,KEY2=oldval2}'
  ```
- [ ] **No other config changes bundled** — one variable per issue

## Apply Change

- [ ] Run the `update-function-configuration` command
- [ ] Verify the change took effect:
  ```bash
  MSYS_NO_PATHCONV=1 aws lambda get-function-configuration \
    --function-name FUNCTION_NAME \
    --query 'Environment.Variables.CHANGED_KEY'
  ```

## Post-Change Verification

- [ ] **Health check passes:**
  ```bash
  curl -s https://api.aletheia.study/health
  ```
- [ ] **Analysis endpoint works** (expected behavior for the new config):
  ```bash
  curl -s -X POST https://api.aletheia.study/ \
    -H "Content-Type: application/json" \
    -H "X-Aletheia-Client-Version: 1.0" \
    -d '{"text":"test"}'
  ```
- [ ] **Extension tested** if the change affects request/response flow (load extension, select text, analyze)
- [ ] **Issue updated** with verification evidence (curl output, screenshots)

## If Verification Fails

1. **Immediately execute the rollback command** (from the pre-change step)
2. Re-run health + analysis checks to confirm rollback
3. Document what went wrong in the issue
4. Do NOT retry without understanding the failure

## Related

- CLAUDE.md § Change Control
- CLAUDE.md § Production Safety
- `docs/retrospectives/2026-02-20-auth-outage.md`
