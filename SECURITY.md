<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

# Security Policy

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability in Zenzic — including issues with the Core engine, credential scanner, path traversal protection, VS Code extension LSP client, or GitHub Action wrapper script — report it privately via one of these channels:

- **GitHub Security Advisories** (preferred): [github.com/PythonWoods/zenzic/security/advisories](https://github.com/PythonWoods/zenzic/security/advisories)
- **Email**: `dev@pythonwoods.dev` — subject line: `[SECURITY] Zenzic — <brief description>`

Please include a clear description of the vulnerability, steps to reproduce, potential impact, and a suggested fix if available.

We will acknowledge your report within **72 hours** and aim to release a patch within **14 days** of confirming the issue.

---

## Scope by Component

The following areas are in-scope for security reports:

| Subsystem | In-Scope Area | Description |
| :--- | :--- | :--- |
| **Core Engine** | **Scanner bypass** | A credential pattern that passes undetected through the credential scanner family |
| **Core Engine** | **Path traversal bypass** | A crafted link that escapes the target root without triggering the path traversal guard (`Z202`) |
| **Core Engine** | **Exit code suppression** | Any method that prevents exit codes `2` (credential leak) or `3` (path traversal) from being emitted |
| **Core Engine** | **Code execution** | A crafted Markdown or config file (`.zenzic.toml`, `mkdocs.yml`) causing code execution during scanning |
| **VS Code Extension** | **LSP IPC manipulation** | Arbitrary code or command injection via LSP language server protocol payloads |
| **GitHub Action** | **Wrapper script injection** | A crafted action input causing arbitrary shell code execution inside action runner wrapper scripts |
| **GitHub Action** | **SARIF upload bypass** | A condition under which a truncated or empty SARIF file is uploaded as a false-clean result |
| **All Components** | **Dependency CVE** | A known CVE in runtime or GitHub Action workflow dependencies |

---

## Security Design Notes

1. **Zero Subprocess in Core**: Zenzic Core has **no subprocess calls** in the analysis path. The tool reads source files and performs all analysis in pure Python using RE2-backed regular expressions without backtracking vulnerabilities.
2. **Path Traversal Guard (`Z202` / `Z203`)**: Resolves link targets strictly within the workspace filesystem boundary. Attempts to traverse outside the root emit non-suppressible exit code `3` findings.
3. **Action Sandbox & Minimal Permissions**: The Zenzic GitHub Action operates with minimal job-level permissions (`contents: read`, `security-events: write`). Action outputs (`$GITHUB_OUTPUT`) are written prior to exit code evaluation.

---

## Supply-Chain Assurance (SLSA-Aligned)

Zenzic distribution workflows enforce a SLSA-aligned integrity baseline for build and release operations:

- GitHub Actions in release-critical workflows are pinned to immutable commit SHAs.
- Dependency synchronization uses locked manifests (`core/uv.lock`, `vscode/package-lock.json`, `actions/package-lock.json`).
- Release artifacts are produced with build provenance attestations (`gh attestation verify`).

---

## Supported Versions

| Package | Current Supported Version | Policy |
| :--- | :--- | :--- |
| **Core Engine** | `0.23.1` (current) | ✅ Active security fixes |
| **VS Code Extension** | `0.23.7` (current) | ✅ Active security fixes |
| **GitHub Action** | `2.9.1` (current) | ✅ Active security fixes |

---

## Disclosure Policy

We follow a **coordinated disclosure** model. We ask that you allow up to 14 days for a patch to be released before any public disclosure. Confirmed reporters will be credited in the release changelog unless they prefer to remain anonymous.
