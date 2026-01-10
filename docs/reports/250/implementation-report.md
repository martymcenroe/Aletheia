# Implementation Report: #250 - Audit Overdue Blocking in CI

## Summary

Added CI job to enforce audit schedule compliance. Audits that are overdue block PR merges.

## Problem

From Issue #250:
> No CI mechanism blocks work when audits are overdue. Quarterly audits can be indefinitely deferred.

Examples from 0800-audit-index.md:
- 0818 ISO 42001: marked quarterly, could be skipped indefinitely
- 0819 Supply Chain: marked quarterly, no enforcement

## Solution

Created `tools/audit_schedule_check.py` to parse audit records and enforce schedules:

### Schedule Thresholds

| Frequency | Block Threshold | Warning Threshold |
|-----------|-----------------|-------------------|
| Weekly | > 7 days overdue | > 5 days (75%) |
| Monthly | > 30 days overdue | > 22 days (75%) |
| Quarterly | > 90 days overdue | > 67 days (75%) |

### Audit Frequency Mapping

From 0800-audit-index.md Section 5.1:

| Frequency | Audits |
|-----------|--------|
| Weekly | 0816 |
| Monthly | 0811, 0815, 0817, 0821 |
| Quarterly | 0809, 0810, 0812, 0814, 0818, 0819, 0820, 0822, 0825, 0827, 0898, 0899 |
| Skip | Per PR (0813), On Event (0808, 0823, 0824) |

### Special Cases

- **New audits (no prior record):** Warning, not blocking. This allows new audit files to be merged without requiring retroactive execution.
- **Per PR audits:** Skipped (handled by CI lint jobs)
- **Event-triggered audits:** Skipped (run on specific events, not schedule)

## Changes

| File | Change |
|------|--------|
| `tools/audit_schedule_check.py` | New script (~200 lines) |
| `.github/workflows/ci.yml` | New `audit-schedule` job |

## Acceptance Criteria

- [x] CI job tracks last audit execution dates
- [x] Blocks merge if any quarterly audit > 90 days overdue
- [x] Blocks merge if any monthly audit > 30 days overdue
- [x] Warning at 75% threshold
