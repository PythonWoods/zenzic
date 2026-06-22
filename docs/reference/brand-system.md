---
sidebar_position: 12
sidebar_label: Brand System
description: "Palette contract, semantic tokens, badge states, and HTML component styling rules for Zenzic Docs."
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Brand System

The Zenzic visual language is token-first.
All UI colors must be consumed through semantic CSS variables defined in
`src/css/custom.css`.

No raw color literals are allowed in component-level styles.

---

## Canonical Sources

1. Runtime tokens and theme behavior: `src/css/custom.css`
2. Visual board (full static artifact): `/assets/brand/zenzic-brand-system.html`

Open the full board directly:

<a href="/assets/brand/zenzic-brand-system.html" target="_blank" rel="noopener noreferrer">
  Zenzic Brand System Visual Board
</a>

---

## Badge States

Zenzic ships two badge types. Each has distinct color states driven by `ZenzicPalette`.

### Audit badge — binary gate

| State | Color | Condition |
|---|---|---|
| `passing` | BRAND indigo `#4f46e5` | exit 0 — no blocking findings |
| `failing` | ERROR rose `#e11d48` | exit 1 / 2 / 3 — blocking findings present |

### Score badge — quality metric 0–100

| State | Color | Condition |
|---|---|---|
| `score = 100` | BRAND indigo `#4f46e5` | Perfect score |
| `fail_under < score < 100` | WARNING amber `#b45309` | Advisory — not blocking |
| `score < fail_under` | ERROR rose `#e11d48` | Gate fails — exit 1 |

Static SVG sources live in `static/assets/brand/svg/`. The visual board shows all states rendered.

---
