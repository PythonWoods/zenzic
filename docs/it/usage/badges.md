---
icon: lucide/award
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Badge Ufficiali & Integrazione CI/CD {#official-badges}

Zenzic fornisce due tipologie di badge ufficiali. Aggiungili al `README.md` del tuo progetto per segnalare l'integrità della documentazione a collaboratori e utenti.

---

## 🛡️ Zenzic Shield (Stato Binario)

![Badge Zenzic Shield](../assets/brand/svg/zenzic-badge-shield.svg)

Usa questo badge per le pipeline strict in cui qualsiasi link non funzionante, ancora morta o credenziale esposta deve bloccare la build. È un gate binario: **passing** oppure **failing**.

### Markdown pronto all'uso

**Passing (verde):**

```markdown
[![Zenzic Shield](https://img.shields.io/badge/🛡️_zenzic_shield-passing-4f46e5?style=flat)](https://github.com/PythonWoods/zenzic)
```

**Failing (rosso):**

```markdown
[![Zenzic Shield](https://img.shields.io/badge/🛡️_zenzic_shield-failing-ef4444?style=flat)](https://github.com/PythonWoods/zenzic)
```

### Step CI raccomandato

```yaml
- name: Lint documentazione (Zenzic Shield)
  run: uvx zenzic check all --strict
```

Inserisci l'URL `passing` nel tuo README. Se questo step fallisce in CI, sostituisci manualmente il badge con `failing` — oppure automatizzalo tramite [dynamic-badges-action](https://github.com/Schneegans/dynamic-badges-action) (vedi [Integrazione CI/CD](../ci-cd.md)).

---

## 💯 Zenzic Score (Metrica di Miglioramento)

![Badge Zenzic Score](../assets/brand/svg/zenzic-badge-score.svg)

Usa questo badge per esporre il punteggio di qualità live (0–100) della documentazione. Ideale per progetti legacy che adottano Zenzic progressivamente: una build verde può comunque mostrare un punteggio non perfetto, incoraggiando il miglioramento continuo senza bloccare il workflow.

### Markdown pronto all'uso

```markdown
[![Zenzic Score](https://img.shields.io/badge/🛡️_zenzic-100%2F100-4f46e5?style=flat)](https://github.com/PythonWoods/zenzic)
```

### Usare `--fail-under` per l'adozione progressiva

```bash
# CI verde a 72/100 — la build passa, il punteggio è visibile
zenzic score --fail-under=70

# CI rossa a 72/100 — soglia non raggiunta
zenzic score --fail-under=80
```

Il flag `--fail-under` disaccoppia l'exit code dal valore del punteggio. I team possono partire da una soglia realistica (es. 60) e alzarla sprint dopo sprint.

---

## 📊 Badge Score Live via JSON

`zenzic score --save` scrive `.zenzic-score.json` alla root del repository:

```text
{"project": "zenzic", "score": 100, "threshold": 0, "status": "success", "timestamp": "...", "categories": [...]}
```

Questo file è il ponte machine-readable verso i badge dinamici di Shields.io.

### Automazione con GitHub Actions

I seguenti due step calcolano il punteggio e lo pubblicano su un [GitHub Gist](https://gist.github.com) che Shields.io legge ad ogni richiesta:

```yaml
- name: Calcola Zenzic Score
  run: |
    uvx zenzic score --save
    echo "SCORE=$(uvx zenzic score --format json | python3 -c \
      'import sys,json; print(json.load(sys.stdin)["score"])')" >> "$GITHUB_ENV"

- name: Aggiorna Badge Score
  uses: Schneegans/dynamic-badges-action@v1.7.0
  with:
    auth: ${{ secrets.GIST_SECRET }}
    gistID: <il-tuo-gist-id>
    filename: zenzic-score.json
    label: "🛡️ zenzic"
    message: "${{ env.SCORE }} / 100"
    color: ${{ env.SCORE == '100' && '4f46e5' || env.SCORE >= '80' && 'f59e0b' || 'ef4444' }}
```

Poi inserisci l'endpoint dinamico nel tuo README:

```markdown
[![Zenzic Score](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/<user>/<gist-id>/raw/zenzic-score.json)](https://github.com/PythonWoods/zenzic)
```

**Configurazione:** crea un Gist, genera un Personal Access Token con scope `gist`, salvalo come `GIST_SECRET` nei segreti del repository e sostituisci `<il-tuo-gist-id>`. Vedi [Integrazione CI/CD](../ci-cd.md) per il workflow completo.

---

## 🎨 Badge Offline / Enterprise

I progetti in ambienti air-gapped o aziendali che non possono chiamare `img.shields.io` possono incorporare direttamente gli asset SVG ufficiali del Brand Kit:

| File | Descrizione |
|---|---|
| `zenzic-badge-shield.svg` | Badge shield statico "passing" |
| `zenzic-badge-score.svg` | Badge score statico "100 / 100" |

**Nota:** `brand-kit.zip` è un artefatto di build. Non è archiviato nel repository — scaricalo dalla
pagina [GitHub Releases](https://github.com/PythonWoods/zenzic/releases/latest), oppure
generalo in locale con `nox -s preflight`.
