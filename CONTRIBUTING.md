# Contributing to Zenzic

Thank you for your interest in contributing to Zenzic!

Zenzic is a documentation quality tool — an engine-agnostic linter and security shield for Markdown documentation. Contributions that improve detection accuracy, add new check types, or improve CI/CD integration are especially welcome.

## Mission

Zenzic is not just a linter. It is a long-term safety layer for documentation teams that
depend on open, auditable source files. We preserve validation continuity across engine
changes (MkDocs 1.x, Zensical, and future adapters) so projects keep control over their
data and quality process regardless of ecosystem churn.

---

## Quick start

```bash
git clone git@github.com:PythonWoods/zenzic.git
cd zenzic
just sync
nox -s dev
```

`just sync` installs all dependency groups via `uv sync --all-groups`.
`nox -s dev` installs pre-commit hooks and downloads the Lucide icon set into
`overrides/.icons/lucide/` (required for `mkdocs serve` and `mkdocs build`).
This directory is excluded from git — it is a generated build asset.

---

## Running tasks

Development tasks use two layers: **just** for interactive speed and **nox** for
reproducible CI isolation. Use `just` day-to-day; use `nox` directly when you need
the exact same environment as CI.

| Task | `just` command | `nox` equivalent | Description |
|:-----|:---------------|:-----------------|:------------|
| Bootstrap | `just sync` | — | Install / update all dependency groups |
| **Self-lint** | **`just check`** | — | **Run Zenzic on its own documentation (strict)** |
| Test suite | `just test` | `nox -s tests` | pytest + branch coverage (Hypothesis **dev** profile) |
| Test suite (thorough) | `just test-full` | — | pytest with Hypothesis **ci** profile (500 examples) |
| Mutation testing | — | `nox -s mutation` | mutmut on `src/zenzic/core/rules.py` |
| Full pipeline | `just preflight` | `nox -s preflight` | lint, typecheck, tests, reuse, security |
| **Pre-push gate** | **`just verify`** | — | **preflight + production build — run before every push** |
| Docs build (fast) | `just build` | — | mkdocs build, no strict enforcement |
| Docs build (prod) | `just build-prod` | `nox -s docs` | mkdocs build --strict, mirrors CI |
| Docs serve | `just serve [port]` | `nox -s docs_serve` | live-reload server (default port 8000) |
| Clean | `just clean` | — | Remove `site/`, `dist/`, `.hypothesis/`, caches |
| Pre-commit setup | — | `nox -s dev` | install hooks + download Lucide icons (once after clone) |
| Version bump | — | `nox -s bump -- patch` | bump version + commit + tag |
| Screenshot | — | `nox -s screenshot` | regenerate `docs/assets/screenshot.svg` |

Run the full pre-push gate with:

```bash
just verify
```

> **Tip:** Before committing documentation updates, run `uvx zenzic clean assets` (or `uv run zenzic clean assets`) to automatically delete any old screenshots or images you are no longer using. This keeps the repository lean.

---

## Code conventions

- **Python ≥ 3.11** with full type annotations (`mypy --strict` must pass).
- **SPDX header** on every source file — `reuse lint` is enforced in CI.
- No placeholder text, `TODO`, or stub comments in committed code.
- Tests must pass with ≥ 80% branch coverage.
- All PRs must target `main`; direct commits are blocked by pre-commit.

---

## Core Laws (non-negotiable)

These rules protect the performance and determinism guarantees of `src/zenzic/core/`.
A PR that violates any of them will be rejected regardless of test coverage.

### Zero I/O in the hot path

`src/zenzic/core/` **must never call** `Path.exists()`, `Path.is_file()`, `open()`,
or any other filesystem or subprocess operation inside a per-link or per-file loop.

The two permitted I/O phases are:

| Phase | Where | What |
| ----- | ----- | ---- |
| **Pass 1** | `validate_links_async` preamble | `rglob` traversal to build `md_contents` and `known_assets` |
| **`InMemoryPathResolver` construction** | `__init__` | Building `_lookup_map` from the pre-read content dict |

Everything after Pass 1 must use only in-memory data structures:

- Internal `.md` resolution → `InMemoryPathResolver.resolve()`
- Non-`.md` asset resolution → `asset_str in known_assets` (`frozenset[str]`, O(1))
- Build-time artifact suppression → `fnmatch` against `excluded_build_artifacts` patterns

### i18n determinism

Any new validation rule that touches file paths **must** be tested in three configurations:

1. **Monolingual** — no i18n plugin in `mkdocs.yml`.
2. **Suffix-mode** — `docs_structure: suffix`; translated files are siblings (`page.it.md`).
3. **Folder-mode, fallback on** — `docs_structure: folder`, `fallback_to_default: true`.

Add your scenarios to `tests/test_tower_of_babel.py` if they involve locale files.
Unit tests that exercise only pure functions belong in `tests/test_validator.py`.

### i18n configuration errors

When `fallback_to_default: true` but no language declares `default: true`, Zenzic raises
`ConfigurationError` (not a generic `ValueError`). Any code path that reads i18n config must
preserve this contract: fail loudly with an actionable message, never silently default to
a wrong locale.

### Adapter contract

Any new validation rule that touches locale paths **must go through the adapter**. Direct
`mkdocs.yml` YAML parsing in `validator.py` or `scanner.py` is prohibited — the adapter is
the single source of truth for locale topology.

```python
# ✅ Correct — use the adapter
from zenzic.core.adapter import get_adapter
adapter = get_adapter(config.build_context, docs_root)
if adapter.is_locale_dir(rel.parts[0]):
    ...

# ❌ Wrong — never parse mkdocs.yml for locale data inside a check
import yaml
doc_config = yaml.load(open("mkdocs.yml"))
locale_dirs = {lang["locale"] for lang in doc_config["plugins"][0]["i18n"]["languages"]}
```

The three methods of the adapter contract are:

| Method | Signature | Purpose |
| :--- | :--- | :--- |
| `is_locale_dir` | `(part: str) -> bool` | Is this path component a locale directory? |
| `resolve_asset` | `(missing_abs: Path, docs_root: Path) -> Path \| None` | Default-locale fallback for a missing asset |
| `is_shadow_of_nav_page` | `(rel: Path, nav_paths: frozenset[str]) -> bool` | Is this locale file a mirror of a nav page? |

To add support for a new build engine, implement a new adapter class with these three methods
and register it in `get_adapter()` in `zenzic.core.adapter`.

### i18n Portability & Integrity

Zenzic supports both i18n strategies used by `mkdocs-static-i18n`:

- **Suffix Mode** (`filename.locale.md`) — translated files are siblings of originals at the
  same directory depth. Relative asset paths are symmetric between languages. Zenzic
  auto-detects locale suffixes from file names without any configuration.
- **Folder Mode** (`docs/it/filename.md`) — non-default locales live in a top-level directory.
  Asset links and orphan detection are handled by `MkDocsAdapter` via `[build_context]` in
  `zenzic.toml`. When `zenzic.toml` is absent, Zenzic reads locale config from `mkdocs.yml`.

**Absolute Link Prohibition**
Zenzic rejects any internal link starting with `/`. Absolute paths presuppose that the site
is hosted at the domain root. If documentation is served from a subdirectory (e.g.
`https://example.com/docs/`), a link to `/assets/logo.png` resolves to
`https://example.com/assets/logo.png` (404), not to the intended asset. Use relative paths
(`../assets/logo.png`) to guarantee portability regardless of the hosting environment.

## Security & Compliance

- **Security First:** Any new path resolution MUST be tested against Path Traversal. Use `PathTraversal` logic from `core`.
- **Bilingual Parity:** Every documentation update MUST be reflected in both `docs/*.md` and the corresponding `docs/it/*.md` folder-mode files.
- **Asset Integrity:** Ensure SVG badges in `docs/assets/brand/` are updated if the scoring logic changes.

---

## Adding a new check

Zenzic's checks live in `src/zenzic/core/`. Each check is a standalone function in either `scanner.py` (filesystem traversal) or `validator.py` (content validation). CLI wiring is in `cli.py`.

When adding a new check:

1. Implement the logic in the appropriate core module (`zenzic.core.scanner` or `zenzic.core.validator`).
2. **Any link or path resolution logic MUST delegate to `InMemoryPathResolver`** — never call
   `os.path.exists()`, `Path.is_file()`, or any other filesystem probe inside a per-link loop.
   The resolver is instantiated once before the loop; re-instantiation per file defeats the
   pre-computed `_lookup_map` and drops throughput from 430 000+ to below 30 000 resolutions/s.
   See [Core Laws — Zero I/O in the hot path](#zero-io-in-the-hot-path) above.
3. If the check involves file paths, test it in all three i18n configurations.
   See [Core Laws — i18n determinism](#i18n-determinism) above.
4. Add a corresponding command (or sub-command) in `cli.py`.
5. Write tests in `tests/` covering both passing and failing cases, including a performance
   baseline (5 000 links resolved in < 100 ms against a mock in-memory corpus).
6. Update `docs/` — Zenzic validates its own docs on every commit.

> **Performance contract:** the `zenzic.core` hot path must remain allocation-free. No `Path`
> object construction, no syscalls, and no `relative_to()` calls inside the resolution loop.
> See `docs/architecture.md` — *IO Purity contract* and *Contributor rules* for the rationale.

---

## Documentation

Zenzic uses **MkDocs Material** for its own documentation (`docs/`). Any behaviour change or
new feature must be documented. `zenzic check all --strict` runs against this repo in CI —
a failing check blocks the PR.

The documentation uses the **Lucide** icon set, downloaded at build time into
`overrides/.icons/lucide/` (excluded from git). Run `nox -s dev` once after cloning to
fetch the icons — after that, `mkdocs serve` works without additional steps.

To preview documentation locally:

```bash
just serve
```

To verify the production build:

```bash
just build
```

---

## Advanced QA: Mutants & Properties

Zenzic uses two advanced testing techniques to ensure the Sentinel's core is battle-hardened.

### Property-Based Testing (Hypothesis)

`tests/test_properties.py` uses [Hypothesis](https://hypothesis.readthedocs.io/) to generate
thousands of random inputs and verify **invariants** that must hold for any input:

- `extract_links()` never crashes, always returns `LinkInfo`, line numbers stay in range.
- `slug_heading()` is lowercase, idempotent, and free of leading/trailing hyphens.
- `CustomRule.check()` returns valid findings with `col_start` in range.
- `InMemoryPathResolver.resolve()` always returns a valid outcome type and catches path traversal.

Run property tests:

```bash
uv run pytest tests/test_properties.py -x -q
```

### Mutation Testing (mutmut)

[mutmut](https://mutmut.readthedocs.io/) modifies your source code (e.g. changes `>` to `>=`)
and checks whether the test suite catches the mutation. A surviving mutant means a test gap.

Target module: `src/zenzic/core/rules.py` — the heart of the Sentinel's detection logic.

Run mutation testing:

```bash
nox -s mutation
```

**Merge requirement:** any new core rule must achieve a **mutation score > 90%**. If `mutmut`
reports surviving mutants in `rules.py`, add targeted tests before merging.

---

## Release procedure (maintainers only)

Releases are **semi-automated**: the developer decides the bump type, one command does the rest.

```bash
# 1. Ensure main is green (preflight passed)
nox -s preflight

# 2. Bump version, create commit and tag automatically
nox -s bump -- patch     # 0.1.0 → 0.1.1  (bug fix)
nox -s bump -- minor     # 0.1.0 → 0.2.0  (new feature, backward compatible)
nox -s bump -- major     # 0.1.0 → 1.0.0  (breaking change)

# 3. Push — this triggers the release workflow
git push && git push --tags
```

The `release.yml` workflow then:

1. Runs `uv build` (sdist + wheel)
2. Publishes to PyPI via `uv publish` (requires `PYPI_TOKEN` secret)
3. Creates a GitHub Release with auto-generated notes

Update `CHANGELOG.md` before bumping: move items from `[Unreleased]` to the new version section.
