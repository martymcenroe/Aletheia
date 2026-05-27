# 0900 - Operational Runbooks Index

## Purpose

Quick reference for the orchestrator (Marty) on how to run tools, commands, agents, audits, and prompts. Runbooks are "how to run X" documents, distinct from audits (what to check) and standards (what rules to follow).

**Supersedes:** `0008-orchestrator-instructions.md` (deprecated)

## Runbook Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Audit Runbooks** | How to invoke audits (ultrathink, model selection) | 0901 |
| **Incident Runbooks** | How to respond to cost, security, or availability incidents | 10902 |
| **Skill Runbooks** | How to use /cleanup, /onboard, /audit, etc. | (TBD) |
| **Agent Runbooks** | How to invoke custom agents | (TBD) |
| **Prompt Runbooks** | Standard prompts for common tasks | (TBD) |

## Runbook Index

| ID | Runbook | Trigger | Frequency | Model |
|----|---------|---------|-----------|-------|
| 0901 | [Nightly AgentOS Audit](AgentOS:runbooks/AgentOS:runbooks/0901-nightly-agentos-audit-audit) | PowerShell | Nightly | Opus + ultrathink |
| 10902 | [Cost Incident Response](10902-runbook-cost-incident-response.md) | Budget alert email, kill switch activation, or suspected attack | As needed | N/A (manual CLI) |
| 10903 | [Lambda Configuration Change](10903-runbook-lambda-config-change.md) | Any `update-function-configuration` call | Every config change | N/A (manual CLI) |
| 10904 | [Admin Dashboard](10904-runbook-admin-dashboard.md) | Access business metrics dashboard | As needed | N/A (browser) |
| 10905 | [Extension Store Publishing](10905-runbook-extension-store-publish.md) | Chrome/Firefox extension version release | Each release | N/A (manual upload) |
| 10906 | [CWS / AMO Image Padding](10906-runbook-cws-image-pad.md) | Producing store-listing screenshots from a source image | Each new image | N/A (Pillow) |

## Model Selection Guide

When running audits or tasks, use the appropriate model to balance cost and capability:

| Model | Cost | Use When |
|-------|------|----------|
| **Opus** | $$$ | Complex reasoning, architecture decisions, ultrathink mode |
| **Sonnet** | $$ | Standard development work, web research, documentation |
| **Haiku** | $ | Simple automation, metric aggregation, file inventory |

See `AgentOS:audits/AgentOS:audits/0800-audit-index` for per-audit model recommendations.

## Ultrathink Mode

"Ultrathink" is the term we use to invoke extended thinking. This is done via PowerShell by the orchestrator and provides deeper analysis for complex audits.

**When to use ultrathink:**
- Nightly AgentOS self-audits
- Architecture reviews
- Conflict detection across documents
- Any task requiring multi-step reasoning

**Invocation:** See individual runbooks for specific commands.

## Related Documents

- `CLAUDE.md` - Agent operating procedures
- `docs/0000-GUIDE.md` - AgentOS overview and filing system
- `AgentOS:audits/AgentOS:audits/0800-audit-index` - Audit index and procedures
- `docs/0008-orchestrator-instructions.md` - (Deprecated, see this index)
