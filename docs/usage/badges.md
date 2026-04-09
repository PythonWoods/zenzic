---
icon: lucide/award
---

# Official Badges & CI/CD Integration {#official-badges}

Zenzic provides two official badge types. Add them to your project's `README.md` to signal documentation integrity to contributors and users.

---

## 🛡️ Zenzic Shield (Binary Status)

![Zenzic Shield badge](../assets/brand/svg/zenzic-badge-shield.svg)

Use this badge for strict pipelines where any broken link, dead anchor, or leaked credential must block the build. It is a binary gate: **passing** or **failing**.

### Copy-paste Markdown

**Passing (green):**

```markdown
[![Zenzic Shield](https://img.shields.io/badge/🛡️_zenzic_shield-passing-4f46e5?style=flat)](https://github.com/PythonWoods/zenzic)
```

**Failing (red):**

```markdown
[![Zenzic Shield](https://img.shields.io/badge/🛡️_zenzic_shield-failing-ef4444?style=flat)](https://github.com/PythonWoods/zenzic)
```

### Recommended CI step

```yaml
- name: Lint documentation (Zenzic Shield)
  run: uvx zenzic check all --strict
```

Place the `passing` URL in your README. If this step fails in CI, manually swap the badge to `failing` — or automate it via [dynamic-badges-action](https://github.com/Schneegans/dynamic-badges-action) (see [CI/CD Integration](../ci-cd.md)).

---

## 💯 Zenzic Score (Improvement Metric)

![Zenzic Score badge](../assets/brand/svg/zenzic-badge-score.svg)

Use this badge to expose the live quality score (0–100) of your documentation. Ideal for legacy projects adopting Zenzic progressively: a green build can still show a non-perfect score, encouraging continuous improvement without blocking the workflow.

### Copy-paste Markdown

```markdown
[![Zenzic Score](https://img.shields.io/badge/🛡️_zenzic-100%2F100-4f46e5?style=flat)](https://github.com/PythonWoods/zenzic)
```

### Using `--fail-under` for progressive adoption

```bash
# Green CI at 72/100 — build passes, score is visible
zenzic score --fail-under=70

# Red CI at 72/100 — floor not met
zenzic score --fail-under=80
```

The `--fail-under` flag decouples the exit code from the score value. Teams can start at a realistic floor (e.g. 60) and raise it sprint by sprint.

---

## 📊 Live Score Badge via JSON

`zenzic score --save` writes `.zenzic-score.json` at the repo root:

```text
{"project": "zenzic", "score": 100, "threshold": 0, "status": "success", "timestamp": "...", "categories": [...]}
```

This file is the machine-readable bridge to dynamic Shields.io badges.

### Automate with GitHub Actions

The following two steps save the score and push it to a [GitHub Gist](https://gist.github.com) that Shields.io reads on every request:

```yaml
- name: Compute Zenzic Score
  run: |
    uvx zenzic score --save
    echo "SCORE=$(uvx zenzic score --format json | python3 -c \
      'import sys,json; print(json.load(sys.stdin)["score"])')" >> "$GITHUB_ENV"

- name: Update Score Badge
  uses: Schneegans/dynamic-badges-action@v1.7.0
  with:
    auth: ${{ secrets.GIST_SECRET }}
    gistID: <your-gist-id>
    filename: zenzic-score.json
    label: "🛡️ zenzic"
    message: "${{ env.SCORE }} / 100"
    color: ${{ env.SCORE == '100' && '4f46e5' || env.SCORE >= '80' && 'f59e0b' || 'ef4444' }}
```

Then reference the dynamic endpoint in your README:

```markdown
[![Zenzic Score](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/<user>/<gist-id>/raw/zenzic-score.json)](https://github.com/PythonWoods/zenzic)
```

**Setup:** create a Gist, generate a Personal Access Token with `gist` scope, save it as `GIST_SECRET` in your repo secrets, and replace `<your-gist-id>`. See [CI/CD Integration](../ci-cd.md) for the complete workflow.

---

## 🎨 Offline / Enterprise Badges

Projects in air-gapped or enterprise environments that cannot call `img.shields.io` can embed the official static SVG assets from the Brand Kit directly:

| File | Description |
|---|---|
| `zenzic-badge-shield.svg` | Static "passing" shield badge |
| `zenzic-badge-score.svg` | Static "100 / 100" score badge |

**Note:** `brand-kit.zip` is a build artifact. It is not stored in the repository — download it
from the [GitHub Releases](https://github.com/PythonWoods/zenzic/releases/latest) page, or
generate it locally with `nox -s preflight`.
