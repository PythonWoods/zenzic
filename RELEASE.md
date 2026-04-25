<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# 🛡️ Zenzic v0.7.0 — Obsidian Maturity

## "Engine-Agnostic. Integrity-Complete. The True Safe Harbor."

**Zenzic v0.7.0** marks the consolidation of our core architecture into a definitive,
engine-agnostic documentation integrity shield. This is not an incremental update —
it is a new standard of precision.

**v0.6.x is superseded.** v0.7.0 is the canonical reference for all deployments.

---

## ⚠️ Breaking Changes

| Change | Migration |
| :--- | :--- |
| MkDocs plugin (`zenzic.integrations.mkdocs`) removed | Remove `plugins: - zenzic` from `mkdocs.yml`; add `zenzic check all` as a CI step |
| `engine = "vanilla"` removed | Replace with `engine = "standalone"` in `zenzic.toml` |
| `zenzic plugins` command removed | Use `zenzic inspect capabilities` |

---

## 🚀 The Big Three

### 1. Sovereign Root Protocol

`zenzic check all /path/to/other-repo` now follows the **target's** configuration, not
the caller's working directory. Zenzic loads `zenzic.toml` from the target root and
resolves all paths relative to it. Every `check`, `score`, `diff`, and `init` command
accepts an optional `PATH` argument with sovereign semantics.

**Why it matters:** Monorepos, CI pipelines, and Genesis Nomad workflows (`zenzic init
/path/to/new-project`) all work correctly without shell gymnastics.

### 2. Matrix Laboratory — 17-Act Interactive Showroom

```bash
uvx zenzic lab          # interactive menu
uvx zenzic lab 3        # single act
uvx zenzic lab 11-16    # Red/Blue Team Matrix
uvx zenzic lab all      # full tour
```

The Lab ships 17 documented acts across four thematic sections:

| Section | Acts | Focus |
| :--- | :---: | :--- |
| 🛡 OS & Environment Guardrails | 0–3 | Linting, Shield, clean run |
| 🔗 Structural & SEO Integrity | 4–6 | Single-file, custom dir, proxy |
| 🏢 Enterprise Adapters & Migration | 7–10 | MkDocs, Docusaurus, Zensical, Z404 |
| 🔴 Red/Blue Team Matrix | 11–16 | Attack/defense, obfuscated credentials, stress tests |

### 3. Agnostic Universalism — Z404 Infrastructure Guard

Broken favicon and logo references are now caught for **every engine** — MkDocs
(`theme.favicon`, `theme.logo`), Zensical (`[project].favicon`, `[project].logo`),
and Docusaurus (`themeConfig.navbar.logo`, `themeConfig.footer.logo`). A missing logo
is a broken first impression; Zenzic treats it as a blocking error.

---

## 🛡️ Security

**Closed 4 critical bypass vectors discovered during an AI-driven red-team siege.**

The Red/Blue Team Matrix (Acts 11–16) revealed and verified defences against:
deep `../` path traversal chains targeting OS system directories (Blood Sentinel — exit 3),
credential obfuscation via Base64 encoding, percent-encoding, and mixed-case normalization
(Shield — exit 2), Windows absolute path injection (`C:\`, UNC shares), and cross-line
credential splitting via the ZRT-007 lookback buffer.

**Multi-Root Shield:** Cross-locale relative links no longer trigger false-positive
`PATH_TRAVERSAL_SUSPICIOUS` while preserving detection of links that escape every
authorised root.

---

## 📋 What's New at a Glance

- **Law of Contemporary Testimony** — code and documentation updated in the same commit;
  documentation that contradicts the code is classified as a bug.
- **`zenzic score [PATH]` and `zenzic diff [PATH]`** — full PATH sovereignty for scoring.
- **`--no-color` / `--force-color`** and `NO_COLOR`/`FORCE_COLOR` environment variables.
- **`--offline` mode** — flat URL resolution for USB/intranet deployments.
- **`--quiet` flag** — single-line summary for pre-commit and CI silent builders.
- **Z502 pointer precision** — `❱` arrow skips SPDX licence headers and frontmatter to
  point at the first actual prose word.
- **1 226 passing tests.** REUSE 3.3 compliant. mypy strict. Zero untyped definitions.

---

## 📦 Install

```bash
# One-shot — no install required
uvx zenzic lab

# Project dependency (version-pinned)
uv add --dev zenzic
zenzic check all --strict
```

## 🔗 Resources

- **Documentation:** [zenzic.dev](https://zenzic.dev)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Full history:** [CHANGELOG.archive.md](CHANGELOG.archive.md)

---

Zenzic is developed by **PythonWoods**, based in Italy, and committed to the craft of
high-performance, deterministic Python engineering.
