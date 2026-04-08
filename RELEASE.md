<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic v0.5.0a4 — Pre-Release Audit Package

**Prepared by:** S-1 (Auditor) + S-0 (Chronicler)
**Date:** 2026-04-08
**Status:** ALPHA — Pending Tech Lead manual verification before rc1 promotion
**Branch:** `fix/sentinel-hardening-v0.5.0a4`

> **Tech Lead note:** This document is your single audit surface. Work through each
> section in order. When every checkbox below is ticked, the project is ready for
> the `rc1` tag. Until then, the "Alpha" designation stands.

---

## 1. Version Anchors

| Location | Expected | Actual | Status |
| :--- | :--- | :--- | :---: |
| `src/zenzic/__init__.py` | `0.5.0a4` | `0.5.0a4` | ✅ |
| `CHANGELOG.md` top entry | `[0.5.0a4]` | `[0.5.0a4]` | ✅ |
| `CHANGELOG.it.md` top entry | `[0.5.0a4]` | `[0.5.0a4]` | ✅ |
| No `rc1` in top-level version files | — | verified | ✅ |

---

## 2. Quality Gates

```text
pytest             756 passed, 0 failed
zenzic check all   ✔ All checks passed (18 info-level CIRCULAR_LINK — expected)
  --strict
```

Gate targets for rc1 promotion:

- [ ] `pytest` ≥ 756 passed, 0 failed
- [ ] `zenzic check all --strict` → exit code 0, no errors, no warnings
- [ ] `ruff check src/` → 0 violations
- [ ] `mypy src/` → 0 errors
- [ ] `mkdocs build --strict` → 0 warnings

---

## 3. New Features in v0.5.0a4 — Review Checklist

### 3.1 Blood Sentinel (Exit Code 3)

**What it does:** path-traversal hrefs pointing to OS system directories
(`/etc/`, `/root/`, `/var/`, `/proc/`, `/sys/`, `/usr/`) are classified as
`PATH_TRAVERSAL_SUSPICIOUS` → severity `security_incident` → **Exit Code 3**.
Exit 3 takes priority over Exit 2 (credential breach). Never suppressed by
`--exit-zero`.

**Files changed:**

- `src/zenzic/ui.py` — `BLOOD = "#8b0000"` palette constant
- `src/zenzic/core/reporter.py` — `security_incident` severity style (blood red)
- `src/zenzic/core/validator.py` — `_RE_SYSTEM_PATH`, `_classify_traversal_intent()`
- `src/zenzic/cli.py` — Exit Code 3 check in `check links` and `check all`

**Tests:** `TestTraversalIntent` (4 tests) + 2 exit-code integration tests in `test_cli.py`

**Verification steps for Tech Lead:**

- [ ] Review `_classify_traversal_intent()` in `src/zenzic/core/validator.py`
- [ ] Verify `PATH_TRAVERSAL_SUSPICIOUS` → `security_incident` mapping in `cli.py`
- [ ] Verify Exit 3 is checked **before** Exit 2 in `check all` exit logic
- [ ] Confirm `--exit-zero` does NOT suppress Exit 3
- [ ] Read `docs/checks.md` § "Blood Sentinel — system-path traversal"

---

### 3.2 Graph Integrity — Circular Link Detection

**What it does:** Phase 1.5 pre-computes a cycle registry via iterative DFS
(Θ(V+E)). Phase 2 checks each resolved link against the registry in O(1). Links
in a cycle emit `CIRCULAR_LINK` at severity **`info`** (not error or warning).

**Design decision — why `info`:**
The project's own documentation has ~34 intentional mutual navigation links
(Home ↔ Features, CI/CD ↔ Usage, etc.). Making this `warning` or `error` would
permanently break `--strict` self-check. The `info` level surfaces the topology
without blocking valid builds.

**Files changed:**

- `src/zenzic/core/validator.py` — `_build_link_graph()`, `_find_cycles_iterative()`, Phase 1.5 block

**Tests:** `TestFindCyclesIterative` (6 unit tests) + `TestCircularLinkIntegration` (3 integration tests)

**Verification steps for Tech Lead:**

- [ ] Review `_find_cycles_iterative()` — WHITE/GREY/BLACK DFS correctness
- [ ] Confirm `CIRCULAR_LINK` severity = `"info"` in `cli.py` Finding constructor
- [ ] Confirm CIRCULAR_LINK never triggers Exit 1 or Exit 2
- [ ] Read `docs/checks.md` § "Circular links"
- [ ] Run `zenzic check all --strict` and confirm only info findings, exit 0

---

### 3.3 Hex Shield

**What it does:** built-in Shield pattern `hex-encoded-payload` detects
3+ consecutive `\xNN` hex escape sequences. Threshold prevents FP on
single-escape regex examples.

**Files changed:**

- `src/zenzic/core/shield.py` — one line appended to `_SECRETS`

**Tests:** 4 tests in `TestShield` in `test_references.py`

**Verification steps for Tech Lead:**

- [ ] Confirm pattern `(?:\\x[0-9a-fA-F]{2}){3,}` in `shield.py`
- [ ] Confirm single `\xNN` is NOT flagged (threshold = 3)
- [ ] Read `docs/usage/advanced.md` § "Detected credential patterns" table

---

### 3.4 INTERNAL_GLOSSARY.toml

**What it does:** canonical EN↔IT term registry. 15 entries. `stable = true`
entries require an ADR before renaming.

**Verification steps for Tech Lead:**

- [ ] Review all 15 terms — correct EN↔IT mapping?
- [ ] All core concepts covered? (VSM, RDP, Shield, Blood Sentinel, etc.)

---

## 4. Documentation Parity Matrix

| Document | EN | IT | Hex Shield | Blood Sentinel | Circular Links |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `docs/checks.md` | ✅ | ✅ | — | ✅ | ✅ |
| `docs/it/checks.md` | — | ✅ | — | ✅ | ✅ |
| `docs/usage/advanced.md` | ✅ | ✅ | ✅ | — | — |
| `docs/it/usage/advanced.md` | — | ✅ | ✅ | — | — |
| `CHANGELOG.md` | ✅ | — | ✅ | ✅ | ✅ |
| `CHANGELOG.it.md` | — | ✅ | ✅ | ✅ | ✅ |

**Check for Tech Lead:**

- [ ] Read `docs/checks.md` §§ "Blood Sentinel" and "Circular links" — prose correct?
- [ ] Read `docs/it/checks.md` §§ "Sentinella di Sangue" and "Link circolari" — translation accurate?
- [ ] Read `docs/usage/advanced.md` Shield table — `hex-encoded-payload` row present and correct?
- [ ] Read `docs/it/usage/advanced.md` — Italian row accurate?

---

## 5. Exit Code Contract (complete picture)

| Exit Code | Trigger | Suppressible |
| :---: | :--- | :---: |
| 0 | All checks passed | — |
| 1 | One or more errors (broken links, syntax errors, etc.) | Via `--exit-zero` |
| 2 | Shield credential detection | **Never** |
| 3 | Blood Sentinel — system-path traversal (`PATH_TRAVERSAL_SUSPICIOUS`) | **Never** |

Priority order in `check all`: Exit 3 → Exit 2 → Exit 1 → Exit 0.

- [ ] Tech Lead: verify this contract matches implementation in `cli.py`

---

## 6. Sandbox Self-Check

Run these commands manually and verify output:

```bash
# 1. Full test suite
uv run pytest --tb=short

# 2. Self-dogfood (strict mode)
uv run zenzic check all --strict

# 3. Static analysis
uv run ruff check src/
uv run mypy src/ --ignore-missing-imports
```

Expected:

- pytest: 756 passed, 0 failed
- check all --strict: exit 0, "✔ All checks passed"
- ruff: 0 violations
- mypy: 0 errors (or pre-existing stubs only)

---

## 7. rc1 Gate Decision

This section is for the Tech Lead's signature.

- [ ] All verification steps in §§ 3.1–3.4 completed
- [ ] Documentation parity matrix §4 confirmed correct
- [ ] Exit code contract §5 verified in code
- [ ] Sandbox self-check §6 passed manually
- [ ] `INTERNAL_GLOSSARY.toml` reviewed and approved
- [ ] No open blocking issues

**Decision:** ☐ Approve rc1 promotion &nbsp;&nbsp; ☐ Defer — open issues remain

---

*"Una Release Candidate non è un premio per aver finito i task, è una promessa di
stabilità che facciamo all'utente."*
— Senior Tech Lead
