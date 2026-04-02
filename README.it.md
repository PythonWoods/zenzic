<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

# 🛡️ Zenzic

<p align="center">
  <img src="docs/assets/brand/svg/zenzic-wordmark.svg#gh-light-mode-only" alt="Zenzic" width="360">
  <img src="docs/assets/brand/svg/zenzic-wordmark-dark.svg#gh-dark-mode-only" alt="Zenzic" width="360">
</p>

<p align="center">
  <a href="https://pypi.org/project/zenzic/"><img src="https://img.shields.io/pypi/v/zenzic?include_prereleases&color=38bdf8&style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/zenzic/"><img src="https://img.shields.io/pypi/pyversions/zenzic?color=10b981&style=flat-square" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-0d9488?style=flat-square" alt="Licenza"></a>
</p>

<p align="center">
  <a href="https://github.com/PythonWoods/zenzic"><img src="https://img.shields.io/badge/🛡️_zenzic_shield-passing-4f46e5?style=flat" alt="Zenzic Shield"></a>
  <a href="https://github.com/PythonWoods/zenzic"><img src="https://img.shields.io/badge/🛡️_zenzic-100%2F100-4f46e5?style=flat" alt="Zenzic Score"></a>
</p>

<p align="center">
  <strong>"Zenzic è il guardiano silenzioso della tua documentazione. Non si limita a controllare i link; audita l'integrità tecnica del tuo progetto."</strong><br>
  <em>Linter di documentazione ad alte prestazioni — autonomo, agnostico rispetto all'engine, e a prova di sicurezza.</em>
</p>

---

> La documentazione non fallisce rumorosamente. Degrada in silenzio.

Link non raggiungibili, pagine orfane, snippet di codice non validi, contenuto placeholder mai
completato e chiavi API esposte si accumulano nel tempo — finché gli utenti non li incontrano in
produzione. Zenzic rileva tutto questo nei progetti [MkDocs][mkdocs] e [Zensical][zensical] come
**CLI autonoma**, senza richiedere l'installazione di alcun framework di build.

Zenzic è **agnostico** — funziona con qualsiasi sistema di documentazione basato su Markdown
(MkDocs, Zensical, o una semplice cartella di file `.md`). Ed è **opinionated**: i link assoluti
sono un errore bloccante, e se dichiari `engine = "zensical"` devi avere `zensical.toml` — nessun
fallback, nessuna supposizione.

---

## v0.5.0a1 — La Sentinella

- **Hybrid Adaptive Engine**: `scan_docs_references` è l'unico entry point unificato per
  tutte le modalità di scansione. Il motore seleziona l'esecuzione sequenziale o parallela
  automaticamente in base alla dimensione del repository (soglia: 50 file).
- **`AdaptiveRuleEngine` con validazione pickle anticipata**: tutte le regole vengono
  validate per la serializzabilità pickle al momento della costruzione. Una regola non
  serializzabile solleva `PluginContractError` immediatamente.
- **`zenzic plugins list`**: nuovo comando che mostra ogni regola registrata nel gruppo
  entry-point `zenzic.rules` — regole Core e plugin di terze parti.
- **Supporto `pyproject.toml` (ISSUE #5)**: incorpora la configurazione Zenzic in
  `[tool.zenzic]` quando `zenzic.toml` è assente. `zenzic.toml` vince sempre se entrambi
  i file esistono.
- **Telemetria delle prestazioni**: `scan_docs_references(verbose=True)` stampa modalità
  motore, numero di worker, tempo di esecuzione e speedup stimato su stderr.
- **`PluginContractError`**: nuova eccezione per le violazioni del contratto delle regole.
- **Documentazione plugin**: `docs/developers/plugins.md` (EN + IT) — contratto completo,
  istruzioni di packaging ed esempi di registrazione `pyproject.toml`.

---

## 📖 Documentazione

- 🚀 **[Guida Utente][docs-it-home]**: Installazione, comandi CLI e tutti i controlli disponibili.
- ⚙️ **[Configurazione][docs-it-config]**: Riferimento completo di `zenzic.toml`, DSL
  `[[custom_rules]]` e sistema di adapter.
- 🔄 **[Guida alla Migrazione][docs-it-migration]**: Come usare Zenzic per validare la migrazione
  da MkDocs a Zensical.
- 🏗️ **[Architettura][docs-it-arch]**: Approfondimento sulla pipeline deterministica, il
  Two-Pass Reference Scanner e il sistema di adapter.
- 🔌 **[Scrivere un Adapter][docs-it-adapter]**: Estendi Zenzic con supporto per il tuo engine
  di documentazione.

<p align="center">
  <a href="https://zenzic.pythonwoods.dev/it/"><strong>Esplora la documentazione completa →</strong></a>
</p>

---

## Cosa controlla Zenzic

| Controllo | Comando CLI | Cosa rileva |
| --- | --- | --- |
| Links | `zenzic check links` | Link interni non raggiungibili, ancore morte, **path traversal** |
| Orfani | `zenzic check orphans` | File `.md` assenti dalla `nav` |
| Snippet | `zenzic check snippets` | Blocchi Python, YAML, JSON e TOML con errori di sintassi |
| Placeholder | `zenzic check placeholders` | Pagine stub e pattern di testo proibiti |
| Asset | `zenzic check assets` | Immagini e file non referenziati da nessuna pagina |
| **Riferimenti** | `zenzic check references` | Dangling References, Dead Definitions, **Zenzic Shield** |

`zenzic score` aggrega tutti i controlli in un punteggio di qualità deterministico 0–100.
`zenzic diff` confronta il punteggio attuale con un baseline salvato — abilitando il rilevamento
delle regressioni su ogni pull request.

**Autofix:** Zenzic fornisce anche utility di pulizia attiva. Esegui `zenzic clean assets` per eliminare automaticamente le immagini non utilizzate identificate da `check assets` (in modo interattivo o tramite `-y`).

---

## Il Porto Sicuro

Zenzic è progettato per essere il punto fisso stabile mentre l'ecosistema degli strumenti di
documentazione cambia attorno a voi. MkDocs 2.0, Zensical, o il prossimo motore — Zenzic
non si rompe perché avete cambiato engine.

Il **Sistema di Scoperta Dinamica degli Adapter** (v0.4.0) è la realizzazione tecnica di questa
promessa: gli adapter di terze parti si installano come pacchetti Python e diventano
immediatamente disponibili senza alcun aggiornamento di Zenzic:

```bash
# Esempio: adapter di terze parti per un ipotetico supporto Hugo
uv pip install zenzic-hugo-adapter   # oppure: pip install zenzic-hugo-adapter
zenzic check all --engine hugo
```

---

## Installazione

### Con `uv` (consigliato)

```bash
# Esecuzione una-tantum senza installazione
uvx zenzic check all

# Strumento globale disponibile in qualsiasi progetto
uv tool install zenzic

# Dipendenza dev del progetto — versione fissata in uv.lock
uv add --dev zenzic
```

### Con `pip`

```bash
pip install zenzic
```

### Rendering MkDocs — extra `zenzic[docs]`

Il core di Zenzic non ha dipendenze: validare il Markdown grezzo richiede solo `zenzic`.
Lo stack MkDocs è necessario solo per **renderizzare** il sito, non per validarlo.

Per installare anche lo stack completo MkDocs:

```bash
# uv
uv add --dev "zenzic[docs]"

# pip
pip install "zenzic[docs]"
```

---

## Utilizzo CLI

```bash
# Controlli individuali
zenzic check links --strict
zenzic check orphans
zenzic check snippets
zenzic check placeholders
zenzic check assets
zenzic check references

# Autofix & Cleanup
zenzic clean assets                # Elimina interattivamente gli asset non utilizzati
zenzic clean assets -y             # Elimina gli asset non utilizzati immediatamente
zenzic clean assets --dry-run      # Mostra cosa verrebbe eliminato senza farlo

# Tutti i controlli in un comando
zenzic check all --strict
zenzic check all --exit-zero       # report senza bloccare la pipeline
zenzic check all --format json     # output machine-readable

# Override dell'adapter engine (nuovo in v0.4.0)
zenzic check all --engine zensical
zenzic check orphans --engine vanilla

# Punteggio qualità (0–100)
zenzic score --save                # persiste il baseline
zenzic diff --threshold 5          # exit 1 se il calo è > 5 punti

# Server di sviluppo
zenzic serve                       # rileva automaticamente mkdocs o zensical
zenzic serve --port 9000
```

### Codici di uscita

| Codice | Significato |
| :---: | :--- |
| `0` | Tutti i controlli selezionati sono passati |
| `1` | Uno o più controlli hanno segnalato problemi |
| **`2`** | **SECURITY CRITICAL — Zenzic Shield ha rilevato una credenziale esposta** |

> **Attenzione:**
> Il **codice di uscita 2** è riservato esclusivamente agli eventi di sicurezza. Se
> `zenzic check references` esce con codice 2, una credenziale è stata trovata nella
> documentazione. Ruotare la credenziale immediatamente.

Lo **Zenzic Shield** rileva 7 famiglie di credenziali (chiavi OpenAI, token GitHub, access key
AWS, chiavi live Stripe, token Slack, chiavi API Google e chiavi private PEM) su **ogni riga del
file sorgente** — incluse le righe dentro i blocchi di codice `bash`, `yaml` e senza etichetta.
Una credenziale in un esempio di codice è comunque una credenziale esposta.

---

## DSL `[[custom_rules]]`

Dichiara regole lint specifiche del progetto in `zenzic.toml` senza scrivere Python:

```toml
[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Rimuovere il marker DRAFT prima della pubblicazione."
severity = "warning"

[[custom_rules]]
id       = "ZZ-NOINTERNAL"
pattern  = "internal\\.corp\\.example\\.com"
message  = "L'hostname interno non deve apparire nella documentazione pubblica."
severity = "error"
```

Le regole si attivano identicamente con tutti gli adapter (MkDocs, Zensical, Vanilla). Nessuna
modifica richiesta dopo la migrazione da un engine all'altro.

---

## Supporto i18n

Zenzic supporta nativamente entrambe le strategie i18n usate da `mkdocs-static-i18n`:

**Suffix Mode** (`pagina.locale.md`) e **Folder Mode** (`docs/it/pagina.md`).

In Folder Mode, dichiara la configurazione locale in `zenzic.toml`:

```toml
[build_context]
engine         = "mkdocs"
default_locale = "en"
locales        = ["it", "fr"]
```

Zenzic usa questa lista per risolvere correttamente i link degli asset tra locale e per
non segnalare mai i file tradotti come orfani.

---

## Changelog & Note di Rilascio

- 📋 [CHANGELOG.md](CHANGELOG.md) — storico completo delle modifiche (unico, in inglese)
- 🚀 [RELEASE.md](RELEASE.md) — manifesto di rilascio v0.4.0 (inglese)
- 🚀 [RELEASE.it.md](RELEASE.it.md) — manifesto di rilascio v0.4.0 (italiano)

> Il changelog è ora mantenuto in un unico file inglese (`CHANGELOG.md`).
> Questa scelta segue gli standard dell'ecosistema Python open source:
> la cronologia delle versioni è documentazione tecnica, non interfaccia utente.
>
> Nota sul ciclo release: la linea `0.4.x` è stata abbandonata (fase
> esplorativa con breaking changes multipli); la linea attiva di
> stabilizzazione è `0.5.x`.

---

## Contribuire

Bug report, miglioramenti alla documentazione e pull request sono benvenuti. Prima di iniziare:

1. Apri un'issue per discutere la modifica — usa il [template appropriato](https://github.com/PythonWoods/zenzic/issues).
2. Leggi la [Guida ai Contributi](CONTRIBUTING.md) — in particolare il setup locale e la checklist **Zenzic Way**.
3. Ogni PR deve superare `nox -s preflight` e includere le intestazioni REUSE/SPDX sui nuovi file.

Consulta anche il [Codice di Condotta](CODE_OF_CONDUCT.md) e la [Policy di Sicurezza](SECURITY.md).

## Citare Zenzic

Il file [`CITATION.cff`](CITATION.cff) è presente nella root del repository. GitHub lo
visualizza automaticamente — clicca **"Cite this repository"** sulla pagina del repo per
ottenere il riferimento in formato APA o BibTeX.

## Licenza

Apache-2.0 — vedi [LICENSE](LICENSE).

---

<p align="center">
  &copy; 2026 <strong>PythonWoods</strong>. Progettato con precisione.<br>
  Based in Italy 🇮🇹 &nbsp;·&nbsp; Committed to the craft of Python development.<br>
  <a href="mailto:dev@pythonwoods.dev">dev@pythonwoods.dev</a>
</p>

<!-- ─── Reference link definitions ──────────────────────────────────────────── -->

[mkdocs]:             https://www.mkdocs.org/
[zensical]:           https://zensical.org/
[docs-it-home]:       https://zenzic.pythonwoods.dev/it/usage/
[docs-it-config]:     https://zenzic.pythonwoods.dev/it/configuration/
[docs-it-migration]:  https://zenzic.pythonwoods.dev/it/guide/migration/
[docs-it-arch]:       https://zenzic.pythonwoods.dev/it/architecture/
[docs-it-adapter]:    https://zenzic.pythonwoods.dev/it/developers/writing-an-adapter/
