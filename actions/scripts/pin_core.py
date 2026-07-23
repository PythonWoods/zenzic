#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import difflib
import pathlib
import re
import sys
from dataclasses import dataclass

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class FileUpdate:
    path: pathlib.Path
    pattern: re.Pattern[str]
    replacement: str
    min_matches: int = 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Align Zenzic Core pin across action files."
    )
    parser.add_argument("version", help="Target core version (MAJOR.MINOR.PATCH)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print unified diffs and do not write files",
    )
    return parser.parse_args()


def replace_checked(content: str, update: FileUpdate) -> tuple[str, int]:
    new_content, count = update.pattern.subn(update.replacement, content)
    if count < update.min_matches:
        raise ValueError(
            f"{update.path}: expected at least {update.min_matches} match(es), found {count}"
        )
    return new_content, count


def diff_text(path: pathlib.Path, before: str, after: str) -> str:
    lines = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=str(path),
        tofile=str(path),
    )
    return "".join(lines)


def main() -> int:
    args = parse_args()
    version = args.version

    if not SEMVER.fullmatch(version):
        print(f"Invalid version '{version}'. Use MAJOR.MINOR.PATCH", file=sys.stderr)
        return 2

    repo_root = pathlib.Path(__file__).resolve().parent.parent

    updates = [
        FileUpdate(
            path=repo_root / "action.yml",
            pattern=re.compile(r'default: "[^\"]+"\s*# x-zenzic-core-pin.*'),
            replacement=f'default: "{version}" # x-zenzic-core-pin',
        ),
        FileUpdate(
            path=repo_root / "README.md",
            pattern=re.compile(r'(^\s{4}version: ")\d+\.\d+\.\d+("$)', re.MULTILINE),
            replacement=rf"\g<1>{version}\g<2>",
            min_matches=1,
        ),
        FileUpdate(
            path=repo_root / "README.md",
            pattern=re.compile(r"(\| `version` \| `)\d+\.\d+\.\d+(`)"),
            replacement=rf"\g<1>{version}\g<2>",
            min_matches=1,
        ),
        FileUpdate(
            path=repo_root / ".bumpversion.toml",
            pattern=re.compile(
                r'(?m)^(\[tool\.bumpversion\.custom_variables\.core_version\]\ncurrent = ")\d+\.\d+\.\d+("\s*)$'
            ),
            replacement=rf"\g<1>{version}\g<2>",
        ),
    ]

    staged: dict[pathlib.Path, tuple[str, str]] = {}
    for update in updates:
        if not update.path.exists():
            raise FileNotFoundError(f"Missing required file: {update.path}")
        before, after = staged.get(update.path, ("", ""))
        if not before:
            before = update.path.read_text(encoding="utf-8")
            after = before
        after, _count = replace_checked(after, update)
        staged[update.path] = (before, after)

    diffs: list[str] = []
    changed_files = 0
    for path, (before, after) in staged.items():
        if before == after:
            continue
        changed_files += 1
        diffs.append(diff_text(path.relative_to(repo_root), before, after))
        if not args.dry_run:
            path.write_text(after, encoding="utf-8")

    if changed_files == 0:
        print("No changes required; files are already aligned.")
        return 0

    if args.dry_run:
        sys.stdout.write("".join(diffs))
    else:
        print(f"Updated {changed_files} file(s) to core version {version}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
