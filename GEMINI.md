# Gemini Operational Protocols

## 2. Execution Rules
- **Authority:** `AgentOS:standards/0002-coding-standards` is the law for Git workflows.
- **One Step Per Turn:** Provide one distinct step, then wait for confirmation.
- **Check First:** Verify paths/content (`ls`, `cat`) before changing them.
- **Copy-Paste Ready:** No placeholders. Use `cat` heredocs for new files.

## 3. Session Logging
At session end, append a summary to the current week's file in `docs/session-logs/YYYY-MM-DD.md` (Monday date).
- **Week boundary:** Monday 3:00 AM CT to following Monday 2:59 AM CT
- **Format:** See `AgentOS:templates/0100-template-index` for the full entry template
- **Include:** date/time, model name (from handshake), summary, files, issues, state on exit
- **If file doesn't exist:** Create it with the header from the template guide
