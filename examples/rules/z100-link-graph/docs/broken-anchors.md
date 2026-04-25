<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Link Graph Stress — Broken Anchor Catalogue

A single file containing ten-plus broken `#anchor` references across the other nodes.
Every link below targets a heading that does not exist in the destination file.

[A — nonexistent overview](a.md#overview)
[A — nonexistent quickstart](a.md#quickstart)
[A — nonexistent api-reference](a.md#api-reference)
[A — nonexistent changelog](a.md#changelog)

[B — nonexistent prerequisites](b.md#prerequisites)
[B — nonexistent troubleshooting](b.md#troubleshooting)
[B — nonexistent faq](b.md#faq)
[B — nonexistent migration-guide](b.md#migration-guide)

[C — nonexistent examples](c.md#examples)
[C — nonexistent contributing](c.md#contributing)
[C — nonexistent license](c.md#license)

Expected: Z102 `BROKEN_ANCHOR` on every link above — exit **1**.
