# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from zenzic.core import regex as re
from zenzic.core.codes import NON_SUPPRESSIBLE_CODES
from zenzic.core.sovereign_context import get_sovereign_context


if TYPE_CHECKING:
    from zenzic.core.rules import RuleFinding


#: Fenced code block line: captures the fence chars and the full info string.
_FENCE_OPEN_RE = re.compile(r"^(?P<fence>[`~]{3,})(?P<info>.*)$")

#: Strict suppression protocol: only exact ``zenzic:ignore:`` directives are valid.
_SUPPRESS_RE = re.compile(
    r"(?:<!--|\{/\*)\s*zenzic:ignore:\s*(?P<code>Z\d{3})(?:[^\n]*?)?(?:-->|\*/\})",
)

#: ADR-084 — Strip backtick inline code spans before counting suppressions.
_INLINE_CODE_STRIP_RE = re.compile(r"``[^`\n]+``|`[^`\n]+`")


@dataclass
class SuppressionDirective:
    code: str
    line_no: int
    consumed: bool = False


class SuppressionTracker:
    """Tracks inline suppressions within a single file to identify Z603 Dead Suppressions."""

    def __init__(self, file_path: Path, text: str):
        self.file_path = file_path
        self.directives: list[SuppressionDirective] = []
        self._parse(text)

    def _parse(self, text: str) -> None:
        inside_fence = False
        open_char = ""
        open_count = 0
        for i, line in enumerate(text.splitlines(), start=1):
            fm = _FENCE_OPEN_RE.match(line)
            if not inside_fence:
                if fm:
                    fence = fm.group("fence")
                    inside_fence = True
                    open_char = fence[0]
                    open_count = len(fence)
                else:
                    stripped = _INLINE_CODE_STRIP_RE.sub("", line)
                    for m in _SUPPRESS_RE.finditer(stripped):
                        self.directives.append(
                            SuppressionDirective(
                                code=m.group("code").upper(),
                                line_no=i,
                                consumed=False,
                            )
                        )
            else:
                if fm:
                    fence = fm.group("fence")
                    info = fm.group("info").strip()
                    if fence[0] == open_char and len(fence) >= open_count and not info:
                        inside_fence = False
                        open_char = ""
                        open_count = 0

    def is_suppressed(self, line_no: int, code: str) -> bool:
        """Return True if the given code is suppressed at the specified line number.

        Marks the suppression directive as consumed if a match is found.
        """
        if get_sovereign_context().force_audit:
            return False

        if code in NON_SUPPRESSIBLE_CODES:
            return False

        code = code.upper()
        suppressed = False
        for d in self.directives:
            if d.line_no == line_no and d.code == code:
                d.consumed = True
                suppressed = True
        return suppressed

    def get_dead_suppressions(self) -> list["RuleFinding"]:
        """Yield Z603 findings for all directives that were never consumed."""
        from zenzic.core.rules import RuleFinding

        findings = []
        for d in self.directives:
            if not d.consumed:
                findings.append(
                    RuleFinding(
                        file_path=self.file_path,
                        line_no=d.line_no,
                        rule_id="Z603",
                        message="Inline suppression directive does not suppress any active finding. Remove the dead comment.",
                        severity="warning",
                    )
                )
        return findings


def count_inline_suppressions(text: str) -> int:
    """Count suppression directives declared in Markdown/MDX source text."""
    tracker = SuppressionTracker(Path("dummy"), text)
    return len(tracker.directives)
