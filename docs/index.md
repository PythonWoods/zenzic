---
template: home.html
title: "Zenzic — Documentation Quality Gate"
hide:
  - navigation
  - toc
  - path
  - feedback
description: "Zenzic is an engine-agnostic Markdown static analyzer and credential scanner designed to enforce documentation quality and security."
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

Zenzic is an engine-agnostic Markdown static analyzer and credential scanner. It is designed to act as a strict quality gate for documentation repositories. By treating documentation as code, Zenzic ensures that broken links, malformed syntax, dangling references, and placeholder text never reach production.

Zenzic provides a fast, deterministic, and highly configurable analysis pipeline that integrates seamlessly into any continuous integration environment. From catching leaked secrets with its credential scanner to enforcing bilingual structural invariants, Zenzic helps maintain Hostile Precision over your project's most important assets.

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

Expected Output:

```text
docs/index.md:1  [Z104]  'missing.md' resolves to nowhere — the target file does not exist.

FAILED: Hard errors detected. Exit code 1 is mandatory.
```

### Next Steps: Real-Time Feedback

To eliminate the latency between authoring a defect and discovering it, install the [Zenzic VS Code Extension](https://github.com/PythonWoods/zenzic/tree/main/vscode) for sub-50ms inline diagnostics.
