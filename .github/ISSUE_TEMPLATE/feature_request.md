---
name: Feature Request
about: Suggest a new feature or enhancement
title: 'feat: '
labels: enhancement
assignees: ''
---

## Summary

A clear description of what you want to happen.

## Motivation

Why is this feature needed? What problem does it solve?

## Proposed Solution

Describe your proposed implementation approach.

## Definition of Done

### Implementation
- [ ] Core feature implemented
- [ ] Unit tests written and passing
- [ ] Integration tests if applicable

### Tools
- [ ] Update/create relevant CLI tools in `tools/`
- [ ] Document tool usage

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Update README.md if user-facing
- [ ] Update relevant ADRs or create new ones
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS (if security-relevant)
- [ ] Run 0810 Privacy Audit - PASS (if privacy-relevant)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Additional Context

Add any other context, screenshots, or references here.
