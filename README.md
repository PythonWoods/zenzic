<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

<p align="center">
  <img src="assets/brand/svg/zenzic-wordmark.svg#gh-light-mode-only" alt="Zenzic" width="360">
  <img src="assets/brand/svg/zenzic-wordmark-dark.svg#gh-dark-mode-only" alt="Zenzic" width="360">
</p>

<p align="center">
  <a href="https://pypi.org/project/zenzic/">
    <img src="https://img.shields.io/pypi/v/zenzic?label=PyPI&color=38bdf8&style=flat-square" alt="PyPI Version">
  </a>
  <a href="https://pypi.org/project/zenzic/">
    <img src="https://img.shields.io/pypi/pyversions/zenzic?color=10b981&style=flat-square" alt="Python Versions">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-Apache--2.0-0d9488?style=flat-square" alt="License">
  </a>
</p>

<p align="center">
  <a href="https://github.com/PythonWoods/zenzic/actions/workflows/ci.yml">
    <img src="https://github.com/PythonWoods/zenzic/actions/workflows/ci.yml/badge.svg" alt="zenzic-audit">
  </a>
  <!-- zenzic:badge -->
  <img src="https://img.shields.io/badge/%F0%9F%9B%A1%EF%B8%8F_zenzic--score-100_%2F_100-4f46e5?style=flat-square" alt="zenzic-score">
  <a href="https://docusaurus.io/">
    <img src="https://img.shields.io/badge/docs_by-Docusaurus-3ECC5F?style=flat-square" alt="Built with Docusaurus">
  </a>
  <a href="https://reuse.software/">
    <img src="https://img.shields.io/badge/REUSE-3.x%20compliant-0d9488?style=flat-square" alt="REUSE 3.x compliant">
  </a>
</p>

<p align="center">
  <strong>Deterministic audit of documentation structures with bidirectional traceability.</strong><br>
  <em>Tiered code governance, frozen security contracts, and RE2-backed deterministic scanning.</em>
</p>

---

## ⚡ Try it now — Zero Installation

Got a folder of Markdown files? Run an instant security and link audit using [`uv`][uv]:

```bash
uvx zenzic check all ./your-folder
```

Zenzic identifies your engine via its configuration files or defaults to **Standalone Mode**
for plain Markdown folders — providing immediate protection for links, credentials, and
file integrity.

---

## 🚀 Quick Start

```bash
pip install zenzic
cd my-docs-repo
zenzic init       # Establish the workspace boundary (creates zenzic.toml)
zenzic check all  # Audit the current directory
```

## 🧠 Core Pillars

- **Pure, deterministic engine:** identical inputs produce identical findings and exits.
- **Tiered code model:** Core, Structure, and Governance findings separated by ownership bands.
- **Frozen contracts for integrators:** `FROZEN_CODES`, `NON_SUPPRESSIBLE_CODES`, and `PLUGIN_FORBIDDEN_EXITS` provide stable enforcement surfaces for CI and plugins.
- **Inspect-first workflow:** use `zenzic inspect codes` to validate live code semantics before touching docs or release notes.

📖 [Full docs →][docs-home] · 🏅 [Badges][docs-badges] · 🔄 [CI/CD guide][docs-cicd]

---

## ⚙️ Commands Overview

| Command | Purpose |
| :--- | :--- |
| `zenzic init` | Scaffold workspace configuration (`.zenzic.toml`) |
| `zenzic check all [PATH]` | Full documentation audit — links, credentials, orphans |
| `zenzic score [--fail-under N] [--stamp]` | Compute the Documentation Quality Score (0–100) |
| `zenzic diff [--base PATH]` | Detect debt regression against a saved baseline |
| `zenzic guard scan [PATH]` | Defense-in-Depth credential pre-gate (always fatal) |
| `zenzic inspect codes` | Query live error-code semantics and suppressibility |

---

> 🚀 **CI/CD Ready:** Use the [Official Zenzic Action](https://github.com/PythonWoods/zenzic-action) to run Zenzic in GitHub Actions — findings surface directly in Code Scanning, PR annotations, and the Security tab.
>
> ```yaml
> - uses: PythonWoods/zenzic-action@v1
>   with:
>     format: sarif
>     upload-sarif: "true"
> ```

<p align="center">
  <img alt="GitHub Code Scanning showing Zenzic findings" src="https://raw.githubusercontent.com/PythonWoods/zenzic-action/main/assets/sarif-showcase.svg" width="760">
</p>

---

## 🔌 Multi-Engine Support

| Engine | Adapter | Highlights |
| :--- | :--- | :--- |
| [Docusaurus v3][docusaurus] | `DocusaurusAdapter` | Versioned docs, `@site/` alias, Ghost Route detection |
| [MkDocs][mkdocs] | `MkDocsAdapter` | i18n suffix + folder modes, `fallback_to_default` |
| [Zensical][zensical] | `ZensicalAdapter` | Transparent Proxy bridges `mkdocs.yml` |
| Any folder | `StandaloneAdapter` | File integrity checks — orphan detection disabled without a nav contract |

See the [Adapter API][docs-arch] for the plugin interface. Third-party adapters install via the `zenzic.adapters` entry-point group.

---

## ⚙️ Configuration

Zero-config by default. See the [Configuration Guide][docs-home] for the full `zenzic.toml` schema and `pyproject.toml` embedding.

```bash
zenzic init        # Generate zenzic.toml with auto-detected values
```

---

## 🔄 CI/CD Integration

```yaml
- uses: PythonWoods/zenzic-action@v1
  with:
    format: sarif
    upload-sarif: "true"
```

For zero-install `uvx` integration and regression gates, see the [CI/CD guide][docs-cicd].

---

## 📦 Installation

```bash
# Zero-install, one-shot audit (recommended for CI and exploration)
uvx zenzic check all ./docs

# Global CLI tool
uv tool install zenzic

# Pinned dev dependency
uv add --dev zenzic

# pip
pip install zenzic
```

---

## 📖 Documentation

| Area | URL | Audience |
| :--- | :--- | :--- |
| 👤 User Guide | [zenzic.dev/docs][docs-home] | Install, configure, CI/CD, finding codes |
| 🔧 Developer Portal | [zenzic.dev/developers][docs-developers] | Adapters, ADRs, CLI architecture, mutation testing |
| 🛡️ Security | [Engineering Ledger][docs-eng-ledger] · [SECURITY.md][security] | Security reviewer |

---

## 🤝 Contributing

1. Open an [issue][issues] to discuss the change.
2. Read the [Contributing Guide][contributing].
3. Every PR must pass `just verify` and include SPDX headers on new files.

See also: [Code of Conduct][coc] · [Security Policy][security]

## 📎 Citing

A [`CITATION.cff`][citation-cff] is present at the root. Click **"Cite this repository"** on GitHub for APA or BibTeX output.

## 📄 License

Apache-2.0 — see [LICENSE][license].

---

<div align="center">
  <a href="https://zenzic.dev">
    <img src="https://raw.githubusercontent.com/PythonWoods/zenzic/main/assets/brand/pythonwoods-logo.svg" alt="PythonWoods" height="50" />
  </a>
  <p>
    <strong>Engineered with precision by PythonWoods in Italy 🇮🇹</strong><br/>
    <em>"Building the Standard for Technical Document Integrity."</em>
  </p>
  <p>
    <a href="https://zenzic.dev"><strong>Documentation</strong></a> &middot;
    <a href="https://github.com/PythonWoods"><strong>GitHub</strong></a> &middot;
    <a href="https://zenzic.dev/blog"><strong>Blog</strong></a>
  </p>
</div>

<!-- ─── Reference link definitions ──────────────────────────────────────────── -->

[mkdocs]:            https://www.mkdocs.org/
[docusaurus]:        https://docusaurus.io/
[zensical]:          https://zensical.org/
[uv]:                https://docs.astral.sh/uv/
[docs-home]:         https://zenzic.dev/docs/
[docs-badges]:       https://zenzic.dev/docs/how-to/add-badges/
[docs-cicd]:         https://zenzic.dev/docs/how-to/configure-ci-cd/
[docs-arch]:         https://zenzic.dev/developers/explanation/engineering-ledger
[docs-developers]:   https://zenzic.dev/developers/
[docs-eng-ledger]:   https://zenzic.dev/developers/explanation/engineering-ledger
[contributing]:      CONTRIBUTING.md
[license]:           LICENSE
[citation-cff]:      CITATION.cff
[coc]:               CODE_OF_CONDUCT.md
[security]:          SECURITY.md
[issues]:            https://github.com/PythonWoods/zenzic/issues
