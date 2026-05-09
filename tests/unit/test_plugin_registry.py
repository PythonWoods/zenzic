# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Plugin registry namespace contract tests (ADR-012 Batch 2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from zenzic.core.exceptions import PluginContractError
from zenzic.core.rules import BaseRule, PluginRegistry, RuleFinding


class _CoreNamespaceRule(BaseRule):
    code = "Z777"
    primary_exit = 1

    @property
    def rule_id(self) -> str:
        return "ZZ-CORE-NAMESPACE"

    def check(self, file_path: Path, text: str) -> list[RuleFinding]:
        return []


class _WrongPrefixRule(BaseRule):
    code = "other:001"
    primary_exit = 1

    @property
    def rule_id(self) -> str:
        return "ZZ-WRONG-PREFIX"

    def check(self, file_path: Path, text: str) -> list[RuleFinding]:
        return []


class _ForbiddenExitRule(BaseRule):
    code = "acme:001"
    primary_exit = 2

    @property
    def rule_id(self) -> str:
        return "ZZ-FORBIDDEN-EXIT"

    def check(self, file_path: Path, text: str) -> list[RuleFinding]:
        return []


class _FakeEP:
    def __init__(self, name: str, cls: type[BaseRule]) -> None:
        self.name = name
        self._cls = cls
        self.dist = type("_Dist", (), {"name": "acme-plugin"})()

    def load(self) -> type[BaseRule]:
        return self._cls


def test_plugin_registry_rejects_core_z_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    reg = PluginRegistry()
    monkeypatch.setattr(reg, "_entry_points", lambda: [_FakeEP("acme", _CoreNamespaceRule)])

    with pytest.raises(
        PluginContractError,
        match="Third-party plugins must use '<plugin-id>:<code>' format",
    ):
        reg.load_selected_rules(["acme"])


def test_plugin_registry_rejects_wrong_plugin_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    reg = PluginRegistry()
    monkeypatch.setattr(reg, "_entry_points", lambda: [_FakeEP("acme", _WrongPrefixRule)])

    with pytest.raises(PluginContractError, match="must start with 'acme:'"):
        reg.load_selected_rules(["acme"])


def test_plugin_registry_rejects_security_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    reg = PluginRegistry()
    monkeypatch.setattr(reg, "_entry_points", lambda: [_FakeEP("acme", _ForbiddenExitRule)])

    with pytest.raises(PluginContractError, match="Plugins cannot emit Exit 2 or 3"):
        reg.load_selected_rules(["acme"])
