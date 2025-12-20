# Lessons Learned

Project-specific lessons for Aletheia (Bedrock, guardrails, semantic validation) are documented inline in ADRs and code comments.

For cross-cutting engineering lessons (Git workflow, AWS deployment, GitHub hygiene, testing philosophy), see my **[Engineering Journal](https://github.com/martymcenroe/martymcenroe/blob/main/ENGINEERING-JOURNAL.md)**.
| 2025-12-20 | Windows Python lacks IANA timezones; `zoneinfo` fails. | **Dependency:** Always add \`tzdata\` to Poetry on Windows. |
| 2025-12-20 | Logs are unreadable in UTC/ISO8601. | **Standard:** Display all timestamps in **America/Chicago** using \`%b %d %H:%M\` format. |
