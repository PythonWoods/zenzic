<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

# 🛡️ Zenzic

<p align="center">
  <img src="assets/brand/svg/zenzic-wordmark.svg#gh-light-mode-only" alt="Zenzic" width="360">
  <img src="assets/brand/svg/zenzic-wordmark-dark.svg#gh-dark-mode-only" alt="Zenzic" width="360">
</p>

<p align="center">
  <a href="https://pypi.org/project/zenzic/">
    <img src="https://img.shields.io/pypi/v/zenzic?label=PyPI&color=38bdf8&style=flat-square&cacheBuster=sentinel-a4" alt="PyPI Version">
  </a>
  <a href="https://pypi.org/project/zenzic/">
    <img src="https://img.shields.io/pypi/pyversions/zenzic?color=10b981&style=flat-square" alt="Python Versions">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-Apache--2.0-0d9488?style=flat-square" alt="License">
  </a>
</p>

<p align="center">
  <a href="https://github.com/PythonWoods/zenzic">
    <img src="https://img.shields.io/badge/🛡️_zenzic_shield-passing-4f46e5?style=flat-square" alt="Zenzic Shield">
  </a>
  <a href="https://github.com/PythonWoods/zenzic">
    <img src="https://img.shields.io/badge/🛡️_zenzic-100%2F100-4f46e5?style=flat-square" alt="Zenzic Score">
  </a>
  <a href="https://docusaurus.io/">
    <img src="https://img.shields.io/badge/docs_by-Docusaurus-3ECC5F?style=flat-square" alt="Built with Docusaurus">
  </a>
</p>

<p align="center">
  <em>Zenzic Shield verifica internamente questo repository per credenziali esposte ad ogni commit.</em>
</p>

<p align="center">
  <strong>Il Safe Harbor per la tua documentazione Markdown.</strong><br>
  <em>Analisi statica engine-agnostic — standalone, con sicurezza rafforzata, zero configurazione richiesta.</em>
</p>

---

## ⚡ Provalo subito — Zero Installazione

Hai una cartella di file Markdown? Esegui un audit istantaneo dei link e della sicurezza usando [`uv`][uv]:

```bash
uvx zenzic check all ./tua-cartella
```

Zenzic identificherà il tuo motore tramite i file di configurazione o passerà alla **modalità Vanilla**
per cartelle indipendenti — garantendo protezione immediata per link, credenziali e integrità strutturale.

---

## 🚀 Quick Start

```bash
pip install zenzic
zenzic lab        # Showroom interattivo — 9 atti, ogni motore, zero configurazione
zenzic check all  # Analizza la cartella corrente
```

📖 [Documentazione completa →][docs-it-home] · 🏅 [Badge][docs-it-badges] · 🔄 [Guida CI/CD][docs-it-cicd]

---

## 🎯 Perché Zenzic?

| Senza Zenzic | Con Zenzic |
| :--- | :--- |
| ❌ Ancore rotte passano silenziosamente in Docusaurus v3 | ✅ Validazione matematica delle ancore tramite VSM |
| ❌ Chiavi API esposte nei blocchi di codice committate su git | ✅ **The Shield** — scanner 9 famiglie di credenziali, exit 2 |
| ❌ Path traversal `../../../../etc/passwd` nei link | ✅ **Blood Sentinel** — exit 3 non sopprimibile |
| ❌ Pagine orfane irraggiungibili da qualsiasi link di navigazione | ✅ Rilevamento semantico degli orfani — non solo file-exists |
| ❌ 404 silenziosi che si accumulano in Google Search Console | ✅ Controlli di integrità Directory Index |
| ❌ Migrazione MkDocs → Zensical con errori sconosciuti | ✅ **Transparent Proxy** — analizza entrambi con un comando |

---

## 🧩 Cosa NON è Zenzic

- **Non è un generatore di siti.** Analizza la sorgente; non costruisce mai HTML.
- **Non è un wrapper di build.** Zero-Trust Execution: nessun sottoprocesso, nessun binario `mkdocs` o `docusaurus` invocato.
- **Non è un correttore ortografico.** Struttura e sicurezza — non prosa.
- **Non è un crawler HTTP.** Tutta la validazione è locale e basata su file.

---

## 📋 Matrice delle Funzionalità

| Funzionalità | Comando | Rileva | Exit |
| :--- | :--- | :--- | :---: |
| Integrità dei link | `check links` | Link rotti, ancore morte | 1 |
| Rilevamento orfani | `check orphans` | File assenti dalla `nav` — invisibili dopo la build | 1 |
| Snippet di codice | `check snippets` | Errori di sintassi in blocchi Python / YAML / JSON / TOML | 1 |
| Contenuto placeholder | `check placeholders` | Pagine stub e pattern di testo vietati | 1 |
| Asset inutilizzati | `check assets` | Immagini e file non referenziati | 1 |
| **Scansione credenziali** | `check references` | **9 famiglie di credenziali** — testo, URL, blocchi di codice | **2** |
| **Path traversal** | `check links` | Tentativi di fuga verso path di sistema | **3** |
| Punteggio qualità | `score` | Metrica composita deterministica 0–100 | — |
| Rilevamento regressioni | `diff` | Calo del punteggio vs baseline salvata — CI-friendly | 1 |

**Correzione automatica:** `zenzic clean assets [-y] [--dry-run]` elimina gli asset inutilizzati.

> 🚀 **v0.6.1 "Obsidian Glass" (Stabile)** — Versioning completo Docusaurus v3, risoluzione
> alias `@site/` e Transparent Proxy Zensical. Vedi [CHANGELOG.md](CHANGELOG.md).

---

## 🛡️ Sicurezza: The Shield & Blood Sentinel

Due livelli di sicurezza sono permanentemente attivi — nessuno è sopprimibile con `--exit-zero`:

**The Shield** scansiona ogni riga — inclusi i blocchi di codice delimitati — alla ricerca di
credenziali. La normalizzazione Unicode sconfigge l'offuscamento (entità HTML, interposizione
di commenti, lookback multi-riga). Famiglie rilevate: AWS, GitHub/GitLab, Stripe, Slack, OpenAI,
Google, intestazioni PEM, payload esadecimali.
**→ Exit 2. Ruota e verifica immediatamente.**

**Blood Sentinel** normalizza ogni link risolto con `os.path.normpath` e rifiuta qualsiasi
percorso che sfugge alla root `docs/`. Intercetta tentativi di tipo `../../../../etc/passwd`
prima di qualsiasi syscall OS.
**→ Exit 3.**

| Exit | Significato |
| :---: | :--- |
| `0` | Tutti i controlli superati |
| `1` | Problemi di qualità rilevati |
| **`2`** | **SICUREZZA — credenziale esposta rilevata** |
| **`3`** | **SICUREZZA — path traversal di sistema rilevato** |

> Aggiungi `zenzic check references` ai tuoi hook pre-commit per bloccare le fughe prima della history git.

---

## 🔌 Supporto Multi-Motore

Zenzic legge i file di configurazione come testo semplice — non importa né esegue mai il tuo framework di build:

| Motore | Adapter | Funzionalità chiave |
| :--- | :--- | :--- |
| [Docusaurus v3][docusaurus] | `DocusaurusAdapter` | Docs versionati, alias `@site/`, rilevamento Ghost Route |
| [MkDocs][mkdocs] | `MkDocsAdapter` | Modalità i18n suffix + folder, `fallback_to_default` |
| [Zensical][zensical] | `ZensicalAdapter` | Transparent Proxy ponte `mkdocs.yml` se `zensical.toml` assente |
| Qualsiasi cartella | `VanillaAdapter` | Zero-config, Directory Index Integrity — nessun motore richiesto |

Adapter di terze parti si installano tramite il gruppo di entry-point `zenzic.adapters`.
Vedi la [Guida Developer][docs-it-arch] per le API degli adapter.

---

## ⚙️ Configurazione

Zero-config di default. Priorità: `zenzic.toml` > `[tool.zenzic]` in `pyproject.toml` > valori predefiniti.

```toml
# zenzic.toml  (tutti i campi sono opzionali)
docs_dir                 = "docs"
fail_under               = 80       # exit 1 se punteggio < soglia; 0 = solo osservazione
excluded_dirs            = ["includes", "assets", "overrides"]
excluded_build_artifacts = ["pdf/*.pdf", "dist/*.zip"]
placeholder_patterns     = ["coming soon", "todo", "stub"]

[build_context]
engine         = "mkdocs"   # mkdocs | docusaurus | zensical | vanilla
default_locale = "en"
locales        = ["it"]
```

```bash
zenzic init             # Genera zenzic.toml con valori auto-rilevati
zenzic init --pyproject # Incorpora [tool.zenzic] in pyproject.toml
```

**Regole di lint personalizzate** — dichiara pattern specifici del progetto in `zenzic.toml`, senza Python:

```toml
[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Rimuovere il marker DRAFT prima della pubblicazione."
severity = "warning"
```

Le regole si attivano identicamente su tutti gli adapter. Nessuna modifica richiesta dopo la migrazione del motore.

---

## 🔄 Integrazione CI/CD

```yaml
- name: 🛡️ Zenzic Sentinel
  run: uvx zenzic check all --strict
  # Exit 1 = qualità · Exit 2 = credenziale esposta · Exit 3 = path traversal
  # Exit 2 e 3 non sono mai sopprimibili.

- name: Gate regressione
  run: |
    uvx zenzic score --save    # sul branch main
    uvx zenzic diff            # sulla PR — exit 1 se il punteggio cala
```

Per automazione badge e gate di regressione, vedi la [guida CI/CD][docs-it-cicd].
Workflow completo: [`.github/workflows/ci.yml`][ci-workflow]

---

## 📦 Installazione

```bash
# Audit one-shot senza installazione (consigliato per CI ed esplorazione)
uvx zenzic check all ./docs

# Tool CLI globale
uv tool install zenzic

# Dipendenza dev con versione fissata
uv add --dev zenzic

# pip
pip install zenzic
pip install "zenzic[mkdocs]"   # + plugin build-time MkDocs
```

> L'extra `[mkdocs]` aggiunge il plugin build-time (`zenzic.integrations.mkdocs`).
> Tutti gli adapter dei motori (Docusaurus, Zensical, Vanilla) sono inclusi nell'installazione base.

**Portabilità:** Zenzic rifiuta i link interni assoluti (che iniziano con `/`). I link relativi
funzionano con qualsiasi percorso di hosting. Gli URL esterni `https://` non sono mai interessati.

---

## 🖥️ Riferimento CLI

```bash
# Controlli
zenzic check links [--strict]
zenzic check orphans
zenzic check snippets
zenzic check placeholders
zenzic check assets
zenzic check references [--strict] [--links]
zenzic check all [--strict] [--exit-zero] [--format json] [--engine ENGINE]
zenzic check all [--exclude-dir DIR] [--include-dir DIR]

# Punteggio e diff
zenzic score [--save] [--fail-under N]
zenzic diff  [--threshold N]

# Correzione automatica
zenzic clean assets [-y] [--dry-run]

# Inizializzazione
zenzic init [--pyproject]

# Showroom interattivo
zenzic lab [--act N] [--list]
```

---

## 📟 Tour Visivo

```text
╭───────────────────────  🛡  ZENZIC SENTINEL  v0.6.1  ────────────────────────╮
│                                                                              │
│  docusaurus • 38 file (18 docs, 20 asset) • 0.9s                             │
│                                                                              │
│  ────────────────────── docs/guides/setup.mdx ───────────────────────────  │
│                                                                              │
│    ✗ 12:   [Z001]  'quickstart.mdx' non trovato in docs                      │
│        │                                                                     │
│    12  │ Leggi la [guida quickstart](quickstart.mdx) prima.                  │
│        │                                                                     │
│  ──────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ✗ 1 errore  • 1 file con risultati • FALLITO                                │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Visita il [portale di documentazione][docs-it-home] per screenshot interattivi ed esempi ricchi.

---

## 🗺️ Roadmap v0.7.0

- [ ] **Auto-fix Engine** — Riparazione automatica di link rotti e ancore orfane.
- [ ] **Estensioni IDE** — Lint in tempo reale per VS Code e Cursor tramite LSP.
- [ ] **AI Context Provider** — Export VSM in formato LLM-friendly per agenti AI.
- [ ] **Adapter Astro & VitePress** — Espandere il Safe Harbor ai framework JS.

---

## 🏗️ Filosofia di Design

Zenzic è costruito su tre contratti operativi:

**Analizza la Sorgente, non la Build.** La VSM (Virtual Site Map) mappa ogni file `.md` al suo
URL canonico senza eseguire la build — gli errori vengono intercettati prima di raggiungere la produzione.

**Zero-Trust Execution.** Nessun sottoprocesso, nessuna esecuzione di codice arbitrario, nessuna
importazione di motori di build. I config Docusaurus `.ts`/`.js` sono analizzati tramite analisi
testuale statica — Node.js non viene mai invocato.

**Esclusione Obbligatoria ad Ogni Entry Point.** Tutta la scoperta dei file passa attraverso
`LayeredExclusionManager` — una gerarchia a 4 livelli (Sistema → VCS → Config → CLI). Nessuna
scansione globale senza un contesto di esclusione esplicito.

Vedi la [Guida all'Architettura][docs-it-arch] per il Two-Pass Reference Pipeline e l'analisi approfondita della VSM.

---

## 🙋 FAQ

**Perché non usare `grep`?** Grep è cieco alla struttura. Zenzic comprende il versioning di
Docusaurus, i fallback i18n di MkDocs e le Ghost Route — pagine che non esistono come file ma
sono URL validi.

**Esegue il mio motore di build?** No. 100% subprocess-free. Analisi statica solo su testo semplice.

**Regge migliaia di file?** Sì. Parallelismo adattivo per la scoperta; lookup VSM O(1) per link;
cache content-addressable (`SHA256(content + config + vsm_snapshot)`) salta i file invariati.

**Shield vs Blood Sentinel?** Shield = segreti *nel* contenuto (exit 2). Blood Sentinel =
link che puntano a *path* di sistema OS (exit 3). Entrambi non sono sopprimibili.

**Non serve `zenzic.toml`?** Corretto. Zenzic identifica il motore dai file di configurazione presenti e applica i default sicuri.
Esegui `zenzic init` in qualsiasi momento per generare un file di configurazione pre-compilato.

**Cos'è `zenzic lab`?** Uno showroom interattivo a 9 atti che copre ogni motore e ogni classe di
errore. Eseguilo una volta prima di integrare Zenzic in qualsiasi progetto.

---

## 🛠️ Sviluppo

```bash
uv sync --all-groups
nox -s tests       # pytest + copertura
nox -s lint        # ruff
nox -s typecheck   # mypy --strict
nox -s preflight   # lint + format + typecheck + pytest + reuse
just verify        # preflight + zenzic check all --strict (self-dogfood)
```

Vedi la [Guida alla Contribuzione][contributing] per la checklist del metodo Zenzic e le convenzioni PR.

---

## 🤝 Contribuire

1. Apri una [issue][issues] per discutere la modifica.
2. Leggi la [Guida alla Contribuzione][contributing] — checklist del metodo Zenzic, funzioni pure,
   nessun sottoprocesso, source-first.
3. Ogni PR deve superare `nox -s preflight` e includere intestazioni REUSE/SPDX sui nuovi file.

Vedi anche: [Codice di Condotta][coc] · [Politica di Sicurezza][security]

## 📎 Citare Zenzic

Un file [`CITATION.cff`][citation-cff] è presente alla radice del repository. Clicca su
**"Cite this repository"** su GitHub per l'output APA o BibTeX.

## 📄 Licenza

Apache-2.0 — vedi [LICENSE][license].

---

<p align="center">
  &copy; 2026 <strong>PythonWoods</strong>. Ingegnerizzato con precisione.<br>
  Con sede in Italia 🇮🇹 &nbsp;·&nbsp; Dediti all'arte dello sviluppo Python.<br>
  <a href="mailto:dev@pythonwoods.dev">dev@pythonwoods.dev</a>
</p>

<!-- ─── Definizioni dei link di riferimento ──────────────────────────────────── -->

[mkdocs]:            https://www.mkdocs.org/
[docusaurus]:        https://docusaurus.io/
[zensical]:          https://zensical.org/
[uv]:                https://docs.astral.sh/uv/
[docs-it-home]:      https://zenzic.dev/it/docs/
[docs-it-badges]:    https://zenzic.dev/it/docs/usage/badges/
[docs-it-cicd]:      https://zenzic.dev/it/docs/guides/ci-cd/
[docs-it-arch]:      https://zenzic.dev/it/docs/internals/architecture-overview/
[ci-workflow]:       .github/workflows/ci.yml
[contributing]:      CONTRIBUTING.it.md
[license]:           LICENSE
[citation-cff]:      CITATION.cff
[coc]:               CODE_OF_CONDUCT.md
[security]:          SECURITY.md
[issues]:            https://github.com/PythonWoods/zenzic/issues
