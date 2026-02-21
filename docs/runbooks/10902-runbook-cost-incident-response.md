# 10902 - Runbook: Cost Incident Response & Service Restoration

**Created:** 2026-02-14
**Trigger:** Budget alert email, kill switch activation, or suspected attack
**Audience:** Orchestrator (Marty)
**Model:** N/A (manual AWS CLI operations)

---

## Quick Reference

| Scenario | Go to |
|----------|-------|
| Got a budget alert email (10/40/80%) | [Section 1](#1-budget-alert-received) |
| Kill switch activated (concurrency set to 0) | [Section 2](#2-restore-after-kill-switch) |
| Bedrock deny policy applied (95% budget) | [Section 3](#3-restore-after-bedrock-deny-policy) |
| Both kill switch AND deny policy fired | [Section 4](#4-restore-after-both) |
| Suspected attack in progress | [Section 5](#5-active-attack-response) |
| Kill switch failed (got failure email) | [Section 6](#6-kill-switch-failure) |
| Monthly reset / new billing cycle | [Section 7](#7-monthly-reset) |

---

## Architecture: What Protects You

```
Layer 1: CloudWatch Alarms (real-time, 1-minute)
  ├── InvocationSpike (>100 in 5 min) → kill switch Lambda + email
  ├── Throttles (>10 in 5 min) → email only (attack indicator)
  └── KillSwitch-Failure (errors) → email ("do it manually!")

Layer 2: AWS Budgets (8-24h delay)
  ├── 10% ($2.50)  → email
  ├── 40% ($10)    → email
  ├── 80% ($20)    → email
  └── 95% ($23.75) → email + IAM deny policy on AletheiaLambdaRole

Layer 3: Account concurrency limit (always active)
  └── 10 concurrent Lambda executions max (AWS account limit)
```

### Key Resources

| Resource | Name/ARN |
|----------|----------|
| Main Lambda | `AletheiaAgent` |
| Kill switch Lambda | `AletheiaKillSwitch` |
| Lambda execution role | `AletheiaLambdaRole` |
| Deny policy | `AletheiaDenyBedrock-BudgetBreach` |
| Budgets action role | `AletheiaBudgetsActionRole` |
| Alert SNS topic | `AletheiaBillingAlerts` |
| Kill switch SNS topic | `AletheiaKillSwitchTrigger` |
| Budget | `Aletheia-Monthly-10USD` |
| CloudWatch alarms | `AletheiaAgent-InvocationSpike`, `AletheiaAgent-Throttles`, `AletheiaKillSwitch-Failure` |

---

## 1. Budget Alert Received

**You received an email saying actual cost exceeded 10%, 40%, or 80%.**

### At 10% ($2.50) — Awareness

No action required. This is normal if you or friends are using the extension.

### At 40% ($10) — Check usage

1. Check if usage is legitimate:
   ```bash
   MSYS_NO_PATHCONV=1 aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda --metric-name Invocations \
     --dimensions Name=FunctionName,Value=AletheiaAgent \
     --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 3600 --statistics Sum --region us-east-1
   ```
2. If invocations look normal (friends using it): no action needed
3. If invocations are abnormally high: go to [Section 5](#5-active-attack-response)

### At 80% ($20) — Prepare to shut down

1. Run the check from 40% above
2. If you expect to exceed $25 this month, consider temporarily disabling:
   ```bash
   MSYS_NO_PATHCONV=1 aws lambda put-function-concurrency \
     --function-name AletheiaAgent \
     --reserved-concurrent-executions 0 --region us-east-1
   ```
3. This is the manual kill switch — same as what the automated one does

---

## 2. Restore After Kill Switch

**The automated kill switch fired (or you ran it manually). AletheiaAgent concurrency is 0 — all requests are blocked.**

### How to tell this happened

- You received an email with subject "ALETHEIA KILL SWITCH ACTIVATED"
- OR users report the extension isn't working
- Verify:
  ```bash
  MSYS_NO_PATHCONV=1 aws lambda get-function-concurrency \
    --function-name AletheiaAgent --region us-east-1
  ```
  If output shows `ReservedConcurrentExecutions: 0`, the kill switch is active.

### Restore service

```bash
MSYS_NO_PATHCONV=1 aws lambda delete-function-concurrency \
  --function-name AletheiaAgent --region us-east-1
```

This removes the reserved concurrency setting entirely, returning AletheiaAgent to the shared pool (max 10 concurrent, your account limit).

### Verify restoration

```bash
MSYS_NO_PATHCONV=1 aws lambda get-function-concurrency \
  --function-name AletheiaAgent --region us-east-1
```

Expected output: empty or no `ReservedConcurrentExecutions` field (meaning it uses the shared pool).

### Before restoring, ask yourself

- [ ] Do I know why the kill switch fired?
- [ ] Was it a real attack or just heavy legitimate usage?
- [ ] Is the billing cycle about to reset? (If so, maybe wait)
- [ ] Am I comfortable with the remaining budget for the month?

---

## 3. Restore After Bedrock Deny Policy

**AWS Budgets applied the `AletheiaDenyBedrock-BudgetBreach` policy at 95% ($23.75). Lambda runs but Bedrock calls fail — users see "Analysis Failed" errors.**

### How to tell this happened

- You received a budget 95% alert email
- Users report "Analysis Failed" or "Analysis unavailable" errors
- Verify the policy is attached:
  ```bash
  MSYS_NO_PATHCONV=1 aws iam list-attached-role-policies \
    --role-name AletheiaLambdaRole --output table --region us-east-1
  ```
  If `AletheiaDenyBedrock-BudgetBreach` appears in the list, the deny policy is active.

### Option A (Preferred): Reverse via Budgets API

This tells AWS Budgets to reverse its own action, keeping the action history clean:

```bash
# First, get the budget action ID
MSYS_NO_PATHCONV=1 aws budgets describe-budget-actions-for-budget \
  --account-id 383687041805 --budget-name "Aletheia-Monthly-10USD" \
  --region us-east-1
```

```bash
# Then reverse it (use the ActionId from above)
MSYS_NO_PATHCONV=1 aws budgets execute-budget-action \
  --account-id 383687041805 --budget-name "Aletheia-Monthly-10USD" \
  --action-id ACTION_ID_HERE \
  --execution-type REVERSE_ACTION --region us-east-1
```

After reversal, the action returns to **STANDBY** and will re-fire if spend crosses 95% again in the same billing cycle.

### Option B: Manual IAM detach

If the Budgets API approach fails, detach the policy directly:

```bash
MSYS_NO_PATHCONV=1 aws iam detach-role-policy \
  --role-name AletheiaLambdaRole \
  --policy-arn arn:aws:iam::383687041805:policy/AletheiaDenyBedrock-BudgetBreach
```

> **Note:** Manual detach leaves the Budget Action in EXECUTION_SUCCESS state. It will NOT re-fire in the same billing cycle, even if spend keeps climbing.

### Verify restoration

```bash
MSYS_NO_PATHCONV=1 aws iam list-attached-role-policies \
  --role-name AletheiaLambdaRole --output table --region us-east-1
```

`AletheiaDenyBedrock-BudgetBreach` should no longer appear.

### IAM eventual consistency warning

After detaching/reversing the deny policy, **already-running Lambda environments may still see the deny for up to ~60 seconds** due to IAM credential caching. If Bedrock calls still fail immediately after reversal, wait 1-2 minutes and test again before escalating.

### Important: Budget Actions reset

The Budget Action resets each billing cycle. On the 1st of the next month, the action returns to "standby" and will fire again if the new month hits 95%. You do NOT need to reconfigure anything.

If you used **Option A (REVERSE_ACTION)**, the action returns to STANDBY and *can* re-fire within the same billing cycle if spend crosses 95% again. If you used **Option B (manual detach)**, the action will NOT re-fire within the same billing cycle.

---

## 4. Restore After Both

**Both the kill switch (concurrency=0) AND the deny policy fired. This means CloudWatch detected a spike AND the budget hit 95%.**

Run both restoration steps in order:

### Step 1: Remove the deny policy

See [Section 3](#3-restore-after-bedrock-deny-policy) for detailed options (Budgets API reversal preferred over manual IAM detach).

### Step 2: Remove the concurrency block

```bash
MSYS_NO_PATHCONV=1 aws lambda delete-function-concurrency \
  --function-name AletheiaAgent --region us-east-1
```

### Step 3: Verify

```bash
MSYS_NO_PATHCONV=1 aws iam list-attached-role-policies \
  --role-name AletheiaLambdaRole --output table --region us-east-1
```
```bash
MSYS_NO_PATHCONV=1 aws lambda get-function-concurrency \
  --function-name AletheiaAgent --region us-east-1
```

### Step 4: Reset CloudWatch alarm

The InvocationSpike alarm will be in ALARM state. It resets automatically when invocations drop below threshold, but you can manually reset it:

```bash
MSYS_NO_PATHCONV=1 aws cloudwatch set-alarm-state \
  --alarm-name AletheiaAgent-InvocationSpike \
  --state-value OK --state-reason "Manual reset after investigation" \
  --region us-east-1
```

---

## 5. Active Attack Response

**You suspect someone is hammering your endpoint right now.**

### Step 1: Kill it immediately

```bash
MSYS_NO_PATHCONV=1 aws lambda put-function-concurrency \
  --function-name AletheiaAgent \
  --reserved-concurrent-executions 0 --region us-east-1
```

### Step 2: Check the damage

```bash
MSYS_NO_PATHCONV=1 aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE --region us-east-1
```

### Step 3: Check who is calling

CloudFlare analytics (rate limiting is handled by CloudFlare Worker `aletheia-api`):
- Log into CloudFlare dashboard → `aletheia.study` → Security → Events
- Check rate limit hits and source IPs

CloudWatch invocation metrics (last hour, per-minute):
```bash
MSYS_NO_PATHCONV=1 aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda --metric-name Invocations \
  --dimensions Name=FunctionName,Value=AletheiaAgent \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 --statistics Sum --region us-east-1
```

### Step 4: Decide next steps

- **If attack is over:** Restore service per [Section 2](#2-restore-after-kill-switch)
- **If attack is ongoing:** Keep Lambda off. Add CloudFlare firewall rules to block source IPs
- **If source IP identified:** Add CloudFlare WAF custom rule to block the IP

---

## 6. Kill Switch Failure

**You received an email: "CRITICAL: Kill switch Lambda errored or was throttled."**

This means the automated kill switch tried to fire but failed — likely because all 10 concurrency slots were in use by AletheiaAgent (concurrency starvation).

### Immediate action: manual kill switch

```bash
MSYS_NO_PATHCONV=1 aws lambda put-function-concurrency \
  --function-name AletheiaAgent \
  --reserved-concurrent-executions 0 --region us-east-1
```

This WILL work even when issued from the CLI, because it's an API call to the Lambda control plane, not a Lambda invocation. It doesn't compete for concurrency slots.

### Why did it fail?

The kill switch Lambda shares the same 10-slot concurrency pool as AletheiaAgent. Under heavy load, AletheiaAgent may consume all slots, leaving none for the kill switch.

**This is a known limitation.** The IAM deny policy (Option A) doesn't have this problem because it's applied by AWS Budgets directly, not by a Lambda.

---

## 7. Monthly Reset

**New billing cycle started. What needs attention?**

### Automatic resets (no action needed)

- Budget tracking resets to $0
- Budget Action returns to standby (will fire again at 95% of new month)
- CloudWatch alarms continue as-is

### Manual checks at month start

1. **If deny policy was applied last month**, verify it was removed:
   ```bash
   MSYS_NO_PATHCONV=1 aws iam list-attached-role-policies \
     --role-name AletheiaLambdaRole --output table --region us-east-1
   ```
   If `AletheiaDenyBedrock-BudgetBreach` still appears, remove it:
   ```bash
   MSYS_NO_PATHCONV=1 aws iam detach-role-policy \
     --role-name AletheiaLambdaRole \
     --policy-arn arn:aws:iam::383687041805:policy/AletheiaDenyBedrock-BudgetBreach
   ```

2. **If kill switch was activated last month**, verify AletheiaAgent is running:
   ```bash
   MSYS_NO_PATHCONV=1 aws lambda get-function-concurrency \
     --function-name AletheiaAgent --region us-east-1
   ```

3. **Review last month's actual spend:**
   ```bash
   MSYS_NO_PATHCONV=1 aws ce get-cost-and-usage \
     --time-period Start=YYYY-MM-01,End=YYYY-MM-01 \
     --granularity MONTHLY --metrics UnblendedCost \
     --group-by Type=DIMENSION,Key=SERVICE --region us-east-1
   ```
   (Replace YYYY-MM with previous and current month)

---

## Appendix: Existing Kill Switch Scripts

The project has existing scripts for manual Lambda control:

| Script | Effect |
|--------|--------|
| `tools/aws/lambda-off.sh` | Sets AletheiaAgent concurrency to 0 |
| `tools/aws/lambda-on.sh` | Removes concurrency limit (restores service) |

These do the same thing as the CLI commands in this runbook.

---

## Appendix: Cost Quick Check

**How much have I spent this month?**

```bash
MSYS_NO_PATHCONV=1 aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u -d '+1 day' +%Y-%m-%d) \
  --granularity MONTHLY --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE --region us-east-1
```

**What's the current budget status?**

```bash
MSYS_NO_PATHCONV=1 aws budgets describe-budget \
  --account-id 383687041805 --budget-name "Aletheia-Monthly-10USD" \
  --region us-east-1
```

> **Note:** The budget name says "10USD" but the actual limit is **$25**. Budget names can't be changed via the API — ignore the naming mismatch.
