<p align="center">
  <img src="images/logo.png" width="128" alt="Zenzic Logo">
</p>

<h1 align="center">Zenzic: Deterministic Document Integrity</h1>

<p align="center">
  <strong>Deterministic Document Integrity Engine and SAST for Markdown/MDX graphs.</strong>
</p>

---

Zenzic is a Deterministic Document Integrity Engine and SAST for Markdown/MDX graphs.

This extension brings the exact same $O(N)$ SAST engine used in your CI/CD pipelines directly into your authoring environment, providing sub-50ms topological feedback as you type.

## Thin Client Architecture

This extension is a strictly **Thin Client**. It contains zero parsing logic, zero regex engines, and zero validation rules. It communicates via the Language Server Protocol (LSP) over standard I/O directly with the Zenzic Python binary installed on your system.

## Key Features

### 1. Security Scanning (SAST)
Hardcoded credentials (Z201) and path traversal sequences (Z202/Z203) are flagged in milliseconds using RE2 validation engine rules, preventing leaks before the file is even saved.

### 2. Graph Topology Analysis (VSM)
Modify a heading in one file, and Zenzic's Virtual Site Map (VSM) instantly invalidates any broken links, orphan pages, or dead navigation nodes across your entire workspace using $O(K)$ incremental graph patching.

### 3. Deterministic CI/CD Enforcement & Quality Scoring
Hover over any diagnostic to see the exact Z-Code, the Zero-DBT Quality Score penalty, and deterministic remediation guidance directly from the Core engine, ensuring 1:1 alignment with your CI/CD quality gate.

## Requirements

This extension requires **Zenzic Core v0.23.7 or higher**.

We recommend installing or updating via `uv`:

```bash
uv tool install --force zenzic
```

## Extension Settings

By default, the extension will look for the `zenzic` binary in your system's PATH. 

If you are using a local virtual environment or a custom installation path, configure the executable path in your workspace or user `settings.json`:

```json
{
  "zenzic.executablePath": "${workspaceFolder}/.venv/bin/zenzic"
}
```

## Troubleshooting

### Zenzic: Outdated Core

- **Cause**: The executable resolved by the extension is older than the minimum required Core version (`v0.23.7`).
- **Remediation**: Upgrade your global binary:
  ```bash
  uv tool install --force zenzic
  ```
  Or point `zenzic.executablePath` in `settings.json` to a virtual environment containing Core `v0.23.7` or higher.

### Zenzic: Not Found (ENOENT)

- **Cause**: The `zenzic` executable is not present in the system `$PATH`. This commonly occurs in Flatpak or Snap editor environments where user binary directories (`~/.local/bin`) are isolated from the process environment.
- **Remediation**: Specify the absolute path to the binary in your workspace or user `settings.json`:
  ```json
  {
    "zenzic.executablePath": "/home/user/.local/bin/zenzic"
  }
  ```

## Architectural Guarantees

- **Zero Telemetry:** Zenzic operates entirely locally. No data is sent to the cloud.
- **Zero LLMs:** All analysis is mathematically deterministic. No probabilistic guessing.
- **Sub-50ms Latency:** Incremental $O(K)$ graph patching ensures real-time feedback regardless of workspace size.

---

For the full finding taxonomy and architectural documentation, visit [zenzic.dev](https://zenzic.dev).
