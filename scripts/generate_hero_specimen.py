# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Generate the Hero Specimen screenshot SVG for the landing page."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from rich.console import Console

from zenzic import __version__
from zenzic.cli import _collect_all_results, _to_findings
from zenzic.core.reporter import SentinelReporter


HERO_SANDBOX = Path(__file__).parent.parent / "tests" / "sandboxes" / "hero_specimen"
OUT = Path(__file__).parent.parent / "docs" / "assets" / "screenshots" / "screenshot-hero.svg"

# helpers from generate_docs_assets
_INERT = {".css", ".js"}
_CONFIG = {".yml", ".yaml", ".toml"}


def _docs_assets_count(docs_root: Path, project_root: Path | None = None) -> tuple[int, int]:
    if not docs_root.is_dir():
        return 0, 0
    docs = sum(
        1
        for p in docs_root.rglob("*")
        if p.is_file() and (p.suffix.lower() == ".md" or p.suffix.lower() in _CONFIG)
    )
    if project_root is not None:
        docs += sum(
            1
            for p in project_root.iterdir()
            if p.is_file() and p.suffix.lower() in {".yml", ".yaml"}
        )
    assets = sum(
        1
        for p in docs_root.rglob("*")
        if p.is_file()
        and p.suffix.lower() not in _INERT
        and p.suffix.lower() not in _CONFIG
        and p.suffix.lower() != ".md"
    )
    return docs, assets


def main() -> None:
    from zenzic.models.config import ZenzicConfig
    from zenzic.ui import emoji

    console = Console(highlight=False, record=True, width=88)

    config, _ = ZenzicConfig.load(HERO_SANDBOX)
    docs_root = (HERO_SANDBOX / config.docs_dir).resolve()

    console.print(f"[dim]{emoji('arrow')}[/] [bold]zenzic check all --strict[/bold]")
    console.print()

    t0 = time.monotonic()
    results = _collect_all_results(HERO_SANDBOX, config, strict=True)
    elapsed = time.monotonic() - t0

    all_findings = _to_findings(results, docs_root)
    reporter = SentinelReporter(console, docs_root)
    docs_count, assets_count = _docs_assets_count(docs_root, HERO_SANDBOX)
    reporter.render(
        all_findings,
        version=__version__,
        elapsed=elapsed,
        docs_count=docs_count,
        assets_count=assets_count,
        engine=config.build_context.engine if hasattr(config, "build_context") else "auto",
    )

    console.save_svg(str(OUT), title="zenzic check all --strict")

    # Cleanup
    site_dir = HERO_SANDBOX / "site"
    if site_dir.exists():
        shutil.rmtree(site_dir)

    print(f"Saved → {OUT}")


if __name__ == "__main__":
    main()
