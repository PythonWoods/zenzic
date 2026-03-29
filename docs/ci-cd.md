---
icon: lucide/workflow
---

# CI/CD Integration

Zenzic is automation-ready out of the box. The `--format json` flag and `--save` option expose machine-readable output that any CI/CD system can consume to drive dynamic badges, quality gates, and regression detection.

---

## JSON Output

Every check command supports `--format json`:

```bash
# Machine-readable report for all checks
zenzic check all --format json

# Machine-readable score with full per-check breakdown
zenzic score --format json
```

### `zenzic check all --format json`

```json
{
  "status": "passed",
  "exit_code": 0,
  "checks": {
    "links":        {"status": "passed", "errors": 0},
    "orphans":      {"status": "passed", "errors": 0},
    "snippets":     {"status": "passed", "errors": 0},
    "placeholders": {"status": "passed", "errors": 0},
    "assets":       {"status": "passed", "errors": 0}
  }
}
```

### `zenzic score --format json`

```json
{
  "project": "zenzic",
  "score": 100,
  "threshold": 0,
  "status": "success",
  "timestamp": "2026-03-24T12:00:00+00:00",
  "categories": [
    {"name": "links",        "weight": 0.35, "issues": 0, "category_score": 1.0, "contribution": 0.35},
    {"name": "orphans",      "weight": 0.20, "issues": 0, "category_score": 1.0, "contribution": 0.20},
    {"name": "snippets",     "weight": 0.20, "issues": 0, "category_score": 1.0, "contribution": 0.20},
    {"name": "placeholders", "weight": 0.15, "issues": 0, "category_score": 1.0, "contribution": 0.15},
    {"name": "assets",       "weight": 0.10, "issues": 0, "category_score": 1.0, "contribution": 0.10}
  ]
}
```

---

## GitHub Actions: Zenzic Shield Gate

The simplest integration — fails the build on any documentation error.

=== "uvx (zero-setup)"

    No Python setup required. `uvx` fetches and runs Zenzic in a throwaway
    environment on every run. Ideal for documentation-only repositories or
    teams that do not otherwise need a Python environment in their CI:

    ```yaml
    # .github/workflows/docs.yml
    name: Documentation Quality

    on:
      push:
        branches: [main]
        paths: ['docs/**', 'mkdocs.yml']

    jobs:
      zenzic:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6

          - name: Lint documentation
            run: uvx zenzic check all --strict

          - name: Check references and run Shield
            run: uvx zenzic check references
    ```

=== "astral-sh/setup-uv (pinned version)"

    Use [`astral-sh/setup-uv`](https://github.com/astral-sh/setup-uv) when you need a pinned Zenzic version,
    faster installs on repeated runs (cached wheel), or when your project
    already uses uv for dependency management:

    ```yaml
    # .github/workflows/docs.yml
    name: Documentation Quality

    on:
      push:
        branches: [main]
        paths: ['docs/**', 'mkdocs.yml']

    jobs:
      zenzic:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6

          - name: Set up uv
            uses: astral-sh/setup-uv@v6
            with:
              enable-cache: true

          - name: Lint documentation
            run: uvx zenzic check all --strict

          - name: Check references and run Shield
            run: uvx zenzic check references
    ```

    The `enable-cache: true` option caches the uv tool cache across runs,
    eliminating the PyPI download on every push.

Exit code `2` means a credential was detected in a reference URL. Rotate it immediately.

---

## GitHub Actions: Dynamic Score Badge

This workflow reads the `.zenzic-score.json` snapshot and pushes the live score to a [Shields.io endpoint](https://shields.io/badges/dynamic-json-badge) via a GitHub Gist, keeping your badge current on every push.

```yaml
# .github/workflows/zenzic-badge.yml
name: Zenzic Score Badge

on:
  push:
    branches: [main]

jobs:
  score:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: 🛡️ Run Zenzic Score
        id: zenzic_step
        run: |
          uvx zenzic score --save   # threshold read from fail_under in zenzic.toml
          SCORE=$(jq '.score' .zenzic-score.json)
          echo "SCORE=$SCORE" >> "$GITHUB_OUTPUT"

      - name: 🔄 Update Gist for Badge
        uses: Schneegans/dynamic-badges-action@v1.7.0
        with:
          auth: ${{ secrets.GIST_SECRET }}
          gistID: ${{ secrets.ZENZIC_GIST_ID }}
          filename: zenzic-score.json
          label: "🛡️ zenzic score"
          message: "${{ steps.zenzic_step.outputs.SCORE }}/100"
          valColorRange: ${{ steps.zenzic_step.outputs.SCORE }}
          maxColorRange: 100
          minColorRange: 0
```

**Setup steps:**

1. Create a [GitHub Gist](https://gist.github.com) (public or secret).
2. Create a [Personal Access Token](https://github.com/settings/tokens) with `gist` scope and store it as `GIST_SECRET` in your repo secrets.
3. Store your Gist's ID (the long hex in the URL) as `ZENZIC_GIST_ID` in your repo secrets.
4. Add the dynamic badge URL to your `README.md`:

```markdown
[![Zenzic Score](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/<user>/<gist-id>/raw/zenzic-score.json)](https://github.com/PythonWoods/zenzic)
```

> **Note:** `valColorRange` / `maxColorRange` / `minColorRange` produce a smooth green→yellow→red gradient based on the score value. `jq` is pre-installed on all GitHub-hosted runners.

---

## Regression Detection

`zenzic diff` compares the current score against the saved `.zenzic-score.json` baseline:

```yaml
- name: Detect score regression
  run: |
    uvx zenzic score --save      # update snapshot
    uvx zenzic diff --threshold 5  # fail if score drops > 5 points
```

Combine with branch protection rules to block merges that degrade documentation quality.

---

## Exit Codes Reference

| Code | Meaning | Badge action |
|:---:|---|---|
| `0` | All checks passed | Keep badge green |
| `1` | One or more checks failed | Set badge to `failing` / `ef4444` |
| **`2`** | **Zenzic Shield: credential detected** | **Rotate credential immediately** |

> For the full badge copy-paste reference, see [Official Badges](usage/badges.md).
