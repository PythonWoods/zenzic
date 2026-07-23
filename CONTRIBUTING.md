# Contributing to Zenzic

Thank you for your interest in contributing to Zenzic!

Zenzic is a Deterministic Document Integrity Engine and SAST platform for Markdown/MDX graphs, organized as a unified monorepo:

| Component | Path | Description | Tech Stack |
| :--- | :--- | :--- | :--- |
| **Core Engine** | [`core/`](core/) | Python library, AST analyzer, VSM topology engine, CLI | Python 3.10+, `uv`, `pytest`, `mypy` |
| **VS Code Extension** | [`vscode/`](vscode/) | Real-time LSP client and inline diagnostics UI | TypeScript, Node.js, `@vscode/vsce` |
| **GitHub Action** | [`actions/`](actions/) | Offical GitHub Action quality gate runner | YAML, Bash, `uvx` |

---

## Contributor Contract

Before proposing rule, code, or documentation changes, contributors must validate impact against the live code registry and architectural constraints:

- **Tier ownership model:** findings are grouped into Core, Structure, and Governance domains; keep changes in the correct band.
- **Frozen contract awareness:** do not alter immutable surfaces (`FROZEN_CODES`, `NON_SUPPRESSIBLE_CODES`, `PLUGIN_FORBIDDEN_EXITS`) without an explicit architecture decision (ADR).
- **Inspect-first workflow:** treat `zenzic inspect codes` as the source of truth before editing examples, checks tables, or changelog narratives.

---

## Enterprise Governance & Contribution Policy

To maintain the security, architectural integrity, and legal compliance of Zenzic, all contributions must adhere to the following Enterprise Governance guidelines:

1. **Issue-First Policy**: No Pull Request will be reviewed, merged, or discussed unless it is preceded by a corresponding Issue that has been formally discussed and approved by the maintainers. Always link the approved Issue in your PR description.
2. **Mandatory Cryptographic Commit Signatures**: Every commit must be cryptographically signed using GPG, SSH, or S/MIME keypairs (appearing as "Verified" on GitHub). Unsigned commits will be rejected by the merge gates.
3. **No AI Slop Clause**: We enforce a strict policy against unverified AI-generated code. Contributors must fully understand, explain, and architecturally justify every single line of code proposed in a PR. Proposing code that you cannot explain will lead to immediate rejection of the contribution.
4. **Developer Certificate of Origin (DCO)**: All commits must include a `Signed-off-by:` line (using `git commit -s`) to certify compliance with the DCO.
5. **Conventional Commits**: Commit messages must strictly follow the Conventional Commits specification (e.g., `feat(core): add block anchor support (#123)`).

---

## First-Time Setup & Prerequisites

| Requirement | Minimum Version | Component |
| :--- | :--- | :--- |
| **Python** | ≥ 3.10 | Core Engine & CLI (`core/`) |
| **uv** | Latest | Package Manager — `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **just** | Latest | Task Runner — `cargo install just` or via package manager |
| **Node.js** | ≥ 24 | VS Code Extension (`vscode/`) & Documentation Site |

```bash
git clone git@github.com:PythonWoods/zenzic.git
cd zenzic

# Sync dependencies across all workspace projects
just sync

# Install pre-commit hooks (commit stage + pre-push verification)
uvx pre-commit install
uvx pre-commit install -t pre-push
```

### Git Commit Signing Setup

Configure SSH commit signing (required — all commits must appear **Verified** on GitHub):

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub   # adjust path if different
git config --global commit.gpgsign true
```

Register your public key as a **Signing Key** at <https://github.com/settings/ssh>.

---

## Local Verification Recipes

Use `just` to run component-specific and monorepo-wide verification tasks:

```bash
# Python Core Engine
just test              # Run core unit tests (pytest)
just check             # Run core quality gate

# VS Code Extension
just vscode-lint       # Run ESLint & REUSE license check
just vscode-build      # Compile TypeScript and package .vsix artifact

# GitHub Action
just action-verify     # Run action verification suite & DQS gate

# Monorepo Full Audit Gate
just verify            # Run complete monorepo verification suite
```

---

## Component Contribution Guidelines

### 1. Python Core (`core/`)

- Place scanner logic in `core/src/zenzic/core/scanner.py` and validator rules in `core/src/zenzic/core/validator.py`.
- Ensure all hot-path link resolution delegates to `InMemoryPathResolver` — zero syscalls or `os.path.exists()` calls inside per-link resolution loops.
- Add unit tests in `core/tests/`.

### 2. VS Code Extension (`vscode/`)

- Client logic resides in `vscode/src/extension.ts`.
- Ensure language server parameters align with `zenzic lsp` output schema.

### 3. GitHub Action (`actions/`)

- Runner wrapper script lives in `actions/zenzic-action-wrapper.sh`.
- Exit code contracts (`2` credential leak, `3` path traversal) are non-suppressible and must propagate to action exit state.
