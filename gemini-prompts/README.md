# Gemini Prompts Library

This directory contains standardized prompts for Gemini CLI reviews in the dual-review automation system.

## Purpose

These prompts ensure consistent, high-quality reviews from Gemini 3 Pro across three workflow phases:
1. **LLD Review** - Design review before implementation
2. **Implementation Review** - Code review after implementation
3. **Issue Filing** - Issue completeness check before filing
4. **Session Logging** - Session summary generation

## Template Format

All prompts use `{{PLACEHOLDER}}` syntax for variable replacement:

```
CRITICAL INSTRUCTIONS:
...

INPUT TO REVIEW:
{{VARIABLE_NAME}}

OUTPUT FORMAT:
...
```

## Versioning

Prompts are versioned in git for audit trail:
- Each change = new commit
- Commit message format: `prompts: update {prompt-name} - {reason}`
- Example: `prompts: update lld-review.txt - add security focus`

## Usage

Prompts are loaded and populated by Claude during workflow execution:

```python
# Load prompt template
prompt = read_file("gemini-prompts/lld-review.txt")

# Replace placeholders
prompt = prompt.replace("{{LLD_CONTENT}}", lld_content)
prompt = prompt.replace("{{LLD_PATH}}", lld_path)

# Invoke Gemini with model check
result = invoke_gemini_with_model_check(prompt, "gemini-3-pro-preview")
```

## Files

| File | Purpose | Variables |
|------|---------|-----------|
| `lld-review.txt` | LLD design review | `{{LLD_PATH}}`, `{{LLD_CONTENT}}` |
| `implementation-review.txt` | Implementation code review | `{{ISSUE_ID}}`, `{{IMPL_REPORT}}`, `{{TEST_REPORT}}`, `{{FILE_DIFFS}}` |
| `issue-review.txt` | Issue completeness check | `{{ISSUE_DRAFT}}` |
| `session-log.txt` | Session summary generation | `{{GIT_STATUS}}`, `{{RECENT_COMMITS}}`, `{{OPEN_PRS}}`, `{{CLEANUP_MODE}}`, `{{TODAY}}`, `{{TIMESTAMP}}` |

## Output Format

All prompts use the three-tier priority system:

```markdown
## [BLOCKING] Issues
- Must fix before proceeding

## [HIGH] Priority Issues
- Should fix before proceeding

## [SUGGESTION] Improvements
- Nice to have

## Summary
Overall assessment
```

## Best Practices

1. **Be Specific:** Prompts should reference exact documentation (e.g., "Follow docs/0601-skill-gemini-lld-review.md")
2. **Set Boundaries:** Explicitly tell Gemini NOT to offer implementation or code snippets
3. **Format Enforcement:** Require specific output markers like `[BLOCKING]`, `[HIGH]`, `[SUGGESTION]`
4. **Context Loading:** Include references to templates and standards (e.g., "Check completeness per docs/0101-TEMPLATE-issue.md")

## Maintenance

Review and update prompts quarterly or when:
- New security concerns emerge
- Workflow changes
- Gemini model behavior changes
- User feedback suggests improvements

---

**Last Updated:** 2026-01-09
**Status:** Active
**Related:** docs/0602-skill-gemini-dual-review.md (Issue #222)
