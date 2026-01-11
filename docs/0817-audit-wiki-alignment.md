# 0817 - Audit: Wiki Alignment

## 1. Purpose

Ensure GitHub Wiki pages accurately reflect the current project state, features, architecture, and policies. Wiki drift from reality confuses users and creates liability.

**Wiki URL:** https://github.com/martymcenroe/Aletheia/wiki

---

## 2. Trigger Conditions

| Trigger | Context |
|---------|---------|
| **Session Closeout** | Part of 0009 Full Mode |
| **After Feature Changes** | When user-facing behavior changes |
| **After Policy Changes** | Privacy, security, or terms updates |
| **Monthly** | Regular alignment check |

---

## 3. Wiki Pages Inventory

| Page | Primary Concern | Check Against |
|------|-----------------|---------------|
| Home | Project status, features | README.md, current milestones |
| Getting-Started | Installation steps | Extension manifests, store listings |
| User-Guide | Usage instructions | Current UI behavior |
| FAQ | Answers accuracy | Current implementation |
| Architecture | System design | 0001-architecture.md (and 0001a-g), actual code |
| Developer-Guide | Setup instructions | pyproject.toml, package.json |
| API-Reference | Endpoints, formats | Lambda handler, actual API |
| Terms-of-Use | Content restrictions | content-safety.js behavior |
| Privacy | Data handling | Actual storage, retention policy |
| Security | Security measures | Current security implementation |
| Contributing | Contribution process | CONTRIBUTING.md, PR templates |

---

## 4. Audit Checklist

### 4.0 Wiki Availability (CRITICAL)

**Run this check FIRST before any content audit.**

```bash
# Clone wiki fresh - this reveals HEAD/branch issues
rm -rf /tmp/wiki-test && git clone https://github.com/martymcenroe/Aletheia.wiki.git /tmp/wiki-test 2>&1

# Check for "nonexistent ref" warning (indicates broken HEAD)
# If clone shows empty directory or "unable to checkout" - wiki is broken

# Verify files exist
ls /tmp/wiki-test/*.md | wc -l  # Should be 11+
```

| Check | Command | Expected | Status |
|-------|---------|----------|--------|
| Wiki clones successfully | `git clone ... 2>&1` | No "nonexistent ref" warning | ☐ |
| Home.md exists | `ls /tmp/wiki-test/Home.md` | File exists | ☐ |
| All pages present | `ls /tmp/wiki-test/*.md \| wc -l` | 11+ files | ☐ |
| Web accessible | Visit wiki URL | Pages render | ☐ |

**If availability fails:** The wiki remote HEAD may be pointing to a nonexistent branch. GitHub wikis require `master` branch. Fix with: `git push origin main:master`

---

### 4.1 Privacy Accuracy (CRITICAL)

| Check | Verify Against | Status |
|-------|----------------|--------|
| Data stored matches reality | DynamoDB schema, Lambda code | ☐ |
| Retention periods accurate | TTL config, anonymization code | ☐ |
| GDPR process current | Issue #147 status | ☐ |
| Third-party services listed | Actual AWS services used | ☐ |

### 4.2 Feature Accuracy

| Check | Verify Against | Status |
|-------|----------------|--------|
| Features list current | Actual extension capabilities | ☐ |
| "Coming soon" items updated | Completed features | ☐ |
| Browser support accurate | Manifest versions, test results | ☐ |
| Store status current | Actual submission status | ☐ |

### 4.3 Technical Accuracy

| Check | Verify Against | Status |
|-------|----------------|--------|
| Architecture diagram current | 0001, actual infrastructure | ☐ |
| API endpoints documented | Lambda handler routes | ☐ |
| Dependencies current | pyproject.toml, package.json | ☐ |
| Setup instructions work | Fresh install test | ☐ |

### 4.4 Policy Accuracy

| Check | Verify Against | Status |
|-------|----------------|--------|
| Terms of Use current | content-safety.js, ADRs | ☐ |
| Security measures listed | Actual implementation | ☐ |
| Content restrictions accurate | RTA detection code | ☐ |

---

## 5. Procedure

```bash
# 5.1 Clone wiki locally (if not already)
cd /c/Users/mcwiz/Projects
git clone https://github.com/martymcenroe/Aletheia.wiki.git Aletheia-wiki 2>/dev/null || cd Aletheia-wiki && git pull

# 5.2 Review each page against source of truth
# Use checklist above

# 5.3 Update any stale content
# Edit .md files in Aletheia-wiki/

# 5.4 Commit and push updates
cd Aletheia-wiki
git add -A
git commit -m "docs: wiki alignment audit updates"
git push origin master
```

---

## 6. Common Drift Patterns

| Pattern | Example | Prevention |
|---------|---------|------------|
| Privacy policy drift | "In-memory only" when actually stored | Update wiki when storage changes |
| Feature status stale | "Coming soon" for shipped features | Update on release |
| Architecture outdated | Old diagrams after refactoring | Update with ADR changes |
| Links broken | Renamed/moved docs | Check links during audit |

---

## 7. Integration Points

| Protocol | Integration |
|----------|-------------|
| **0009 Full Mode** | Add wiki review step |
| **Feature releases** | Update relevant wiki pages |
| **Privacy changes** | Immediate Privacy.md update |
| **Issue closeout** | Check if wiki update needed |

---

## 8. Audit Record

| Date | Auditor | Pages Updated | Issues Found |
|------|---------|---------------|--------------|
| 2026-01-06 | Claude Opus 4.5 | All pages (timestamps added) | Wiki was BLANK - remote HEAD pointed to nonexistent branch. Fixed by pushing `master` branch. Added §4.0 availability check. |
| 2026-01-04 | Claude Opus 4.5 | Privacy, FAQ, Architecture, Security, Terms-of-Use (new) | Privacy was inaccurate (said in-memory only) |

---

## 9. History

| Date | Change |
|------|--------|
| 2026-01-06 | Added §4.0 Wiki Availability check after wiki went blank due to missing `master` branch. |
| 2026-01-04 | Created. Triggered by privacy page inaccuracy discovery. |
