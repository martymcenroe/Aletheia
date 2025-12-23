# 0103 - Template: Implementation Report

## Usage
After completing implementation of a feature, create a report in `docs/reports/` named `{IssueID}-implementation-report.md`.

This captures what was actually built, enabling future reference and audit.

---

## Template

```markdown
# {IssueID} - Implementation Report: {Feature Title}

## Metadata
* **Issue:** #{IssueID}
* **LLD:** `docs/1{IssueID}-{feature-name}.md`
* **Implementer:** {Model Name} via {Interface}
* **Date:** {YYYY-MM-DD}
* **Branch:** {branch-name}

## Files Created

| File | Size | Description |
|:-----|:-----|:------------|
| `path/to/file.js` | X.X KB | {What it does} |

## Files Modified

| File | Changes | Description |
|:-----|:--------|:------------|
| `path/to/file.js` | +XX lines | {What changed} |

## Implementation Details

### {Component 1}
- {Specific implementation detail}
- {Line numbers if helpful}

### {Component 2}
- {Specific implementation detail}

## Security Compliance

*Reference ADRs and coding standards that were followed.*

- [ ] {Security requirement from LLD} — {How it was met}
- [ ] {Security requirement} — {How it was met}

## Ready for Testing

{Brief statement of readiness and pointer to smoke test in LLD}

1. {Key test area}
2. {Key test area}
```

---

## Tips for Good Reports

1. **Be specific:** Include file sizes, line counts, line numbers where helpful
2. **Reference the LLD:** Link to the design doc for context
3. **Security checklist:** Explicitly confirm each security requirement was met
4. **Keep it factual:** This is a record, not a narrative
