---
template: home.html
title: "Zenzic — Documentation Quality Gate"
hide:
  - navigation
  - toc
  - path
  - feedback
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

### Credential Scanner

<span style="font-family: monospace; font-size: 0.8em; color: #9ca3af;">MODULE: src/zenzic/core/scanners</span>

| Parameter | Specification |
| :--- | :--- |
| **SCOPE** | Every line, including `` `bash` `` & `` `yaml` `` fences. |
| **ALGORITHM** | RE2 DFA-pure regex. Zero catastrophic backtracking. |
| **SEVERITY** | <span style="color: #ef4444; font-weight: bold;">🔴 FATAL (Exit 2)</span> |
| **SUPPRESSIBLE** | `FALSE` |
