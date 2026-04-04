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
| Mutation testing | — | `nox -s mutation` | mutmut on `rules.py`, `shield.py`, `reporter.py` |
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

### VSM Sovereignty

Any existence check on an internal resource (page, image, anchor) **must** query
the Virtual Site Map — never the filesystem.

**Why:** The VSM includes **Ghost Routes** — canonical URLs generated by build
plugins (e.g. `reconfigure_material: true`) that have no physical `.md` file
on disk. A `Path.exists()` call returns `False` for a Ghost Route. The VSM
returns `REACHABLE`. The VSM is the oracle; the filesystem is not.

**Grade-1 violation:** Using `os.path.exists()`, `Path.is_file()`, or any other
filesystem probe to validate an internal link is a Grade-1 architectural
violation. PRs containing this pattern will be closed without review.

```python
# ❌ Grade-1 violation — asks the filesystem, misses Ghost Routes
if (docs_root / relative_path).exists():
    ...

# ✅ Correct — asks the VSM
route = vsm.get(canonical_url)
if route and route.status == "REACHABLE":
    ...
```

Related: see `docs/arch/vsm_engine.md` — *Anti-Pattern Catalogue* for the
complete list of banned filesystem calls inside rules.

### Ghost Route Awareness

Orphan detection rules must respect routes flagged as Ghost Routes in the VSM.
A Ghost Route is not an orphan — it is a route that the build engine generates
at build time from a plugin, with no source `.md` file.

**Action:** Every new global-scan rule that performs orphan detection must
accept an `include_ghosts: bool = False` constructor parameter. When
`include_ghosts=False` (the default), routes with `status == "ORPHAN_BUT_EXISTING"`
that were generated by a Ghost Route mechanism must be excluded from findings.

```python
class MyOrphanRule(BaseRule):
    def __init__(self, include_ghosts: bool = False) -> None:
        self._include_ghosts = include_ghosts

    def check_vsm(self, file_path, text, vsm, anchors_cache, context=None):
        for url, route in vsm.items():
            if route.status == "ORPHAN_BUT_EXISTING":
                # Skip Ghost Route-derived orphans unless explicitly included
                if not self._include_ghosts and _is_ghost_derived(route):
                    continue
                ...
```

## Security & Compliance

- **Security First:** Any new path resolution MUST be tested against Path Traversal. Use `PathTraversal` logic from `core`.
- **Bilingual Parity:** Every documentation update MUST be reflected in both `docs/*.md` and the corresponding `docs/it/*.md` folder-mode files.
- **Asset Integrity:** Ensure SVG badges in `docs/assets/brand/` are updated if the scoring logic changes.

---

## The Shield & The Canary

This section documents the **four security obligations** that apply to every
PR touching `src/zenzic/core/`. A PR that resolves a bug without satisfying
all four will be rejected by the Architecture Lead.

These rules exist because the v0.5.0a3 security review (2026-04-04) demonstrated
that four individually reasonable design choices — each correct in isolation —
composed into four distinct attack vectors. See
`docs/internal/security/shattered_mirror_report.md` for the full post-mortem.

---

### Obligation 1 — The Security Tax (Worker Timeout)

Every PR that modifies `ProcessPoolExecutor` usage in `scanner.py` must
preserve the `future.result(timeout=_WORKER_TIMEOUT_S)` call. The current
timeout is **30 seconds**.

**What this means:**

```python
# ✅ Required form — always use submit() + result(timeout=...)
futures_map = {executor.submit(_worker, item): item[0] for item in work_items}
for fut, md_file in futures_map.items():
    try:
        raw.append(fut.result(timeout=_WORKER_TIMEOUT_S))
    except concurrent.futures.TimeoutError:
        raw.append(_make_timeout_report(md_file))  # Z009 finding

# ❌ Forbidden — blocks indefinitely on ReDoS or deadlocked workers
raw = list(executor.map(_worker, work_items))
```

**The Z009 finding** (`ANALYSIS_TIMEOUT`) is not a crash. It is a structured
finding that surfaces in the standard report UI. A worker that times out does
not kill the scan — the coordinator continues with the remaining workers.

**If your change naturally requires a longer timeout** (e.g. a new rule
performs expensive computation), increase `_WORKER_TIMEOUT_S` with a comment
explaining the cost and a benchmark proving the worst-case input.

---

### Obligation 2 — The Regex-Canary Protocol

Every `[[custom_rules]]` entry that specifies a `pattern` is subject to the
**Regex-Canary**, a POSIX `SIGALRM`-based stress test that runs at
`AdaptiveRuleEngine` construction time.

**How the canary works:**

```python
# _assert_regex_canary() in rules.py — runs automatically for every CustomRule
_CANARY_STRINGS = (
    "a" * 30 + "b",   # classic (a+)+  trigger
    "A" * 25 + "!",   # uppercase variant
    "1" * 20 + "x",   # numeric variant
)
_CANARY_TIMEOUT_S = 0.1   # 100 ms
```

The canary applies each of the three strings to the rule's `check()` method
under a 100 ms watchdog. If the pattern does not complete within 100 ms on
any of these strings, the engine raises `PluginContractError` before the scan
begins.

**Testing your pattern against the canary before committing:**

```python
from pathlib import Path
from zenzic.core.rules import CustomRule, _assert_regex_canary
from zenzic.core.exceptions import PluginContractError

rule = CustomRule(
    id="MY-001",
    pattern=r"your-pattern-here",
    message="Found.",
    severity="warning",
)

try:
    _assert_regex_canary(rule)
    print("✅ Canary passed — pattern is safe for production")
except PluginContractError as e:
    print(f"❌ Canary failed — ReDoS risk detected:\n{e}")
```

Or from the shell:

```bash
uv run python -c "
from zenzic.core.rules import CustomRule, _assert_regex_canary
r = CustomRule(id='T', pattern=r'YOUR_PATTERN', message='.', severity='warning')
_assert_regex_canary(r)
print('safe')
"
```

**Patterns to avoid** (catastrophic backtracking triggers):

| Pattern | Why dangerous |
|---------|---------------|
| `(a+)+` | Nested quantifiers — exponential paths |
| `(a\|aa)+` | Alternation with overlap |
| `(a*)*` | Nested star — infinite empty matches |
| `.+foo.+bar` | Greedy multi-wildcard with suffix |

**Patterns that are always safe:**

| Pattern | Notes |
|---------|-------|
| `TODO` | Literal match, O(n) |
| `^(DRAFT\|WIP):` | Anchored alternation, O(1) at each position |
| `[A-Z]{3}-\d+` | Bounded character classes |
| `\bfoo\b` | Word-boundary anchored |

**Platform note:** `_assert_regex_canary()` uses `signal.SIGALRM`, which is
only available on POSIX systems (Linux, macOS). On Windows, the canary is a
no-op. The worker timeout (Obligation 1) is the universal backstop.

**Canary overhead:** Measured at **0.12 ms** per engine construction with 10
safe rules (20-iteration median). This is a one-time cost at scan startup and
is well within the acceptable "Security Tax" budget.

---

### Obligation 3 — The Shield's Dual-Stream Invariant

The Shield stream and the Content stream in `ReferenceScanner.harvest()` must
**never share a generator**. This is the architectural lesson from ZRT-001.

```python
# ✅ CORRECT — independent generators, independent filtering contracts
with file_path.open(encoding="utf-8") as fh:
    for lineno, line in enumerate(fh, start=1):  # Shield: ALL lines
        list(scan_line_for_secrets(line, file_path, lineno))

for lineno, line in _iter_content_lines(file_path):  # Content: filtered
    ...

# ❌ FORBIDDEN — sharing a generator silently drops frontmatter from Shield
with file_path.open(encoding="utf-8") as fh:
    shared = _skip_frontmatter(fh)
    for lineno, line in shared:
        list(scan_line_for_secrets(...))   # ← blind to frontmatter
    for lineno, line in shared:            # ← already exhausted
        ...
```

**Shield performance:** The dual-scan (raw + normalised line) runs at
approximately **235,000 lines/second** (measured: 12.74 ms median for 3,000
lines over 20 iterations). The normalizer adds one pass per line but the
`seen` set prevents duplicate findings, keeping output deterministic.

If a PR refactors `harvest()` and the CI benchmark drops below **100,000
lines/second**, reject and investigate before merging.

---

### Obligation 4 — Mutation Score ≥ 90% for Core Changes

Any PR that modifies `src/zenzic/core/` must maintain or improve the mutation
score on the affected module. The current baseline for `rules.py` is **86.7%**
(242/279 mutants killed).

The target for rc1 is **≥ 90%**. A PR that adds a new rule or modifies
detecting logic without killing the corresponding mutants will be rejected.

**Running mutation testing:**

```bash
nox -s mutation
```

**Interpreting surviving mutants:**

Not all surviving mutants are equivalent. Before marking a mutant as
acceptable, confirm that:

1. The mutant changes observable behaviour (it is not logically equivalent).
2. No existing test catches the mutant (it is a genuine gap).
3. Adding a test to kill it would be redundant or trivially circular.

If unsure, add the test. The mutation suite is a living document of the
Sentinel's threat model.

**ResolutionContext pickle validation (Eager Validation 2.0):**

`ResolutionContext` is a `@dataclass(slots=True)` with only `Path` fields.
`Path` is pickleable by the standard library. The object serializes to 157
bytes. However, if `ResolutionContext` ever gains a field that is not
pickleable (e.g. a file handle, a lock, a lambda), the parallel engine will
fail silently.

To guard against this, any PR that adds a field to `ResolutionContext` must
include:

```python
# In tests/test_redteam_remediation.py (or a dedicated test):
def test_resolution_context_is_pickleable():
    import pickle
    ctx = ResolutionContext(docs_root=Path("/docs"), source_file=Path("/docs/a.md"))
    assert pickle.loads(pickle.dumps(ctx)) == ctx
```

This test already exists in the test suite as of v0.5.0a4.

**Shield Reporting Integrity (The Mutation Gate for Commit 2+):**

The conformance requirement for the mutation score on the Shield is **broader**
than detection alone. It also covers the **reporting pipeline**:

> *A secret that is detected but not correctly reported is a CRITICAL bug —
> indistinguishable from a secret that was never detected at all.*

Any PR that touches the `_map_shield_to_finding()` conversion function,
the `SECURITY_BREACH` severity path in `SentinelReporter`, or the exit-code
routing in `cli.py` **must kill all three of these mandatory mutants** before
the PR is accepted:

| Mutant name | What is changed | Test that must kill it |
|-------------|----------------|------------------------|
| **The Invisible** | `severity="security_breach"` → `severity="warning"` in `_map_shield_to_finding()` | `test_map_always_emits_security_breach_severity` |
| **The Amnesiac** | `_obfuscate_secret()` returns `raw` instead of the redacted form | `test_obfuscate_never_leaks_raw_secret` |
| **The Silencer** | `_map_shield_to_finding()` returns `None` instead of a `Finding` | `test_pipeline_appends_breach_finding_to_list` |

**Running the mutation gate:**

```bash
nox -s mutation
```

The session targets `rules.py`, `shield.py`, and `reporter.py` as configured in
`[tool.mutmut]` in `pyproject.toml`. No posargs are required.

> **Infrastructure note — `mutmut_pytest.ini`:**
> `mutmut` v3 generates trampolines in a `mutants/` working copy. For these
> to be visible to pytest, `mutants/src/` must precede the installed
> site-packages on `sys.path`. `mutmut_pytest.ini` (tracked in the repo)
> provides an isolated pytest config (`import-mode=prepend`,
> `pythonpath = src`) used exclusively by the `nox -s mutation` session.
> The main `pyproject.toml` pytest config is not affected.

**Fallback — Manual Mutation Verification (The Sentinel's Trial):**

If the automated tool cannot report a score (e.g. due to an editable-install
mapping issue), apply each mutant by hand and confirm the test fails:

```bash
# 1. Apply mutant, run the specific test, confirm FAIL, revert.
git diff  # verify only one targeted line changed
pytest tests/test_redteam_remediation.py::TestShieldReportingIntegrity -v
git checkout -- src/  # revert
```

Manual verification is accepted as a temporary waiver per Architecture Lead
approval. Document the results in the PR description before merging.

If the score is below 90% (automated) or any of the three trials pass when
they should fail (manual), add targeted tests before reopening the PR. Do not
mark surviving mutants as equivalent without explicit Architecture Lead approval.

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
