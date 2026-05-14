<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Release Procedure — Zenzic Core

## Release Metadata

| Field    | Value      |
| :------- | :--------- |
| Version  | v0.7.1     |
| Codename | Basalt<!-- zenzic-ignore: Z601 - release codename -->     |
| Date     | 2026-05-14 |
| Status   | Stable     |

## Release Checklist

Before tagging, every item must be green:

- [ ] `just verify` — exits 0 (pre-commit hooks → pytest → `zenzic check all --strict`)
- [ ] `zenzic check all .` — zero findings in the repo root
- [ ] `pyproject.toml` version matches the tag (`0.7.1`)
- [ ] `CITATION.cff` version and date updated
- [ ] `CHANGELOG.md` — `[Unreleased]` section moved to the new version heading
- [ ] Bilingual sync verified — `Z602 I18N_PARITY` clean on `zenzic-doc`
- [ ] `zenzic-doc` and `zenzic-action` RELEASE.md updated to match this version

## Build & Distribute

```bash
# Bump version
uv run bump-my-version bump minor

# Build wheel + sdist
python -m build

# Publish to PyPI
uv publish
```

Distribution target: **PyPI** — `pip install zenzic` / `uvx zenzic`.

## Tag & Push

```bash
git tag v0.7.1
git push origin release/v0.7.1 --tags
```

Create a GitHub Release from the tag. Copy the `## v0.7.1` section from
`CHANGELOG.md` as the release body.

## Changelog Reference

For a detailed list of changes, see [CHANGELOG.md](./CHANGELOG.md).
For full history, see [Historical Archives](./changelogs/README.md).
