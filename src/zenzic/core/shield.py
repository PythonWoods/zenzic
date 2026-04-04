# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Zenzic Shield: secret-detection engine integrated into the Pass 1 harvesting phase.

All functions are pure (no I/O). The Shield is intentionally "lazy but effective":
regex patterns are pre-compiled once at import time and applied line-by-line via
the generator pipeline, so secrets are flagged the moment a line is processed —
never after loading the full file.

Supported patterns
------------------
- OpenAI API key:       ``sk-[a-zA-Z0-9]{48}``
- GitHub token:         ``gh[pousr]_[a-zA-Z0-9]{36}``
- AWS access key:       ``AKIA[0-9A-Z]{16}``
- Stripe live key:      ``sk_live_[0-9a-zA-Z]{24}``
- Slack token:          ``xox[baprs]-[0-9a-zA-Z]{10,48}``
- Google API key:       ``AIza[0-9A-Za-z\\-_]{35}``
- Generic private key:  ``-----BEGIN [A-Z ]+ PRIVATE KEY-----``

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


# ─── Pre-scan Normalizer (ZRT-003: split-token bypass defence) ────────────────

# Unwrap inline code spans: `AKIA` → AKIA
_BACKTICK_INLINE_RE = re.compile(r"`([^`]*)`")
# Remove concatenation operators that split tokens: `AKIA` + `KEY` → AKIAKEY
_CONCAT_OP_RE = re.compile(r"[`'\"\s]*\+[`'\"\s]*")
# Replace table-cell separators with spaces
_TABLE_PIPE_RE = re.compile(r"\|")


def _normalize_line_for_shield(line: str) -> str:
    """Strip Markdown noise tokens to reconstruct secrets split by obfuscation.

    Applies three transformations in order:

    1. Unwrap backtick code spans — ``AKIA`` → ``AKIA``.
    2. Remove string-concatenation operators (`` ` `` + `` ` ``) that authors
       sometimes place between key fragments in documentation tables.
    3. Replace table-pipe separators with spaces and collapse whitespace.

    This allows the Shield to catch split-token patterns such as::

        | Key ID | `AKIA` + `1234567890ABCDEF` |

    while leaving detection of normal clean lines unaffected.

    Args:
        line: Raw text line from the Markdown source.

    Returns:
        Normalised string ready for regex scanning.
    """
    normalized = _BACKTICK_INLINE_RE.sub(r"\1", line)  # unwrap `...` spans
    normalized = _CONCAT_OP_RE.sub("", normalized)  # remove + concat ops
    normalized = _TABLE_PIPE_RE.sub(" ", normalized)  # collapse table pipes
    return " ".join(normalized.split())  # collapse whitespace


# ─── Pre-compiled secret signatures ───────────────────────────────────────────

_SECRETS: list[tuple[str, re.Pattern[str]]] = [
    ("openai-api-key", re.compile(r"sk-[a-zA-Z0-9]{48}")),
    ("github-token", re.compile(r"gh[pousr]_[a-zA-Z0-9]{36}")),
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("stripe-live-key", re.compile(r"sk_live_[0-9a-zA-Z]{24}")),
    ("slack-token", re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}")),
    ("google-api-key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----")),
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
        col_start: 0-based column index of the match start in the raw line.
            Used by the reporter for surgical caret rendering.
        match_text: The matched secret substring (unredacted).
            The reporter is responsible for obfuscating this before display.
    """

    file_path: Path
    line_no: int
    secret_type: str
    url: str
    col_start: int = 0
    match_text: str = ""


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
        m = pattern.search(url)
        if m:
            yield SecurityFinding(
                file_path=path,
                line_no=line_no,
                secret_type=secret_type,
                url=url,
                col_start=m.start(),
                match_text=m.group(0),
            )


def scan_line_for_secrets(
    line: str,
    file_path: Path | str,
    line_no: int,
) -> Iterator[SecurityFinding]:
    """Scan an arbitrary text line for known secret patterns.

    Used for defence-in-depth: even if a secret appears outside a URL (e.g. in
    link text or plain prose), the Shield will catch it.

    Two forms of the line are scanned:

    * **Raw** — the line exactly as it appears in the source, ensuring that
      normally-formatted secrets (e.g. in prose or frontmatter values) are
      always caught.
    * **Normalised** (ZRT-003 fix) — the line after stripping Markdown noise
      tokens (backtick spans, table pipes, concatenation operators) so that
      split-token obfuscation patterns are reconstructed before scanning.
      See :func:`_normalize_line_for_shield`.

    Duplicate findings (same secret type on the same line whether matched by
    the raw or normalised form) are suppressed via a ``seen`` set.

    Args:
        line: Raw text line from the Markdown source.
        file_path: Path identifier (no disk access).
        line_no: 1-based line number.

    Yields:
        :class:`SecurityFinding` for each match found.
    """
    path = Path(file_path)
    normalized = _normalize_line_for_shield(line)
    seen: set[str] = set()

    for line_form in (line, normalized):
        for secret_type, pattern in _SECRETS:
            if secret_type in seen:
                continue
            m = pattern.search(line_form)
            if m:
                seen.add(secret_type)
                match_text = m.group(0)
                # Prefer col_start from the raw line; fall back to 0 when the
                # secret was only detected in the normalised form (col position
                # is meaningless after stripping Markdown noise).
                raw_m = pattern.search(line)
                yield SecurityFinding(
                    file_path=path,
                    line_no=line_no,
                    secret_type=secret_type,
                    url=line.strip(),  # always report the raw line for context
                    col_start=raw_m.start() if raw_m else 0,
                    match_text=match_text,
                )
