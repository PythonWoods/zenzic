<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic v0.5.0a5 — Pre-Release Audit Package

**Prepared by:** S-0 (Chronicler)
**Date:** 2026-04-09
**Status:** ALPHA — Pending Tech Lead manual verification before rc1 promotion
**Branch:** `main` (merged from `refactor/zrt-doc-002-visual-language`)

> **Tech Lead note:** This document is your single audit surface. Work through each
> section in order. When every checkbox below is ticked, the project is ready for
> the `rc1` tag. Until then, the "Alpha" designation stands.

---

## 1. Version Anchors

| Location | Expected | Actual | Status |
| :--- | :--- | :--- | :---: |
| `src/zenzic/__init__.py` | `0.5.0a5` | `0.5.0a5` | ✅ |
| `pyproject.toml` `[project]` | `0.5.0a5` | `0.5.0a5` | ✅ |
| `pyproject.toml` `[tool.bumpversion]` | `0.5.0a5` | `0.5.0a5` | ✅ |
| `mkdocs.yml` | `0.5.0a5` | `0.5.0a5` | ✅ |
| `CITATION.cff` | `0.5.0a5` | `0.5.0a5` | ✅ |
| `CHANGELOG.md` top entry | `[0.5.0a5]` | `[0.5.0a5]` | ✅ |
| `CHANGELOG.it.md` top entry | `[0.5.0a5]` | `[0.5.0a5]` | ✅ |
| `docs/community/index.md` BibTeX | `0.5.0a5` | `0.5.0a5` | ✅ |
| `docs/it/community/index.md` BibTeX | `0.5.0a5` | `0.5.0a5` | ✅ |
| `uv.lock` | `0.5.0a5` | `0.5.0a5` | ✅ |

---

## 2. Quality Gates

Gate targets for rc1 promotion:

- [ ] `pytest` — all passing, 0 failed
- [ ] `zenzic check all --strict` → exit code 0, no errors, no warnings
- [ ] `ruff check src/` → 0 violations
- [ ] `mypy src/` → 0 errors
- [ ] `mkdocs build --strict` → 0 warnings
- [ ] Version grep audit — zero non-historical `0.5.0a4` references

---

## 3. Changes in v0.5.0a5 — Review Checklist

### 3.1 Sentinel Style Guide

**What it is:** Canonical visual-language reference defining card grids,
admonition types, icon vocabulary, and anchor-ID conventions.

**Files added:**

- `docs/internal/style-guide-sentinel.md` (EN)
- `docs/it/internal/style-guide-sentinel.md` (IT)

**Verification steps for Tech Lead:**

- [ ] Read both files — conventions clear and consistent?
- [ ] Verify all documented patterns are actually applied in the codebase

---

### 3.2 Automated Screenshot Pipeline

**What changed:** `scripts/generate_docs_assets.py` now generates all 5
documentation SVGs (was 3). `screenshot-blood.svg` and
`screenshot-circular.svg` were previously hand-crafted static assets.

**New sandbox fixtures:**

- `tests/sandboxes/screenshot_blood/` — triggers `PATH_TRAVERSAL_SUSPICIOUS`
- `tests/sandboxes/screenshot_circular/` — triggers `CIRCULAR_LINK`

**Verification steps for Tech Lead:**

- [ ] Run `uv run python scripts/generate_docs_assets.py` — all 5 SVGs generated?
- [ ] Visually inspect `docs/assets/screenshots/screenshot-blood.svg` — Blood Sentinel output correct?
- [ ] Visually inspect `docs/assets/screenshots/screenshot-circular.svg` — Circular link output correct?
- [ ] Confirm SVGs contain version `0.5.0a5` in the banner

---

### 3.3 Card Grid & Admonition Normalisation

**What changed:** Documentation pages refactored to use Material for MkDocs
card-grid syntax. Ad-hoc callout styles replaced with canonical admonition
types (`tip`, `warning`, `info`, `example`).

**Verification steps for Tech Lead:**

- [ ] Spot-check 3–5 documentation pages for consistent card grids
- [ ] Verify no non-Material icons remain (`:fontawesome-*:` or `:octicons-*:`)
- [ ] Run `mkdocs build --strict` — no rendering warnings?

---

### 3.4 Strategic Anchor IDs

**What changed:** 102 explicit `{ #anchor-id }` anchors placed across 70
documentation files for stable deep-linking.

**Verification steps for Tech Lead:**

- [ ] Verify anchors follow kebab-case convention
- [ ] Spot-check that cross-document `#anchor` links resolve correctly

---

### 3.5 Infrastructure Fixes

**What changed:**

- `CHANGELOG.it.md` added to `[tool.bumpversion.files]` in `pyproject.toml`
- `docs/assets/pdf_cover.html.j2` removed (orphan legacy artifact)
- CSS card hover overrides added to `docs/assets/stylesheets/`

**Verification steps for Tech Lead:**

- [ ] Confirm `pdf_cover.html.j2` no longer exists on disk
- [ ] Confirm `CHANGELOG.it.md` has bumpversion entry in `pyproject.toml`
- [ ] Verify CSS hover effects render correctly in local `mkdocs serve`

---

## 4. Documentation Parity Matrix

| Document | EN | IT |
| :--- | :---: | :---: |
| Style Guide Sentinel | ✅ | ✅ |
| `docs/checks.md` | ✅ | ✅ |
| `docs/usage/advanced.md` | ✅ | ✅ |
| `CHANGELOG.md` / `CHANGELOG.it.md` | ✅ | ✅ |
| `README.md` / `README.it.md` | ✅ | ✅ |

---

## 5. Sandbox Self-Check

Run these commands manually and verify output:

```bash
# 1. Full test suite
uv run pytest --tb=short

# 2. Self-dogfood (strict mode)
uv run zenzic check all --strict

# 3. Static analysis
uv run ruff check src/
uv run mypy src/ --ignore-missing-imports

# 4. Documentation build
uv run mkdocs build --strict

# 5. Version grep audit (should return only historical references)
grep -rn "0.5.0a4" --include="*.md" --include="*.py" --include="*.toml" --include="*.yml" --include="*.cff"
```

---

## 6. rc1 Gate Decision

This section is for the Tech Lead's signature.

- [ ] All verification steps in §§ 3.1–3.5 completed
- [ ] Documentation parity matrix §4 confirmed correct
- [ ] Sandbox self-check §5 passed manually
- [ ] No open blocking issues

**Decision:** ☐ Approve rc1 promotion &nbsp;&nbsp; ☐ Defer — open issues remain

---

*"Una Release Candidate non è un premio per aver finito i task, è una promessa di
stabilità che facciamo all'utente."*
— Senior Tech Lead
