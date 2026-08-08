# Implementation Report — Issue #817

## Problem

`tests/unit/test_signal_inspector.py::TestLiveWebsites` fetches real websites
and asserts against their **current** robots.txt. One case
(`test_noarchive_net_blocked_without_force`) fails on a clean checkout of
`main` because the third-party site's policy appears to have changed:

```
AssertionError: assert <FetchStatus.SUCCESS> == <FetchStatus.ROBOTS_BLOCKED>
```

A suite that is red for reasons outside this repository stops being a signal.
Every developer must first work out which failures are theirs — the same tax a
permanently-red suite always imposes, and one that was paid twice while landing
the session-renewal work.

## What was already true

The class was **already** marked `@pytest.mark.live` (line 399), the `live`
marker was **already** declared in `pyproject.toml`, and the class docstring
**already** said:

> Run with: `poetry run pytest -v -m live`

Nothing enforced any of that. A declared marker does not exclude anything by
itself, so the live tests ran on every default invocation despite the stated
intent that they be opt-in.

The original issue proposed replacing the live calls with recorded fixtures.
That turned out to be unnecessary: the intended design was already in the tree
and simply had no mechanism behind it. Adding fixtures would have discarded a
genuine end-to-end check that still has value when run deliberately.

## Change

One line in `[tool.pytest.ini_options]`:

```toml
addopts = "-m 'not live'"
```

Live tests are now opt-in via `poetry run pytest -m live`, exactly as the class
docstring always said.

## Why CI is deliberately unaffected

CI runs `pytest tests/ -v -m "not audit"`. A `-m` given on the command line
overrides one supplied through `addopts` (later occurrence wins), so **CI still
runs the live tests**. That is intentional:

- The failure is environment-specific — these pass in GitHub Actions and fail
  from the operator's network, so CI genuinely does exercise the real-world
  check.
- Excluding them from CI as well would need an edit to `.github/workflows/`,
  which the fine-grained PAT cannot push (it deliberately lacks `workflow`
  scope). That would require the gpg-gated classic-PAT path and a human
  passphrase.

So the split is: the local suite is a clean signal again, and CI keeps the
real-world coverage. If the live checks later become flaky in CI too, that is a
separate decision and a separate change.

## Verification performed

| Command | Result |
|---|---|
| `pytest tests/unit -q` | `879 passed, 4 deselected` — green |
| `pytest tests/unit -q -m "not audit"` (CI's form) | live tests still run; the known failure appears |
| `pytest tests/unit -q -m live` | `1 failed, 3 passed, 879 deselected` — opt-in works |
| `ruff check src/ tests/` | clean |

The middle row is the important one: it proves CI behavior is unchanged rather
than assumed.

## Blast radius

Test configuration only. No production code path.

The real risk is that a default run now covers slightly less than before. That
is the intended trade, and it is bounded: the same four tests still execute in
CI on every push.

## Rollback

`git revert <sha>`. No deploy dependency.
