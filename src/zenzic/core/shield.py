# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Zenzic Shield: secret-detection engine integrated into the Pass 1 harvesting phase.

All functions are pure (no I/O). The Shield is intentionally "lazy but effective":
regex patterns are pre-compiled once at import time and applied line-by-line via
the generator pipeline, so secrets are flagged the moment a line is processed —
never after loading the full file.

Supported patterns
------------------
- OpenAI API key:   ``sk-[a-zA-Z0-9]{48}``
- GitHub token:     ``gh[pousr]_[a-zA-Z0-9]{36}``
- AWS access key:   ``AKIA[0-9A-Z]{16}``

Exit code contract
------------------
Any secret detected **must** cause the CLI to exit with **code 2**.
The Shield itself returns findings; callers are responsible for the exit.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


# ─── Pre-compiled secret signatures ───────────────────────────────────────────

_SECRETS: list[tuple[str, re.Pattern[str]]] = [
    ("openai-api-key", re.compile(r"sk-[a-zA-Z0-9]{48}")),
    ("github-token", re.compile(r"gh[pousr]_[a-zA-Z0-9]{36}")),
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
]


# ─── Data classes ─────────────────────────────────────────────────────────────


@dataclass(slots=True)
class SecurityFinding:
    """A single secret detected by the Shield during Pass 1 harvesting.

    Attributes:
        file_path: Path to the file where the secret was found.
        line_no: 1-based line number of the offending line.
        secret_type: Human-readable label for the secret kind
            (e.g. ``"openai-api-key"``).
        url: The URL or text fragment in which the secret was embedded.
    """

    file_path: Path
    line_no: int
    secret_type: str
    url: str


# ─── Pure / I/O-agnostic functions ────────────────────────────────────────────


def scan_url_for_secrets(
    url: str,
    file_path: Path | str,
    line_no: int,
) -> Iterator[SecurityFinding]:
    """Scan a single URL string for known secret patterns.

    Called once per URL discovered during Pass 1 harvesting.  This keeps the
    detection responsibility inside the Shield module while the scanner drives
    the iteration.

    Args:
        url: The raw URL string extracted from a reference definition or inline link.
        file_path: Path identifier used to label findings (no disk access).
        line_no: 1-based line number where the URL appeared.

    Yields:
        :class:`SecurityFinding` for each secret pattern that matches.
    """
    path = Path(file_path)
    for secret_type, pattern in _SECRETS:
        if pattern.search(url):
            yield SecurityFinding(
                file_path=path,
                line_no=line_no,
                secret_type=secret_type,
                url=url,
            )


def scan_line_for_secrets(
    line: str,
    file_path: Path | str,
    line_no: int,
) -> Iterator[SecurityFinding]:
    """Scan an arbitrary text line for known secret patterns.

    Used for defence-in-depth: even if a secret appears outside a URL (e.g. in
    link text or plain prose), the Shield will catch it.

    Args:
        line: Raw text line from the Markdown source.
        file_path: Path identifier (no disk access).
        line_no: 1-based line number.

    Yields:
        :class:`SecurityFinding` for each match found.
    """
    path = Path(file_path)
    for secret_type, pattern in _SECRETS:
        if pattern.search(line):
            yield SecurityFinding(
                file_path=path,
                line_no=line_no,
                secret_type=secret_type,
                url=line.strip(),
            )
