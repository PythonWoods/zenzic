<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# 🛡️ Zenzic v0.6.1 — Obsidian Glass

## "Precision, Security, and the new Standalone Standard."

We are proud to announce the stable release of **Zenzic v0.6.1 "Obsidian Glass"**. This version marks a major milestone in our mission to provide the most resilient, engine-agnostic documentation integrity suite for the modern engineering stack.

Documentation should be portable, secure, and verifiable regardless of the build engine you choose. With *Obsidian Glass*, Zenzic breaks the final chains of engine dependency — and speaks a professional language that enterprises can audit.

### 🚀 Key Highlights

#### 1. Standalone Engine — A New Identity

We replaced the informal "Vanilla" mode with a robust **Standalone Engine**, ensuring Zenzic is the perfect companion even for pure Markdown folders that have no build framework at all. The `StandaloneAdapter` is now the canonical engine for framework-free projects, and `zenzic init` writes `engine = "standalone"` automatically when no framework configuration is detected.

> *"We replaced the 'Vanilla' mode with a robust Standalone Engine, ensuring Zenzic is the perfect companion even for pure Markdown folders."*

**Breaking change:** `engine = "vanilla"` in any `zenzic.toml` now raises `ConfigurationError [Z000]`. Update to `engine = "standalone"`.

#### 2. Zenzic Finding Codes (Zxxx)

Introducing **Zenzic Finding Codes**: every diagnostic message now carries a unique `Zxxx` identifier, giving the Sentinel a professional language for enterprise-grade reporting and future tooling integrations.

> *"Introducing Zenzic Finding Codes (Zxxx): giving our Sentinel a professional language for enterprise-grade reporting."*

| Code | Meaning |
|------|---------|
| Z101 | LINK_BROKEN |
| Z201 | SHIELD_SECRET |
| Z401 | MISSING_DIRECTORY_INDEX |
| Z402 | ORPHAN_PAGE |

Full registry: `src/zenzic/core/codes.py`.

#### 3. Interactive Lab (`zenzic lab`)

The `zenzic lab` command is now **menu-driven**. Run it without arguments to see all nine acts and choose what to explore. Run `zenzic lab <N>` to dive straight into a specific scenario.

#### 4. Zensical Transparent Proxy (Legacy Bridge)

Migrating from MkDocs to Zensical? Do it one step at a time. Zenzic now includes a transparent bridge that allows the **Zensical engine** to understand your legacy `mkdocs.yml` structure. No configuration changes required — Zenzic identifies your project and bridges the gap automatically.

#### 2. Docusaurus v3 Multi-Versioning

Zenzic is now a first-class citizen for large-scale Docusaurus projects. We’ve implemented native support for `versions.json` and the `versioned_docs/` directory. Your versioned routes are now automatically tracked in the **Virtual Site Map (VSM)**, ensuring that links to older documentation are validated with the same rigor as your latest release.

#### 3. Global Offline Mode (`--offline`)

Distributed documentation on USB drives? Local intranets without directory-index support? The new `--offline` flag forces all adapters to resolve Markdown sources to flat `.html` files (e.g., `intro.md` → `/intro.html`). Ensure your documentation remains navigable even in air-gapped environments.

#### 4. @site/ Alias Resolution

For Docusaurus users, we’ve added support for the `@site/` path alias. Zenzic now correctly resolves project-relative links like `[logo](@site/static/img/logo.png)` without requiring complex exclusion rules.

### 🛠️ Migration & Call to Action

If you are currently using MkDocs and considering a move to a more modern, TOML-based or MDX-powered architecture, **Zenzic v0.6.1 is your safety net**.

1. Install Zenzic: `uv tool install zenzic`
2. Run `zenzic check all` on your existing MkDocs project.
3. Switch your engine to `zensical` or `docusaurus` and watch Zenzic validate the migration in real-time.

**If you used `engine = "vanilla"`:** update your `zenzic.toml` to `engine = "standalone"` before upgrading.

---

### 🇮🇹 Engineered with Precision

Zenzic is developed by **PythonWoods**, based in Italy, and committed to the craft of high-performance, deterministic Python engineering.

[**Read the Full Documentation →**](https://zenzic.dev)
