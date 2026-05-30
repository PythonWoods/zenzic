# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""STEP 3 — zenzic inspect routes: JSON purity, data contract, --kind filter tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from zenzic.core import regex as re
from zenzic.main import app


runner = CliRunner()


# ── Fixture builder ───────────────────────────────────────────────────────────


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
        "---\ntags: [tutorial, python]\n---\n# Post\n\nContent.\n",
        encoding="utf-8",
    )


def _invoke_json(tmp_path: Path, extra_args: list[str] | None = None) -> dict:
    """Invoke `zenzic inspect routes --json` against tmp_path and return parsed dict."""
    args = ["inspect", "routes", "--json"] + (extra_args or [])
    with patch("zenzic.cli._inspect.find_repo_root", return_value=tmp_path):
        result = runner.invoke(app, args)
    assert result.exit_code == 0, f"CLI exited {result.exit_code}:\n{result.output}"
    return json.loads(result.stdout)


def _invoke_raw(tmp_path: Path, args: list[str]) -> CliRunner:
    """Return the raw CliRunner result (no assertions)."""
    with patch("zenzic.cli._inspect.find_repo_root", return_value=tmp_path):
        return runner.invoke(app, args)


# ── Pure unit: digest formula ─────────────────────────────────────────────────


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
        # Both orders must produce the same digest because sorted() is applied
        assert self._digest(url, files_a) == self._digest(url, files_b)

    def test_different_urls_produce_different_digests(self) -> None:
        sf = ["docs/page.md"]
        assert self._digest("/docs/page/", sf) != self._digest("/docs/other/", sf)

    def test_different_source_files_produce_different_digests(self) -> None:
        url = "/blog/tags/python/"
        d1 = self._digest(url, ["blog/post-a.md"])
        d2 = self._digest(url, ["blog/post-a.md", "blog/post-b.md"])
        assert d1 != d2


# ── Integration: JSON structure contract ─────────────────────────────────────


class TestInspectRoutesJSON:
    """End-to-end: CLI output must respect the full data contract."""

    def test_top_level_routes_key_is_present(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path)
        assert "routes" in data
        assert isinstance(data["routes"], list)

    def test_each_record_has_required_fields(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path)
        assert len(data["routes"]) > 0
        for rec in data["routes"]:
            assert "url" in rec, f"missing 'url' in {rec}"
            assert "kind" in rec, f"missing 'kind' in {rec}"
            assert "source_files" in rec, f"missing 'source_files' in {rec}"
            assert "digest" in rec, f"missing 'digest' in {rec}"

    def test_source_files_is_non_empty_list_of_strings(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path)
        for rec in data["routes"]:
            assert isinstance(rec["source_files"], list), f"source_files not a list in {rec}"
            assert len(rec["source_files"]) > 0, f"source_files is empty in {rec}"
            for sf in rec["source_files"]:
                assert isinstance(sf, str)

    def test_digest_matches_formula_for_physical_route(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path)
        physical = [r for r in data["routes"] if r["kind"] == "physical"]
        assert len(physical) > 0, "Expected at least one physical route"
        for rec in physical:
            url = rec["url"]
            sf = rec["source_files"]
            expected = hashlib.sha256((url + ":" + ",".join(sorted(sf))).encode()).hexdigest()
            assert rec["digest"] == expected, (
                f"Digest mismatch for {url}: got {rec['digest']!r}, expected {expected!r}"
            )

    def test_digest_matches_formula_for_virtual_route(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path)
        virtual = [r for r in data["routes"] if r["kind"] != "physical"]
        assert len(virtual) > 0, "Expected at least one virtual route"
        for rec in virtual:
            url = rec["url"]
            sf = rec["source_files"]
            expected = hashlib.sha256((url + ":" + ",".join(sorted(sf))).encode()).hexdigest()
            assert rec["digest"] == expected, f"Digest mismatch for virtual {url}"

    def test_physical_route_has_kind_physical(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path)
        physical = [r for r in data["routes"] if r["kind"] == "physical"]
        assert len(physical) > 0

    def test_virtual_tag_route_has_kind_tag(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path)
        tag_routes = [r for r in data["routes"] if r["kind"] == "tag"]
        assert len(tag_routes) > 0, "Expected tag virtual routes from blog posts"
        tag_urls = {r["url"] for r in tag_routes}
        assert "/blog/tags/tutorial/" in tag_urls or any("tutorial" in u for u in tag_urls), (
            f"Expected /blog/tags/tutorial/ in {tag_urls}"
        )

    def test_tag_index_route_has_kind_tag_index(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path)
        tag_index = [r for r in data["routes"] if r["kind"] == "tag_index"]
        assert len(tag_index) == 1, f"Expected exactly one tag_index, got {tag_index}"
        assert tag_index[0]["url"] == "/blog/tags/"

    def test_physical_docs_source_file_is_repo_relative(self, tmp_path: Path) -> None:
        """docs/intro.md must appear as 'docs/intro.md' not 'intro.md'."""
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path)
        physical = [r for r in data["routes"] if r["kind"] == "physical"]
        all_sources = [sf for r in physical for sf in r["source_files"]]
        assert any(sf.startswith("docs/") for sf in all_sources), (
            f"Expected at least one docs/ source file, got: {all_sources}"
        )

    def test_output_is_sorted_by_url(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path)
        urls = [r["url"] for r in data["routes"]]
        assert urls == sorted(urls), "Routes must be sorted by URL"


# ── Integration: --kind filter ────────────────────────────────────────────────


class TestKindFilter:
    """--kind flag must filter the route list correctly."""

    def test_kind_physical_excludes_virtual_routes(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path, ["--kind", "physical"])
        assert all(r["kind"] == "physical" for r in data["routes"])

    def test_kind_virtual_excludes_physical_routes(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path, ["--kind", "virtual"])
        assert all(r["kind"] != "physical" for r in data["routes"])
        assert len(data["routes"]) > 0, "Expected virtual routes with tagged blog posts"

    def test_kind_all_includes_both(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        data = _invoke_json(tmp_path, ["--kind", "all"])
        kinds = {r["kind"] for r in data["routes"]}
        assert "physical" in kinds
        assert len(kinds) > 1  # at least one non-physical kind

    def test_kind_invalid_exits_1(self, tmp_path: Path) -> None:
        _make_docusaurus_repo(tmp_path)
        with patch("zenzic.cli._inspect.find_repo_root", return_value=tmp_path):
            result = runner.invoke(app, ["inspect", "routes", "--kind", "bogus"])
        assert result.exit_code == 1


# ── JSON Purity Invariant (Rule R20 Machine Silence) ─────────────────────────


class TestJSONPurity:
    """stdout must contain EXCLUSIVELY valid JSON when --json is active.

    No Rich markup, no ANSI escape codes, no banners, no leading/trailing text.
    This is the JSON Purity Invariant (Rule R20 Machine Silence).
    """

    _ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

    def test_stdout_is_parseable_without_strip(self, tmp_path: Path) -> None:
        """json.loads(result.stdout) must succeed with no preprocessing."""
        _make_docusaurus_repo(tmp_path)
        result = _invoke_raw(tmp_path, ["inspect", "routes", "--json"])
        assert result.exit_code == 0
        # Must parse with NO strip() — any leading/trailing non-JSON content fails here
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


# ── JSON Purity Invariant — subprocess (OS-level stdout capture) ──────────────


class TestJSONPuritySubprocess:
    """Gold-standard purity check: real OS process, stdout captured at the kernel level.

    Unlike CliRunner-based tests, this class invokes `zenzic` as a true subprocess
    so no mock, monkey-patch, or Click test harness can mask a Rich/logging leak.
    If stdout contains even a single non-JSON character the test fails.
    """

    _ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

    @staticmethod
    def _make_subprocess_fixture(tmp_path: Path) -> None:
        """Like _make_docusaurus_repo but also writes .zenzic.toml (needed by find_repo_root)."""
        _make_docusaurus_repo(tmp_path)
        (tmp_path / ".zenzic.toml").write_text(
            '[build_context]\nengine = "docusaurus"\n', encoding="utf-8"
        )

    @staticmethod
    def _zenzic_exe() -> Path:
        """Resolve the `zenzic` executable installed alongside the current interpreter."""
        return Path(sys.executable).parent / "zenzic"

    def test_subprocess_stdout_is_valid_json_without_preprocessing(self, tmp_path: Path) -> None:
        """json.loads(proc.stdout) must succeed with no strip() — gold-standard purity."""
        self._make_subprocess_fixture(tmp_path)
        proc = subprocess.run(
            [str(self._zenzic_exe()), "inspect", "routes", "--json"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, f"zenzic exited {proc.returncode}; stderr:\n{proc.stderr}"
        # Gold standard: no preprocessing whatsoever
        data = json.loads(proc.stdout)
        assert "routes" in data

    def test_subprocess_stdout_contains_no_ansi_codes(self, tmp_path: Path) -> None:
        """Real stdout must be free of ANSI escape sequences."""
        self._make_subprocess_fixture(tmp_path)
        proc = subprocess.run(
            [str(self._zenzic_exe()), "inspect", "routes", "--json"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, f"zenzic exited {proc.returncode}; stderr:\n{proc.stderr}"
        assert not self._ANSI_RE.search(proc.stdout), (
            "ANSI escape code found in subprocess stdout — Rich/logging leaked outside CliRunner"
        )

    def test_subprocess_stderr_is_empty_on_success(self, tmp_path: Path) -> None:
        """On success, nothing must appear on stderr (no banners, no warnings)."""
        self._make_subprocess_fixture(tmp_path)
        proc = subprocess.run(
            [str(self._zenzic_exe()), "inspect", "routes", "--json"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, f"zenzic exited {proc.returncode}; stderr:\n{proc.stderr}"
        assert proc.stderr == "", f"Expected empty stderr on success, got:\n{proc.stderr}"
