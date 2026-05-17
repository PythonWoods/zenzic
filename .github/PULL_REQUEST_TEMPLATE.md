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

Zenzic's Core is built on four non-negotiable design pillars. Every PR that touches `src/`
must satisfy all that apply.

### 1. Determinism & Pure Functions

- [ ] Core validation logic is **deterministic and side-effect-free**: same input always
  produces the same output, with no file I/O, network access, or global state mutations
  inside pure functions.
- [ ] I/O is confined to CLI wrappers and scanner edges — never inside validator, checker,
  or rule modules.

### 2. Zero Subprocess

- [ ] No `subprocess.run`, `os.system`, `os.popen`, or equivalent shell calls have been
  added anywhere in the linting path (`src/zenzic/core/`).
- [ ] Any new parsers use pure Python stdlib (e.g. `tomllib`, `json`, `yaml.safe_load`).

### 3. ReDoS Immunity

- [ ] All new regex patterns use **`zenzic.core.regex`** (the RE2-backed ACL facade) —
  direct `import re` is forbidden in governed paths (`src/zenzic/` and `tests/`),
  and family-repository tooling must preserve the same ACL contract.
- [ ] New patterns are pre-compiled as module-level constants (`_NAME_RE = re.compile(...)`);
  no inline raw-string compilation inside loops or hot paths.

### 4. Namespace Contract

- [ ] New finding codes respect the **Frozen Codes** list (`FROZEN_CODES` in `codes.py`):
  existing codes are immutable; new codes follow the Tier Model (`Z4xx` Structure,
  `Z6xx` Governance).
- [ ] No code previously in `FROZEN_CODES` has been removed, renamed, or had its
  suppressibility changed.

---

## Quality gates

- [ ] `just verify` passes end-to-end (pre-commit + coverage ≥ 80% + `zenzic check all --strict` self-dogfood).
- [ ] New behaviour is covered by tests — happy path and at least one failure case.
- [ ] `nox -s lint` passes (`ruff check` + `mypy --strict`).
- [ ] REUSE/SPDX headers are present on every new file.

---

## Notes for reviewers

<!-- Anything unusual about this PR that reviewers should know? -->
