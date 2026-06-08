# Contributing to Zenzic

Thank you for your interest in contributing to Zenzic!

Zenzic is a documentation quality tool — an engine-agnostic linter and credential scanner
for Markdown and MDX documentation. Contributions that improve detection accuracy, add
new check types, or improve CI/CD integration are especially welcome.

## Two Repositories, Two Doors

Zenzic is split into two independent repositories:

| Repository | Purpose | Stack |
|:-----------|:--------|:------|
| **[zenzic](https://github.com/PythonWoods/zenzic)** (this repo) | Core analysis engine — the Python library and CLI | Python 3.10+, `uv`, `pytest`, `mypy` |
| **[zenzic-doc](https://github.com/PythonWoods/zenzic-doc)** | User-facing documentation site | React, Docusaurus v3, MDX |

**If you want to contribute to the analysis engine** (new checks, adapters, bug fixes,
performance improvements) — you are in the right place.

**If you want to contribute to the documentation** (guides, tutorials, translations) —
head to [zenzic-doc](https://github.com/PythonWoods/zenzic-doc).

> **Brand System** — The visual identity and color palette reference live at
> <https://zenzic.dev/assets/brand/zenzic-brand-system.html>

## Mission

Zenzic is not just a linter. It is a long-term safety layer for documentation teams that
depend on open, auditable source files. We preserve validation continuity across engine
changes (MkDocs, Docusaurus, Zensical, and future adapters) so projects keep control over
their data and quality process regardless of ecosystem churn.

## Contributor Contract

Before proposing rule or docs changes, contributors must validate impact against
the live code registry and tier ownership model.

- **Tier ownership model:** findings are grouped into Core, Structure, and
    Governance domains; keep changes in the correct band.
- **Frozen contract awareness:** do not alter immutable surfaces
    (`FROZEN_CODES`, `NON_SUPPRESSIBLE_CODES`, `PLUGIN_FORBIDDEN_EXITS`) without
    an explicit architecture decision.
- **Inspect-first workflow:** treat `zenzic inspect codes` as the source of
    truth before editing examples, checks tables, or changelog narratives.

---

## Enterprise Governance & Contribution Policy

To maintain the security, architectural integrity, and legal compliance of Zenzic, all contributions must adhere to the following Enterprise Governance guidelines:

1. **Issue-First Policy**: No Pull Request will be reviewed, merged, or discussed unless it is preceded by a corresponding Issue that has been formally discussed and approved by the maintainers. Always link the approved Issue in your PR description.
2. **Mandatory Cryptographic Commit Signatures**: Every commit must be cryptographically signed using GPG, SSH, or S/MIME keypairs (appearing as "Verified" on GitHub). Unsigned commits will be rejected by the merge gates.
3. **No AI Slop Clause**: We enforce a strict policy against unverified AI-generated code. Contributors must fully understand, explain, and architecturally justify every single line of code proposed in a PR. Proposing code that you cannot explain will lead to immediate rejection of the contribution.
4. **Developer Certificate of Origin (DCO)**: All commits must include a `Signed-off-by:` line (using `git commit -s`) to certify compliance with the DCO.
5. **Conventional Commits**: Commit messages must strictly follow the Conventional Commits specification (e.g., `feat: add block anchor support (#123)`).

---

## Prerequisites

| Requirement | Version | Notes |
|:------------|:--------|:------|
| **Python** | ≥ 3.10 | Core engine and CLI (Floor); validated on 3.10 & 3.14-dev in CI |
| **uv** | required | Package manager — `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **just** | required | Task runner — `cargo install just` or via your OS package manager |
| **Node.js** | ≥ 24 | Required for docs CI (`zenzic-doc`) |

The core Python library and CLI work without Node. Node 24 is only needed if you are
contributing to the documentation site or running the full CI suite locally.

---

## Quick start

```bash
git clone git@github.com:PythonWoods/zenzic.git
cd zenzic
just sync
```

`just sync` installs all dependency groups via `uv sync --all-groups`.

Install the pre-commit hooks immediately after sync (mandatory):

```bash
uvx pre-commit install              # commit-stage: light hooks (ruff, format, hygiene)
```

Run the full verification gate before pushing:

```bash
just verify
```

`just verify` is the canonical entry point: pre-commit on all files → `pytest tests/` →
`zenzic check all --strict` → `zenzic score --stamp` → `zenzic score --check-stamp`.
The same sequence runs in GitHub Actions —
**locale ≡ remote, no drift**.

---

## The 4-Lifecycle-Gates Model

Zenzic enforces a deterministic quality pipeline with one atomic
entry-point. `just verify` is the Final Guard/CI gate, while commit hooks run
the light subset:

| Stage | Trigger | What runs | Speed |
|:------|:--------|:----------|:------|
| **TDD inner loop** | `just test` | `pytest -n auto` (no coverage, parallel) | ⚡ instant |
| **Commit** | `git commit` | Light hooks (ruff, format, file hygiene) | < 5 s |
| **Final Guard** | `just verify` (manual or CI) | pre-commit → `pytest tests/` → `zenzic check all --strict` → `zenzic score --stamp` → `zenzic score --check-stamp` | < 60 s |
| **CI** | GitHub Actions | `just verify` (identical) | matches local |

---

## Running tasks

Development tasks use two layers: **just** for interactive speed and **nox** for
reproducible CI isolation. Use `just` day-to-day; use `nox` directly when you need
the exact same environment as CI.

| Task | `just` command | `nox` equivalent | Description |
|:-----|:---------------|:-----------------|:------------|
| Bootstrap | `just sync` | — | Install / update all dependency groups |
| **Self-lint** | **`just check`** | — | **Run Zenzic on its own examples (strict)** |
| Test (fast) | `just test` | — | pytest `-n auto`, no coverage (TDD inner loop) |
| Test (audit) | `just test-cov` | `nox -s tests` | pytest serial + branch coverage JSON (matches CI artifacts) |
| Test (thorough) | `just test-full` | — | pytest with Hypothesis **ci** profile (500 examples) |
| Mutation testing | — | `nox -s mutation` | mutmut on `rules.py`, `credentials.py`, `reporter.py` |
| **Final Guard** | **`just verify`** | — | **pre-commit → `pytest tests/` → `zenzic check all --strict` → `zenzic score --stamp` → `zenzic score --check-stamp`** |
| Show version | `just version` | — | Print current version from bump-my-version |
| Release dry-run | `just release-dry patch` | — | Simulate a bump (full diff output) |
| Release dry-run (compact) | `just release-dry patch --short` | — | Simulate a bump — 3-line summary only |
| Contract check | `just release-contracts` | — | Verify justfile architectural contracts (run by `verify`) |
| Clean | `just clean` | — | Remove `dist/`, `.hypothesis/`, caches |
| Version bump | — | `nox -s bump -- patch` | bump version + commit + tag |

Run the full pre-push gate with:

```bash
just verify
```

Validate code registry expectations during development with:

```bash
zenzic inspect codes
```

> **Nox — Development Checklist**
>
> Zenzic uses Nox to guarantee parity between the local environment and CI. For rapid
> development, use `nox -s fmt` to format and `nox -s tests-3.12` (substituting your Python
> version) to run tests only on your current interpreter.

### Cross-platform compatibility

Current CI validation runs on Ubuntu for eligible push/PR events that match workflow path filters. When working with file
paths in any contribution, use `pathlib.Path` throughout — never string concatenation or
`os.sep`. Key rules:

- `Path("a") / "b"` — always, never `"a" + os.sep + "b"` or `"a/b"` as a string literal.
- Use `.as_posix()` only at the point of comparison against URLs or POSIX-style config values.
- Test fixtures that construct paths must use `tmp_path / "subdir"`, not `"/tmp/subdir"`.
- PRs that introduce `str` path concatenation will be rejected by CI governance checks.

### CI Pillar Matrix

Zenzic adopts a **Pillar Matrix** strategy — testing the boundaries rather than every
intermediate version:

| Slot | OS | Python | Purpose |
|------|----|--------|---------|
| **Floor** | ubuntu-latest | `3.10` | Enforces minimum compatibility. If it passes here, it passes everywhere ≥ 3.10. |
| **Peak** | ubuntu-latest | `3.14` | Peak CPython contract and primary development target. |

Windows/macOS anchors can be enabled as additional matrix slots when cross-platform expansion is scheduled.

If `just verify` passes on your local Python (e.g. 3.11 or 3.13), CI failure is highly
unlikely — the matrix covers the language boundary conditions, not every minor release.

### CI/CD & Workflow

- **Draft PRs:** We run CI exclusively on `main` and Pull Requests to save resources. Open a **Draft PR** early to get continuous CI feedback on your branch.
- **Hooks:** Use `pre-commit` for local mutations. Do not use `post-commit`.
- **Full Guide:** Read the complete workflow in our [Developer Documentation](https://zenzic.dev/developers/how-to/contribute/pull-requests).

---

## Code conventions

- **Python ≥ 3.10** with full type annotations (`mypy --strict` must pass).
- **SPDX header** on every source file — `reuse lint` is enforced in CI.
- No placeholder text, `TODO`, or stub comments in committed code.
- Tests must pass with ≥ 80% branch coverage.
- All PRs should target `main`; avoid direct commits.
- Update `CHANGELOG.md` in the same commit as the code change.

## REUSE Compliance & Copyright

This project is REUSE-compliant and enforced as a merge gate.

- Significant changes (new logic, new content, or substantial refactors) **MUST** add an author copyright line via SPDX.
- Trivial edits (for example, typo-only fixes) do not require adding a new copyright line.
- Any PR that adds new files or significantly modifies existing files without required SPDX attribution is rejected (Exit Code 1 in CI gate policy).

Example header pattern:

```text
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-FileCopyrightText: 2026 Contributor Name <contributor@example.com>
SPDX-License-Identifier: Apache-2.0
```

Legal model:

- No CLA is required.
- Contributions are governed by DCO (Developer Certificate of Origin) plus REUSE/SPDX attribution.
- Contributors retain copyright over significant modifications.

## Security & Compliance

- **Security First:** Any new path resolution MUST be tested against Path Traversal. Use `PathTraversal` logic from `core`.
- **Credential Scanner Obfuscation Tests:** Every new credential pattern or normalizer rule MUST include obfuscation regression tests: Unicode format characters (category Cf), HTML entity encoding, comment interleaving (HTML `<!-- -->` and MDX `{/* */}`), and cross-line split tokens. See `tests/test_credentials_obfuscation.py` for reference.
- **Bilingual Parity:** Documentation lives in [zenzic-doc](https://github.com/PythonWoods/zenzic-doc). Refer documentation contributors there.
- **Machine-Local Config:** Project-specific secrets (forbidden terms for Z204) go in `.zenzic.local.toml` — never committed. Run `zenzic init --local` to generate a fresh local config aligned to your engine version.

### Supply-chain Requirements

Every GitHub Action introduced or modified in this repository must be pinned to
an immutable commit SHA.

Required format:

```yaml
- uses: owner/action-name@0123456789abcdef0123456789abcdef01234567 # vX
```

Mandatory rules:

- Never use floating refs (`@v4`, `@main`, `@master`, `@latest`) in tracked workflow files.
- Keep the version hint comment (`# vX` or `# vX.Y.Z`) for human-readable reviews.
- Dependabot (`package-ecosystem: github-actions`) is the automation authority for SHA refresh.
- PRs that touch workflows must preserve SHA pinning and mention supply-chain impact in the PR description.

For advanced guides on writing new checks, extending adapters, CLI architecture, credential scanner obligations, and mutation testing, see the [Developer Portal](https://zenzic.dev/developers/).

## Documentation

Zenzic's user-facing documentation lives in a separate repository:
**[zenzic-doc](https://github.com/PythonWoods/zenzic-doc)** (Docusaurus v3, React, MDX).

This core repository contains only:

- `README.md` / `README.it.md` — project overview and quick start.
- `CONTRIBUTING.md` / `CONTRIBUTING.it.md` — developer guide (this file).
- `examples/` — maintained fixtures that Zenzic self-validates.

To contribute documentation improvements, open a PR in the `zenzic-doc` repository.

## 🚀 Cross-Repo Validation (Branch Parity Rule)

To ensure consistency between the core engine (**zenzic**) and the documentation (**zenzic-doc**), our CI system enforces the **Rule of Branch Parity**.

### 🔍 How it works

1. **Local Development**: The linter always looks for the core repository in the adjacent folder (`../zenzic`). You are responsible for keeping local branches aligned.
2. **In CI (GitHub Actions)**: The documentation pipeline attempts to clone the core repository by looking for a branch with the **exact same name** as the one being built in the doc repo.
3. **Fallback**: If the mirrored branch is not found in the core repo, the CI will automatically fall back to the `main` branch.

### 🛠️ Operational Summary for Contributors

| Scenario | Required Action | CI Behavior |
| :--- | :--- | :--- |
| **Documentation Fix** | Push only to `zenzic-doc` | Validates against core `main`. |
| **New Feature (Synchronized)** | Push to `zenzic` **BEFORE** pushing to `zenzic-doc` | Validates against the exact feature code. |
| **Naming Convention** | Use identical branch names in both repos | Guarantees perfect "Dogfooding". |

> **Note**: Never push documentation changes that depend on core features not yet present on the remote server (even if on different branches), otherwise the build will fail due to misalignment.

---

## Maintainer Only: Workflow Hardening

### Immutable Pre-Commit Hooks (ADR-089)

All `rev:` keys in `.pre-commit-config.yaml` must point to a **40-char commit
hash**, never to a semantic tag (`v1.2.3`). Git tags are mutable: an upstream
maintainer (or an attacker who compromises one) can move a tag silently,
poisoning the local Gate 2 without any diff in this repository.

This is an **internal CI policy for the Zenzic project**, not a public Zenzic
linter rule: it constrains how *we* develop Zenzic, not how Zenzic users
develop their own documentation. The orchestrator-level enforcement lives in
`just check-pinning` (dependency of `just verify`); violations raise
`[ADR-089] FATAL` at pre-push.

**Threat-model note.** The local risk is strictly smaller than the GHA one
because `pre-commit` clones each hook repo into `~/.cache/pre-commit/` and
freezes it until the user runs `pre-commit autoupdate` or `pre-commit clean`.
GitHub Actions instead re-resolves the ref on every workflow run. Pinning is
still mandatory locally for (a) new-clone safety, (b) architectural parity
with the remote ADR-089 enforcement, (c) auditability.

**Updating pinned hooks.** The naive `pre-commit autoupdate` rewrites SHAs
back to mutable tags, undoing the hardening. Always use:

```bash
uvx pre-commit autoupdate --freeze
```

`--freeze` resolves each tag to its commit SHA and preserves the `# vX.Y.Z`
annotation comment automatically. Commit the diff and verify with
`just check-pinning`.

---

## Maintainer Only: Release Procedure

Releases are **semi-automated**: the developer decides the bump type, one command does the rest.

```bash
# 1. Ensure branch is clean and checks are green
just verify

# 2. Preview version changes (dry-run)
just release-dry patch   # or minor/major

# 3. Apply the version bump, commit, and create tag
just release patch       # or minor/major

# 4. Push commit and tag — this triggers the release workflow
git push && git push --tags
```

### Bump Verification

Before executing the final bump, maintainers must run a dry-run to identify
hardcoded version strings that are not covered by the automation:

```bash
just release-dry patch  # or minor/major
```

Review the diff output. If a file containing a version string (for example a
README example or `SECURITY.md`) is missing from the dry-run diff, it must be
added to the bump configuration before proceeding.

Note on `CHANGELOG.md`: the changelog is excluded from automatic bumping.
Maintainers must manually update the version header and date in the log as the
final act of semantic governance.

The `release.yml` workflow then:

1. Runs `uv build` (sdist + wheel)
2. Packages the brand kit assets (`assets/brand/`)
3. Generates build provenance attestation
4. Creates a GitHub Release with auto-generated notes and attached artifacts

Update `CHANGELOG.md` before bumping: move items from `[Unreleased]` to the new version section.
