<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

# Security Policy

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability in Zenzic — including issues with the **Shield**
credential scanner, the **path traversal** protection, or any other part of the Core —
report it privately via one of these channels:

- **GitHub Security Advisories** (preferred): [github.com/PythonWoods/zenzic/security/advisories](https://github.com/PythonWoods/zenzic/security/advisories)
- **Email**: `dev@pythonwoods.dev` — subject line: `[SECURITY] Zenzic — <brief description>`

Please include a clear description of the vulnerability, steps to reproduce, potential
impact, and a suggested fix if available.

We will acknowledge your report within **72 hours** and aim to release a patch within
**14 days** of confirming the issue.

## Scope

The following areas are in-scope for security reports:

| Area | Description |
| :--- | :---------- |
| **Shield bypass** | A credential pattern that passes undetected through the seven-family scanner |
| **Path traversal bypass** | A crafted link that escapes the `docs/` root without triggering `PathTraversal` |
| **Dependency CVE** | A known CVE in a runtime dependency (`typer`, `rich`, `pyyaml`, `pydantic`, `httpx`) |
| **Code execution** | A crafted Markdown or config file that causes arbitrary code execution during linting |
| **Exit code suppression** | Any method that prevents exit code `2` from being emitted on a Shield finding |

Out-of-scope: documentation content errors, cosmetic output formatting, or issues that
only affect `nox` development sessions (not the published `zenzic` package).

## Security design notes

Zenzic v0.4.0+ has **no subprocess calls** in the linting path. The tool reads raw source
files and performs all analysis in pure Python. It does not execute `mkdocs build` or any
other build tool during `check`, `score`, or `diff`. The attack surface is limited to:

- **Crafted Markdown files** — Zenzic parses Markdown with a pure state-machine; the path
  traversal shield rejects any href that resolves outside `docs/`.
- **Crafted config files** — `zenzic.toml`, `mkdocs.yml`, and `zensical.toml` are parsed
  as plain data (TOML/YAML). No code is evaluated. Custom rules (`[[custom_rules]]`) are
  plain regex patterns compiled once at load time.
- **Dependencies** — run `nox -s security` (pip-audit) regularly to detect known CVEs in
  the dependency tree.

## Supported versions

| Version | Support status |
| :------ | :------------- |
| `0.7.x` (current) | ✅ All security fixes |
| `0.6.x` | ⚠️ Critical security fixes only |
| `< 0.6` | ❌ End of life — no support |

## Disclosure policy

We follow a **coordinated disclosure** model. We ask that you allow up to 14 days for a
patch to be released before any public disclosure. Confirmed reporters will be credited in
the release changelog unless they prefer to remain anonymous.
