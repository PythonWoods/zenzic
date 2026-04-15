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
    <img src="https://img.shields.io/pypi/v/zenzic?include_prereleases&label=PyPI&color=38bdf8&style=flat-square&cacheBuster=sentinel-a4" alt="PyPI Version">
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
  <em>Zenzic Shield audita internamente questo repository per credenziali esposte ad ogni commit.</em>
</p>

<p align="center">
  <strong>"Zenzic è il Safe Harbor (Porto Sicuro) per l'integrità della tua documentazione. Non si limita a controllare i link; audita la resilienza tecnica del tuo progetto."</strong><br>
  <em>Sentinella della documentazione — autonoma, agnostica rispetto all'engine, e a prova di sicurezza.</em>
</p>

```bash
╭───────────────────────  🛡  ZENZIC SENTINEL  v0.6.1rc1  ───────────────────────╮
│                                                                              │
│  docusaurus • 38 files (18 docs, 20 assets) • 0.9s                           │
│                                                                              │
│  ──────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ✔ All checks passed. Your documentation is secure.                          │
│                                                                              │
│    💡 4 info findings suppressed — use --show-info for details.              │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

> La documentazione non fallisce rumorosamente. Degrada in silenzio.

Link non raggiungibili, pagine orfane, snippet di codice non validi, contenuto placeholder mai
completato e chiavi API esposte si accumulano nel tempo — finché gli utenti non li incontrano in
produzione. Zenzic rileva tutto questo nei progetti [Docusaurus][docusaurus], [MkDocs][mkdocs] e
[Zensical][zensical] come **CLI autonoma**, senza richiedere l'installazione di alcun framework
di build.

Zenzic è **agnostico** — funziona con qualsiasi sistema di documentazione basato su Markdown
(Docusaurus, MkDocs, Zensical, o una semplice cartella di file `.md`) senza installare alcun
framework di build. Legge i file sorgente e le configurazioni di build come testo puro. Ed è
**opinionated**: i link assoluti sono un errore bloccante, l'identità dell'engine deve essere
dimostrabile, e la CLI è 100% subprocess-free.

---

## Capacità Principali

- **Sicurezza** — Shield (8 famiglie di credenziali, Exit 2) & Sentinella di Sangue (path traversal verso directory di sistema, Exit 3). Regex ReDoS-safe (F2-1), protezione jailbreak (F4-1). Nessuno dei due è sopprimibile con `--exit-zero`.
- **Integrità** — Rilevamento link circolari O(V+E), Virtual Site Map con cache content-addressable, punteggio qualità deterministico 0–100.
- **Intelligenza** — Multi-engine: MkDocs, Docusaurus v3, Zensical e Vanilla. Cache adapter a livello di modulo. Gli adapter di terze parti si installano come pacchetti Python tramite entry point.
- **Discovery** — Iterazione file universale VCS-aware (zero `rglob`), `ExclusionManager` obbligatorio su ogni entry point, gerarchia di Esclusione a 4 livelli, parser `.gitignore` pure-Python.

> 🚀 **Ultima Release: v0.6.1rc1 "Obsidian Bastion"** — vedi [CHANGELOG.md](CHANGELOG.md) per i dettagli.

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
  <a href="https://zenzic.dev/docs/it/"><strong>Esplora la documentazione completa →</strong></a>
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

## Standard di Portabilità

Zenzic applica due regole che rendono la documentazione portabile su qualsiasi ambiente di hosting
e indipendente da qualsiasi motore di build specifico.

### Applicazione dei Percorsi Relativi

Zenzic **rifiuta i link interni che iniziano con `/`**. I percorsi assoluti dipendono dall'ambiente:
un link a `/assets/logo.png` funziona quando il sito è alla radice del dominio, ma restituisce 404
quando è ospitato in una sottodirectory (es. `https://example.com/docs/assets/logo.png` ≠
`https://example.com/assets/logo.png`).

```markdown
<!-- Rifiutato da Zenzic -->
[Scarica](/assets/guide.pdf)

<!-- Corretto — funziona con qualsiasi hosting path -->
[Scarica](../assets/guide.pdf)
```

Il messaggio di errore include un suggerimento di correzione esplicito. Gli URL esterni (`https://...`) non
sono interessati.

### Supporto i18n: Risoluzione Locale Multi-Engine

Zenzic supporta nativamente documentazione locale-aware su tutti gli engine:

**MkDocs — Suffix Mode** (`pagina.locale.md`) e **Folder Mode** (`docs/it/pagina.md`) tramite
`mkdocs-static-i18n`. I link da pagine tradotte a pagine non tradotte sono risolti attraverso
il fallback alla locale di default quando `fallback_to_default: true` è impostato.

**Docusaurus v3 — directory i18n** (`i18n/it/docusaurus-plugin-content-docs/current/`).
Zenzic scopre gli alberi di locale da `docusaurus.config.ts` automaticamente. I link tra
pagine locale e asset della locale di default sono risolti senza configurazione.

**Zensical** — Solo Suffix Mode (`pagina.locale.md`), simile a MkDocs.

In Folder Mode (MkDocs) e Docusaurus i18n, Zenzic usa la sezione `[build_context]` in
`zenzic.toml` per identificare le directory di locale:

```toml
# zenzic.toml
[build_context]
engine         = "mkdocs"      # "mkdocs", "docusaurus", "zensical" o "vanilla"
default_locale = "en"
locales        = ["it", "fr"]  # nomi delle directory locale non default
```

Quando `zenzic.toml` è assente, Zenzic legge la configurazione locale direttamente da `mkdocs.yml`
(rispettando `docs_structure`, `fallback_to_default` e `languages`). Non è richiesta alcuna
configurazione per i progetti che non usano i18n.

## Integrazioni di Prima Classe

Zenzic è **agnostico rispetto al motore di build**. Funziona con qualsiasi sistema di documentazione
basato su Markdown — MkDocs, Docusaurus, Zensical, o una semplice cartella di file `.md`. Non è necessario
installare alcun framework di build; Zenzic legge solo i file sorgente grezzi.

Dove un ecosistema di documentazione definisce convenzioni consolidate per la struttura multi-locale
o la generazione di artefatti a build-time, Zenzic fornisce supporto avanzato, opt-in, leggendo il file
di configurazione del progetto (YAML, TOML, o testo piano JS/TS) — senza mai importare o eseguire il
framework stesso.

### Adapter Engine

Zenzic traduce la conoscenza engine-specifica in risposte engine-agnostiche attraverso un sottile
**adapter layer**:

```text
zenzic.toml  →  get_adapter()  →  Adapter  →  Core (Scanner + Validator)
```

L'adapter risponde alle domande che il Core necessita senza conoscere nulla degli interni di MkDocs o
Zensical:

| Metodo | Domanda |
| :--- | :--- |
| `is_locale_dir(part)` | Questa componente del percorso è una directory locale non default? |
| `resolve_asset(path)` | Esiste un fallback nella locale di default per questo asset mancante? |
| `is_shadow_of_nav_page(rel, nav)` | Questo file di locale è un mirror di una pagina nella nav? |
| `get_nav_paths()` | Quali percorsi `.md` sono dichiarati nella nav? |
| `get_ignored_patterns()` | Quali pattern di filename sono file locale non default (suffix mode)? |
| `get_route_info(rel)` | Metadati di routing completi: URL canonico, stato, slug, route base path? |

Quattro adapter sono disponibili, selezionati automaticamente da `get_adapter()`:

| Adapter | Quando selezionato | Sorgente config |
| :--- | :--- | :--- |
| `MkDocsAdapter` | `engine = "mkdocs"` o engine sconosciuto | `mkdocs.yml` (YAML) |
| `DocusaurusAdapter` | `engine = "docusaurus"` | `docusaurus.config.ts` / `.js` (testo piano) |
| `ZensicalAdapter` | `engine = "zensical"` | `zensical.toml` (TOML, zero YAML) |
| `VanillaAdapter` | Nessun file config, nessuna locale dichiarata | — (tutti no-op) |

**Applicazione Nativa** — `engine = "zensical"` richiede che `zensical.toml` sia presente.
Se è assente, Zenzic lancia `ConfigurationError` immediatamente. Non c'è nessun fallback a
`mkdocs.yml` e nessuna degradazione silenziosa. L'identità Zensical deve essere dimostrabile.

### Come funziona — Virtual Site Map (VSM)

La maggior parte degli analizzatori di documentazione controlla se un file collegato esiste su disco.
Zenzic va oltre: costruisce un **Virtual Site Map** prima che qualsiasi regola venga eseguita.

```text
File sorgente  ──►  Adapter  ──►  VSM  ──►  Rule Engine  ──►  Violazioni
  .md + config      (conoscenza     (URL → stato)   (funzioni pure)
                    engine-
                    specifica)
```

Il VSM mappa ogni file sorgente `.md` all'URL canonico che il motore di build servirà —
**senza eseguire il build**. Ogni route porta uno stato:

| Stato | Significato |
| :--- | :--- |
| `REACHABLE` | La pagina è nella nav; gli utenti possono trovarla. |
| `ORPHAN_BUT_EXISTING` | Il file esiste su disco ma è assente dalla `nav:`. Gli utenti non possono trovarlo tramite navigazione. |
| `CONFLICT` | Due file mappano allo stesso URL (es. `index.md` + `README.md`). Il risultato del build è indefinito. |
| `IGNORED` | Il file non verrà servito (`README.md` non elencato, directory `_private/` di Zensical). |

Questo rende Zenzic unicamente preciso: un link a una pagina `ORPHAN_BUT_EXISTING`
viene intercettato come `UNREACHABLE_LINK` — il file esiste, il link risolve, ma
l'utente otterrà un 404 dopo il build perché la pagina non è navigabile.

**Ghost Routes** (`reconfigure_material: true`) — quando `mkdocs-material`
auto-genera entry point di locale (es. `/it/`) a build-time, queste pagine
non appaiono mai nella `nav:`. Zenzic rileva questo flag e le marca `REACHABLE`
automaticamente, evitando falsi warning di orfani.

**Cache content-addressable** — Zenzic evita di ri-lintare file invariati usando
come chiave `SHA256(content) + SHA256(config)`. Per le regole VSM-aware
la chiave include anche `SHA256(vsm_snapshot)`, garantendo l'invalidazione quando
lo stato di routing di qualsiasi file cambia. I timestamp non vengono mai consultati —
la cache è corretta in ambienti CI dove `git clone` resetta `mtime`.

### MkDocs — fallback i18n

Quando `mkdocs.yml` dichiara il plugin i18n con `fallback_to_default: true`, Zenzic rispecchia
la logica di risoluzione del plugin: un link da una pagina tradotta a una pagina non tradotta **non**
viene segnalato come rotto, perché il build servirà la versione nella locale di default. Supportato sia per
`docs_structure: suffix` che per `docs_structure: folder`.

```yaml
# mkdocs.yml
plugins:
  - i18n:
      docs_structure: folder
      fallback_to_default: true
      languages:
        - locale: en
          default: true
          build: true
        - locale: it
          build: true
```

Se `mkdocs.yml` è assente (o il plugin i18n non è configurato), Zenzic torna alla validazione
a locale singola — nessun errore, nessun warning, nessun framework richiesto.

### Artefatti di build (`excluded_build_artifacts`)

Si applica a qualsiasi sistema di documentazione. Se i link puntano a file generati a build-time
(PDF, ZIP), dichiara i loro pattern glob in `zenzic.toml`:

```toml
# zenzic.toml
excluded_build_artifacts = ["pdf/*.pdf", "dist/*.zip"]
```

Zenzic sopprime gli errori per i percorsi corrispondenti al momento del lint. Il build resta
responsabile della generazione degli artefatti; Zenzic si fida del link senza richiedere il file su disco.

### Link in stile referenza

I link `[testo][id]` sono risolti attraverso la stessa pipeline dei link inline — incluso il
fallback i18n — per tutti i sistemi di documentazione.

```markdown
[Riferimento API][api-ref]

[api-ref]: api.md
```

---

## Adapter vs. Integrazioni: L'Ecosistema Zenzic

Zenzic separa **comprendere** dal **agire** attraverso due punti di estensione distinti:

| | Adapter | Integrazione (Plugin) |
| :--- | :--- | :--- |
| **Scopo** | Permettere a Zenzic di *capire* il tuo sito. | Permettere a Zenzic di *sorvegliare* la tua build. |
| **Direzione** | Engine → Zenzic | Zenzic → Engine |
| **Dipendenze** | Nessuna — analisi testuale pura. | Richiesta (`mkdocs` lib per il plugin MkDocs). |
| **Attivazione** | Automatica su ogni `zenzic check`. | Opt-in via config engine (es. `mkdocs.yml`). |
| **Obiettivo** | Discovery e routing zero-config. | Blocco della build in caso di errori. |
| **Posizione** | `zenzic.core.adapters.*` | `zenzic.integrations.*` |

**In pratica:** l'Adapter è la *mente* — legge `mkdocs.yml` come testo puro e costruisce
la VSM. L'Integrazione (plugin) è il *braccio* — si aggancia agli eventi di `mkdocs build`
e solleva un `PluginError` se i controlli di qualità falliscono.

La maggior parte degli utenti ha bisogno solo degli adapter (automatici). Installa
un'integrazione solo quando vuoi che Zenzic diventi un guardiano nel pipeline di build.

### Plugin MkDocs

```bash
# Installa l'extra opzionale
pip install "zenzic[mkdocs]"
```

```yaml
# mkdocs.yml
plugins:
  - zenzic:
      strict: false
      fail_on_error: true
      checks: [orfani, snippet, segnaposto, assets]
```

La classe del plugin si trova in `zenzic.integrations.mkdocs:ZenzicPlugin` ed è
auto-scoperta da MkDocs tramite l'entry point `mkdocs.plugins` — nessun percorso manuale
richiesto.

---

## Installazione

### Con `uv` (consigliato)

[`uv`][uv] è il modo più veloce per installare e eseguire Zenzic:

```bash
# Esecuzione una-tantum senza installazione
uvx --pre zenzic check all

# Strumento globale disponibile in qualsiasi progetto
uv tool install --pre zenzic

# Dipendenza dev del progetto — versione fissata in uv.lock
uv add --dev --pre zenzic
```

### Con `pip`

```bash
# Installazione globale (considera un ambiente virtuale)
pip install --pre zenzic

# Dentro un ambiente virtuale (consigliato)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --pre zenzic
```

### Lean e Agnostico per Design

Zenzic esegue un'**analisi statica** dei tuoi file di configurazione (`mkdocs.yml`, `docusaurus.config.ts`, `zensical.toml`, `pyproject.toml`). **Non esegue** il motore di build né i suoi plugin — è 100% subprocess-free. La configurazione di Docusaurus (`.ts`/`.js`) viene analizzata tramite parsing statico del testo, senza mai invocare Node.js.

Questo significa che **non è necessario installare** MkDocs, Docusaurus, Material for MkDocs o altri
plugin di build nel tuo ambiente di linting. Zenzic rimane leggero e privo di dipendenze, rendendolo
ideale per pipeline CI/CD veloci e isolate.

**Extra di installazione:**

| Comando | Cosa ottieni |
| :--- | :--- |
| `pip install zenzic` | CLI core + adapter Docusaurus, Zensical e Vanilla. Nessuna libreria engine richiesta. |
| `pip install "zenzic[mkdocs]"` | Core + il **plugin MkDocs** (`zenzic.integrations.mkdocs`). Aggiunge `mkdocs` come dipendenza. |

> L'extra MkDocs è necessario **solo** se vuoi l'integrazione plugin a build-time.
> Per l'uso standalone della CLI (`zenzic check all`), l'installazione base è sufficiente per ogni engine.
>
> **Artefatti di build:** Se la documentazione punta a file generati a build-time
> (PDF, ZIP), aggiungi i loro pattern glob a `excluded_build_artifacts` in `zenzic.toml`
> anziché pre-generarli. Vedi la sezione [Integrazioni di Prima Classe](#integrazioni-di-prima-classe).

### Setup progetto

```bash
zenzic init             # crea zenzic.toml con engine rilevato automaticamente
zenzic init --pyproject # incorpora [tool.zenzic] in pyproject.toml
```

Quando `pyproject.toml` esiste, `zenzic init` chiede interattivamente se incorporare
la configurazione lì. Usa `--pyproject` per saltare il prompt.

---

## Utilizzo CLI

```bash
# Controlli individuali
zenzic check links --strict
zenzic check orphans
zenzic check snippets
zenzic check placeholders
zenzic check assets

# Autofix & Cleanup
zenzic clean assets                # Elimina interattivamente gli asset non utilizzati
zenzic clean assets -y             # Elimina gli asset non utilizzati immediatamente
zenzic clean assets --dry-run      # Mostra cosa verrebbe eliminato senza farlo

# Pipeline dei riferimenti
zenzic check references           # Harvest → Cross-Check → Shield → Punteggio integrità
zenzic check references --strict  # Tratta le Dead Definitions come errori
zenzic check references --links   # Valida anche gli URL dei riferimenti via HTTP asincrono

# Tutti i controlli in un comando
zenzic check all --strict
zenzic check all --exit-zero       # report senza bloccare la pipeline
zenzic check all --format json     # output machine-readable
zenzic check all --engine docusaurus  # override esplicito dell'engine

# Controllo esclusioni
zenzic check all --exclude-dir drafts --exclude-dir temp
zenzic check all --include-dir guides  # Scansiona solo directory specifiche

# Punteggio qualità (0–100)
zenzic score
zenzic score --save                # persiste il baseline
zenzic score --fail-under 80       # exit 1 se sotto la soglia

# Rilevamento regressioni contro snapshot salvato
zenzic diff                        # exit 1 su qualsiasi calo
zenzic diff --threshold 5          # exit 1 solo se il calo è > 5 punti
```

> **Nota (v0.6.1+):** `zenzic serve` è stato rimosso. A partire dalla v0.6.1, Zenzic si
> focalizza esclusivamente sull'analisi. Per visualizzare i documenti, usa il comando nativo
> del tuo engine: `mkdocs serve`, `docusaurus start`, o `zensical serve`.

### Codici di uscita

| Codice | Significato |
| :---: | :--- |
| `0` | Tutti i controlli selezionati sono passati |
| `1` | Uno o più controlli hanno segnalato problemi |
| **`2`** | **SECURITY CRITICAL — Zenzic Shield ha rilevato una credenziale esposta** |
| **`3`** | **SECURITY CRITICAL — Sentinella di Sangue ha rilevato un path traversal di sistema** |

> **Attenzione:**
> Il **codice di uscita 2** è riservato agli eventi Shield (credenziali esposte). Il **codice
> di uscita 3** è riservato alla Sentinella di Sangue (path traversal verso directory di sistema
> come `/etc/`, `/root/`). Entrambi non vengono mai soppressi da `--exit-zero`. Ruotare e
> verificare immediatamente.

---

## 🛡️ Zenzic Shield

Lo **Zenzic Shield** è un sistema di sicurezza a due livelli integrato nel core engine:

| Livello | Protegge contro |
| --- | --- |
| **Rilevamento credenziali** | Chiavi API / token esposti incorporati nelle URL dei riferimenti |
| **Path traversal** | Escape da `docs/` in stile `../../../../etc/passwd` |

### Rilevamento credenziali

Il livello credenziali viene eseguito durante il **Pass 1** (Harvesting) della pipeline dei riferimenti
e scansiona ogni URL di riferimento per pattern di credenziali noti prima che qualsiasi richiesta HTTP
venga emessa.

```markdown
<!-- Questa definizione innescherebbe un Exit 2 immediato -->
[api-docs]: https://api.example.com/?key=sk-xxxx-xxxx-xxxx-xxxx-xxxx-xxxx
```

```bash
╔══════════════════════════════════════╗
║        SECURITY CRITICAL             ║
║  Secret(s) detected in documentation ║
╚══════════════════════════════════════╝

  [SHIELD] docs/api.md:12 — openai-api-key detected in URL
    https://api.example.com/?key=sk-xxxx-xxxx-x...

Build aborted. Rotate the exposed credential immediately.
```

**Come funziona:**

1. Lo Shield viene eseguito *dentro* il Pass 1 — prima che il Pass 2 validi i link e prima che qualsiasi
   ping HTTP venga emesso. Un documento contenente una credenziale esposta non viene mai usato per effettuare
   richieste in uscita.
2. I pattern usano quantificatori a lunghezza esatta (`{48}`, `{36}`, `{16}`) — nessun backtracking, O(1) per riga.
3. Otto famiglie di credenziali sono coperte out of the box:

| Tipo | Pattern |
| --- | --- |
| Chiave API OpenAI | `sk-[a-zA-Z0-9]{48}` |
| Token GitHub | `gh[pousr]_[a-zA-Z0-9]{36}` |
| Access key AWS | `AKIA[0-9A-Z]{16}` |
| Chiave live Stripe | `sk_live_[0-9a-zA-Z]{24}` |
| Token Slack | `xox[baprs]-[0-9a-zA-Z]{10,48}` |
| Chiave API Google | `AIza[0-9A-Za-z\-_]{35}` |
| Chiave privata PEM | `-----BEGIN [A-Z ]+ PRIVATE KEY-----` |
| Payload hex-encoded | 3+ sequenze consecutive `\xNN` |

1. **Nessun punto cieco** — lo Shield scansiona ogni riga del file sorgente, incluse le righe dentro
   blocchi di codice fenced (`bash`, `yaml`, senza etichetta, ecc.). Una credenziale inserita in un esempio
   di codice è comunque una credenziale esposta.

> **Suggerimento:**
> Aggiungi `zenzic check references` ai tuoi hook pre-commit per intercettare credenziali esposte prima che
> vengano mai committate nel version control.

### Path traversal

Il livello di path traversal viene eseguito dentro `InMemoryPathResolver` durante `check links`. Normalizza
ogni href risolto con `os.path.normpath` (puro C, zero system call) e verifica che il risultato
sia contenuto dentro `docs/` usando un singolo confronto di prefisso stringa — $O(1)$, zero allocazioni.

```bash
Attack href:   ../../../../etc/passwd
After resolve: /etc/passwd
Shield check:  /etc/passwd does not start with /docs/ → PathTraversal returned, link rejected
```

Qualsiasi href che esce dalla root docs viene evidenziato come un errore `PathTraversal` distinto — mai
collassato silenziosamente in un generico "file non trovato".

---

## Integrazione CI/CD

### GitHub Actions

```yaml
- name: Lint documentazione
  run: uvx --pre zenzic check all

- name: Controlla riferimenti ed esegui Shield
  run: uvx --pre zenzic check references
```

Workflow completo: [`.github/workflows/zenzic.yml`][ci-workflow]

Per l'automazione dinamica dei badge e il rilevamento delle regressioni, consulta la [guida all'integrazione CI/CD][docs-it-cicd].

---

## Configurazione

Tutti i campi sono opzionali. Zenzic funziona senza alcun file di configurazione.

Zenzic segue una catena di priorità a tre livelli **Agnostic Citizen**:

1. `zenzic.toml` alla root del repository — sovrano; ha sempre la precedenza.
2. `[tool.zenzic]` in `pyproject.toml` — usato quando `zenzic.toml` è assente.
3. Default built-in.

```toml
# zenzic.toml  (oppure [tool.zenzic] in pyproject.toml)
docs_dir = "docs"
excluded_dirs = ["includes", "assets", "stylesheets", "overrides", "hooks"]
snippet_min_lines = 1
placeholder_max_words = 50
placeholder_patterns = ["coming soon", "todo", "stub"]
fail_under = 80   # exit 1 se il punteggio scende sotto questa soglia; 0 = modalità osservativa

# Contesto engine e i18n — richiesto solo per progetti multi-locale in folder mode.
# Quando assente, Zenzic legge la configurazione locale direttamente da mkdocs.yml.
[build_context]
engine         = "mkdocs"   # "mkdocs", "docusaurus", "zensical" o "vanilla"
default_locale = "en"
locales        = ["it"]     # nomi delle directory locale non default
```

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

Le regole si attivano identicamente con tutti gli adapter (MkDocs, Docusaurus, Zensical, Vanilla). Nessuna
modifica richiesta dopo la migrazione da un engine all'altro.

---

## Sviluppo

Per un workflow di sviluppo più veloce e interattivo usando **just**, o per istruzioni dettagliate su
come aggiungere nuovi controlli, consulta la [Guida ai Contributi][contributing].

```bash
uv sync --group dev
nox -s dev         # Installa gli hook pre-commit (una volta)

nox -s tests       # pytest + coverage
nox -s lint        # ruff check
nox -s format      # ruff format
nox -s typecheck   # mypy --strict
nox -s preflight   # pipeline CI completa (lint + test + self-check)
```

---

## Visual Tour

L'audit completo della Sentinella — banner, rilevamento engine e verdetto:

```bash
╭───────────────────────  🛡  ZENZIC SENTINEL  v0.6.1rc1  ───────────────────────╮
│                                                                              │
│  docusaurus • 38 files (18 docs, 20 assets) • 0.9s                           │
│                                                                              │
│  ────────────────────── docs/guides/setup.mdx ───────────────────────────  │
│                                                                              │
│    ✗ 12:   [Z001]  'quickstart.mdx' not found in docs                        │
│        │                                                                     │
│    12  │ Read the [quickstart guide](quickstart.mdx) first.                  │
│        │                                                                     │
│                                                                              │
│  ──────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ✗ 1 error  • 1 file with findings                                           │
│                                                                              │
│  FAILED: One or more checks failed.                                          │
│                                                                              │
│    💡 4 info findings suppressed — use --show-info for details.              │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Lo **Shield** intercetta credenziali esposte prima che qualsiasi richiesta HTTP venga emessa.
La **Sentinella di Sangue** blocca tentativi di path traversal che escono dalla root `docs/`.
Entrambi attivano codici di uscita non sopprimibili (2 e 3). Il **VSM** (Virtual Site Map)
assicura che la validazione dei link operi su URL canonici — non su percorsi filesystem —
così che pagine orfane e slug override vengano rilevati accuratamente su tutti gli engine.

Per screenshot interattivi ed esempi visivi completi, visita il
[portale documentazione](https://zenzic.dev/docs/it/).

---

## Contribuire

Bug report, miglioramenti alla documentazione e pull request sono benvenuti. Prima di iniziare:

1. Apri un'issue per discutere la modifica — usa il [template appropriato][issues].
2. Leggi la [Guida ai Contributi][contributing] — in particolare il setup locale e la checklist **Zenzic Way** (funzioni pure, nessun sottoprocesso, source-first).
3. Ogni PR deve superare `nox -s preflight` (test + lint + typecheck + self-dogfood) e includere le intestazioni REUSE/SPDX sui nuovi file.

Consulta anche il [Codice di Condotta][coc] e la [Policy di Sicurezza][security].

## Citare Zenzic

Il file [`CITATION.cff`][citation-cff] è presente nella root del repository. GitHub lo
visualizza automaticamente — clicca **"Cite this repository"** sulla pagina del repo per
ottenere il riferimento in formato APA o BibTeX.

## Licenza

Apache-2.0 — vedi [LICENSE][license].

---

<p align="center">
  &copy; 2026 <strong>PythonWoods</strong>. Progettato con precisione.<br>
  Based in Italy 🇮🇹 &nbsp;·&nbsp; Committed to the craft of Python development.<br>
  <a href="mailto:dev@pythonwoods.dev">dev@pythonwoods.dev</a>
</p>

<!-- ─── Reference link definitions ──────────────────────────────────────────── -->

[mkdocs]:             https://www.mkdocs.org/
[docusaurus]:         https://docusaurus.io/
[zensical]:           https://zensical.org/
[uv]:                 https://docs.astral.sh/uv/
[docs-it-home]:       https://zenzic.dev/docs/it/usage/
[docs-it-config]:     https://zenzic.dev/docs/it/configuration/
[docs-it-migration]:  https://zenzic.dev/docs/it/guide/migration/
[docs-it-arch]:       https://zenzic.dev/docs/it/architecture/
[docs-it-adapter]:    https://zenzic.dev/docs/it/developers/writing-an-adapter/
[docs-it-cicd]:       https://zenzic.dev/docs/it/ci-cd/
[ci-workflow]:        .github/workflows/ci.yml
[contributing]:       CONTRIBUTING.md
[license]:            LICENSE
[citation-cff]:       CITATION.cff
[coc]:                CODE_OF_CONDUCT.md
[security]:           SECURITY.md
[issues]:             https://github.com/PythonWoods/zenzic/issues
