# Gemini Operational Protocols

## 1. Session Initialization (The Handshake)
**CRITICAL:** When a session begins via `docs/GUIDE.md`:
1.  **Analyze:** Silently parse the provided `git status` or issue context.
2.  **Halt & Ask:** Your **FIRST** output must be exactly:
    > "ACK. State determination complete. Please identify my model version."
3.  **Wait:** Do not proceed until the user replies (e.g., "3.0 Pro").
4.  **Update Identity:** Incorporate the version into your Metadata Tag (e.g., `[Gemini 3.0 Pro...]`) for all future turns.

## 2. Execution Rules
- **Authority:** `docs/0002-coding-standards.md` is the law for Git workflows.
- **One Step Per Turn:** Provide one distinct step, then wait for confirmation.
- **Check First:** Verify paths/content (`ls`, `cat`) before changing them.
- **Copy-Paste Ready:** No placeholders. Use `cat` heredocs for new files.

## 3. Session Logging
At session end, append a summary to the current week's file in `docs/session-logs/YYYY-MM-DD.md` (Monday date).
- **Week boundary:** Monday 3:00 AM CT to following Monday 2:59 AM CT
- **Format:** See `docs/0100-TEMPLATE-GUIDE.md` for the full entry template
- **Include:** date/time, model name (from handshake), summary, files, issues, state on exit
- **If file doesn't exist:** Create it with the header from the template guide
