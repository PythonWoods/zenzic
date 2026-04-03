---
template: home.html
hide:
  - navigation
  - toc
  - path
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD041 MD036 -->

<div class="zz-hero" markdown>

![Zenzic](assets/brand/svg/zenzic-wordmark.svg#only-light){ .zz-hero__logo }
![Zenzic](assets/brand/svg/zenzic-wordmark-dark.svg#only-dark){ .zz-hero__logo }

Linter di documentazione ad alte prestazioni per qualsiasi progetto Markdown.
Intercetta link non validi, pagine orfane e credenziali esposte — prima dei tuoi utenti.
{: .zz-hero__tagline }

[Inizia](guide/index.md){ .md-button .md-button--primary }
[Vedi su GitHub](https://github.com/PythonWoods/zenzic){ .md-button }
{: .zz-hero__actions }

</div>

<div class="zz-hero__screenshot-wrap" markdown>

![Output terminale Zenzic con sei controlli superati](assets/screenshots/screenshot.svg){ .zz-hero__screenshot }

</div>

---

<div class="grid cards zz-features" markdown>

- :lucide-link-2-off: &nbsp; __Link non validi__

    ---

    Rileva link interni morti, ancore mancanti e URL esterni irraggiungibili — a livello sorgente, prima della build.

    ```bash
    zenzic check links
    ```

- :lucide-file: &nbsp; __Pagine orfane__

    ---

    Trova file `.md` presenti su disco ma assenti dalla navigazione del sito. Invisibili ai lettori.

    ```bash
    zenzic check orphans
    ```

- :lucide-code: &nbsp; __Snippet non validi__

    ---

    Compila ogni blocco Python con `compile()`. Intercetta gli errori di sintassi prima che i lettori copino codice non funzionante.

    ```bash
    zenzic check snippets
    ```

- :lucide-pencil: &nbsp; __Stub placeholder__

    ---

    Segnala pagine sotto la soglia di parole o con pattern come `TODO`, `WIP`, `coming soon`.

    ```bash
    zenzic check placeholders
    ```

- :lucide-image: &nbsp; __Asset non utilizzati__

    ---

    Segnala immagini e file presenti in `docs/` ma mai referenziati da nessuna pagina.

    ```bash
    zenzic check assets
    ```

- :lucide-shield-check: &nbsp; __Zenzic Shield__

    ---

    Scansiona ogni URL di riferimento alla ricerca di credenziali esposte — API key, token, chiavi AWS. Esce con codice `2` immediatamente.

    ```bash
    zenzic check references
    ```

</div>

---

<div class="zz-sentinel-section" markdown>

## Sentinel in Azione

Ogni segnalazione è ancorata a file, riga e sorgente. Output strutturato per occhi umani e parsing automatico.

<div class="grid cards" markdown>

- :lucide-terminal: &nbsp; __Reporter con gutter__

    ---

    Ogni errore mostra la riga sorgente esatta con contesto gutter. Nessun log da scorrere per trovare il problema.

    ```text
    docs/guida.md
      ✘ 16:    [FILE_NOT_FOUND]  'setup.md' not found in docs
        │
     16 │ Leggi la [guida di setup](setup.md) prima di continuare.
        │
    ```

- :lucide-shield: &nbsp; __Zenzic Shield__

    ---

    Scansiona ogni riga — compresi i blocchi `bash` e `yaml` — alla ricerca di credenziali esposte. Exit code `2` è riservato esclusivamente agli eventi di sicurezza.

    ```text
    docs/tutorial.md
      ✘ 42:    [CREDENTIAL_LEAK]  Token GitHub rilevato
        │
     42 │ Authorization: Bearer ghp_example123token
        │
    ```

- :lucide-chart-bar: &nbsp; __Punteggio qualità__

    ---

    `zenzic score` emette un singolo __intero deterministico 0–100__. Salva un baseline e blocca le pull request sulle regressioni.

    ```bash
    zenzic score --save          # salva il baseline
    zenzic diff --threshold 5   # exit 1 se il punteggio scende > 5
    ```

</div>

</div>

---

<div class="zz-score-section" markdown>

## Punteggio qualità

`zenzic score` aggrega tutti e sei i controlli in un singolo __intero 0–100__ ponderato per gravità. Deterministico — traccialo in CI, confrontalo tra branch, blocca le regressioni.

```bash
zenzic score --save
zenzic diff --threshold 5
```

</div>

---

<div class="zz-trust-section" markdown>

Apache-2.0 &nbsp;·&nbsp; Python 3.11+ &nbsp;·&nbsp; zero dipendenze runtime

</div>
