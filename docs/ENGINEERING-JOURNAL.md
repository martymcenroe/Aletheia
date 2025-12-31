# Engineering Journal

> "Experts recognize, Beginners reason" — but experts became experts by documenting what they learned.

This is my running log of hard-won lessons, gotchas, and rules I've established through building. Updated continuously.

---

## Git & GitHub

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-08 | Branching from a stale `main` causes files created *after* that point to vanish from the workspace. | **Always** `git checkout main && git pull` before creating a new branch. |
| 2025-12-08 | Squash merge creates new commit SHA on main; original branch commits still exist but aren't "merged" by SHA comparison. `git log main..branch` shows commits even after merge. | Use `git merge-base --is-ancestor <merge-commit> main` to verify squash-merged work is in main. Ignore "not fully merged" warning if PR merged; use `git branch -D` for cleanup. |
| 2025-12-11 | The first branch pushed becomes default; cannot PR branch into itself. | Initialize and push `main` upstream before creating feature branches. |
| 2025-12-16 | Merged branches accumulate as effluvium without explicit cleanup. | Enable `delete_branch_on_merge` on all repos. |
| 2025-12-17 | Claude Code works fine in Git Bash on Windows as of v2.0.71. | Test compatibility yourself before trusting outdated articles. |
| 2025-12-20 | `git branch -r` shows cached remote refs, not live GitHub state. After `delete_branch_on_merge` triggers, local still shows "zombie" branches. | Run `git fetch --prune` before any branch audit. |
| 2025-12-20 | Branches are pointers, not history. Deleting a merged branch loses nothing — work is preserved in merge commits and PR history. | Delete merged branches confidently; recover via PR page or `git reflog` if needed. |
| 2025-12-20 | `git stash` saves uncommitted changes; `git stash pop` restores them. Useful when you edit on wrong branch. | Stash before switching branches if you have uncommitted work in the wrong place. |
| 2025-12-20 | Windows Git converts symlinks to regular files by default (copies content instead of preserving link). True symlinks require Developer Mode + Admin + `core.symlinks=true`. | Use `sync-journal` bash function to manually copy cross-repo files. Mac can use real symlinks. |

## GitHub CLI (`gh`)

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-04 | `gh issue close` strictly accepts only 1 argument. | Use bash loops for bulk ops: `for id in x y; do gh issue close $id; done` |
| 2025-12-16 | Bulk repo settings changes require loops + `gh api --method PATCH`. | Use `--input -` with heredoc for nested JSON payloads. |
| 2025-12-20 | `gh pr list --state closed --json mergedAt,mergeCommit` reveals whether PRs were actually merged vs. just closed. | Use this to audit if branch work reached main before deleting. |

## GitHub Security & Settings

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-16 | Secret scanning is free for public repos only; private repos require GitHub Advanced Security (paid). | Don't chase "n/a" on private repos — it's a pricing wall, not a config issue. |
| 2025-12-16 | Dependabot security updates are disabled by default on all repos. | Enable via `gh api repos/OWNER/REPO/vulnerability-alerts --method PUT` |

## AWS & Lambda

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-04 | Pip on Windows installs `.pyd` binaries; Lambda needs Linux `.so`. | **Always** use `deploy.sh` with `--platform manylinux2014_x86_64` (or `manylinux_2_28` for AL2023). |
| 2025-12-04 | `awslambda` (streaming) is strictly incompatible with standard handlers. | Use standard JSON buffering for MVP. Revisit streaming only if latency demands it. |
| 2025-12-08 | Console access requires `iam:CreateLoginProfile` and is separate from CLI keys. | If Console access is disabled, use `aws iam create-login-profile` from an Admin CLI profile. |
| 2025-12-24 | Lambda concurrency=0 is instant kill switch. Use for cost control ("Denial of Wallet" defense). | Create on/off/status scripts in `tools/aws/`. Run off script at end of every session. |

## Python & Testing

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-04 | Local python scripts don't auto-update if you paste into the wrong file. | **Always** verify file content (`cat file.py`) or use a diagnostic print to confirm code version. |
| 2025-12-05 | Tests must respect the *execution order* of validators. A "Fail Fast" check will mask downstream checks. | Assert the *first* failure reason in the chain, not just the existence of *a* failure. |
| 2025-12-20 | Windows Python lacks IANA timezones; `zoneinfo` fails without `tzdata`. | **Dependency:** Always add `tzdata` to Poetry on Windows projects. |
| 2025-12-20 | Logs in UTC/ISO8601 are unreadable for humans. | **Standard:** Display timestamps in `America/Chicago` using `%b %d %H:%M` format. |
| 2025-12-22 | PIL transparency threshold is R+G+B sum (0-765). Low values (30) leave anti-aliasing artifacts; 250 worked for clean edges. | Use `--threshold 250` for icon generation with black-to-transparent conversion. |
| 2025-12-28 | Windows Print Spooler removes jobs that complete quickly, causing error 87 when polling. | Treat error 87 as "job completed successfully" in spooler monitoring code. |
| 2025-12-28 | SumatraPDF command-line printing doesn't use printer defaults. | Always specify `-print-settings duplex` or `-print-settings simplex` explicitly. |

---

## Publishing & Compliance

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-09 | `<all_urls>` permission triggers multi-week manual review in Chrome Web Store. | Use `activeTab` for "Click-to-Run" privacy by default. |
| 2025-12-09 | Don't overengineer Privacy Policy hosting for store compliance. | A single `index.html` on GitHub Pages (`gh-pages` branch) is sufficient. |

## Workflow & Process

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-09 | Multi-user LLM accounts create auth friction and cost ($4/mo). | Adopt Single-User CLI model. Orchestrator commits all code. |
| 2025-12-22 | Windows Explorer caches file metadata. Files show old timestamps even after modification. | Trust ls -la in terminal, not Explorer's Date column. |
| 2025-12-28 | Visual debugging (bright magenta backgrounds, large text) is more effective than console.log for injected scripts. If you can't see debug output, the code isn't running. | When debugging injected content, make changes SO obvious they can't be missed. Proves whether code executes at all. |
| 2025-12-28 | Test scripts for long breaks need: environment setup, verification steps, expected outputs, "where you left off" summary. | Design test docs for "cold start"—assume reader has zero context. Include absolute paths and verification commands. |
| 2025-12-29 | Implementation friction signals architectural misalignment. Deployment pain wasn't a bug—it was feedback that LangGraph/LangChain solved problems Aletheia didn't have. | When deployment is painful, question whether the architecture matches requirements. Simplify before debugging. |
| 2025-12-31 | Willison Protocol: "Your job is to deliver code you have proven to work." Tests must fail on revert (not "green by default"). | Capture proof artifacts (screenshots, logs). If you can't prove it works, you haven't finished. |

---

## Adding New Lessons

When something bites you, add it here immediately. Format:
```markdown
| YYYY-MM-DD | What happened / what I learned | The rule I now follow |
```

Resist the urge to categorize perfectly on first write — just capture it. Reorganize quarterly.

---


