---

description: "Extend Zenzic with custom adapters, plugin rules, and integrations."
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Developer Guide

Welcome to the Zenzic engineering community. We build tools that bridge the gap
between human documentation and executable truth. Our codebase follows rigorous
standards for performance, type safety (`mypy --strict`), and accessibility.

This section covers everything you need to extend, adapt, or contribute to Zenzic.

Operational governance and release troubleshooting start here:

- [Governance Playbook: Troubleshooting and Invariants](how-to/release-governance-protocol.md)
- [Shared Sovereign Verification Model](explanation/sovereign-verification-model.md)
- [Supply-Chain Assurance Profile](reference/supply-chain-assurance-profile.md)

---

## In this section

- [Writing Plugin Rules](how-to/write-plugin.md) — implement `BaseRule` subclasses, register

  them via `entry_points`, and satisfy the pickle / purity contract.

- [Writing an Adapter](how-to/implement-adapter.md) — implement the `BaseAdapter` protocol

  to teach Zenzic about a new documentation engine.

- [Example Projects](reference/adapter-examples.md) — four self-contained runnable fixtures that

  demonstrate correct and incorrect Zenzic configurations.

- [Governance Playbook: Troubleshooting and Invariants](how-to/release-governance-protocol.md) —

  Release A CAP policy, suppression rules, and Zenzic failure playbooks.

- [Shared Sovereign Verification Model](explanation/sovereign-verification-model.md) —

  Family-wide nox/just/CI contract: fail-closed core resolution and local == CI.

- [Supply-Chain Assurance Profile](reference/supply-chain-assurance-profile.md) —

  Immediate advanced assurance baseline with auditable controls and runbook commands.

---

## Interactive Workflow with Just

Zenzic uses [`just`](https://github.com/casey/just) as its interactive command runner.
`just` is the fast day-to-day layer; `nox` is the reproducible CI layer underneath.

| Command | Description |
|:--------|:------------|
| `just sync` | Install / update all dependency groups (`uv sync --all-groups`) |
| `just check` | **Self-lint — run Zenzic on its own documentation (strict)** |
| `just test` | Run the test suite (delegates to `nox -s tests`, Hypothesis **dev** profile) |
| `just test-full` | Run the test suite with Hypothesis **ci** profile (500 examples) |
| `just verify` | **Pre-push gate: lint-all + build + verify-codes + strict audit + score stamp + freshness check** |
| `just build` | Build the documentation site (fast, no strict enforcement) |
| `just build-prod` | Build the documentation site (strict mode, mirrors CI) |
| `just serve [port]` | Start the live-reload documentation server (default port 8000) |
| `just clean` | Remove generated artefacts (`site/`, `dist/`, `.hypothesis/`, caches, score file) |

The Zenzic self-linting duty — `just check` — is the first command to run after
any documentation change. Run `just verify` before every push to `main`.

<details>
<summary>Hypothesis profiles</summary>

Property-based tests use [Hypothesis](https://hypothesis.readthedocs.io/) with
three profiles, controlled by the `HYPOTHESIS_PROFILE` environment variable:

| Profile | Examples per test | When to use |
|:--------|------------------:|:------------|
| **dev** (default) | 50 | Day-to-day development (`just test`) |
| **ci** | 500 | CI pipelines and `just test-full` |
| **purity** | 1 000 | Pre-release exhaustive validation |

```bash
just test                          # dev profile (fast)
just test-full                     # ci profile (thorough)
HYPOTHESIS_PROFILE=purity just test  # pre-release
```

</details>

<details>
<summary>Mutation testing</summary>

Use `nox -s mutation` to run [mutmut](https://mutmut.readthedocs.io/) against
`src/zenzic/core/rules.py`. This is deliberately **not** part of `just verify`
— run it manually after working on the rule engine:

```bash
nox -s mutation
```

</details>

---

## Contributing

Full contribution guidelines, code conventions, Core Laws, and the pre-PR checklist
are in [`CONTRIBUTING.md`](https://github.com/PythonWoods/zenzic/blob/main/CONTRIBUTING.md)
on GitHub.

When you open a pull request, GitHub automatically loads the
[PR checklist](https://github.com/PythonWoods/zenzic/blob/main/.github/PULL_REQUEST_TEMPLATE.md)
— verify all items before requesting a review.
