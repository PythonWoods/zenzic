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

![Zenzic Sentinel — output completo con punteggio qualità](assets/screenshots/screenshot.svg){ .zz-hero__screenshot }

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

<div class="zz-sentinel-section">
<h2 id="sentinel-in-azione">Sentinel in Azione</h2>
<p>Ogni segnalazione è ancorata a file, riga e sorgente. Output strutturato per occhi umani e parsing automatico.</p>
<div class="grid cards">
<ul>
<li>
<p><span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19h8"/><path d="m4 17 6-6-6-6"/></svg></span> &nbsp; <strong>Reporter con gutter</strong></p>
<hr>
<p>Ogni errore mostra la riga sorgente esatta con contesto gutter. Nessun log da scorrere per trovare il problema.</p>
<div class="zz-sentinel-demo" aria-hidden="true">
<div class="zz-sentinel-demo__rule">docs/guida.md</div>
<div class="zz-sentinel-demo__finding">
<span class="zz-sentinel-demo__icon zz-sentinel-demo__icon--error">✘</span>
<span class="zz-sentinel-demo__badge">FILE_NOT_FOUND</span>
<span class="zz-sentinel-demo__message">'intro.md' non raggiungibile dalla nav</span>
</div>
<div class="zz-sentinel-demo__snippet zz-sentinel-demo__snippet--dim"><span class="zz-sentinel-demo__line-no">15</span><span class="zz-sentinel-demo__gutter">│</span><span>prima di continuare.</span></div>
<div class="zz-sentinel-demo__snippet"><span class="zz-sentinel-demo__line-no">16</span><span class="zz-sentinel-demo__gutter zz-sentinel-demo__gutter--active">❱</span><span>Vedi la guida introduttiva per i dettagli.</span></div>
<div class="zz-sentinel-demo__snippet zz-sentinel-demo__snippet--dim"><span class="zz-sentinel-demo__line-no">17</span><span class="zz-sentinel-demo__gutter">│</span><span>Poi configura l'ambiente.</span></div>
</div>
</li>
<li>
<p><span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg></span> &nbsp; <strong>Zenzic Shield</strong></p>
<hr>
<p>Scansiona ogni riga — compresi i blocchi <code>bash</code> e <code>yaml</code> — alla ricerca di credenziali esposte. Exit code <code>2</code> è riservato esclusivamente agli eventi di sicurezza.</p>
<div class="zz-sentinel-demo" aria-hidden="true">
<div class="zz-sentinel-demo__rule">docs/tutorial.md</div>
<div class="zz-sentinel-demo__finding">
<span class="zz-sentinel-demo__icon zz-sentinel-demo__icon--error">✘</span>
<span class="zz-sentinel-demo__badge zz-sentinel-demo__badge--breach">CREDENTIAL_LEAK</span>
<span class="zz-sentinel-demo__message">Token GitHub rilevato</span>
</div>
<div class="zz-sentinel-demo__snippet zz-sentinel-demo__snippet--dim"><span class="zz-sentinel-demo__line-no">41</span><span class="zz-sentinel-demo__gutter">│</span><span>Imposta l'header Authorization:</span></div>
<div class="zz-sentinel-demo__snippet"><span class="zz-sentinel-demo__line-no">42</span><span class="zz-sentinel-demo__gutter zz-sentinel-demo__gutter--active">❱</span><span>Bearer ghp_example123token</span></div>
<div class="zz-sentinel-demo__snippet zz-sentinel-demo__snippet--dim"><span class="zz-sentinel-demo__line-no">43</span><span class="zz-sentinel-demo__gutter">│</span><span>in ogni richiesta API.</span></div>
</div>
</li>
<li>
<p><span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2h-4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8"/><path d="M16.706 2.706A2.4 2.4 0 0 0 15 2v5a1 1 0 0 0 1 1h5a2.4 2.4 0 0 0-.706-1.706z"/><path d="M5 7a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h8a2 2 0 0 0 1.732-1"/></svg></span> &nbsp; <strong>Raggruppato per file</strong></p>
<hr>
<p>I finding sono raggruppati sotto un header di file, invece di scorrere come log piatti. Vedi dove vive il problema prima ancora di leggere il dettaglio.</p>
<div class="zz-sentinel-demo" aria-hidden="true">
<div class="zz-sentinel-demo__rule">docs/guida.md</div>
<div class="zz-sentinel-demo__finding">
<span class="zz-sentinel-demo__icon zz-sentinel-demo__icon--error">✘</span>
<span class="zz-sentinel-demo__badge">FILE_NOT_FOUND</span>
<span class="zz-sentinel-demo__message">'intro.md' non raggiungibile dalla nav</span>
</div>
<div class="zz-sentinel-demo__finding">
<span class="zz-sentinel-demo__icon zz-sentinel-demo__icon--warning">⚠</span>
<span class="zz-sentinel-demo__badge zz-sentinel-demo__badge--warning">ZZ-NODRAFT</span>
<span class="zz-sentinel-demo__message">Rimuovi i marker DRAFT prima della pubblicazione.</span>
</div>
</div>
</li>
<li>
<p><span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h.01"/><path d="M3 12h.01"/><path d="M3 19h.01"/><path d="M8 5h13"/><path d="M8 12h13"/><path d="M8 19h13"/></svg></span> &nbsp; <strong>Riepilogo severità</strong></p>
<hr>
<p>Ogni esecuzione termina con un riepilogo compatto: conteggi per severità, numero di file coinvolti e verdetto finale. Capisci subito se il controllo è fallito davvero o se ha emesso solo warning.</p>
<p><em>Nota: l'output CLI di Zenzic resta volutamente in inglese, anche nella documentazione italiana, per mantenere log, CI e screenshot coerenti tra tutti gli ambienti.</em></p>
<div class="zz-sentinel-demo" aria-hidden="true">
<div class="zz-sentinel-demo__summary-row">
<span class="zz-sentinel-demo__count zz-sentinel-demo__count--error">✘ 2 errors</span>
<span class="zz-sentinel-demo__count zz-sentinel-demo__count--warning">⚠ 1 warning</span>
<span class="zz-sentinel-demo__count zz-sentinel-demo__count--muted">• 1 file with findings</span>
</div>
<div class="zz-sentinel-demo__verdict zz-sentinel-demo__verdict--failed">FAILED: One or more checks failed.</div>
</div>
</li>
</ul>
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
