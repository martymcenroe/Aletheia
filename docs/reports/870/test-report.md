# Test Report — Issue #870 (with the code half of #869)

## Result

```
pytest -q                          →  961 passed, 3 skipped, 4 deselected   exit 0
ruff check src/ tests/ tools/...   →  All checks passed
mypy src/ --ignore-missing-imports →  Success: no issues found in 32 source files
bash -n provision.sh               →  ok (ShellCheck runs in CI; not installed locally)
```

Up from 934 at #835.

## New — `tests/unit/test_operator_retention.py`

- **Operator identification:** separators parse; unset means no operator;
  exact match only (a prefix, a suffix, a case change, `None` and `""` all fail).
- **`save_state`:** an operator row has `user_id` and no `ttl`. A non-operator
  authenticated row has no `user_id` and a `ttl` 30 days out. An anonymous row
  has no `user_id`. With the variable unset, nobody is attributed and
  `OPERATOR_USER_IDS_UNSET` is logged, without logging the ID itself.
- **Handler:** an authenticated operator is attributed. A body `userId` equal
  to the operator ID is **not**, whether the request is anonymous or signed in
  as someone else.
- **Cleanup script:** every writing mode, run for real (not a dry run) over rows
  built to trigger it, touches no retained row: operator rows that do have a
  `ttl`, and legacy rows with neither attribute. Each mode also has a **control
  row it must act on**, so a mode that silently did nothing cannot pass.
  `--normalize` never re-creates a retained row. The tool exits before scanning
  when SSM is unreadable or empty, and the choke point raises if the guard was
  never loaded.
- **Backfill:** only rows with neither attribute are selected; the write is
  conditional and sets `user_id` only; an ID that is not configured is refused;
  several configured IDs require a choice.

## Changed

- `tests/unit/test_lambda_auth.py`: the table fixture has no GSI, matching
  production. The old "deletes analysis records" test is replaced by one
  asserting erasure leaves the table untouched, and by a regression test for
  the production 500 (erasure succeeds against a table with no index).
- `tests/integration/`: the fixture table has no GSI. Tests 010, 020, 031, 033
  and 037 now assert the analysis rows **survive** while every account surface
  is still wiped. 037 pins the summary keys to exactly the four account
  surfaces. 041 and 042 exercise `save_state` against the table. 050 (a GSI
  query) is removed, and 060 now asserts the table has no GSI.

## Mutation testing

Four defects were reintroduced together:

| Probe | Caught by |
|---|---|
| `save_state` attributes any user, not only the operator | other-user and unconfigured `save_state` tests |
| handler falls back to `body["userId"]` | both body-spoof handler tests |
| cleanup choke point returns every row | all five cleanup-script guard tests |
| erasure queries `user_id-index` again | all erasure tests, including the 500 regression |

Result: `16 failed, 49 passed`. The probes were then reverted by exact edit,
not `git checkout` (the #835 near-miss), and a source scan confirmed no probe
remained: `grep -rn MUTATION-PROBE src/ tools/ tests/` matched only a stale
`.pyc`.

## Not covered

- **Nothing here touches AWS.** The live behaviour is verified after the deploy:
  a real operator analysis, the backfilled rows, and `data_hygiene.py --scan`.
- **`provision.sh` is not executed by any test.** The fail-fast on an empty SSM
  value is checked by reading, not by running it.
