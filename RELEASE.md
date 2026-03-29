<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic v0.4.0: The Agnostic Framework for Documentation Integrity

**Release date:** 2026-03-28
**Status:** Release Candidate 2 — ready for shipment

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
- **Migration guide** — [MkDocs → Zensical](docs/guides/migration.md) four-phase workflow with
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
zenzic check all   # self-dogfood: 6/6 OK
pytest             # 433 passed, 0 failed in 2.47s
coverage           # 98.4% line coverage
ruff check .       # 0 violations
mypy src/          # 0 errors
```

---

*Zenzic v0.4.0 is released under the Apache-2.0 license.*
*Built and maintained by [PythonWoods](https://github.com/PythonWoods).*

---

Based in Italy 🇮🇹 | Committed to the craft of Python development.
Contact: <dev@pythonwoods.dev>
