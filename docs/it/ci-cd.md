---
icon: lucide/workflow
---

# Integrazione CI/CD

Zenzic è pronto all'automazione. Il flag `--format json` e l'opzione `--save` espongono output machine-readable che qualsiasi sistema CI/CD può consumare per pilotare badge dinamici, quality gate e rilevamento delle regressioni.

---

## Output JSON

Ogni comando di controllo supporta `--format json`:

```bash
# Report machine-readable per tutti i controlli
zenzic check all --format json

# Punteggio machine-readable con dettaglio per controllo
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
    {"name": "placeholders", "weight": 0.15, "issues": 0, "category_score": 1.0, "contribution": 0.10}
  ]
}
```

---

## GitHub Actions: Gate Zenzic Shield

L'integrazione più semplice — blocca la build a qualsiasi errore di documentazione.

=== "uvx (zero-setup)"

    Nessun setup Python richiesto. `uvx` scarica ed esegue Zenzic in un
    ambiente temporaneo ad ogni esecuzione. Ideale per repository
    documentazione-only o team che non hanno altrimenti bisogno di Python in CI:

    ```yaml
    # .github/workflows/docs.yml
    name: Qualità Documentazione

    on:
      push:
        branches: [main]
        paths: ['docs/**', 'mkdocs.yml']

    jobs:
      zenzic:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6

          - name: Lint documentazione
            run: uvx --pre zenzic check all --strict

          - name: Controllo riferimenti e Shield
            run: uvx --pre zenzic check references
    ```

=== "astral-sh/setup-uv (versione fissata)"

    Usa [`astral-sh/setup-uv`](https://github.com/astral-sh/setup-uv) quando hai bisogno di una versione
    Zenzic fissata, installazioni più veloci (cache wheel), o quando il progetto
    usa già uv per la gestione delle dipendenze:

    ```yaml
    # .github/workflows/docs.yml
    name: Qualità Documentazione

    on:
      push:
        branches: [main]
        paths: ['docs/**', 'mkdocs.yml']

    jobs:
      zenzic:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6

          - name: Setup uv
            uses: astral-sh/setup-uv@v6
            with:
              enable-cache: true

          - name: Lint documentazione
            run: uvx --pre zenzic check all --strict

          - name: Controllo riferimenti e Shield
            run: uvx --pre zenzic check references
    ```

    L'opzione `enable-cache: true` mantiene la cache degli strumenti uv tra
    le esecuzioni, eliminando il download da PyPI ad ogni push.

L'exit code `2` indica che una credenziale è stata rilevata in un URL di riferimento. Ruotala immediatamente.

---

## GitHub Actions: Badge Score Dinamico

Questo workflow legge lo snapshot `.zenzic-score.json` e pubblica il punteggio live su un [endpoint Shields.io](https://shields.io/badges/dynamic-json-badge) tramite GitHub Gist, mantenendo il badge aggiornato ad ogni push.

```yaml
# .github/workflows/zenzic-badge.yml
name: Badge Zenzic Score

on:
  push:
    branches: [main]

jobs:
  score:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: 🛡️ Calcola Zenzic Score
        id: zenzic_step
        run: |
          uvx --pre zenzic score --save   # soglia letta da fail_under in zenzic.toml
          SCORE=$(jq '.score' .zenzic-score.json)
          echo "SCORE=$SCORE" >> "$GITHUB_OUTPUT"

      - name: 🔄 Aggiorna Gist per Badge
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

**Passi di configurazione:**

1. Crea un [GitHub Gist](https://gist.github.com) (pubblico o segreto).
2. Crea un [Personal Access Token](https://github.com/settings/tokens) con scope `gist` e salvalo come `GIST_SECRET` nei segreti del repository.
3. Salva l'ID del tuo Gist (l'esadecimale lungo nell'URL) come `ZENZIC_GIST_ID` nei segreti del repository.
4. Aggiungi l'URL del badge dinamico al tuo `README.md`:

```markdown
[![Zenzic Score](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/<user>/<gist-id>/raw/zenzic-score.json)](https://github.com/PythonWoods/zenzic)
```

> **Nota:** `valColorRange` / `maxColorRange` / `minColorRange` producono un gradiente verde→giallo→rosso basato sul valore del punteggio. `jq` è preinstallato su tutti i runner GitHub-hosted.

---

## Rilevamento Regressioni

`zenzic diff` confronta il punteggio corrente con il baseline `.zenzic-score.json` salvato:

```yaml
- name: Rileva regressione del punteggio
  run: |
    uvx --pre zenzic score --save         # aggiorna snapshot
    uvx --pre zenzic diff --threshold 5   # fallisce se il punteggio scende > 5 punti
```

Combina con le branch protection rules per bloccare i merge che degradano la qualità della documentazione.

---

## Codici di Uscita

| Codice | Significato | Azione badge |
|:---:|---|---|
| `0` | Tutti i controlli superati | Mantieni il badge verde |
| `1` | Uno o più controlli falliti | Imposta il badge a `failing` / `ef4444` |
| **`2`** | **Zenzic Shield: credenziale rilevata** | **Ruota la credenziale immediatamente** |

> Per il riferimento completo dei badge pronti all'uso, vedi [Badge Ufficiali](usage/badges.md).
