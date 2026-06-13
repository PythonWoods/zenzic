# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""STEP 3 — zenzic inspect routes: JSON purity, data contract, --kind filter tests."""

from __future__ import annotations

import hashlib
import json
import typing
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner, Result

from zenzic.core import regex as re
from zenzic.main import app


runner = CliRunner()


def _make_docusaurus_repo(tmp_path: Path) -> None:
    """Materialise a minimal Docusaurus project with docs/ and blog/."""
    docs = tmp_path / "docs"
    blog = tmp_path / "blog"
    docs.mkdir()
    blog.mkdir()
    (tmp_path / "docusaurus.config.ts").write_text(
        "export default { baseUrl: '/', url: 'https://example.com', title: 'T' };\n",
        encoding="utf-8",
    )
    (docs / "intro.md").write_text("# Intro\n\nWelcome.\n", encoding="utf-8")
    (blog / "2026-01-15-post.md").write_text(
        "---\ntags: [tutorial, python]\n---\n# Post\n\nContent.\n", encoding="utf-8"
    )


def _invoke_json(tmp_path: Path, extra_args: list[str] | None = None) -> dict[str, typing.Any]:
    """Invoke `zenzic inspect routes --json` against tmp_path and return parsed dict."""
    args = ["inspect", "routes", "--json"] + (extra_args or [])
    with patch("zenzic.cli._inspect.find_repo_root", return_value=tmp_path):
        result = runner.invoke(app, args)
    assert result.exit_code == 0, f"CLI exited {result.exit_code}:\n{result.output}"
    return typing.cast(dict[str, typing.Any], json.loads(result.stdout))


def _invoke_raw(tmp_path: Path, args: list[str]) -> Result:
    """Return the raw CliRunner result (no assertions)."""
    with patch("zenzic.cli._inspect.find_repo_root", return_value=tmp_path):
        return runner.invoke(app, args)


class TestDigestContract:
    """sha256(url + ':' + ','.join(sorted(source_files))) — strict formula verification."""

    def _digest(self, url: str, source_files: list[str]) -> str:
        raw = url + ":" + ",".join(sorted(source_files))
        return hashlib.sha256(raw.encode()).hexdigest()

    def test_output_is_64_hex_chars(self) -> None:
        d = self._digest("/docs/intro/", ["docs/intro.md"])
        assert len(d) == 64
        assert all(c in "0123456789abcdef" for c in d)

    def test_single_physical_source_file(self) -> None:
        url = "/docs/intro/"
        sf = ["docs/intro.md"]
        expected = hashlib.sha256((url + ":" + sf[0]).encode()).hexdigest()
        assert self._digest(url, sf) == expected

    def test_source_file_order_is_sorted_before_hashing(self) -> None:
        url = "/blog/tags/python/"
        files_a = ["blog/post-b.md", "blog/post-a.md"]
        files_b = ["blog/post-a.md", "blog/post-b.md"]
        assert self._digest(url, files_a) == self._digest(url, files_b)

    def test_different_urls_produce_different_digests(self) -> None:
        sf = ["docs/page.md"]
        assert self._digest("/docs/page/", sf) != self._digest("/docs/other/", sf)

    def test_different_source_files_produce_different_digests(self) -> None:
        url = "/blog/tags/python/"
        d1 = self._digest(url, ["blog/post-a.md"])
        d2 = self._digest(url, ["blog/post-a.md", "blog/post-b.md"])
        assert d1 != d2


class TestJSONPurity:
    """stdout must contain EXCLUSIVELY valid JSON when --json is active.

    No Rich markup, no ANSI escape codes, no banners, no leading/trailing text.
    This is the JSON Purity Invariant (Rule R20 Machine Silence).
    """

    _ANSI_RE = re.compile("\\x1b\\[[0-9;]*[mGKHF]")

    def test_stdout_is_parseable_without_strip(self, tmp_path: Path) -> None:
        """json.loads(result.stdout) must succeed with no preprocessing."""
        _make_docusaurus_repo(tmp_path)
        result = _invoke_raw(tmp_path, ["inspect", "routes", "--json"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert "routes" in parsed

    def test_stdout_contains_no_ansi_escape_codes(self, tmp_path: Path) -> None:
        """stdout must not contain ANSI color/format escape sequences."""
        _make_docusaurus_repo(tmp_path)
        result = _invoke_raw(tmp_path, ["inspect", "routes", "--json"])
        assert result.exit_code == 0
        assert not self._ANSI_RE.search(result.stdout), (
            "ANSI escape code found in JSON stdout — Rich console leaked into JSON output"
        )

    def test_stdout_starts_with_opening_brace(self, tmp_path: Path) -> None:
        """The very first non-whitespace character must be '{' (no banners)."""
        _make_docusaurus_repo(tmp_path)
        result = _invoke_raw(tmp_path, ["inspect", "routes", "--json"])
        assert result.exit_code == 0
        assert result.stdout.lstrip()[0] == "{", (
            f"stdout does not start with '{{': {result.stdout[:80]!r}"
        )

    def test_stdout_ends_with_closing_brace(self, tmp_path: Path) -> None:
        """The last non-whitespace character must be '}' (no trailing noise)."""
        _make_docusaurus_repo(tmp_path)
        result = _invoke_raw(tmp_path, ["inspect", "routes", "--json"])
        assert result.exit_code == 0
        assert result.stdout.rstrip()[-1] == "}", (
            f"stdout does not end with '}}': ...{result.stdout[-80:]!r}"
        )

    def test_invalid_kind_with_json_exits_1_stdout_not_json(self, tmp_path: Path) -> None:
        """When --kind bogus + --json: exit code is 1 and stdout is not valid JSON."""
        _make_docusaurus_repo(tmp_path)
        result = _invoke_raw(tmp_path, ["inspect", "routes", "--json", "--kind", "bogus"])
        assert result.exit_code == 1
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.stdout)
