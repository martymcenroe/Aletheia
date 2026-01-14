# 0829 - Audit: Lambda Failure Remediation

## 1. Purpose

Proactively detect and remediate Lambda failures from CloudWatch logs before users report them.

**Why this exists:** The reactive cycle (user reports → agent fixes → breaks again → repeat) wastes time and frustrates users. This audit catches failures automatically and either fixes them or queues them for review.

**Key difference from other audits:** This audit doesn't just detect problems—it attempts to fix them on worktrees. Unfixable issues are drafted (not filed) for orchestrator review.

---

## 2. Trigger

| Trigger | When |
|---------|------|
| **On-demand** | `/audit lambda-failures` |
| **Part of cleanup** | `/cleanup --full` |
| **After deployment** | Recommended 1 hour post-deploy |

---

## 3. Procedure

### Phase 1: Establish Baseline

Get the Lambda's last deployment timestamp:

```bash
MSYS_NO_PATHCONV=1 aws lambda get-function --function-name AletheiaAgent --query 'Configuration.LastModified' --output text
```

Record as `DEPLOY_TIMESTAMP`. All queries filter to errors **after** this timestamp.

**If Lambda doesn't exist:** FAIL audit, report "Lambda not deployed".

### Phase 2: Query CloudWatch Errors

Query for all error patterns since deployment:

```bash
MSYS_NO_PATHCONV=1 aws logs filter-log-events --log-group-name /aws/lambda/AletheiaAgent --start-time <EPOCH_MS> --filter-pattern "ERROR" --query 'events[*].message' --output text
```

Also query for:
- `"Task timed out"` — Lambda timeout
- `"errorMessage"` — Unhandled exceptions
- `"status\":4"` or `"status\":5"` — HTTP 4xx/5xx responses
- `"Traceback"` — Python exceptions

**Log retention:** CloudWatch logs are retained for 14 days (per 0010 privacy policy). Errors older than 14 days are lost.

### Phase 3: Categorize & Deduplicate

Group errors by root cause:

| Category | Pattern | Example |
|----------|---------|---------|
| **Timeout** | "Task timed out" | Cold start + Bedrock latency |
| **Validation** | "ValidationError" | Missing required field |
| **Bedrock** | "ThrottlingException", "ModelError" | Rate limit, model unavailable |
| **Auth** | "401", "403", "UnauthorizedException" | Token expired, WAF block |
| **JSON** | "JSONDecodeError" | Malformed request/response |
| **Other** | Anything else | Unknown |

**Deduplication:** Same stack trace + same error message = same root cause. Count occurrences but investigate once.

### Phase 4: Investigate & Remediate

For each unique error category:

#### 4.1 Investigate

1. Read relevant source files (lambda_function.py, guardrails/, etc.)
2. Trace the error path using stack trace
3. Identify root cause
4. Determine if fixable

#### 4.2 If Fixable

1. Create worktree:
   ```bash
   git -C /c/Users/mcwiz/Projects/Aletheia worktree add ../Aletheia-fix-{short-desc} -b fix-{short-desc}
   ```

2. Implement fix in worktree

3. Run tests:
   ```bash
   poetry run pytest /c/Users/mcwiz/Projects/Aletheia-fix-{short-desc}/tests/
   ```

4. If tests pass:
   - Stage changes
   - Create PR (do NOT merge)
   - Report as **FIXED (PR pending)**

5. If tests fail:
   - Treat as "Not Fixable"
   - Clean up worktree

#### 4.3 If Not Fixable

Draft an issue to `tmp/pending-issues/`:

```markdown
# tmp/pending-issues/lambda-failure-{timestamp}.md

## Title
[Concise description of the failure]

## Error Details
- **First seen:** [timestamp]
- **Occurrences:** [count]
- **Error type:** [category from Phase 3]
- **Stack trace:**
```
[truncated stack trace]
```

## Investigation Notes
[What was tried, why it couldn't be fixed automatically]

## Suggested Approach
[How a human might fix this]

## Related
- CloudWatch log group: /aws/lambda/AletheiaAgent
- Time range: [start] to [end]
```

Report as **PENDING ISSUE**.

### Phase 5: Generate Report

Create report at `tmp/audit-reports/0829-lambda-failures-{date}.md`:

```markdown
# Lambda Failure Remediation Audit - {date}

## Summary

| Metric | Value |
|--------|-------|
| Deployment timestamp | {DEPLOY_TIMESTAMP} |
| Errors since deploy | {total_count} |
| Unique root causes | {unique_count} |
| Fixed (PR pending) | {fixed_count} |
| Pending issues drafted | {pending_count} |

## Errors by Category

| Category | Count | Status |
|----------|-------|--------|
| Timeout | X | FIXED (PR #NNN) |
| Bedrock | Y | PENDING ISSUE |
| ... | ... | ... |

## PRs Created

- PR #NNN: Fix timeout in semantic guardrail
- PR #NNN: Handle malformed Bedrock response

## Pending Issues

- `tmp/pending-issues/lambda-failure-2026-01-10-001.md`: Bedrock throttling during peak hours
- `tmp/pending-issues/lambda-failure-2026-01-10-002.md`: JSON decode error on emoji input

## Next Actions

1. Review and merge PRs listed above
2. Review pending issues and file if appropriate
3. Monitor for recurrence after fixes deployed
```

---

## 4. Success Criteria

| Criterion | Requirement |
|-----------|-------------|
| All errors queried | Errors from DEPLOY_TIMESTAMP to now |
| All errors categorized | No "Unknown" without investigation |
| All errors actioned | Either FIXED or PENDING ISSUE |
| PRs tested | All PRs have passing tests before creation |
| Issues drafted | Unfixable errors have issue drafts |

---

## 5. Model Recommendation

| Model | Suitability | Rationale |
|-------|-------------|-----------|
| **Opus** | Recommended | Root cause analysis requires deep reasoning, fix implementation requires careful code changes |
| Sonnet | Acceptable | Can handle straightforward errors, may struggle with complex debugging |
| Haiku | Not recommended | Log parsing only, cannot implement fixes |

---

## 6. Integration with Cleanup

When running `/cleanup --full`:

1. Run this audit before session log
2. Include summary in cleanup report:
   ```
   Lambda Failures: X errors since deploy, Y fixed (PR pending), Z pending issues
   ```
3. Alert orchestrator if pending issues > 0

---

## 7. AWS CLI Reference

All commands require `MSYS_NO_PATHCONV=1` prefix on Windows.

### Get Lambda deployment timestamp
```bash
MSYS_NO_PATHCONV=1 aws lambda get-function --function-name AletheiaAgent --query 'Configuration.LastModified' --output text
```

### Convert ISO timestamp to epoch milliseconds
```bash
date -d "2026-01-10T12:00:00Z" +%s000
```

### Query errors since timestamp
```bash
MSYS_NO_PATHCONV=1 aws logs filter-log-events \
    --log-group-name /aws/lambda/AletheiaAgent \
    --start-time 1736510400000 \
    --filter-pattern "ERROR" \
    --query 'events[*].{time:timestamp,msg:message}' \
    --output table
```

### Get recent invocation errors
```bash
MSYS_NO_PATHCONV=1 aws logs tail /aws/lambda/AletheiaAgent --since 1h --filter-pattern "ERROR"
```

---

## 8. Audit Record

| Date | Auditor | Errors Found | Fixed | Pending | Issues Created |
|------|---------|--------------|-------|---------|----------------|
| 2026-01-10 | Claude Opus 4.5 | 1 | 1 (PR #301 merged) | 0 | 0 |

---

## 9. References

- [CloudWatch Logs Filter Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html)
- [Lambda Troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-invocation.html)
- docs/0812-audit-performance.md (latency targets)
- docs/0827-audit-infrastructure-integration.md (infrastructure health)
