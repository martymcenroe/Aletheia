# Pre-Launch Retrospective: February 2026

**Period:** 2026-02-15 to 2026-02-19
**Scope:** Authentication, billing, rate limiting, admin tooling, infrastructure

---

## What Went Well

### Rapid Feature Delivery
- 8 GitHub issues resolved in ~3 days (Issues #362-#369, #376, #378, #381, #383)
- Full auth stack: LinkedIn OAuth, JWT, rate limiting, Stripe billing, admin dashboards
- Each feature followed LLD-first workflow with implementation reports and test reports

### Testing Culture
- 975+ unit tests, all passing
- TDD pattern enforced: tests written before implementation on key features
- Pre-commit hooks catch regressions before push (ruff, mypy, gitleaks)

### Cost Discipline
- CloudFlare migration saved $7/month (Issue #349)
- Total auth infrastructure cost: ~$0.73/month
- DynamoDB PAY_PER_REQUEST means zero cost at zero traffic

---

## Lessons Learned

### Category: Environment & Tooling

**1. MSYS2 Bash on Windows Has Sharp Edges**
- `unset VAR` does not work — use `VAR=` to empty a variable
- `~` expansion is unreliable — always use absolute paths
- Path format differs by tool: Bash uses `/c/Users/...`, Read/Write/Edit use `C:\Users\...`
- `MSYS_NO_PATHCONV=1` required for AWS CLI commands with `/aws/lambda/...` paths
- **Action:** Documented in CLAUDE.md and MEMORY.md for all future sessions

**2. OneDrive Files On-Demand Is a Landmine**
- Traversing `C:\Users\<user>\` triggers massive automatic downloads from OneDrive
- File search tools can accidentally hit OneDrive-synced directories
- **Action:** Added "Dangerous Paths" section to CLAUDE.md with explicit warnings

**3. Nested Claude CLI Sessions Require `CLAUDECODE=`**
- Setting `CLAUDECODE=` (empty string) is required for AssemblyZero workflows that spawn nested Claude sessions
- `unset CLAUDECODE` does not work in MSYS2 (see lesson #1)
- **Action:** Documented in CLAUDE.md workflow instructions

### Category: Python & Lambda Packaging

**4. `PYTHONUNBUFFERED=1` Is Required for Background Runs**
- Python buffers stdout when not connected to a TTY
- Background `poetry run` commands produce zero output without this flag
- **Action:** Added to all workflow command examples in CLAUDE.md

**5. Lambda Requires `src/` Package Structure**
- Both Lambdas (Analysis + Auth) must be packaged as `zip -rq lambda.zip src/`
- Auth Lambda imports from `src/auth/` subpackage (`jwt_service`, `token_cap_service`, etc.)
- Changing to flat file deployment would break all relative imports
- **Action:** Documented in provision.sh comments

**6. Lambda Layer Size Management**
- Cherry-pick strategy: install only runtime deps, not full `poetry export`
- Remove `__pycache__`, `*.dist-info`, `tests/` from layer to reduce size
- Adding `stripe` SDK increased layer but stayed well within 250MB limit
- **Action:** Provisioning script handles cleanup automatically

### Category: Workflow & Process

**7. AssemblyZero SQLite Deadlock (Bug #379)**
- Implementation workflow uses shared SQLite database at `~/.assemblyzero/testing_workflow.db`
- Concurrent agents on different repos deadlock each other
- `ASSEMBLYZERO_WORKFLOW_DB` env var exists but doesn't propagate through `poetry run --directory`
- **Workaround:** Use `--no-worktree` flag and run workflows sequentially
- **Fix:** Each issue now gets its own SQLite DB (merged in AssemblyZero)

**8. Test Plan Validator Format Sensitivity (Bug #382)**
- Multi-ref format `(Req 1, Req 2)` in test plan table breaks validation
- Must put `(Req N)` on individual Scenario rows only
- **Action:** Documented in CLAUDE.md workflow gotchas

**9. Pre-Commit Hook Sequencing Matters**
- Order: trim whitespace → fix EOF → check yaml/json → large files → detect secrets → ruff → mypy → gitleaks → project policy → pre-merge gate → audit compliance
- Ruff must run before mypy (formatting affects type analysis)
- gitleaks (detect-secrets) catches hardcoded API keys — critical for a project storing AWS credentials
- **Action:** Hook order maintained in `.pre-commit-config.yaml`

### Category: Infrastructure & Security

**10. IAM Resource ARNs Need `/index/*` Suffix for GSIs**
- DynamoDB table ARN alone (`arn:aws:dynamodb:*:*:table/my-table`) does not grant GSI access
- Must add `arn:aws:dynamodb:*:*:table/my-table/index/*` explicitly
- Symptom: `AccessDeniedException` on any GSI Query operation
- **Action:** Fixed in provision.sh for both agent state table and users table (Issue #378)

**11. Secrets Manager Permissions Must List Each Secret**
- IAM policy must include ARN for every secret the Lambda reads
- Adding Stripe handler without adding Stripe secret ARNs causes runtime 500 errors
- Symptom: `AccessDeniedException` in CloudWatch logs, generic 500 to client
- **Action:** Fixed in provision.sh (Issue #383); checklist added to deployment runbook

**12. DynamoDB TTL Attribute Must Match Existing Data**
- TTL attribute name in `update-time-to-live` must match the attribute already present in items
- Coupons table uses `expiry` (not `ttl`) — using wrong attribute name causes silent non-deletion
- Items with `expiry = 0` are unaffected (DynamoDB ignores epoch-0 or far-future values)
- **Action:** Documented in provision.sh comments (Issue #381)

---

## Bugs Filed Against AssemblyZero

| Bug | Title | Status |
|-----|-------|--------|
| #379 | SQLite deadlock in implementation workflow | Fixed |
| #380 | Workflow execution catalog missing | Open |
| #382 | Test plan validator multi-ref parsing | Open |
| #389 | Drafter path-guessing bug | Open |
| #390-#394 | 5 bugs from first implementation spec run (#364) | Various |
| #395 | Missing Anthropic API provider | Open |

---

## Metrics

| Metric | Value |
|--------|-------|
| Issues resolved | 12 (across 3 sessions) |
| Unit tests added | ~400+ |
| Total test count | 975+ |
| PRs merged | 10+ |
| AssemblyZero bugs filed | 9 |
| Cost saved | $7/month (CloudFlare migration) |
| Auth infrastructure cost | ~$0.73/month |

---

## Recommendations for Future Sessions

1. **Run workflows sequentially** until AssemblyZero SQLite fix propagates
2. **Always check IAM permissions** when adding new Secrets Manager secrets or DynamoDB GSIs
3. **Test Lambda locally** with `sam local invoke` before deploying (not yet set up — future improvement)
4. **Add integration tests** for auth flow end-to-end (currently unit-tested only)
5. **Set up CloudWatch alarms** for Stripe webhook failures once billing goes live
