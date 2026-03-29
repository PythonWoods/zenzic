# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Zenzic Rule Engine — pluggable, pure-function linting rules.

Architecture
------------
Rules are pure functions: they receive immutable data (file path, line text,
line number) and return a list of :class:`RuleFinding` objects.  No I/O is
permitted inside a rule — this is enforced by the interface contract and
documented clearly.

Two kinds of rules coexist in the same engine:

* **CustomRule** — declared directly in ``zenzic.toml`` as ``[[custom_rules]]``
  entries.  No Python required.  Ideal for project-specific vocabulary checks.
* **BaseRule** subclasses — Python classes registered via the
  ``zenzic.rules`` entry-point group.  For complex, multi-line logic that
  a regex cannot express.

Both kinds are applied through the same :class:`RuleEngine.run` interface so
the scanner only sees one surface.

Zenzic Way compliance
---------------------
* **Lint the Source:** Rules receive raw Markdown text — never HTML.
* **No Subprocesses:** The rule module does not import or invoke any process.
* **Pure Functions First:** :meth:`BaseRule.check` must be deterministic and
  side-effect-free.  :class:`RuleEngine.run` is also pure (list in, list out).
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# ─── Finding ──────────────────────────────────────────────────────────────────

Severity = Literal["error", "warning", "info"]


@dataclass(slots=True)
class RuleFinding:
    """A single issue found by a rule.

    Attributes:
        file_path: Path to the source file (used for display only).
        line_no: 1-based line number of the offending content.
        rule_id: Identifier of the rule that produced this finding.
        message: Human-readable description of the issue.
        severity: ``"error"``, ``"warning"``, or ``"info"``.
    """

    file_path: Path
    line_no: int
    rule_id: str
    message: str
    severity: Severity = "error"

    @property
    def is_error(self) -> bool:
        """Return ``True`` when this finding blocks a passing check."""
        return self.severity == "error"


# ─── Abstract base ─────────────────────────────────────────────────────────────


class BaseRule(ABC):
    """Abstract interface for all Zenzic linting rules.

    Subclass this to create a Python-native rule.  Register it via the
    ``zenzic.rules`` entry-point group so Zenzic discovers it automatically::

        # pyproject.toml
        [project.entry-points."zenzic.rules"]
        my_rule = "my_package.rules:MyRule"

    **Contract:**

    * :meth:`check` must be **pure** — no I/O, no global state mutation.
    * :meth:`check` must be **deterministic** — same input always yields same output.
    * Raising an exception inside :meth:`check` is a bug in the rule.  The engine
      catches it and emits a single ``"error"`` finding describing the failure,
      then continues with the next rule.
    """

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Stable, unique identifier for this rule (e.g. ``"ZZ001"``).

        Used in output and in ``[[custom_rules]]`` ``id`` fields.
        """

    @abstractmethod
    def check(
        self,
        file_path: Path,
        text: str,
    ) -> list[RuleFinding]:
        """Analyse the raw Markdown content of one file.

        Args:
            file_path: Absolute path to the file (for labelling findings only —
                do **not** read from it; the content is already in *text*).
            text: Complete raw Markdown source of the file.

        Returns:
            A list of :class:`RuleFinding` objects, or an empty list if the
            file passes this rule.
        """


# ─── CustomRule (TOML-driven) ──────────────────────────────────────────────────


@dataclass
class CustomRule(BaseRule):
    """A regex-based rule declared in ``[[custom_rules]]`` inside ``zenzic.toml``.

    Each entry in the ``[[custom_rules]]`` array maps directly to one
    ``CustomRule`` instance.  The pattern is applied line-by-line.

    TOML example::

        [[custom_rules]]
        id = "ZZ-NOINTERNAL"
        pattern = "internal\\.corp\\.example\\.com"
        message = "Internal hostname must not appear in public documentation."
        severity = "error"

        [[custom_rules]]
        id = "ZZ-NODRAFT"
        pattern = "(?i)\\bDRAFT\\b"
        message = "Remove DRAFT marker before publishing."
        severity = "warning"

    Attributes:
        id: Rule identifier, surfaced in findings as ``rule_id``.
        pattern: Regular-expression string applied to each non-blank line.
        message: Human-readable explanation shown in the finding.
        severity: ``"error"`` (default), ``"warning"``, or ``"info"``.
    """

    id: str
    pattern: str
    message: str
    severity: Severity = "error"
    _compiled: re.Pattern[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        try:
            self._compiled = re.compile(self.pattern)
        except re.error as exc:
            raise ValueError(
                f"CustomRule '{self.id}': invalid regex pattern {self.pattern!r} — {exc}"
            ) from exc

    @property
    def rule_id(self) -> str:
        return self.id

    def check(self, file_path: Path, text: str) -> list[RuleFinding]:
        """Apply the pattern line-by-line to *text*."""
        findings: list[RuleFinding] = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            if self._compiled.search(line):
                findings.append(
                    RuleFinding(
                        file_path=file_path,
                        line_no=lineno,
                        rule_id=self.id,
                        message=self.message,
                        severity=self.severity,
                    )
                )
        return findings


# ─── RuleEngine ───────────────────────────────────────────────────────────────


class RuleEngine:
    """Applies a collection of :class:`BaseRule` instances to a Markdown file.

    The engine is stateless after construction — :meth:`run` is a pure
    function that maps ``(path, text)`` to a list of findings.

    Usage::

        engine = RuleEngine(config.custom_rules)
        findings = engine.run(Path("docs/guide.md"), text)

    Args:
        rules: Iterable of :class:`BaseRule` (or :class:`CustomRule`) instances
            to apply.  Order is preserved in the output.
    """

    def __init__(self, rules: Sequence[BaseRule]) -> None:
        self._rules = rules

    def __bool__(self) -> bool:
        """Return ``True`` when the engine has at least one rule."""
        return bool(self._rules)

    def run(self, file_path: Path, text: str) -> list[RuleFinding]:
        """Run all rules against *text* and return consolidated findings.

        Exceptions raised inside individual rules are caught and converted to
        a single ``"error"`` finding with ``rule_id="RULE-ENGINE-ERROR"`` so
        that one faulty plugin cannot abort the scan of the entire docs tree.

        Args:
            file_path: Path to the file being checked (labelling only).
            text: Raw Markdown content of the file.

        Returns:
            Flat list of :class:`RuleFinding` objects from all rules,
            in rule-definition order.
        """
        findings: list[RuleFinding] = []
        for rule in self._rules:
            try:
                findings.extend(rule.check(file_path, text))
            except Exception as exc:  # noqa: BLE001
                findings.append(
                    RuleFinding(
                        file_path=file_path,
                        line_no=0,
                        rule_id="RULE-ENGINE-ERROR",
                        message=(
                            f"Rule '{rule.rule_id}' raised an unexpected exception: "
                            f"{type(exc).__name__}: {exc}"
                        ),
                        severity="error",
                    )
                )
        return findings
