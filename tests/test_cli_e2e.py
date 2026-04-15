# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""End-to-end CLI tests for Zenzic security exit-code contract.

These tests exercise the **full** CLI pipeline — no mocks on the scanner,
validator, or reporter.  They verify the documented exit-code contract:

    Exit 0 — all checks passed
    Exit 1 — general failures (broken links, syntax errors, …)
    Exit 2 — Shield credential detection (NEVER suppressed by --exit-zero)
    Exit 3 — Blood Sentinel system-path traversal (NEVER suppressed)

Gap closed: ``docs/internal/arch_gaps.md`` § "Security Pipeline Coverage".
"""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from zenzic.main import app


runner = CliRunner()

_BLOOD_SANDBOX = Path(__file__).resolve().parent / "sandboxes" / "screenshot_blood"


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_sandbox(tmp_path: Path, files: dict[str, str]) -> Path:
    """Create a minimal Zenzic project in *tmp_path*.

    Writes ``zenzic.toml`` and the given *files* (paths relative to the
    sandbox root).  Returns the sandbox root.
    """
    toml = tmp_path / "zenzic.toml"
    toml.write_text(
        textwrap.dedent("""\
            docs_dir = "docs"

            [build_context]
            engine = "mkdocs"
        """),
        encoding="utf-8",
    )
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(content), encoding="utf-8")
    return tmp_path


# ── Blood Sentinel — Exit 3 (system-path traversal) ─────────────────────────


class TestBloodSentinelE2E:
    """Blood Sentinel must exit 3 on system-path traversal."""

    def test_blood_sandbox_exits_3(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """check all on the blood sandbox triggers Exit 3."""
        sandbox = tmp_path / "blood"
        shutil.copytree(_BLOOD_SANDBOX, sandbox)
        monkeypatch.chdir(sandbox)

        result = runner.invoke(app, ["check", "all"])

        assert result.exit_code == 3, (
            f"Expected exit 3 (security_incident), got {result.exit_code}.\n"
            f"Output:\n{result.stdout}"
        )
        assert "PATH_TRAVERSAL_SUSPICIOUS" in result.stdout

    def test_blood_exit_3_not_suppressed_by_exit_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--exit-zero must NOT suppress Exit 3 — documented contract."""
        sandbox = tmp_path / "blood"
        shutil.copytree(_BLOOD_SANDBOX, sandbox)
        monkeypatch.chdir(sandbox)

        result = runner.invoke(app, ["check", "all", "--exit-zero"])

        assert result.exit_code == 3, (
            f"--exit-zero must not suppress Exit 3 (security_incident), "
            f"got {result.exit_code}.\nOutput:\n{result.stdout}"
        )


# ── Shield Breach — Exit 2 (credential leak) ────────────────────────────────


class TestShieldBreachE2E:
    """Shield must exit 2 when a credential is detected."""

    _BREACH_DOC = """\
        # Cloud Setup

        This page documents the initial cloud provider configuration steps
        for the deployment pipeline.  Follow the instructions carefully.

        ## Provider Credentials

        Refer to the provisioning guide for credential rotation procedures
        and the secret management policy before deploying to production.

        [AWS Dashboard](https://console.aws.amazon.com?key=AKIA1234567890ABCDEF)
    """

    def test_shield_breach_exits_2(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """check all exits 2 when an AWS key is embedded in a link URL."""
        _make_sandbox(tmp_path, {"docs/index.md": self._BREACH_DOC})
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "all"])

        assert result.exit_code == 2, (
            f"Expected exit 2 (security_breach), got {result.exit_code}.\nOutput:\n{result.stdout}"
        )
        assert "ZENZIC SENTINEL" in result.stdout

    def test_shield_exit_2_not_suppressed_by_exit_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--exit-zero must NOT suppress Exit 2 — documented contract."""
        _make_sandbox(tmp_path, {"docs/index.md": self._BREACH_DOC})
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "all", "--exit-zero"])

        assert result.exit_code == 2, (
            f"--exit-zero must not suppress Exit 2 (security_breach), "
            f"got {result.exit_code}.\nOutput:\n{result.stdout}"
        )


# ── --exit-zero suppresses Exit 1 (general errors) ──────────────────────────


class TestExitZeroContractE2E:
    """--exit-zero suppresses general failures but not security exits."""

    _BROKEN_LINK_DOC = """\
        # Home

        This page contains a broken link to exercise the general failure
        exit path.  The target file does not exist in this sandbox.

        [Broken](this-page-does-not-exist.md)
    """

    def test_broken_link_exits_1(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """check all exits 1 on a broken link (baseline)."""
        _make_sandbox(tmp_path, {"docs/index.md": self._BROKEN_LINK_DOC})
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "all"])

        assert result.exit_code == 1, (
            f"Expected exit 1 (general failure), got {result.exit_code}.\nOutput:\n{result.stdout}"
        )

    def test_exit_zero_suppresses_exit_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--exit-zero must suppress Exit 1 (broken links)."""
        _make_sandbox(tmp_path, {"docs/index.md": self._BROKEN_LINK_DOC})
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "all", "--exit-zero"])

        assert result.exit_code == 0, (
            f"--exit-zero should suppress Exit 1, got {result.exit_code}.\nOutput:\n{result.stdout}"
        )

    def test_clean_sandbox_exits_0(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A clean sandbox with no issues exits 0."""
        _make_sandbox(
            tmp_path,
            {
                "docs/index.md": """\
                    # Welcome

                    This is a perfectly valid documentation page with enough words
                    to pass the placeholder check.  It contains no broken links,
                    no credentials, and no path traversal attempts.  The content
                    is intentionally verbose to exceed the minimum word count
                    threshold enforced by the short-content scanner.
                """,
            },
        )
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "all"])

        assert result.exit_code == 0, (
            f"Expected exit 0 (clean), got {result.exit_code}.\nOutput:\n{result.stdout}"
        )
        assert "All checks passed" in result.stdout


# ── Priority: Exit 3 wins over Exit 2 ───────────────────────────────────────


class TestExitCodePriorityE2E:
    """When both security_incident and security_breach coexist, Exit 3 wins."""

    def test_exit_3_beats_exit_2(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Exit 3 (Blood Sentinel) takes priority over Exit 2 (Shield breach)."""
        _make_sandbox(
            tmp_path,
            {
                "docs/index.md": """\
                    # Dual Threat

                    This page has both a system-path traversal and a leaked
                    credential to verify the exit-code priority contract.

                    [Host](../../../../etc/shadow)

                    [AWS](https://console.aws.amazon.com?key=AKIA1234567890ABCDEF)
                """,
            },
        )
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "all"])

        assert result.exit_code == 3, (
            f"Exit 3 (security_incident) must beat Exit 2 (security_breach), "
            f"got {result.exit_code}.\nOutput:\n{result.stdout}"
        )


# ── --format json on individual check commands ──────────────────────────────


class TestJsonFormatE2E:
    """--format json outputs structured JSON on individual check commands."""

    def test_check_links_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """check links --format json outputs valid JSON with findings/summary keys."""
        _make_sandbox(tmp_path, {"docs/index.md": "# Hello\n\nEnough words to not be a placeholder for the scanner."})
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "links", "--format", "json"])

        assert result.exit_code == 0
        import json

        data = json.loads(result.stdout)
        assert "findings" in data
        assert "summary" in data
        assert "errors" in data["summary"]
        assert "elapsed_seconds" in data["summary"]

    def test_check_orphans_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """check orphans --format json outputs valid JSON."""
        _make_sandbox(tmp_path, {"docs/index.md": "# Home\n\nWords words words words words words words."})
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "orphans", "--format", "json"])

        assert result.exit_code == 0
        import json

        data = json.loads(result.stdout)
        assert "findings" in data
        assert "summary" in data

    def test_check_snippets_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """check snippets --format json outputs valid JSON."""
        _make_sandbox(tmp_path, {"docs/index.md": "# Home\n\nWords words words."})
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "snippets", "--format", "json"])

        assert result.exit_code == 0
        import json

        data = json.loads(result.stdout)
        assert "findings" in data
        assert "summary" in data

    def test_check_references_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """check references --format json outputs valid JSON."""
        _make_sandbox(tmp_path, {"docs/index.md": "# Home\n\nWords words words."})
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "references", "--format", "json"])

        assert result.exit_code == 0
        import json

        data = json.loads(result.stdout)
        assert "findings" in data
        assert "summary" in data

    def test_check_assets_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """check assets --format json outputs valid JSON."""
        _make_sandbox(tmp_path, {"docs/index.md": "# Home\n\nWords words words."})
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "assets", "--format", "json"])

        assert result.exit_code == 0
        import json

        data = json.loads(result.stdout)
        assert "findings" in data
        assert "summary" in data

    def test_check_links_json_exit_code_on_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """check links --format json still exits 1 on broken links."""
        _make_sandbox(tmp_path, {"docs/index.md": "# Home\n\n[Broken](nope.md)"})
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check", "links", "--format", "json"])

        assert result.exit_code == 1
        import json

        data = json.loads(result.stdout)
        assert data["summary"]["errors"] > 0
        assert len(data["findings"]) > 0
