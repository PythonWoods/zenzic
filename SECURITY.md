<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

# Security Policy

## Reporting Security Issues

The Zenzic team takes security seriously. If you discover a vulnerability, please report it responsibly — **do not open a public issue**.

### How to Report

- **GitHub Security Advisories**: Open a private advisory at [github.com/PythonWoods/zenzic/security/advisories](https://github.com/PythonWoods/zenzic/security/advisories)
- **Email**: `dev@pythonwoods.dev` with `[SECURITY]` in the subject line

### What to Include

- Clear description of the vulnerability
- Steps to reproduce
- Potential impact and scope
- Suggested remediation (if available)

## Response Process

1. Acknowledgment within 48 hours
2. Investigation and validation
3. Fix development and testing
4. Coordinated disclosure

Initial triage and plan within 72 hours.

## Supported Versions

Only the latest release and the `main` branch receive active security updates.

## Security Notes

Zenzic is a CLI tool that reads local files and runs `mkdocs build` as a subprocess. It does not handle credentials, network requests, or user-supplied data from external sources. The primary security surface is:

- **Subprocess execution**: `mkdocs build --strict` is invoked with the repository's own `mkdocs.yml` — only run Zenzic against repositories you trust.
- **Dependencies**: keep dependencies up to date; run `nox -s security` (pip-audit) regularly to detect known CVEs.
- **Path Traversal Protection**: Zenzic v0.3.0+ implements the Zenzic Shield inside `InMemoryPathResolver`. While Zenzic mitigates unauthorized file access via crafted Markdown links (e.g. `../../../../etc/passwd`), Zenzic is a static analysis tool; it does not replace filesystem-level permissions.
- **Path Traversal Protection**: Zenzic v0.3.0+ implements the Zenzic Shield inside `InMemoryPathResolver`. While we mitigate unauthorised file access via crafted Markdown links (e.g. `../../../../etc/passwd`-style hrefs), Zenzic is a static analysis tool; it does not replace filesystem-level permissions or OS security controls.
