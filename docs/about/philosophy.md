---
icon: lucide/lightbulb
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Philosophy

## Documentation is infrastructure

Source code has compilers, type checkers, and linters that prevent broken code from reaching
production. Documentation has historically had none of these. A broken link, a leaked credential,
or a stub page that was never completed can ship to users without any automated gate catching it.

Zenzic exists to close that gap. Documentation health should be measurable, deterministic, and
rigorously enforced — caught with the same mathematical certainty as a type error in source code.

---

## The Safe Harbor principle

The documentation tooling ecosystem is not stable. MkDocs introduces breaking changes. New build
systems emerge. Teams migrate from one generator to another. In this environment, a quality tool
that is tightly coupled to a specific build engine creates a dangerous dependency: when the engine
changes, the quality gate breaks, and projects are left without verification during the exact
window when mistakes are most likely.

Zenzic is designed to be a **Safe Harbor** — a fixed, stable point that remains valid before,
during, and after a build engine migration. This is not a coincidental feature; it is the core
architectural commitment.

The implementation of this commitment is **absolute engine-agnosticism**:

- Zenzic reads raw Markdown files and configuration as plain data. It never imports or executes a
  documentation framework.
- Engine-specific knowledge (nav structure, i18n conventions, locale fallback rules) is
  encapsulated in **adapters** — thin, replaceable components that translate engine semantics into
  a neutral protocol. The Core never sees a `MkDocsAdapter` or `ZensicalAdapter` — it sees only
  a `BaseAdapter` that answers five questions.
- Third-party adapters install as Python packages and are discovered at runtime via entry-points.
  Adding support for a new engine (Hugo, Docusaurus, Sphinx) requires no Zenzic release.

The practical consequence: a project migrating from MkDocs to Zensical can run `zenzic check all`
continuously against both configurations simultaneously. A project that has not yet decided on a
build engine can still validate its documentation quality today.

---

## The frictionless sentinel

A linter is only as good as its false-positive rate. When tools blindly raise errors, developers
learn to ignore them — and a tool that is ignored provides no safety.

Zenzic's architecture is designed around a single constraint: **every finding must be
actionable**. This shapes several decisions:

- **In-memory multi-pass algorithms.** The Two-Pass Reference Pipeline separates definition
  harvesting from usage checking, eliminating the false positives caused by forward references
  that a naive single-pass scanner would produce.
- **i18n fallback awareness.** A link from a translated page to a default-locale asset is not a
  broken link — the build engine will serve the fallback at runtime. Zenzic suppresses it.
- **Vanilla mode for nav-agnostic projects.** When Zenzic has no nav declaration to compare
  against, it skips the orphan check entirely rather than flagging every file as an orphan.

The goal is a tool that is **utterly silent when your documentation is sound**, and surgically
precise when it is not.

---

## Determinism as a first-class property

Quality scores are worthless if they are not reproducible. Zenzic guarantees that for any given
documentation state, it always produces the same score — no nondeterminism from network state,
build artifacts, or filesystem ordering.

This determinism is what makes `zenzic diff` reliable. Tracking a score over time only makes
sense if the score is computed by a pure function of the source files. The `--save` / `diff`
workflow is built entirely on this guarantee.

---

## Security is not optional

Credential leaks in documentation are a real attack vector. A developer copies an API key into a
Markdown example and commits it. The reference pipeline's **Shield** component addresses this
directly: every reference URL is scanned for known credential patterns during Pass 1, before any
HTTP request is issued and before any downstream processing touches the URL.

Exit code `2` is reserved exclusively for security events. It can never be suppressed by
`--exit-zero`, `--strict`, or any other flag. A Shield detection is a build-blocking security
incident — by design.

---

*Zenzic is proudly built and maintained by PythonWoods, dedicated to crafting resilient tools
for the Python ecosystem.*
