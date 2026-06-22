---

sidebar_position: 6
description: "Family-wide nox/just/CI contract for deterministic local/CI parity and fail-closed core resolution."
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Shared Sovereign Verification Model

This page defines the shared verification contract used across the zenzic family
repositories (`zenzic`, `zenzic-doc`, `zenzic-action`).

The intent is operational determinism: local and CI must run the same logic
against the same core semantics.

---

## 1) Why this model exists

- Prevent local/CI behavioral drift.
- Prevent stale published-core execution in repository quality gates.
- Keep contributor expectations explicit, auditable, and stable over time.

This model is mandatory for repository gates (not optional guidance).

---

## 2) Core Resolution Contract

Resolution order is sovereign and deterministic:

1. Explicit override: `ZENZIC_CORE_PATH`
2. CI topology: `./_zenzic_core`
3. Sibling development topology: `../zenzic`

Validation rule:

- Every candidate path must contain `src/zenzic`.

Fail-closed rule:

- If no candidate is valid, verification stops with an explicit error.
- PyPI fallback is prohibited in repository quality gates.

---

## 3) CI Topology Contract

CI workflows must:

1. Resolve branch parity against the core repository (target branch first,
   fallback to `main` only when target branch does not exist in core).
2. Checkout core to `./_zenzic_core`.
3. Run the same verification entrypoint used locally (`just verify`).

Recommended explicitness:

- Export `ZENZIC_CORE_PATH=_zenzic_core` in the verify step environment.
- For repositories with non-homonymous branch naming, set
  `ZENZIC_CORE_REF` as an explicit CI override.
- Governed override metadata is mandatory when `ZENZIC_CORE_REF` is used:
  `ZENZIC_CORE_REF_TICKET`, `ZENZIC_CORE_REF_REASON`,
  `ZENZIC_CORE_REF_APPROVER`, `ZENZIC_CORE_REF_EXPIRES_ON`.
- Fail-closed applies to every override path: missing metadata, malformed
  expiry date, expired override, or non-existent branch in core must stop CI.

---

## 4) Layer Responsibilities

| Layer | Required behavior | Non-negotiable invariant |
|---|---|---|
| `justfile` | Primary operator entrypoint (`check`, `verify`) | Uses sovereign resolution order and fail-closed stop |
| `noxfile.py` | Deterministic automation wrapper for sessions | Uses the same sovereign order as `justfile` |
| `.github/workflows/*.yml` | Shared execution topology | Checks out `_zenzic_core` before running verify |
| `release-contracts` recipe | Drift guard | Rejects PyPI fallback patterns and auto-tagging in release paths |

---

## 5) Contributor Runbook

For the step-by-step setup procedure on how to configure your local workspace and run the verification suite, see the [Contributor Runbook in the Release Protocol](../how-to/release-governance-protocol.md#contributor-runbook-local-setup).

---

## 6) Anti-Drift Policy

The following are prohibited in repository quality gates:

- `uvx zenzic@...` fallback as a substitute for local core semantics.
- Temporary config workarounds used to mask core-version drift.
- Divergent local and CI verification entrypoints.

Temporary compatibility shims are allowed only as short-lived transitions and
must be removed once structural parity is restored.
