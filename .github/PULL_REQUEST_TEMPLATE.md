<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD041 -->

## Description

<!-- Describe your changes in detail. Link the issue this PR resolves. -->

Closes #

## Type of change

- [ ] Bug fix
- [ ] New feature (new adapter, check, Shield pattern, CLI flag)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactor (no behaviour change)
- [ ] Test coverage

---

## The Zenzic Way — mandatory checklist

Zenzic's Core is built on three non-negotiable design pillars. Every PR that touches `src/`
must satisfy all that apply.

### 1. Source-first

- [ ] This change operates on **raw source files** only — it does not call `mkdocs build`,
  import a documentation framework, or depend on generated HTML or build artefacts.

### 2. No subprocesses

- [ ] No `subprocess.run`, `os.system`, or equivalent shell calls have been added to the
  linting path (`src/zenzic/core/`).
- [ ] Any new parsers use pure Python stdlib (e.g. `tomllib`, `json`, `yaml.safe_load`,
  `compile()`).

### 3. Pure functions

- [ ] Core validation logic is **deterministic and side-effect-free**: no file I/O, no
  network access, no global state mutations inside pure functions.
- [ ] I/O is confined to CLI wrappers and scanner edges, not to validator or checker modules.

---

## Quality gates

- [ ] `nox -s tests` passes (all existing tests green, coverage ≥ 80%).
- [ ] New behaviour is covered by tests — happy path and at least one failure case.
- [ ] `nox -s lint` and `nox -s typecheck` pass (`ruff check` + `mypy --strict`).
- [ ] `nox -s preflight` passes end-to-end (includes `zenzic check all --strict` self-dogfood).
- [ ] REUSE/SPDX headers are present on every new file (`nox -s reuse`).

---

## Notes for reviewers

<!-- Anything unusual about this PR that reviewers should know? -->
