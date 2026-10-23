# Test Report: #926

| AC | Check | Result |
|---|---|---|
| AC1 | `grep -n 'Pending upload'` | Names `1.1.3` |
| AC2 | `grep -n 'On your own\|On this site'` | Both in §6 step 3; `On your own` in §15 step 5 |
| AC3 | Read §15 | All 13 steps name a path, URL or agent action; operator steps carry a success sign and a failure path |
| AC4 | `git diff` of §11j and §11l | Only warning paragraphs added; paste-ready blocks byte-identical |
| AC5 | Read §11.smoke-test | Sign-in (2), enable site (3), core flow (4), restart (5), in that order |
| AC6 | Read §16 | Four new rows present, and the "Version already exists" row names the unlisted cause |
| AC7 | `grep -n '^# [0-9]'` and every `§N` in the body | Headings 11 to 18 in order. Every body reference resolves; the matches below the 2.1.0 change-log row are historical and unchanged |
| AC8 | `grep -n '10907' docs/runbooks/10905-runbook-cws-publish.md` | Reads §13 |
| AC9 | Header and change log | 2.1.0 in both |
| AC10 | `poetry run pytest -q` in the worktree, 2026-10-23 | 961 passed, 3 skipped, 4 deselected (the opt-in `live` tests) |

No test file reads either runbook. The one `tests/` match for `runbooks` is `tests/unit/test_metrics_emf.py`, which reads a CloudWatch JSON file under `docs/runbooks/`, not a runbook.
