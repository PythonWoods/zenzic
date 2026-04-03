<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic v0.4.0: The Agnostic Framework for Documentation Integrity

**Release date:** 2026-04-01
**Status:** Release Candidate 4 — routing-aware, VSM Rule Engine, pre-release freeze

---

## Why this release matters now

The documentation tooling ecosystem is fractured. MkDocs 2.0 is on the horizon, carrying breaking
changes to plugin APIs and configuration formats. Zensical is emerging as a production-ready
alternative. Teams are migrating, experimenting, and hedging. In this environment, any quality
gate that is tightly coupled to a specific build engine has an expiry date.

v0.4.0 answers that uncertainty with a clear architectural commitment: **Zenzic will never break
because your documentation engine changed.**

This is not a marketing claim. It is a precise technical guarantee backed by three design pillars
and two sprints of structural surgery.

---

## The Three Pillars

### 1. Source-first — no build required

Zenzic analyses raw Markdown files and configuration as plain data. It never calls `mkdocs build`,
never imports a documentation framework, never depends on generated HTML. A broken link is caught
in 11 milliseconds against 5,000 files — before your CI runner has finished checking out the repo.

This makes Zenzic usable as a pre-commit hook, a pre-build gate, a PR check, and a migration
validator simultaneously. The same tool. The same score. The same findings. Regardless of which
engine you run.

### 2. No subprocesses in the Core

The reference implementation of "engine-agnostic linting" is to shell out to the engine and parse
its output. That approach inherits every instability of the engine: version skew, environment
differences, missing binaries on CI runners.

Zenzic's Core is pure Python. Link validation uses `httpx`. Nav parsing uses `yaml` and `tomllib`.
There are no `subprocess.run` calls in the linting path. The engine binary does not need to be
installed for `zenzic check all` to pass.

### 3. Pure functions, pure results

All validation logic in Zenzic lives in pure functions: no file I/O, no network access, no global
state, no terminal output. I/O happens only at the edges — CLI wrappers that read files and print
findings. Pure functions are trivially testable (433 passing tests at 98.4% coverage), composable
into higher-order pipelines, and deterministic across environments.

The score you get on a developer laptop is the score CI gets. The score CI gets is the score you
track in version control. Determinism is not a feature; it is the foundation on which `zenzic diff`
and regression detection are built.

---

## What's New in rc4

### Ghost Routes — MkDocs Material i18n entry points

When `reconfigure_material: true` is active in the i18n plugin, MkDocs Material
auto-generates locale entry points (e.g. `it/index.md`) that never appear in `nav:`.
The VSM now marks these as `REACHABLE` Ghost Routes, eliminating false orphan warnings
on locale root pages. A `WARNING` is emitted when both `reconfigure_material: true`
and `extra.alternate` are declared simultaneously (redundant configuration).

### VSM Rule Engine — routing-aware lint rules

`BaseRule` gains an optional `check_vsm()` interface. Rules that override it receive
the full pre-built VSM and can validate links against routing state without any I/O.
`RuleEngine.run_vsm()` dispatches all VSM-aware rules and converts `Violation` objects
to the standard `RuleFinding` type for uniform output.

The first built-in VSM rule — `VSMBrokenLinkRule` (code `Z001`) — validates all inline
Markdown links against the VSM. A link is valid only when its target URL is present
and `REACHABLE`. Both "not in VSM" and "UNREACHABLE_LINK" cases produce a structured
`Violation` with file path, line number, and the offending source line as context.

### Content-addressable cache (`CacheManager`)

Rule results are now cached with SHA-256 keying:

| Rule type | Cache key |
| :--- | :--- |
| Atomic (content only) | `SHA256(content) + SHA256(config)` |
| Global (VSM-aware) | `SHA256(content) + SHA256(config) + SHA256(vsm_snapshot)` |

Timestamps are never consulted — the cache is CI-safe by construction. Writes are
atomic (`.tmp` rename). The cache is loaded once at startup and saved once at the end
of a run; all in-run operations are pure in-memory.

### Performance — O(N) torture tests (10k nodes)

The VSM Rule Engine and cache infrastructure are validated at scale: 10,000 links all
valid completes in < 1 s; 10,000 links all broken completes in < 1 s;
`engine.run_vsm` with a 10,000-node VSM completes in < 0.5 s.

---

## What Changed in rc3

### i18n Anchor Fix — AnchorMissing now has i18n fallback suppression

`AnchorMissing` now participates in the same i18n fallback logic as `FileNotFound`. Previously,
a link like `[text](it/page.md#heading)` would fire a false positive when the Italian page existed
but its heading was translated — because the `AnchorMissing` branch in `validate_links_async` had
no suppression path. `_should_suppress_via_i18n_fallback()` was defined but never called.

**Fix:** new `resolve_anchor()` method added to `BaseAdapter` protocol and all three adapters
(`MkDocsAdapter`, `ZensicalAdapter`, `VanillaAdapter`). When an anchor is not found in a locale
file, `resolve_anchor()` checks whether the anchor exists in the default-locale equivalent via
the `anchors_cache` already in memory. No additional disk I/O.

### Shared utility — `remap_to_default_locale()`

The locale path-remapping logic that was independently duplicated in `resolve_asset()` and
`is_shadow_of_nav_page()` is now a single pure function in `src/zenzic/core/adapters/_utils.py`.
`resolve_asset()`, `resolve_anchor()`, and `is_shadow_of_nav_page()` in both `MkDocsAdapter` and
`ZensicalAdapter` all delegate to it. `_should_suppress_via_i18n_fallback()`, `I18nFallbackConfig`,
`_I18N_FALLBACK_DISABLED`, and `_extract_i18n_fallback_config()` — 118 lines of dead code —
are permanently removed from `validator.py`.

### Visual Snippets for custom rule findings

Custom rule violations (`[[custom_rules]]` from `zenzic.toml`) now display the offending source
line below the finding header:

```text
[ZZ-NODRAFT] docs/guide/install.md:14 — Remove DRAFT marker before publishing.
  │ > DRAFT: section under construction
```

The `│` indicator is rendered in the finding's severity colour. Standard findings (broken links,
orphans, etc.) are unaffected.

### JSON schema — 7 keys

`--format json` output now emits a stable 7-key schema:
`links`, `orphans`, `snippets`, `placeholders`, `unused_assets`, `references`, `nav_contract`.

### `strict` and `exit_zero` as `zenzic.toml` fields

Both flags can now be declared in `zenzic.toml` as project-level defaults:

```toml
strict    = true   # equivalent to always passing --strict
exit_zero = false  # exit code 0 even on findings (CI soft-gate)
```

CLI flags continue to override the TOML values.

### Usage docs split — three focused pages

`docs/usage/index.md` was a monolithic 580-line page covering install, commands, CI/CD, scoring,
advanced features, and programmatic API. Split into three focused pages:

- `usage/index.md` — Install options, init→config→check workflow, engine modes
- `usage/commands.md` — CLI commands, flags, exit codes, JSON output, quality score
- `usage/advanced.md` — Three-pass pipeline, Zenzic Shield, alt-text, programmatic API,
  multi-language docs

Italian mirrors (`it/usage/`) updated in full parity.

### Multi-language snippet validation

`zenzic check snippets` now validates four languages using pure Python parsers — no subprocesses
for any language. Python uses `compile()`, YAML uses `yaml.safe_load()`, JSON uses `json.loads()`,
and TOML uses `tomllib.loads()` (Python 3.11+ stdlib). Blocks with unsupported language tags
(`bash`, `javascript`, `mermaid`, etc.) are treated as plain text and not syntax-checked.

### Shield deep-scan — no more blind spots

The credential scanner now operates on every line of the source file, including lines inside
fenced code blocks. A credential committed in a `bash` example is still a committed credential —
Zenzic will find it. The link and reference validators continue to ignore fenced block content to
prevent false positives from illustrative example URLs.

The Shield now covers seven credential families: OpenAI API keys, GitHub tokens, AWS access keys,
Stripe live keys, Slack tokens, Google API keys, and generic PEM private keys.

---

## Professional Packaging & PEP 735

v0.4.0-rc3 adopts the latest Python packaging standards end-to-end, making Zenzic lighter for
end users and measurably faster in CI.

### Lean core install

`pip install zenzic` installs only the five runtime dependencies (`typer`, `rich`,
`pyyaml`, `pydantic`, `httpx`). The MkDocs build stack is not a dependency of `zenzic` —
it is a contributor tool, managed via the `docs` [PEP 735](https://peps.python.org/pep-0735/)
dependency group (`uv sync --group docs`).

For the vast majority of users (Hugo sites, Zensical projects, plain Markdown wikis, CI
pipelines) this means a ~60% smaller install and proportionally faster cold-start times on
ephemeral CI runners.

### PEP 735 — atomic dependency groups

Development dependencies are declared as [PEP 735](https://peps.python.org/pep-0735/) groups
in `pyproject.toml`, managed by `uv`:

| Group | Purpose | CI job |
| :---- | :------ | :----- |
| `test` | pytest + coverage | `quality` matrix (3.11 / 3.12 / 3.13) |
| `lint` | ruff + mypy + pre-commit + reuse | `quality` matrix |
| `docs` | MkDocs stack | `docs` job |
| `release` | nox + bump-my-version + pip-audit | `security` job |
| `dev` | All of the above (local development) | — |

Each CI job syncs only the group it needs. The `quality` job never installs the MkDocs stack.
The `docs` job never installs pytest. This eliminates install time wasted on unused packages
and reduces the surface area for dependency conflicts across jobs. Combined with the `uv`
cache in GitHub Actions, subsequent CI runs restore the full environment in under 3 seconds.

### `CITATION.cff`

A [`CITATION.cff`](CITATION.cff) file (CFF 1.2.0 format) is now present at the repository
root. GitHub renders it automatically as a "Cite this repository" button. Zenodo, Zotero, and
other reference managers that support the format can import it directly.

---

## The Documentation Firewall

v0.4.0-rc3 completes a strategic shift in what Zenzic is. It began as a link checker. It became
an engine-agnostic linter. With rc3, it becomes a **Documentation Firewall** — a single gate that
enforces correctness, completeness, and security simultaneously.

The three dimensions of the firewall:

**1. Correctness** — Zenzic validates the syntax of every structured data block in your docs.
Your Kubernetes YAML examples, your OpenAPI JSON fragments, your TOML configuration snippets — if
you ship broken config examples, your users will copy broken config. `check snippets` catches this
before it reaches production, using the same parsers your users will run.

**2. Completeness** — Orphan detection, placeholder scanning, and the `fail_under` quality gate
ensure that every page linked in the nav exists, contains real content, and scores above the
team's agreed threshold. A documentation site is not "done" when all pages exist — it is done
when all pages are complete.

**3. Security** — The Shield scans every line of every file, including code blocks, for seven
families of leaked credentials. No fencing, no labels, no annotations can hide a secret from
Zenzic. The exit code 2 contract is non-negotiable and non-suppressible: a secret in docs is a
build-blocking incident, not a warning.

This is what "Documentation Firewall" means: not a tool you run once before a release, but a
gate that runs on every commit, enforces three dimensions of quality simultaneously, and exits
with a machine-readable code that your CI pipeline can act on without human interpretation.

---

## The Great Decoupling (v0.4.0-rc2)

The headline change in this release is the **Dynamic Adapter Discovery** system. In v0.3.x,
Zenzic owned its adapters — `MkDocsAdapter` and `ZensicalAdapter` were imported directly by the
factory. Adding support for a new engine required a Zenzic release.

In v0.4.0, Zenzic is a **framework host**. Adapters are Python packages that register themselves
under the `zenzic.adapters` entry-point group. When installed, they become available immediately:

```bash
# Example: third-party adapter for a hypothetical Hugo support package
uv pip install zenzic-hugo-adapter   # or: pip install zenzic-hugo-adapter
zenzic check all --engine hugo
```

No Zenzic update. No configuration change. Just install and use.

The built-in adapters (`mkdocs`, `zensical`, `vanilla`) are registered the same way — there is
no privileged path for first-party adapters. This is not future-proofing; it is a structural
guarantee that the third-party adapter API is exactly as capable as the first-party one.

The factory itself is now protocol-only. `scanner.py` imports zero concrete adapter classes. The
`has_engine_config()` protocol method replaced the `isinstance(adapter, VanillaAdapter)` check
that was the last coupling point. The Core is now genuinely adapter-agnostic.

---

## The [[custom_rules]] DSL

v0.4.0 ships the first version of the project-specific lint DSL. Teams can declare regex rules
in `zenzic.toml` without writing any Python:

```toml
[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Remove DRAFT marker before publishing."
severity = "warning"
```

Rules are adapter-independent — they fire identically with MkDocs, Zensical, or a plain
Markdown folder. Patterns are compiled once at config-load time; there is no per-file regex
compilation overhead regardless of how many rules are declared.

This DSL is the first step toward Zenzic as a complete documentation policy engine, not just a
structural linter.

---

## The Shield (Defence-in-Depth hardening)

The credential scanner (`Shield`) now runs on every non-definition line during Pass 1, not only
on reference URL values. A developer who pastes an API key into a Markdown paragraph — not a
reference link — is caught before any URL is pinged, before any HTTP request is issued, before
any downstream tool sees the credential.

Exit code `2` remains reserved exclusively for Shield events. It cannot be suppressed by
`--exit-zero`, `--strict`, or any other flag. A Shield detection is a build-blocking security
incident — unconditionally.

---

## Documentation as a first-class citizen

The v0.4.0 documentation was itself validated with `zenzic check all` at every step — the
canonical dogfood mandate.

Key structural changes:

- **Configuration split** — the single `configuration.md` god-page decomposed into four focused
  pages: [Overview](docs/configuration/index.md), [Core Settings](docs/configuration/core-settings.md),
  [Adapters & Engine](docs/configuration/adapters-config.md),
  [Custom Rules DSL](docs/configuration/custom-rules-dsl.md).
- **Italian parity** — `docs/it/` now mirrors the full English structure. The documentation
  is production-ready for international teams.
- **Migration guide** — [MkDocs → Zensical](docs/guide/migration.md) four-phase workflow with
  the baseline/diff/gate approach as the migration safety net.
- **Adapter guide** — [Writing an Adapter](docs/developers/writing-an-adapter.md) full
  protocol reference, `from_repo` pattern, entry-point registration, and test utilities.

### Frictionless Onboarding

v0.4.0 introduces `zenzic init` — a single command that scaffolds a `zenzic.toml` with smart
engine discovery. If `mkdocs.yml` is present, the generated file pre-sets `engine = "mkdocs"`.
If `zensical.toml` is present, it pre-sets `engine = "zensical"`. Otherwise the scaffold is
engine-agnostic (Vanilla mode).

```bash
uvx zenzic init        # zero-install bootstrap
# or: zenzic init      # if already installed globally
```

For teams running Zenzic for the first time, a Helpful Hint panel appears automatically when no
`zenzic.toml` is found — pointing directly to `zenzic init`. The hint disappears the moment the
file is created. Zero friction to get started; zero noise once configured.

---

## Upgrade path

### From v0.3.x

No `zenzic.toml` changes are required for MkDocs projects. The adapter discovery is fully
backwards-compatible: `engine = "mkdocs"` continues to work exactly as before.

**One behavioural change:** an unknown `engine` string now falls back to `VanillaAdapter` (skip
orphan check) instead of `MkDocsAdapter`. If your `zenzic.toml` specifies a custom engine name
that mapped to MkDocs behaviour, add the explicit `engine = "mkdocs"` declaration.

### From v0.4.0-alpha.1

The `--format` CLI flag is unchanged. The internal `format` parameter in `check_all`, `score`,
and `diff` Python APIs has been renamed to `output_format` — update any programmatic callers.

---

## Checksums and verification

```text
zenzic check all   # self-dogfood: 7/7 OK
pytest             # 529 passed, 0 failed
coverage           # ≥ 80% (hard gate)
ruff check .       # 0 violations
mypy src/          # 0 errors
mkdocs build --strict  # 0 warnings
```

---

*Zenzic v0.4.0 is released under the Apache-2.0 license.*
*Built and maintained by [PythonWoods](https://github.com/PythonWoods).*

---

Based in Italy 🇮🇹 | Committed to the craft of Python development.
Contact: <dev@pythonwoods.dev>
