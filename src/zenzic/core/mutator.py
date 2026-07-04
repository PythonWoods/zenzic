# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""AST Mutation API and Engine."""

from __future__ import annotations

import copy
from typing import Protocol

from zenzic.core.ast import CodeSpanNode, LinkNode, Node, TextNode


class Mutation(Protocol):
    """Protocol for AST mutations."""

    def apply(self, node: Node) -> bool:
        """Apply the mutation to the given node in-place.

        Returns True if a mutation occurred, False otherwise.
        """
        ...


def _has_text_content(node: Node) -> bool:
    """Returns True if the node contains any non-whitespace text or code content recursively."""
    if isinstance(node, TextNode):
        stripped = node.text
        for char in ("*", "_", "~", "`"):
            stripped = stripped.replace(char, "")
        return bool(stripped.strip())
    if isinstance(node, CodeSpanNode):
        stripped = node.code
        for char in ("*", "_", "~", "`"):
            stripped = stripped.replace(char, "")
        return bool(stripped.strip())
    return any(_has_text_content(child) for child in node.children)


class EmptyLinkTextMutation:
    """Z108 Auto-Fix: Injects placeholder text into empty links."""

    def apply(self, node: Node) -> bool:
        mutated = False
        if isinstance(node, LinkNode):
            is_empty = not any(_has_text_content(child) for child in node.children)

            if is_empty:
                node.children = [TextNode(text="MISSING LINK LABEL")]
                mutated = True

        for child in node.children:
            if self.apply(child):
                mutated = True

        return mutated


class Mutator:
    """Engine that applies a list of Mutations to an AST."""

    def __init__(self, mutations: list[Mutation]) -> None:
        self.mutations = mutations

    def mutate(self, ast: Node) -> tuple[Node, bool]:
        """Applies all mutations to a deep copy of the AST.

        Returns a tuple of (new_ast, changed).
        """
        new_ast = copy.deepcopy(ast)
        changed = False
        for mutation in self.mutations:
            if mutation.apply(new_ast):
                changed = True
        return new_ast, changed
