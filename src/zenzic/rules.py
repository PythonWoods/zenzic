# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Public namespace for Zenzic plugin rule authors.

This module re-exports the stable API surface that plugin authors should use.
Import from ``zenzic.rules`` in your plugin code::

    from zenzic.rules import BaseRule, RuleFinding

The test helper :func:`run_rule` lets you validate a rule against a Markdown
string in a single call — no engine setup required.

.. versionadded:: 0.5.0a3
"""

from __future__ import annotations

from pathlib import Path

from zenzic.core.rules import (
    AdaptiveRuleEngine,
    BaseRule,
    CustomRule,
    RuleFinding,
    Severity,
    Violation,
)


__all__ = [
    "AdaptiveRuleEngine",
    "BaseRule",
    "CustomRule",
    "RuleFinding",
    "Severity",
    "Violation",
    "run_rule",
]


def run_rule(
    rule: BaseRule,
    text: str,
    *,
    file_path: Path | str = Path("test.md"),
) -> list[RuleFinding]:
    """Run a single rule against *text* and return findings.

    This is the recommended way for plugin authors to test their rules::

        from zenzic.rules import BaseRule, RuleFinding, run_rule

        def test_my_rule():
            findings = run_rule(MyRule(), "some DRAFT content")
            assert len(findings) == 1
            assert findings[0].severity == "warning"

    Args:
        rule: A :class:`BaseRule` instance to test.
        text: Raw Markdown content to scan.
        file_path: Optional file path for labelling (default: ``test.md``).

    Returns:
        List of :class:`RuleFinding` objects.
    """
    engine = AdaptiveRuleEngine([rule])
    return engine.run(Path(file_path), text)
