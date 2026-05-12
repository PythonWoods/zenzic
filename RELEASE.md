<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Release Procedure — Zenzic Core

## Release Metadata

| Field    | Value      |
| :------- | :--------- |
| Version  | v0.8.0     |
| Codename | Basalt     |
| Date     | 2026-05-12 |
| Status   | Stable     |

## Release Checklist

Before tagging, every item must be green:

- [ ] `just verify` — exits 0 (pre-commit hooks → pytest → `zenzic check all --strict`)
- [ ] `zenzic check .` — zero findings in the repo root
- [ ] `pyproject.toml` version matches the tag (`0.8.0`)
- [ ] `CITATION.cff` version and date updated
- [ ] `CHANGELOG.md` — `[Unreleased]` section moved to the new version heading
- [ ] Bilingual sync verified — `Z907 I18N_PARITY` clean on `zenzic-doc`
- [ ] `zenzic-doc` and `zenzic-action` RELEASE.md updated to match this version

## Build & Distribute

```bash
# Bump version
uv run bump-my-version bump minor   # or patch / major

# Build wheel + sdist
python -m build

# Publish to PyPI
uv publish
```

Distribution target: **PyPI** — `pip install zenzic` / `uvx zenzic`.

## Tag & Push

```bash
git tag v0.8.0
git push origin release/v0.8.0 --tags
```

Create a GitHub Release from the tag. Copy the `## v0.8.0` section from
`CHANGELOG.md` as the release body.

## Changelog Reference

For a detailed list of changes, see [CHANGELOG.md](./CHANGELOG.md).
Full history: [CHANGELOG.archive.md](./CHANGELOG.archive.md).
