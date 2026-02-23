# Incident Retrospective Template

> Copy this template to `docs/retrospectives/YYYY-MM-DD-short-name.md` and fill it in.

---

# Incident: [SHORT TITLE]

**Date:** YYYY-MM-DD
**Severity:** [S1 Total Outage / S2 Partial Outage / S3 Degraded / S4 Near-Miss]
**Duration:** [detection → resolution]

## Timeline

| Time (CT) | Event |
|-----------|-------|
| HH:MM | [Trigger / first symptom] |
| HH:MM | [Detection — how was it noticed?] |
| HH:MM | [Mitigation — what stopped the bleeding?] |
| HH:MM | [Resolution — root cause fixed and verified] |

## Impact

- **Who:** [which users / endpoints / features]
- **Duration:** [how long were they affected]
- **Scope:** [% of requests, traffic, etc.]

## Root Cause (5 Whys)

1. **Why** did [symptom]? — Because [X].
2. **Why** did [X]? — Because [Y].
3. **Why** did [Y]? — Because [Z].
4. **Why** did [Z]? — Because [A].
5. **Why** did [A]? — Because [root cause].

## Evidence

- `file:line` references
- Log snippets
- curl output / screenshots

## Action Items

| Issue | Description | Status |
|-------|-------------|--------|
| #NNN | [action] | Open / Closed |

## Lessons Learned

### What went well
- [X]

### What didn't go well
- [X]

### What to change
- [X]
