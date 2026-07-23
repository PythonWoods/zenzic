# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Base custom rule for AST-based analysis (API v2)."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Generator
from typing import TYPE_CHECKING

from zenzic.core.rules import BaseRule


if TYPE_CHECKING:
    from pathlib import Path

    from zenzic.core.ast import BlockNode, Node
    from zenzic.core.rules import RuleFinding
    from zenzic.core.validator import HtmlNodeInfo


class BaseASTRule(BaseRule):
    """Abstract base class for Custom AST Rules (API v2).

    Uses a deterministic visitation budget instead of thread timeouts or signals
    to prevent ReDoS, infinite loops, and execution lockups.
    """

    def __init__(
        self,
        rule_id: str,
        severity: str = "warning",
        max_visits: int = 10000,
    ) -> None:
        self._rule_id = rule_id
        self.severity = severity
        self.max_visits = max_visits
        self.visit_count = 0

    @property
    def rule_id(self) -> str:
        return self._rule_id

    def check_budget(self) -> None:
        """Increment the visitation count and raise ZenzicRuleTimeout if it exceeds the limit."""
        self.visit_count += 1
        if self.visit_count > self.max_visits:
            from zenzic.core.exceptions import ZenzicRuleTimeout

            raise ZenzicRuleTimeout(
                f"Rule {self.rule_id} exceeded its execution budget of {self.max_visits} operations."
            )

    def check(self, file_path: Path, text: str) -> list[RuleFinding]:
        """Parse raw text to Markdown AST and HTML elements, then execute visitor checks."""
        from zenzic.core.ast import BlockNode
        from zenzic.core.parser import parse
        from zenzic.core.validator import PolyglotExtractor

        self.visit_count = 0
        findings: list[RuleFinding] = []

        try:
            # Parse Markdown document AST
            doc = parse(text)

            # Recursive AST traversal
            def walk(node: Node) -> None:
                self.check_budget()

                if isinstance(node, BlockNode):
                    for finding in self.visit_block_node(node, file_path):
                        findings.append(finding)

                for child in node.children:
                    walk(child)

            walk(doc)

            # Process HTML nodes via PolyglotExtractor
            html_nodes = PolyglotExtractor().extract(text)
            for html_node in html_nodes:
                self.check_budget()
                for finding in self.visit_html_node(html_node, file_path):
                    findings.append(finding)

        except Exception:
            raise

        return findings

    @abstractmethod
    def visit_block_node(
        self,
        node: BlockNode,
        file_path: Path,
    ) -> Generator[RuleFinding, None, None]:
        """User-defined visitor for AST BlockNodes (e.g., Paragraph, Heading)."""

    @abstractmethod
    def visit_html_node(
        self,
        node: HtmlNodeInfo,
        file_path: Path,
    ) -> Generator[RuleFinding, None, None]:
        """User-defined visitor for extracted HTML nodes (e.g., tags 'a', 'img')."""
