# Zenzic — Agent Guidelines

Zenzic is an engine-agnostic linter and security shield for Markdown documentation (Docusaurus v3, MkDocs, Zensical, bare Markdown). It ships as a CLI (`zenzic`), a Python library, and a native MkDocs plugin. Python ≥ 3.11 required.

## Build & Test

```bash
uv sync --all-groups          # install all dependency groups (once after clone)
just test                     # run tests — Hypothesis dev profile (50 examples)
just test-full                # CI-grade run (500 examples)
just preflight                # full local CI: lint + format + typecheck + pytest + reuse
just verify                   # preflight + self-lint (zenzic check all --strict)
```

Common individual sessions:

```bash
nox -s lint -- --fix          # ruff autofix
nox -s fmt                    # ruff format in-place
nox -s typecheck              # mypy --strict on src/
nox -s reuse                  # SPDX/REUSE compliance check
```

See [justfile](../justfile) for the full recipe list and [noxfile.py](../noxfile.py) for session definitions.

## Architecture

```text
src/zenzic/
├── main.py / cli.py          # Typer CLI (commands: check, score, diff)
├── core/                     # Hot-path analysis engine (zero I/O — see Core Laws)
│   ├── adapter.py            # BaseAdapter Protocol + RouteMetadata
│   ├── adapters/             # docusaurus_v3, mkdocs, zensical, vanilla
│   ├── discovery.py          # Universal file discovery (os.walk + LayeredExclusionManager)
│   ├── exclusion.py          # LayeredExclusionManager (4-level: System → VCS → Config → CLI)
│   ├── rules.py              # AdaptiveRuleEngine + O(V+E) circular detection
│   ├── shield.py             # Credential scanner (9 families, 8-step normalization, lookback buffer)
│   ├── resolver.py           # InMemoryPathResolver (link resolution)
│   ├── scanner.py            # Two-Pass Reference Pipeline (Harvest → Cross-Check → Report)
│   └── validator.py          # validate_links_async orchestrator
├── models/                   # Pydantic models (config, references, vsm)
└── integrations/mkdocs.py    # Native MkDocs plugin
```

Third-party adapters and rules are discoverable via `zenzic.adapters` / `zenzic.rules` entry-point groups.

## Core Laws

1. **Zero I/O in the hot path**: nothing inside `src/zenzic/core/` may call `Path.exists()`, `open()`, or subprocesses inside per-link or per-file loops. Only two I/O phases are permitted: `discovery.py` file enumeration (via `os.walk` + `LayeredExclusionManager`) and `InMemoryPathResolver.__init__`.
2. **Subprocess-free linting**: `zenzic check` never calls `mkdocs build` or any external process.
3. **Mandatory ExclusionManager**: every file-discovery entry point requires a `LayeredExclusionManager` argument — no `Optional`, no `None` default. Omitting it is a `TypeError` at call time, not a silent full-tree scan at runtime.

Violating any of these laws is a blocking defect — do not introduce exceptions.

## Code Conventions

- **Type checking**: `mypy --strict` must pass on all of `src/`. Never suppress with `# type: ignore` without a comment explaining why.
- **Linting**: ruff rules `E, F, W, I, B, C4, UP, A`; line length 100; isort `known-first-party = ["zenzic"]`.
- **SPDX headers**: every source file must start with `# SPDX-FileCopyrightText: ...` and `# SPDX-License-Identifier: Apache-2.0`. Run `nox -s reuse` to verify.
- **No stubs**: no `TODO`, placeholder text, or stub implementations in committed code.
- **Coverage**: ≥ 80% branch coverage enforced by pytest. Mutation goal ≥ 90% on `rules.py`, `shield.py`, `reporter.py`.
- **Discovery**: never use `Path.rglob()` or `glob.glob()` directly. All file enumeration goes through `discovery.iter_markdown_sources()` or `discovery.walk_files()` with a `LayeredExclusionManager`.

## Tests

- Tests live in `tests/`; helpers in `tests/_helpers.py`; fixtures in `tests/conftest.py`.
- Hypothesis profiles: `dev` (50), `ci` (500), `purity` (1000) — set via `HYPOTHESIS_PROFILE`.
- Markers: `slow`, `integration` — run with `-m "not slow"` to skip heavy tests locally.
- The `_reset_zenzic_logger` autouse fixture resets the `RichHandler` after each test; do not remove it.

## Key Docs

- [CONTRIBUTING.md](../CONTRIBUTING.md) — dev workflow, PR conventions, Core Laws reference
- [SECURITY.md](../SECURITY.md) — vulnerability reporting and scope
- [CHANGELOG.md](../CHANGELOG.md) — version history
- [RELEASE.md](../RELEASE.md) — release checklist
