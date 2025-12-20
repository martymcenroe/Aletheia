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

## Python & Testing

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-04 | Local python scripts don't auto-update if you paste into the wrong file. | **Always** verify file content (`cat file.py`) or use a diagnostic print to confirm code version. |
| 2025-12-05 | Tests must respect the *execution order* of validators. A "Fail Fast" check will mask downstream checks. | Assert the *first* failure reason in the chain, not just the existence of *a* failure. |

## Publishing & Compliance

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-09 | `<all_urls>` permission triggers multi-week manual review in Chrome Web Store. | Use `activeTab` for "Click-to-Run" privacy by default. |
| 2025-12-09 | Don't overengineer Privacy Policy hosting for store compliance. | A single `index.html` on GitHub Pages (`gh-pages` branch) is sufficient. |

## Workflow & Process

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-09 | Multi-user LLM accounts create auth friction and cost ($4/mo). | Adopt Single-User CLI model. Orchestrator commits all code. |

---

## Adding New Lessons

When something bites you, add it here immediately. Format:
```markdown
| YYYY-MM-DD | What happened / what I learned | The rule I now follow |
```

Resist the urge to categorize perfectly on first write — just capture it. Reorganize quarterly.

---

*Last updated: 2025-12-20*