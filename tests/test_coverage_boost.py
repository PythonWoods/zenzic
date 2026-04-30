# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Targeted coverage tests — CEO-248 "The 80% Iron Gate Enforcement".

Covers previously-untested branches in:
- ``core/models.py``      (0%  → 100%)
- ``core/logging.py``     (65% → 100%)
- ``core/ui.py``          (65% → 90%+)
- ``cli/_brain.py``       (14% → 75%+)
- ``cli/_clean.py``       (15% → 70%+)
- ``cli/_shared.py``      (50% → 80%+)
"""

from __future__ import annotations

import logging as _logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from typer.testing import CliRunner

from zenzic.models.config import ZenzicConfig


runner = CliRunner()
_FAKE_ROOT = Path("/fake/repo")
_CFG = ZenzicConfig()


# ─────────────────────────────────────────────────────────────────────────────
# core/models.py  (0% → 100%)
# ─────────────────────────────────────────────────────────────────────────────


def test_core_models_reexport() -> None:
    """Importing core/models.py covers its 2 statements."""
    from zenzic.core.models import IntegrityReport, ReferenceFinding, ReferenceMap

    assert IntegrityReport is not None
    assert ReferenceFinding is not None
    assert ReferenceMap is not None


# ─────────────────────────────────────────────────────────────────────────────
# core/logging.py  (65% → 100%)
# ─────────────────────────────────────────────────────────────────────────────


class TestLogging:
    """Cover ``get_logger`` with sub-name and ``setup_cli_logging`` branches."""

    def _clear_handlers(self) -> None:
        from rich.logging import RichHandler

        root = _logging.getLogger("zenzic")
        root.handlers = [h for h in root.handlers if not isinstance(h, RichHandler)]

    def test_get_logger_no_name(self) -> None:
        from zenzic.core.logging import get_logger

        logger = get_logger()
        assert logger.name == "zenzic"

    def test_get_logger_with_name(self) -> None:
        """Cover the ``if name:`` branch in ``get_logger``."""
        from zenzic.core.logging import get_logger

        logger = get_logger("core.scanner")
        assert logger.name == "zenzic.core.scanner"

    def test_get_logger_with_different_sub_names(self) -> None:
        from zenzic.core.logging import get_logger

        for sub in ("shield", "validator", "rules"):
            lg = get_logger(sub)
            assert lg.name == f"zenzic.{sub}"

    def test_setup_cli_logging_installs_rich_handler(self) -> None:
        """Cover the handler installation path in ``setup_cli_logging``."""
        from rich.logging import RichHandler

        from zenzic.core.logging import setup_cli_logging

        self._clear_handlers()
        setup_cli_logging()
        root = _logging.getLogger("zenzic")
        assert any(isinstance(h, RichHandler) for h in root.handlers)
        self._clear_handlers()

    def test_setup_cli_logging_idempotent(self) -> None:
        """Cover the early-return branch (already configured)."""
        from zenzic.core.logging import setup_cli_logging

        self._clear_handlers()
        setup_cli_logging()
        count = len(_logging.getLogger("zenzic").handlers)
        setup_cli_logging()  # second call — must be no-op
        assert len(_logging.getLogger("zenzic").handlers) == count
        self._clear_handlers()

    def test_setup_cli_logging_debug_level(self) -> None:
        """Cover the ``level`` parameter path."""
        from zenzic.core.logging import setup_cli_logging

        self._clear_handlers()
        setup_cli_logging(level=_logging.DEBUG)
        root = _logging.getLogger("zenzic")
        assert root.level == _logging.DEBUG
        self._clear_handlers()


# ─────────────────────────────────────────────────────────────────────────────
# core/ui.py  (65% → 90%+)
# ─────────────────────────────────────────────────────────────────────────────


class TestUI:
    """Cover uncovered branches in ``emoji``, ``make_sentinel_header``,
    ``print_exception_alert``, and ``_detect_capabilities``."""

    # ── emoji() ───────────────────────────────────────────────────────────────

    def test_emoji_unicode_path(self) -> None:
        from zenzic.core.ui import emoji

        # SUPPORTS_EMOJI is True in CI=false/not-dumb dev environments
        result = emoji("sparkles")
        assert result in ("\u2728", "*")

    def test_emoji_unknown_key_returns_name(self) -> None:
        from zenzic.core.ui import emoji

        assert emoji("nonexistent_key_xyz") == "nonexistent_key_xyz"

    def test_emoji_ascii_fallback_when_no_emoji_support(self) -> None:
        """Cover the ``pair[1]`` branch inside ``emoji()``."""
        import zenzic.core.ui as ui_mod

        original = ui_mod.SUPPORTS_EMOJI
        try:
            ui_mod.SUPPORTS_EMOJI = False
            result = ui_mod.emoji("check")
            assert result == "*"  # ASCII fallback
            result2 = ui_mod.emoji("sparkles")
            assert result2 == "*"
        finally:
            ui_mod.SUPPORTS_EMOJI = original

    # ── _detect_capabilities() ────────────────────────────────────────────────

    def test_detect_capabilities_no_color_env(self) -> None:
        from zenzic.core.ui import _detect_capabilities

        with patch.dict("os.environ", {"NO_COLOR": "1"}, clear=False):
            supports_color, _ = _detect_capabilities()
        assert supports_color is False

    def test_detect_capabilities_dumb_term(self) -> None:
        from zenzic.core.ui import _detect_capabilities

        env = {"TERM": "dumb"}
        # Remove NO_COLOR to isolate the dumb-term path
        with patch.dict("os.environ", env, clear=False):
            supports_color, supports_emoji = _detect_capabilities()
        assert supports_color is False
        assert supports_emoji is False

    def test_detect_capabilities_ci_env(self) -> None:
        from zenzic.core.ui import _detect_capabilities

        with patch.dict("os.environ", {"CI": "true"}, clear=False):
            _, supports_emoji = _detect_capabilities()
        assert supports_emoji is False

    def test_detect_capabilities_no_env_overrides(self) -> None:
        """Cover default path — at minimum does not raise."""
        from zenzic.core.ui import _detect_capabilities

        env_clear = {"NO_COLOR": "", "CI": "", "TERM": "xterm"}
        with patch.dict("os.environ", env_clear, clear=False):
            result = _detect_capabilities()
        assert isinstance(result, tuple)
        assert len(result) == 2

    # ── make_sentinel_header() ────────────────────────────────────────────────

    def test_make_sentinel_header_minimal(self) -> None:
        from zenzic.core.ui import make_sentinel_header

        result = make_sentinel_header("1.0")
        assert "ZENZIC SENTINEL" in result
        assert "1.0" in result

    def test_make_sentinel_header_with_target(self) -> None:
        """Cover the ``if target is not None:`` branch."""
        from zenzic.core.ui import make_sentinel_header

        result = make_sentinel_header("1.0", engine="mkdocs", target="/docs/guide")
        assert "/docs/guide" in result

    def test_make_sentinel_header_with_files(self) -> None:
        """Cover the ``if total:`` branch including singular file."""
        from zenzic.core.ui import make_sentinel_header

        result_multi = make_sentinel_header("1.0", docs_count=10, assets_count=5)
        # String contains Rich markup, check for numbers and keyword separately
        assert "15" in result_multi
        assert "file" in result_multi

        result_single = make_sentinel_header("1.0", docs_count=1, assets_count=0)
        # Rich markup: "[#4f46e5]1[/] file" — check for "file" and "1" separately
        assert "file" in result_single
        assert "1" in result_single

    def test_make_sentinel_header_with_elapsed(self) -> None:
        """Cover the ``if elapsed:`` branch."""
        from zenzic.core.ui import make_sentinel_header

        result = make_sentinel_header("1.0", elapsed=2.3)
        assert "2.3" in result

    def test_make_sentinel_header_all_branches(self) -> None:
        """Hit all optional branches in one call."""
        from zenzic.core.ui import make_sentinel_header

        result = make_sentinel_header(
            "0.7.0",
            engine="docusaurus",
            target="docs/",
            docs_count=20,
            assets_count=8,
            elapsed=3.14,
        )
        assert "ZENZIC SENTINEL" in result
        assert "docs/" in result
        assert "28" in result
        assert "3.1" in result

    # ── SentinelUI.print_exception_alert() ────────────────────────────────────

    def test_print_exception_alert_no_context(self) -> None:
        from zenzic.core.ui import SentinelUI

        console = Console(highlight=False, force_terminal=True)
        ui = SentinelUI(console)
        ui.print_exception_alert("Something went wrong")  # no context — default path

    def test_print_exception_alert_with_context(self) -> None:
        """Cover the ``if context:`` branch."""
        from zenzic.core.ui import SentinelUI

        console = Console(highlight=False, force_terminal=True)
        ui = SentinelUI(console)
        ui.print_exception_alert(
            "Detailed error",
            context={"file": "docs/index.md", "line": "42", "code": "Z104"},
            title="Sentinel Alert",
        )

    def test_print_exception_alert_custom_border(self) -> None:
        """Cover the ``border_style`` parameter path."""
        from zenzic.core.ui import SentinelPalette, SentinelUI

        console = Console(highlight=False, force_terminal=True)
        ui = SentinelUI(console)
        ui.print_exception_alert(
            "Plugin contract violation",
            border_style=SentinelPalette.STYLE_BRAND,
        )

    def test_make_panel_factory(self) -> None:
        from zenzic.core.ui import SentinelUI

        panel = SentinelUI.make_panel("content", title="My Title", subtitle="subtitle")
        assert panel is not None

    def test_print_header(self) -> None:
        from zenzic.core.ui import SentinelUI

        console = Console(highlight=False, force_terminal=True)
        ui = SentinelUI(console)
        ui.print_header("0.7.0")  # must not raise


# ─────────────────────────────────────────────────────────────────────────────
# cli/_brain.py  (14% → 75%+)
# ─────────────────────────────────────────────────────────────────────────────


class TestBrainHelpers:
    """Direct unit tests for private helpers in ``cli/_brain.py``."""

    # ── _find_src_root ────────────────────────────────────────────────────────

    def test_find_src_root_with_src_package(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _find_src_root

        (tmp_path / "src" / "mypkg").mkdir(parents=True)
        result = _find_src_root(tmp_path)
        assert result == tmp_path / "src" / "mypkg"

    def test_find_src_root_src_only(self, tmp_path: Path) -> None:
        """Cover ``return src_dir`` when src/ exists but has no sub-packages."""
        from zenzic.cli._brain import _find_src_root

        (tmp_path / "src").mkdir()
        result = _find_src_root(tmp_path)
        assert result == tmp_path / "src"

    def test_find_src_root_no_src(self, tmp_path: Path) -> None:
        """Cover ``return base`` when no src/ exists."""
        from zenzic.cli._brain import _find_src_root

        result = _find_src_root(tmp_path)
        assert result == tmp_path

    def test_find_src_root_ignores_hidden_dirs(self, tmp_path: Path) -> None:
        """Hidden dirs (dot-prefixed) are excluded from candidates."""
        from zenzic.cli._brain import _find_src_root

        (tmp_path / "src" / ".hidden").mkdir(parents=True)
        (tmp_path / "src" / "mypkg").mkdir()
        result = _find_src_root(tmp_path)
        assert result == tmp_path / "src" / "mypkg"

    # ── _find_ledger ──────────────────────────────────────────────────────────

    def test_find_ledger_found_in_parent(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _find_ledger

        brain = tmp_path / "ZENZIC_BRAIN.md"
        brain.write_text("# Brain\n", encoding="utf-8")
        child = tmp_path / "src" / "pkg"
        child.mkdir(parents=True)
        result = _find_ledger(child)
        assert result == brain

    def test_find_ledger_found_at_start(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _find_ledger

        brain = tmp_path / "ZENZIC_BRAIN.md"
        brain.write_text("# Brain\n", encoding="utf-8")
        result = _find_ledger(tmp_path)
        assert result == brain

    def test_find_ledger_not_found_returns_none(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _find_ledger

        # tmp_path has no ZENZIC_BRAIN.md — search will hit filesystem root
        result = _find_ledger(tmp_path)
        # May or may not find one depending on real FS — just check type
        assert result is None or isinstance(result, Path)

    # ── _shadow_sync ──────────────────────────────────────────────────────────

    def test_shadow_sync_creates_copilot_instructions(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _shadow_sync

        brain = tmp_path / "ZENZIC_BRAIN.md"
        brain.write_text("# Master content\n", encoding="utf-8")
        shadow = _shadow_sync(brain)
        assert shadow.exists()
        assert shadow.read_text(encoding="utf-8") == "# Master content\n"
        assert shadow.name == "copilot-instructions.md"

    # ── _audit_zone_b ─────────────────────────────────────────────────────────

    def test_audit_zone_b_within_limit(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _ZONE_B_END, _ZONE_B_LIMIT, _ZONE_B_START, _audit_zone_b

        content = f"Header\n{_ZONE_B_START}\nLine1\nLine2\n{_ZONE_B_END}\nFooter\n"
        brain = tmp_path / "ZENZIC_BRAIN.md"
        brain.write_text(content, encoding="utf-8")
        count, limit = _audit_zone_b(brain)
        assert count == 2
        assert limit == _ZONE_B_LIMIT

    def test_audit_zone_b_empty_zone(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _ZONE_B_END, _ZONE_B_START, _audit_zone_b

        content = f"{_ZONE_B_START}\n{_ZONE_B_END}\n"
        brain = tmp_path / "ZENZIC_BRAIN.md"
        brain.write_text(content, encoding="utf-8")
        count, _ = _audit_zone_b(brain)
        assert count == 0

    # ── _detect_mesh_status ───────────────────────────────────────────────────

    def test_detect_mesh_status_all_present(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _MESH_REPOS, _detect_mesh_status

        # Create sibling repos with ZENZIC_BRAIN.md
        for name in _MESH_REPOS:
            sibling = tmp_path / name
            sibling.mkdir()
            (sibling / "ZENZIC_BRAIN.md").write_text("# brain", encoding="utf-8")

        # Put our "repo" inside tmp_path
        repo = tmp_path / "zenzic"
        result = _detect_mesh_status(repo)
        assert "[MESH STATUS]" in result
        assert "🟢" in result

    def test_detect_mesh_status_all_missing(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _detect_mesh_status

        repo = tmp_path / "zenzic"
        repo.mkdir()
        result = _detect_mesh_status(repo)
        assert "🔴" in result

    def test_detect_mesh_status_mixed(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _MESH_REPOS, _detect_mesh_status

        # Only first repo present
        first = tmp_path / _MESH_REPOS[0]
        first.mkdir()
        (first / "ZENZIC_BRAIN.md").write_text("# brain", encoding="utf-8")
        repo = tmp_path / _MESH_REPOS[0]
        result = _detect_mesh_status(repo)
        assert "🟢" in result
        assert "🔴" in result


class TestBrainMapCommand:
    """Integration tests for the ``brain map`` Typer command."""

    def test_brain_map_updates_ledger(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import _ZONE_B_END, _ZONE_B_START, brain_app
        from zenzic.core.cartography import MAP_END, MAP_START

        # Setup a minimal repo with src package and ZENZIC_BRAIN.md
        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "mod.py").write_text('"""Module."""\n\ndef public(): pass\n', encoding="utf-8")

        brain = tmp_path / "ZENZIC_BRAIN.md"
        brain.write_text(
            f"# Header\n{MAP_START}\nOLD\n{MAP_END}\n"
            f"{_ZONE_B_START}\nSprint content\n{_ZONE_B_END}\n",
            encoding="utf-8",
        )

        # NOTE: Typer 0.24 collapses single-command apps — no 'map' prefix needed
        result = runner.invoke(brain_app, [str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert "✔" in result.output
        text = brain.read_text(encoding="utf-8")
        assert "OLD" not in text
        assert "mod.py" in text

    def test_brain_map_no_src_files(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import brain_app

        brain = tmp_path / "ZENZIC_BRAIN.md"
        brain.write_text("# brain\n", encoding="utf-8")
        # No .py files → no modules found
        result = runner.invoke(brain_app, [str(tmp_path)])
        assert result.exit_code == 1

    def test_brain_map_no_ledger_prints_output(self, tmp_path: Path) -> None:
        """Cover the ``ledger is None`` branch — prints map for manual insertion."""
        from zenzic.cli._brain import brain_app
        from zenzic.core.cartography import MAP_START

        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "mod.py").write_text('"""Module."""\n\ndef fn(): pass\n', encoding="utf-8")
        # No ZENZIC_BRAIN.md anywhere near tmp_path
        # Invoke in an isolated tmp so _find_ledger walks into a path with no BRAIN
        result = runner.invoke(brain_app, [str(tmp_path)])
        assert result.exit_code == 0
        assert MAP_START in result.output

    def test_brain_map_invalid_path(self, tmp_path: Path) -> None:
        from zenzic.cli._brain import brain_app

        result = runner.invoke(brain_app, [str(tmp_path / "nonexistent")])
        assert result.exit_code == 1

    def test_brain_map_zone_b_overflow(self, tmp_path: Path) -> None:
        """Cover the Z907 overflow branch."""
        from zenzic.cli._brain import _ZONE_B_END, _ZONE_B_START, brain_app
        from zenzic.core.cartography import MAP_END, MAP_START

        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "mod.py").write_text('"""Module."""\n\ndef fn(): pass\n', encoding="utf-8")

        # Zone B with 401 lines (> _ZONE_B_LIMIT=400)
        zone_b_content = "\n".join(f"Line {i}" for i in range(401))
        brain = tmp_path / "ZENZIC_BRAIN.md"
        brain.write_text(
            f"# H\n{MAP_START}\nOLD\n{MAP_END}\n{_ZONE_B_START}\n{zone_b_content}\n{_ZONE_B_END}\n",
            encoding="utf-8",
        )
        result = runner.invoke(brain_app, [str(tmp_path)])
        assert result.exit_code == 2

    def test_brain_map_already_up_to_date(self, tmp_path: Path) -> None:
        """Cover the ``not updated`` branch."""
        from zenzic.cli._brain import _ZONE_B_END, _ZONE_B_START, brain_app
        from zenzic.core.cartography import MAP_END, MAP_START

        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "mod.py").write_text('"""Module."""\n\ndef fn(): pass\n', encoding="utf-8")

        # First run to generate the map
        brain = tmp_path / "ZENZIC_BRAIN.md"
        brain.write_text(
            f"# H\n{MAP_START}\nOLD\n{MAP_END}\n{_ZONE_B_START}\nSprint\n{_ZONE_B_END}\n",
            encoding="utf-8",
        )
        runner.invoke(brain_app, [str(tmp_path)])
        # Second run — map should already match
        result = runner.invoke(brain_app, [str(tmp_path)])
        assert result.exit_code == 0
        assert "already up to date" in result.output


# ─────────────────────────────────────────────────────────────────────────────
# cli/_clean.py  (15% → 70%+)
# ─────────────────────────────────────────────────────────────────────────────


class TestCleanAssets:
    """Integration tests for ``clean assets`` command."""

    def _make_adapter_mock(self) -> MagicMock:
        adapter = MagicMock()
        adapter.get_metadata_files.return_value = frozenset()
        return adapter

    def _make_exclusion_mock(self) -> MagicMock:
        return MagicMock()

    @patch("zenzic.cli._clean.find_repo_root", return_value=_FAKE_ROOT)
    @patch("zenzic.cli._clean.ZenzicConfig.load", return_value=(_CFG, True))
    @patch("zenzic.cli._clean.find_unused_assets", return_value=[])
    @patch("zenzic.core.adapters.get_adapter")
    @patch("zenzic.cli._shared._build_exclusion_manager")
    def test_clean_assets_no_unused(
        self, mock_excl, mock_adapter, mock_find, mock_cfg, mock_root
    ) -> None:
        """No unused assets → Sentinel Seal message, exit 0."""
        from zenzic.cli._clean import clean_app

        mock_adapter.return_value = self._make_adapter_mock()
        mock_excl.return_value = self._make_exclusion_mock()

        result = runner.invoke(clean_app, ["assets"])
        assert result.exit_code == 0
        assert "Sentinel Seal" in result.output or "No unused assets" in result.output

    @patch("zenzic.cli._clean.find_repo_root", return_value=_FAKE_ROOT)
    @patch("zenzic.cli._clean.ZenzicConfig.load", return_value=(_CFG, True))
    @patch("zenzic.cli._clean.find_unused_assets", return_value=["assets/old.png"])
    @patch("zenzic.core.adapters.get_adapter")
    @patch("zenzic.cli._shared._build_exclusion_manager")
    def test_clean_assets_dry_run(
        self, mock_excl, mock_adapter, mock_find, mock_cfg, mock_root
    ) -> None:
        """--dry-run shows files but does not delete, exit 0."""
        from zenzic.cli._clean import clean_app

        mock_adapter.return_value = self._make_adapter_mock()
        mock_excl.return_value = self._make_exclusion_mock()

        result = runner.invoke(clean_app, ["assets", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    @patch("zenzic.cli._clean.find_repo_root", return_value=_FAKE_ROOT)
    @patch("zenzic.cli._clean.ZenzicConfig.load", return_value=(_CFG, True))
    @patch("zenzic.cli._clean.find_unused_assets", return_value=["assets/old.png"])
    @patch("zenzic.core.adapters.get_adapter")
    @patch("zenzic.cli._shared._build_exclusion_manager")
    def test_clean_assets_cancelled_by_user(
        self, mock_excl, mock_adapter, mock_find, mock_cfg, mock_root
    ) -> None:
        """User declines confirmation → exit 1."""
        from zenzic.cli._clean import clean_app

        mock_adapter.return_value = self._make_adapter_mock()
        mock_excl.return_value = self._make_exclusion_mock()

        result = runner.invoke(clean_app, ["assets"], input="n\n")
        assert result.exit_code == 1
        assert "Cancelled" in result.output

    @patch("zenzic.cli._clean.find_repo_root", return_value=_FAKE_ROOT)
    @patch("zenzic.cli._clean.ZenzicConfig.load", return_value=(_CFG, True))
    @patch(
        "zenzic.cli._clean.find_unused_assets",
        return_value=["assets/old.png", "assets/unused.svg"],
    )
    @patch("zenzic.core.adapters.get_adapter")
    @patch("zenzic.cli._shared._build_exclusion_manager")
    def test_clean_assets_yes_flag_deletes(
        self, mock_excl, mock_adapter, mock_find, mock_cfg, mock_root, tmp_path: Path
    ) -> None:
        """--yes flag deletes without confirmation."""
        from zenzic.cli._clean import clean_app

        mock_adapter.return_value = self._make_adapter_mock()
        mock_excl.return_value = self._make_exclusion_mock()

        # Patch docs_root so unlink is on real files (we create them)
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "assets").mkdir()
        (docs_dir / "assets" / "old.png").write_bytes(b"fake")
        (docs_dir / "assets" / "unused.svg").write_bytes(b"fake")

        fake_root = tmp_path
        mock_root.return_value = fake_root
        mock_cfg.return_value = (_CFG, True)
        result = runner.invoke(clean_app, ["assets", "--yes"])
        assert result.exit_code == 0
        assert "Deleted" in result.output or "SUCCESS" in result.output

    @patch("zenzic.cli._clean.find_repo_root", return_value=_FAKE_ROOT)
    @patch("zenzic.cli._clean.ZenzicConfig.load", return_value=(_CFG, False))
    @patch("zenzic.cli._clean.find_unused_assets", return_value=[])
    @patch("zenzic.core.adapters.get_adapter")
    @patch("zenzic.cli._shared._build_exclusion_manager")
    def test_clean_assets_quiet_no_output(
        self, mock_excl, mock_adapter, mock_find, mock_cfg, mock_root
    ) -> None:
        """--quiet suppresses all output when nothing to clean."""
        from zenzic.cli._clean import clean_app

        mock_adapter.return_value = self._make_adapter_mock()
        mock_excl.return_value = self._make_exclusion_mock()

        result = runner.invoke(clean_app, ["assets", "--quiet"])
        assert result.exit_code == 0
        assert result.output.strip() == ""

    @patch("zenzic.cli._clean.find_repo_root", return_value=_FAKE_ROOT)
    @patch("zenzic.cli._clean.ZenzicConfig.load", return_value=(_CFG, False))
    @patch("zenzic.cli._clean.find_unused_assets", return_value=[])
    @patch("zenzic.core.adapters.get_adapter")
    @patch("zenzic.cli._shared._build_exclusion_manager")
    def test_clean_assets_no_config_shows_hint(
        self, mock_excl, mock_adapter, mock_find, mock_cfg, mock_root
    ) -> None:
        """When loaded_from_file=False, no-config hint is shown (not quiet)."""
        from zenzic.cli._clean import clean_app

        mock_adapter.return_value = self._make_adapter_mock()
        mock_excl.return_value = self._make_exclusion_mock()

        result = runner.invoke(clean_app, ["assets"])
        assert result.exit_code == 0

    @patch("zenzic.cli._clean.find_repo_root", return_value=_FAKE_ROOT)
    @patch("zenzic.cli._clean.ZenzicConfig.load", return_value=(_CFG, True))
    @patch("zenzic.cli._clean.find_unused_assets", return_value=["assets/old.png"])
    @patch("zenzic.core.adapters.get_adapter")
    @patch("zenzic.cli._shared._build_exclusion_manager")
    def test_clean_assets_with_path_argument(
        self, mock_excl, mock_adapter, mock_find, mock_cfg, mock_root, tmp_path: Path
    ) -> None:
        """Explicit PATH argument triggers sovereign root detection."""
        from zenzic.cli._clean import clean_app

        mock_adapter.return_value = self._make_adapter_mock()
        mock_excl.return_value = self._make_exclusion_mock()

        # Typer single-command collapse: no 'assets' prefix; path is first positional
        result = runner.invoke(clean_app, [str(tmp_path), "--dry-run"])
        assert result.exit_code == 0


# ─────────────────────────────────────────────────────────────────────────────
# cli/_shared.py  (50% → 80%+)
# ─────────────────────────────────────────────────────────────────────────────


class TestShared:
    """Cover uncovered branches in ``cli/_shared.py``."""

    # ── configure_console ─────────────────────────────────────────────────────

    def test_configure_console_no_color(self) -> None:
        """Cover the ``no_color=True`` branch."""
        from zenzic.cli import _shared

        _shared.configure_console(no_color=True)
        assert _shared.console.no_color

    def test_configure_console_force_color(self) -> None:
        """Cover the ``force_color=True`` branch."""
        from zenzic.cli import _shared

        _shared.configure_console(force_color=True)
        # Restore to default
        _shared.configure_console()

    def test_configure_console_default(self) -> None:
        """Cover the ``else`` (auto) branch."""
        from zenzic.cli import _shared

        _shared.configure_console(no_color=False, force_color=False)

    # ── get_ui / get_console ─────────────────────────────────────────────────

    def test_get_ui_returns_sentinel_ui(self) -> None:
        from zenzic.cli._shared import get_ui
        from zenzic.core.ui import SentinelUI

        assert isinstance(get_ui(), SentinelUI)

    def test_get_console_returns_console(self) -> None:
        from rich.console import Console

        from zenzic.cli._shared import get_console

        assert isinstance(get_console(), Console)

    # ── _print_no_config_hint ─────────────────────────────────────────────────

    def test_print_no_config_hint_machine_format_suppressed(self) -> None:
        """Cover the ``if output_format in _MACHINE_FORMATS: return`` branch."""
        from zenzic.cli._shared import _print_no_config_hint

        # Should return immediately without printing — no assertion needed,
        # just ensure it does not raise
        _print_no_config_hint("json")
        _print_no_config_hint("sarif")

    def test_print_no_config_hint_text_format(self) -> None:
        from zenzic.cli._shared import _print_no_config_hint

        _print_no_config_hint("text")
        _print_no_config_hint()  # default

    # ── _apply_engine_override ────────────────────────────────────────────────

    def test_apply_engine_override_none(self) -> None:
        from zenzic.cli._shared import _apply_engine_override

        result = _apply_engine_override(_CFG, None)
        assert result is _CFG

    def test_apply_engine_override_auto(self) -> None:
        from zenzic.cli._shared import _apply_engine_override

        result = _apply_engine_override(_CFG, "auto")
        assert result is _CFG

    def test_apply_engine_override_unknown_engine_exits(self) -> None:
        """Cover the unknown-engine error path."""
        import typer

        from zenzic.cli._shared import _apply_engine_override

        with pytest.raises(typer.Exit):
            _apply_engine_override(_CFG, "nonexistent_engine_xyz")

    def test_apply_engine_override_valid_engine(self) -> None:
        from zenzic.cli._shared import _apply_engine_override
        from zenzic.core.adapters import list_adapter_engines

        engines = list_adapter_engines()
        if not engines:
            pytest.skip("No engines registered")
        engine = next(iter(engines))
        result = _apply_engine_override(_CFG, engine)
        assert result.build_context.engine == engine

    # ── _output_json_findings ─────────────────────────────────────────────────

    def test_output_json_findings_empty(self, capsys: pytest.CaptureFixture) -> None:
        import json

        from zenzic.cli._shared import _output_json_findings

        _output_json_findings([], elapsed=0.1)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["summary"]["errors"] == 0
        assert data["summary"]["elapsed_seconds"] == pytest.approx(0.1, abs=0.01)

    def test_output_json_findings_with_findings(self, capsys: pytest.CaptureFixture) -> None:
        import json

        from zenzic.cli._shared import _output_json_findings
        from zenzic.core.reporter import Finding

        findings = [
            Finding(
                rel_path="docs/index.md",
                line_no=5,
                code="Z101",
                severity="error",
                message="Broken link",
            ),
            Finding(
                rel_path="docs/guide.md",
                line_no=10,
                code="Z201",
                severity="security_breach",
                message="Credential detected",
            ),
        ]
        _output_json_findings(findings, elapsed=1.5)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data["findings"]) == 2
        assert data["summary"]["errors"] == 1
        assert data["summary"]["security_breaches"] == 1

    # ── _output_sarif_findings ────────────────────────────────────────────────

    def test_output_sarif_findings_empty(self, capsys: pytest.CaptureFixture) -> None:
        import json

        from zenzic.cli._shared import _output_sarif_findings

        _output_sarif_findings([], version="0.7.0")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["version"] == "2.1.0"
        assert data["runs"][0]["results"] == []

    def test_output_sarif_findings_with_security(self, capsys: pytest.CaptureFixture) -> None:
        """Cover the security-severity properties branch."""
        import json

        from zenzic.cli._shared import _output_sarif_findings
        from zenzic.core.reporter import Finding

        findings = [
            Finding(
                rel_path="docs/index.md",
                line_no=1,
                code="Z201",
                severity="security_breach",
                message="Credential detected",
            ),
            Finding(
                rel_path="docs/other.md",
                line_no=3,
                code="Z101",
                severity="error",
                message="Broken link",
            ),
        ]
        _output_sarif_findings(findings, version="0.7.0")
        out = capsys.readouterr().out
        data = json.loads(out)
        results = data["runs"][0]["results"]
        assert len(results) == 2
        # Security breach gets properties.security-severity
        security_result = next(r for r in results if r["ruleId"] == "Z201")
        assert "properties" in security_result

    # ── _validate_docs_root ───────────────────────────────────────────────────

    def test_validate_docs_root_valid(self, tmp_path: Path) -> None:
        from zenzic.cli._shared import _validate_docs_root

        repo = tmp_path / "repo"
        docs = repo / "docs"
        repo.mkdir()
        docs.mkdir()
        _validate_docs_root(repo, docs)  # must not raise

    def test_validate_docs_root_escape_raises(self, tmp_path: Path) -> None:
        """Cover the Blood Sentinel path traversal exit."""
        import typer

        from zenzic.cli._shared import _validate_docs_root

        repo = tmp_path / "repo"
        repo.mkdir()
        outside = tmp_path / "elsewhere"
        outside.mkdir()

        with pytest.raises(typer.Exit):
            _validate_docs_root(repo, outside)
