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


def fix_missing_or_empty_href(attrs: str, tag: str) -> tuple[str, bool]:
    if tag != "a":
        return attrs, False
    from zenzic.core.validator import _RE_POLY_ATTR

    attrs_dict = {}
    for m in _RE_POLY_ATTR.finditer(attrs):
        key = m.group("key").lower()
        val = m.group("val")
        if val is not None:
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                val = val[1:-1]
        attrs_dict[key] = (val, m.start(), m.end())

    if "href" not in attrs_dict:
        new_attrs = attrs.rstrip() + ' href="#"'
        return new_attrs, True

    val, start, end = attrs_dict["href"]
    if val is None or val.strip() == "":
        prefix = attrs[:start]
        suffix = attrs[end:]
        new_attrs = prefix + 'href="#"' + suffix
        return new_attrs, True

    return attrs, False


class HtmlMissingHrefMutation:
    """Z121 Auto-Fix: Injects href="#" into missing or empty <a> tag href attributes."""

    def apply(self, node: Node) -> bool:
        mutated = False
        from zenzic.core.ast import TextNode

        if isinstance(node, TextNode):
            from zenzic.core.validator import _RE_POLY_TAG

            text = node.text
            new_text = ""
            last_idx = 0
            for m in _RE_POLY_TAG.finditer(text):
                tag = m.group(1).lower()
                attrs_str = m.group("attrs")

                if tag == "a":
                    new_attrs, changed = fix_missing_or_empty_href(attrs_str, tag)
                    if changed:
                        new_text += text[last_idx : m.start()] + f"<a {new_attrs}>"
                        last_idx = m.end()
                        mutated = True

            if mutated:
                new_text += text[last_idx:]
                node.text = new_text

        for child in node.children:
            if self.apply(child):
                mutated = True
        return mutated


class DeadSuppressionMutation:
    """Z603 Auto-Fix: Removes dead inline suppression comments and attributes."""

    def __init__(self, dead_lines: set[int]) -> None:
        self.dead_lines = dead_lines
        self.current_line = 1

    def apply(self, node: Node) -> bool:
        mutated = False
        from zenzic.core.ast import CodeSpanNode, LinkNode, TextNode

        if isinstance(node, TextNode):
            text = node.text
            lines = text.splitlines(keepends=True)
            new_lines = []
            node_line_start = self.current_line

            for i, line in enumerate(lines):
                line_no = node_line_start + i
                if line_no in self.dead_lines:
                    # 1. Check for standard zenzic:ignore comment
                    from zenzic.core.suppressions import _SUPPRESS_RE

                    m = _SUPPRESS_RE.search(line)
                    if m:
                        comment_text = m.group(0)
                        stripped_line = line.replace(comment_text, "")
                        if not stripped_line.strip():
                            line = ""
                            mutated = True
                        else:
                            import re as std_re

                            line = std_re.sub(r"\s*<!--.*?-->\s*", " ", line)
                            if stripped_line.endswith("\n") and not line.endswith("\n"):
                                line = line.rstrip() + "\n"
                            mutated = True

                    # 2. Check for dead data-zenzic-ignore HTML attribute
                    from zenzic.core.validator import _RE_POLY_TAG

                    new_line = ""
                    last_idx = 0
                    for tag_match in _RE_POLY_TAG.finditer(line):
                        attrs_str = tag_match.group("attrs")
                        tag = tag_match.group(1)
                        if "data-zenzic-ignore" in attrs_str:
                            import re as std_re

                            new_attrs = std_re.sub(
                                r"\bdata-zenzic-ignore\b\s*(=\s*\"[^\"]*\"\s*|=\s*'[^']*'\s*)?",
                                "",
                                attrs_str,
                            )
                            new_attrs = std_re.sub(r"\s+", " ", new_attrs).strip()
                            if new_attrs:
                                new_tag = f"<{tag} {new_attrs}>"
                            else:
                                new_tag = f"<{tag}>"
                            new_line += line[last_idx : tag_match.start()] + new_tag
                            last_idx = tag_match.end()
                            mutated = True
                    if mutated:
                        new_line += line[last_idx:]
                        line = new_line

                new_lines.append(line)

            self.current_line += text.count("\n")
            if mutated:
                node.text = "".join(new_lines)

        elif isinstance(node, CodeSpanNode):
            self.current_line += node.code.count("\n")
        elif isinstance(node, LinkNode):
            for child in node.children:
                if self.apply(child):
                    mutated = True
            self.current_line += node.url.count("\n")
        else:
            for child in node.children:
                if self.apply(child):
                    mutated = True

        return mutated

