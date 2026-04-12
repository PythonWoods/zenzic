<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic v0.6.0a1 — Obsidian Glass Audit Protocol

**Prepared by:** S-1 (Auditor)
**Date:** 2026-04-12
**Status:** ALPHA — Pending Tech Lead manual verification before rc1 promotion
**Branch:** `feat/docusaurus-adapter-v0.6.0a1`
**Codename:** Obsidian Glass — The Platform-Agnostic Leap

> **Tech Lead note:** This release marks the evolution from MkDocs-specific linter to
> **Documentation Platform Analyser**. The Core repository now contains zero documentation
> build infrastructure — all docs live in `zenzic-doc`. Work through each gate below.
> When every checkbox is ticked, the project is ready for `rc1`.

---

## 1. Version Anchors

| Location | Expected | Status |
| :--- | :--- | :---: |
| `src/zenzic/__init__.py` | `0.6.0a1` | ☐ |
| `pyproject.toml` `[project]` | `0.6.0a1` | ☐ |
| `pyproject.toml` `[tool.bumpversion]` | `0.6.0a1` | ☐ |
| `CITATION.cff` | `0.6.0a1` | ☐ |
| `CHANGELOG.md` top entry | `[0.6.0a1]` | ☐ |
| `CHANGELOG.it.md` top entry | `[0.6.0a1]` | ☐ |

**Removed from tracking** (Clean Harbor):

- `mkdocs.yml` — deleted (docs migrated to `zenzic-doc`)
- `docs/community/index.md` BibTeX — deleted (docs migrated)
- `docs/it/community/index.md` BibTeX — deleted (docs migrated)
- `uv.lock` — not tracked by bumpversion (updated by `uv lock`)

---

## 2. The Adapter Gate (Core Logic)

- [ ] `DocusaurusAdapter` satisfies the `@runtime_checkable` `BaseAdapter` protocol (9 methods)
- [ ] `baseUrl` extraction via regex confirmed (zero Node.js dependency — Pillar 2)
- [ ] Ghost Route mapping for `/it/` and `/` (locale entry points) verified
- [ ] `from_repo()` auto-discovers `docusaurus.config.ts` / `.js`
- [ ] `classify_route()` marks `_`-prefixed files as `IGNORED`
- [ ] Adapter registered in `_factory.py`, `__init__.py`, and `pyproject.toml` entry-point
- [ ] VSM cross-validation: 34 routes, 34 REACHABLE, 0 CONFLICT, 0 IGNORED

---

## 3. The Clean Harbor Gate (Repo Hygiene)

- [ ] `mkdocs.yml` — physically deleted
- [ ] `overrides/` — physically deleted
- [ ] `scripts/generate_docs_assets.py` — physically deleted
- [ ] `scripts/generate_hero_specimen.py` — physically deleted
- [ ] `scripts/generate_social.py` — physically deleted
- [ ] `.github/workflows/deploy-docs.yml` — physically deleted
- [ ] `.github/workflows/zenzic.yml` — physically deleted
- [ ] `.github/ISSUE_TEMPLATE/docs_issue.yml` — physically deleted
- [ ] `docs/` → `.temp/docs/` (staging, gitignored)
- [ ] `.temp/` in `.gitignore` — single entry, no duplicates
- [ ] `noxfile.py` — `docs`, `docs_serve`, `screenshot`, `audit_sandboxes` sessions removed
- [ ] `noxfile.py` — `_download_lucide_icons()`, `_build_brand_kit_zip()`, `_SYNC_DOCS` removed
- [ ] `noxfile.py` — `preflight` no longer runs `mkdocs build`
- [ ] `pyproject.toml` — `docs` dependency group removed
- [ ] `pyproject.toml` — `dev` group no longer includes `docs`
- [ ] `pyproject.toml` — bumpversion entries for `mkdocs.yml`, `docs/community/*.md` removed
- [ ] `ci.yml` — `docs:` job removed, `docs/**` path trigger removed
- [ ] `justfile` — `build`, `build-prod`, `serve`, `live` targets removed

---

## 4. The README Sovereignty Gate

- [ ] `README.md` and `README.it.md` images point to `assets/` (root), not `docs/assets/`
- [ ] `assets/brand/svg/` contains wordmark SVGs with `.license` sidecars
- [ ] `assets/screenshots/` contains hero + full audit SVGs with `.license` sidecars
- [ ] No remaining `docs/assets` references in any README (excluding inline prose examples)
- [ ] `ci-workflow` reference link updated from `zenzic.yml` to `ci.yml`
- [ ] MkDocs badge replaced with Docusaurus badge
- [ ] v0.6.0a1 Highlights section added (EN + IT)
- [ ] `REUSE.toml` updated with `assets/**` annotation

---

## 5. Quality Gates

Gate targets for rc1 promotion:

- [ ] `pytest` — all passing, 0 failed
- [ ] `ruff check src/` → 0 violations
- [ ] `mypy src/` → 0 errors
- [ ] `reuse lint` → compliant
- [ ] `pip install -e .` → `zenzic --help` outputs usage (uvx-ready)
- [ ] `uv run zenzic --version` → `Zenzic v0.6.0a1`
- [ ] Version grep audit — zero non-historical `0.5.0a5` references

---

## 6. Docusaurus Validation (zenzic-doc)

Run against the live `zenzic-doc` repository:

```bash
cd /path/to/zenzic
uv run zenzic check all --engine docusaurus /path/to/zenzic-doc/docs
```

Expected result:

```text
VSM: 34 routes | 34 REACHABLE | 0 CONFLICT | 0 IGNORED
```

- [ ] `zenzic check all --engine docusaurus` → exit code 0
- [ ] Zero CONFLICT routes
- [ ] `zenzic-doc` has `release-docs.yml` workflow for Docusaurus deploy

---

## 7. Sandbox Self-Check

Run these commands manually and verify output:

```bash
# 1. Full test suite
uv run pytest --tb=short

# 2. Self-dogfood
uv run zenzic check all --strict

# 3. Static analysis
uv run ruff check src/
uv run mypy src/ --ignore-missing-imports

# 4. Entry-point verification
pip install -e . && zenzic --version

# 5. Version grep audit (should return only historical/changelog references)
grep -rn "0.5.0a5" --include="*.py" --include="*.toml" --include="*.cff"
```

---

## 8. rc1 Gate Decision

This section is for the Tech Lead's signature.

- [ ] All gates (§§ 2–6) verified
- [ ] Sandbox self-check § 7 passed manually
- [ ] No open blocking issues

**Decision:** ☐ Approve rc1 promotion &nbsp;&nbsp; ☐ Defer — open issues remain

---

*"La Sentinella non rilascia sulla fiducia, rilascia sull'evidenza."*
— Senior Tech Lead
