---
description: "Deterministic 3-Step Quickstart: Install Zenzic, trigger a SAST/topological check, and integrate inline diagnostics in under 60 seconds."
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Quickstart Guide

This guide walks you through Zenzic's deterministic documentation analysis pipeline. In under 60 seconds, you will install the CLI, simulate a broken link defect, and execute a full topological audit.

---

## 🚀 Deterministic 3-Step Quickstart (< 60 Seconds)

Experience zero-config topological failure detection in under 60 seconds:

```bash
# Step 1: Install Zenzic CLI
uv tool install zenzic

# Step 2: Create a document with a broken relative link
mkdir docs
echo "[broken](missing.md)" > docs/index.md

# Step 3: Run full documentation graph analysis
zenzic check all
```

### Explanation of Steps

1. **Step 1 (`uv tool install zenzic`)**: Installs the sovereign Zenzic CLI binary into your environment using `uv`.
2. **Step 2 (`echo "[broken](missing.md)" > docs/index.md`)**: Creates a minimal documentation file containing a relative markdown link referencing `missing.md`, which does not exist in the repository filesystem.
3. **Step 3 (`zenzic check all`)**: Triggers the Virtual Site Map (VSM) scanner to resolve the documentation graph topology and detect link integrity errors.

---

## Expected Terminal Output

When Zenzic detects a missing link target during graph analysis, it outputs deterministic line-level diagnostics:

```text
docs/index.md:1  [Z104]  'missing.md' resolves to nowhere — the target file does not exist.

FAILED: Hard errors detected. Exit code 1 is mandatory.
```

### Exit Code Contract

- **Exit Code `0`**: All documentation links, credentials, and structural invariants are verified cleanly.
- **Exit Code `1`**: Hard errors detected (e.g. `Z104: FILE_NOT_FOUND`, `Z101: BROKEN_LINK`).
- **Exit Code `2`**: Fatal security findings detected (e.g. `Z201: CREDENTIAL_LEAK`, `Z202: PATH_TRAVERSAL`).

---

## Next Steps: Real-Time Feedback

To eliminate the latency between authoring a defect and discovering it in CI, install the [Zenzic VS Code Extension](https://github.com/PythonWoods/zenzic/tree/main/vscode) for sub-50ms inline diagnostics directly inside your editor.
