# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Example test for the plugin-scaffold-demo rule using the run_rule helper.

Run with::

    pytest tests/test_rules.py -v
"""

from __future__ import annotations

from zenzic.rules import run_rule

from plugin_scaffold_demo.rules import PluginScaffoldDemoRule


def test_todo_detected() -> None:
    """A line containing TODO must produce a warning."""
    findings = run_rule(PluginScaffoldDemoRule(), "# Guide\n\nTODO: write this section.\n")
    assert len(findings) == 1
    assert findings[0].rule_id == "PLUGINSC-001"
    assert findings[0].severity == "warning"
    assert findings[0].line_no == 3


def test_clean_content_no_findings() -> None:
    """Content without TODO markers must produce zero findings."""
    findings = run_rule(PluginScaffoldDemoRule(), "# Guide\n\nAll done.\n")
    assert findings == []
