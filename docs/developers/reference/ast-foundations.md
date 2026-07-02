---
description: "Reference guide for the Abstract Syntax Tree (AST) architecture and lossless serialization guarantees in Zenzic."
---
<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# AST Foundations

The Abstract Syntax Tree (AST) implemented in Zenzic supports the v0.19.0 Deterministic Markdown Renderer pipeline.

## Core Architecture

The AST is designed strictly to adhere to the Absolute Determinism and Law of the Mirror principles.

### Base Nodes

- `Node`: The fundamental tree element. Contains a list of `children`.
- `BlockNode`: Represents block-level elements (e.g., `Paragraph`, `Heading`).
- `InlineNode`: Represents inline elements (e.g., `TextNode`).

### Structural Nodes

- `Document`: The root `BlockNode` containing all parsed elements.
- `Paragraph`: A `BlockNode` aggregating `TextNode` objects. Blank lines evaluate to distinct `Paragraph` nodes to preserve the source structure identically.
- `Heading`: A `BlockNode` containing the exact `marker` (e.g., `#`), `level`, `prefix_space`, and text content to guarantee lossless rebuilding.

### Inline Nodes

- `TextNode`: Contains raw text strings.
- `LinkNode`: Represents `[text](url)`. Contains a `polyglot_data` dict field to hold metadata extracted by the `PolyglotExtractor` (e.g., HTML attributes).
- `CodeSpanNode`: Represents `` `code` ``.
- `EmphasisNode`: Represents `*text*` or `_text_`.
- `StrongNode`: Represents `**text**` or `__text__`.

## Serialization Guarantee

The serialization function `zenzic.core.parser.serialize(node)` operates on any AST node and emits a string that is strictly byte-for-byte identical to the original parser input (Lossless Round-trip).

## Mutation API & Auto-Fix Engine

Zenzic implements a non-destructive AST `Mutator` engine to support the `zenzic fix` command.

- **The `Mutation` Protocol:** Developers can write standalone `Mutation` classes (e.g., `EmptyLinkTextMutation`) containing an `apply(node)` method. Mutations traverse the AST and modify nodes in-place.
- **The `Mutator` Engine:** To preserve immutability and ensure deterministic outputs, the `Mutator` applies all defined mutations to a `copy.deepcopy` of the original AST, returning the new AST along with a boolean indicating if changes occurred.
- **Dry-Run Safety:** By default, the `zenzic fix --dry-run` command evaluates mutations and prints a standard unified `diff` to `stdout`. Disk I/O is strictly blocked in this phase to guarantee safety.

## Parsing Constraints

- **RE2 Rigor (ADR-013):** The block-level AST builder uses only DFA-pure tokenization patterns via `zenzic.core.regex`. Lookarounds are strictly forbidden.
- **O(N) Inline Tokenization:** To avoid catastrophic backtracking commonly associated with regex-based inline Markdown parsing (especially for nested emphasis), the inline tokenizer (`parse_inline`) is implemented as a strict character-by-character linear state machine. This guarantees $O(N)$ worst-case time complexity.
- **Zero Subprocess:** The logic is completely native to Python.
- **Determinism:** The pipeline relies solely on statically determinable input matching.
