# 0814 - Audit: License Compliance

## 1. Purpose

Ensure all dependencies use licenses compatible with Aletheia's MIT license and distribution model.

**Aletheia License:** MIT (permissive, commercial-friendly)

---

## 2. License Compatibility Matrix

### Compatible Licenses (Green)

| License | Compatible? | Notes |
|---------|-------------|-------|
| MIT | ✅ Yes | Same as ours |
| BSD-2-Clause | ✅ Yes | Permissive |
| BSD-3-Clause | ✅ Yes | Permissive |
| Apache-2.0 | ✅ Yes | Permissive (attribution required) |
| ISC | ✅ Yes | Permissive |
| CC0 | ✅ Yes | Public domain |
| Unlicense | ✅ Yes | Public domain |

### Conditional Licenses (Yellow)

| License | Compatible? | Notes |
|---------|-------------|-------|
| LGPL-2.1 | ⚠️ Conditional | OK if dynamically linked |
| LGPL-3.0 | ⚠️ Conditional | OK if dynamically linked |
| MPL-2.0 | ⚠️ Conditional | File-level copyleft |

### Incompatible Licenses (Red)

| License | Compatible? | Notes |
|---------|-------------|-------|
| GPL-2.0 | ❌ No | Strong copyleft |
| GPL-3.0 | ❌ No | Strong copyleft |
| AGPL-3.0 | ❌ No | Network copyleft |
| SSPL | ❌ No | Not OSI approved |
| Proprietary | ❌ No | Requires separate license |

---

## 3. Python Dependencies Audit

### Command

```bash
poetry show --tree | head -50
pip-licenses --format=markdown  # if installed
```

### Dependency Check

| Package | License | Status |
|---------|---------|--------|
| boto3 | Apache-2.0 | |
| botocore | Apache-2.0 | |
| requests | Apache-2.0 | |
| pytest | MIT | |
| ruff | MIT | |
| mypy | MIT | |
| pillow | HPND | |

---

## 4. JavaScript Dependencies Audit

### Command

```bash
npx license-checker --summary
npx license-checker --onlyAllow "MIT;Apache-2.0;BSD-2-Clause;BSD-3-Clause;ISC"
```

### Dependency Check

| Package | License | Status |
|---------|---------|--------|
| playwright | Apache-2.0 | |
| eslint | MIT | |

---

## 5. Attribution Requirements

### Licenses Requiring Attribution

| License | Requirement | Location |
|---------|-------------|----------|
| Apache-2.0 | NOTICE file | LICENSE or NOTICE |
| BSD-3-Clause | Copyright in docs | LICENSE |

### Current Attribution

- [ ] LICENSE file includes all required attributions
- [ ] Third-party licenses documented
- [ ] NOTICE file exists (if required)

---

## 6. Audit Procedure

1. List all Python dependencies: `poetry show`
2. Check each license against §2 matrix
3. List all JS dependencies: `npm ls --all`
4. Check each license against §2 matrix
5. Verify attribution requirements met
6. Document any issues

---

## 7. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|
| | | | |

---

## 8. References

- [SPDX License List](https://spdx.org/licenses/)
- [Choose a License](https://choosealicense.com/)
- [OSI Approved Licenses](https://opensource.org/licenses)
