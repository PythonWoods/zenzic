<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD041 -->

## Description
<!-- Describe the architectural intent of the changes. Link the approved Issue. -->
Closes #

## Type of Change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (fix or feature that breaks backward compatibility)
- [ ] Documentation / D.I.A. update
- [ ] Technical Debt removal / Refactoring

## Engineering Quality Gates

- [ ] **TDD / Tests:** New or updated tests cover these changes. The test suite passes locally.
- [ ] **Static Analysis:** `uv run zenzic check all --strict` passes. The DQS score has not regressed.
- [ ] **D.I.A. (Documentation Impact Analysis):** If this PR modifies CLI, rules, or core behavior, the user documentation has been updated simultaneously.
- [ ] **Zero Subprocess:** No unauthorized shell executions or non-Python dependencies are introduced.

## Enterprise Governance

- [ ] **Issue-First:** This PR addresses an explicitly approved Issue.
- [ ] **Signatures:** Every commit is cryptographically signed (GPG/SSH).
- [ ] **DCO:** Every commit contains a valid `Signed-off-by:` line.
- [ ] **Semantics:** Commit messages follow the Conventional Commits specification.
- [ ] **Absolute Ownership:** I have verified and can architecturally justify every single line of code. No unreviewed AI-generated code is included.
