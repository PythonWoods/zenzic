<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Registro delle modifiche

Tutte le modifiche rilevanti a Zenzic sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Le versioni seguono il [Semantic Versioning](https://semver.org/).

---

## [Non rilasciato]

## [0.7.0] — 2026-04-22 — Obsidian Maturity (Stable)

> ⚓ Zenzic v0.7.0 segna il consolidamento dell'architettura core e il pieno allineamento con le specifiche ufficiali. Sostituisce v0.6.1.

### ⚠️ BREAKING CHANGE — Plugin MkDocs Rimosso (Direttiva CEO 055)

> **DEPRECAZIONE E RIMOZIONE:** Il plugin MkDocs interno (`zenzic.integrations.mkdocs`) è stato
> rimosso permanentemente. Zenzic è ora una **CLI Sovrana**. Ciò garantisce che ogni utente,
> indipendentemente dal motore utilizzato, benefici della piena potenza della Virtual Site Map (VSM),
> dello Shield (scansione delle credenziali con hardening ZRT-006/007) e del Blood Sentinel
> (rilevamento path-traversal). Le integrazioni engine interne sono ufficialmente sostituite dal
> workflow CLI engine-agnostico.

**Migrazione:** Rimuovi `pip install "zenzic[mkdocs]"` e la voce `plugins: - zenzic` da
`mkdocs.yml`. Aggiungi `zenzic check all` come step CI (prima o dopo `mkdocs build`):

```yaml
# GitHub Actions — sostituisci il gate del plugin MkDocs con:
- run: zenzic check all --strict
```

L'extra opzionale `[mkdocs]` non esiste più. `pip install zenzic` è l'installazione completa.

---

### Refactoring Architetturale — CLI Sovrana e Legge del Core (Direttive 061–068)

#### ⚠️ BREAKING CHANGE — Comando `zenzic plugins` Rimosso (Direttiva CEO 068)

> **RIMOSSO:** Il comando `zenzic plugins` è stato eliminato completamente nella v0.7.0.
> `zenzic inspect` è ora l'**unica** interfaccia di introspezione. Invocare
> `zenzic plugins` produce: `No such command 'plugins'`.
>
> **Migrazione:** Sostituisci ogni script o step CI che chiama `zenzic plugins list`
> con `zenzic inspect capabilities`.

#### Modificato

- **`zenzic plugins` ribrandizzato in `zenzic inspect`; sotto-comando `list` → `capabilities`, poi rimosso (Direttive 061-B, 068 — "The Sovereign Rebranding" / "Decapitazione Totale di 'Plugins'").**
  Il comando di introspezione è ora esclusivamente `zenzic inspect capabilities`.
  `inspect` è il nome canonico; `plugins` è scomparso dalla CLI.

- **`src/zenzic/ui.py` spostato in `src/zenzic/core/ui.py` (Direttiva 062-B — "The Core Law Enforcement").**
  `SentinelReporter` (nel `core/`) importava `zenzic.ui`, violando la legge dei layer per cui il
  core non deve mai guardare verso l'alto. `ObsidianPalette`, `ObsidianUI`, `make_banner`,
  `emoji` e `SUPPORTS_COLOR` risiedono ora canonicamente in `zenzic.core.ui`. Il vecchio percorso
  `zenzic.ui` è mantenuto come stub di compatibilità a una riga
  (`from zenzic.core.ui import *`) per non impattare il codice di terze parti.

- **`src/zenzic/lab.py` spostato in `src/zenzic/cli/_lab.py` (Direttiva 063 — "The Final Relocation").**
  Il comando Lab è orchestrazione CLI, non logica core. Lo spostamento nel package `cli/`
  lo allinea con `_check.py`, `_clean.py` e `_inspect.py` — tutti i comandi vivono nello stesso layer.

- **`run_rule()` spostata da `src/zenzic/rules.py` a `src/zenzic/core/rules.py` (Direttiva 064 — "Bonifica dell'SDK").**
  L'helper di test che esegue una singola regola plugin su una stringa Markdown fa ora parte del
  core engine. `src/zenzic/rules.py` è ridotta a una façade SDK di sei righe che ri-esporta
  `BaseRule`, `CustomRule`, `RuleFinding`, `Severity`, `Violation` e `run_rule` dal `core`.
  Tutti gli statement `from zenzic.rules import ...` esistenti rimangono validi senza modifiche.

#### Rimosso

- **Directory `src/zenzic/integrations/` eliminata fisicamente (Direttiva 066 — "The Physical Purge").**
  Il plugin `zenzic.integrations.mkdocs` era già stato deprecato dalla Direttiva 055 (Breaking
  Change sopra). La directory è ora eliminata dal repository — nessun file fantasma rimane.
  Zenzic è una **CLI Sovrana** pura; non esistono hook engine incorporati.

---

### Supporto Protocollo Docusaurus (Direttiva CEO 117)

#### Aggiunto

- **Schema URL `pathname:///` — Compatibilità Docusaurus (Direttiva CEO 117).**
  Zenzic riconosce ora nativamente lo schema URL `pathname:///` usato in Docusaurus per
  referenziare asset statici (PDF, pagine HTML standalone, download) che vivono al di
  fuori del router React e vengono serviti direttamente dal dev server / CDN.
  - **Consapevolezza del motore:** il bypass è attivo **solo** quando `engine = "docusaurus"`.
    I progetti che usano `mkdocs`, `zensical` o `standalone` riceveranno comunque un errore
    `Z105 ABSOLUTE_PATH` per qualsiasi link `pathname:///`, guidando la migrazione.
  - **Implementazione:** costante `_DOCUSAURUS_SKIP_SCHEMES` aggiunta a `validator.py`;
    il loop di validazione risolve la tupla di skip effettiva per-run da `config.build_context.engine`.
    `pathname:` rimosso dagli `_SKIP_SCHEMES` globali per preservare l'isolamento del motore.
  - **Testato:** `TestPathnameProtocolSupport` in `test_docusaurus_adapter.py` copre
    l'isolamento delle costanti, il no-error Docusaurus e l'asserzione MkDocs Z105.
  - **Documentato:** `docs/reference/engines.mdx` e il mirror IT aggiungono la sezione
    "Schemi URL speciali" nel capitolo Docusaurus.

---

### L'Universalismo Agnostico: Z404 per Tutti i Motori (Direttiva CEO 087)

#### Aggiunto

- **Z404 esteso a MkDocs e Zensical (Direttiva 087).** `check_config_assets()`
  implementato in `_mkdocs.py` (controlla `theme.favicon` + `theme.logo` rispetto a `docs_dir/`)
  e `_zensical.py` (controlla `[project].favicon` + `[project].logo` rispetto a `[project].docs_dir/`).
  I nomi di icone (es. `material/library`) vengono saltati tramite filtro sull'estensione immagine.
  Il blocco Z404 in `cli.py` è stato sostituito con un dispatch multi-motore (`docusaurus` / `mkdocs` / `zensical`).
- **Lab Atti 9 & 10: MkDocs Favicon Guard + Zensical Logo Guard (Direttiva 087).**
  Due nuovi atti Lab con fixture di esempio corrispondenti (`examples/mkdocs-z404/`,
  `examples/zensical-z404/`) dimostrano il rilevamento Z404 su tutti e tre i motori
  supportati. Il validatore dell'atto è stato aggiornato a `0–10`.

#### Modificato

- **Documentazione Z404 riscritta come agnostica rispetto al motore (Direttiva 087).**
  La sezione Z404 di `finding-codes.mdx` (EN + IT) ora copre tutti e tre i motori—
  Docusaurus, MkDocs, Zensical—con tabelle di campi per motore, snippet di rimedio
  per motore e una nota sulla Copertura Adapter aggiornata che conferma il supporto universale.

---

### Il Passaggio Obsidian Mirror: Lab, Shield & Allineamento Docs (Direttive 082–086)

#### Aggiunto

- **Z404 CONFIG_ASSET_MISSING (Direttiva 085).** L'adapter Docusaurus analizza ora
  staticamente `docusaurus.config.ts` e verifica che ogni percorso `favicon:` e `image:`
  (OG social card) risolva in un file reale all'interno di `static/`. Implementato come
  `check_config_assets()` in `_docusaurus.py` — puro regex, zero subprocess. Codice
  registrato in `codes.py`; collegato tramite `_AllCheckResults.config_asset_issues` in
  `cli.py`. Severità: `warning` (promuovibile a Exit 1 via `--strict`).
- **Lab Obsidian Seal (Direttiva 086).** Ogni esecuzione `zenzic lab <N>` si chiude
  ora con un pannello **Obsidian Seal** dedicato (bordo indigo, colori Sentinel Palette)
  che mostra il conteggio file, tempo trascorso, throughput in file/s e un verdetto
  pass/fail per atto. I sommari di esecuzione completa mostrano un Obsidian Seal
  aggregato con throughput totale tra tutti gli atti.
- **Campi di throughput nel Lab (Direttiva 086).** `_ActResult` aggiunge le proprietà
  `docs_count`, `assets_count`, `total_files` e `throughput`. La tabella di sommario
  completa include ora una colonna **Files** e una colonna **files/s**.
- **Copertura Dependabot GitHub Actions (Direttiva 085).** `zenzic-doc/.github/dependabot.yml`
  esteso con un ecosystem `github-actions` e due dependency group (`docusaurus-all`,
  `react-ecosystem`) per ridurre il rumore di PR.
- **`scripts/bump-version.sh` + recipe `just bump` per zenzic-doc (Direttiva 083).**
  Script di bump automatizzato che copre tutte e sei le stringhe di versione hardcoded
  nel portale doc: `docusaurus.config.ts`, `Quickstart.tsx`, `Hero.tsx`,
  `src/pages/index.tsx` (LD+JSON `softwareVersion`), `i18n/en/code.json`,
  `i18n/it/code.json`.
- **Workflow GitHub Release per zenzic-doc (Direttiva 082).** Aggiunto
  `.github/workflows/release.yml` — si attiva sui tag `v*.*.*`, costruisce il sito
  Docusaurus e crea un GitHub Release con l'artefatto di build allegato.

#### Modificato

- **UI del Lab ricostruita con Sentinel Palette (Direttiva 086).** `_print_summary`
  usa ora lo stile header `INDIGO`, colonne dim `SLATE` e il titolo branded
  `⬡ ZENZIC LAB — Full Run Summary` al posto del semplice `Lab Summary`.
- **Pannelli titolo atto ora con bordo Indigo (Direttiva 082).** Il Panel per-atto
  usa `border_style="#4f46e5"` per corrispondere alla Sentinel Palette — identico
  all'output live di `SentinelReporter`.
- **Z404 documentato su tutte le superfici (Direttiva 086).** `finding-codes.mdx`
  (EN + IT) contiene ora una sezione completa `Config Asset Integrity / Integrità
  Asset di Configurazione` con spiegazione tecnica, tabella campi, motivazione
  severità, passi di rimedio e nota sulla copertura adapter. `README.md` e
  `README.it.md` includono entrambi una riga `Config asset integrity` che referenzia
  `Z404` nella Capability Matrix.
- **Dipendenze zenzic-doc aggiornate (Direttiva 086).** `package.json` aggiornato:
  `tailwindcss` 4.2.2 → 4.2.4 · `@tailwindcss/postcss` 4.2.2 → 4.2.4 ·
  `autoprefixer` 10.4.27 → 10.5.0 · `postcss` 8.5.9 → 8.5.10 ·
  `typescript` 6.0.2 → 6.0.3. Build di produzione confermata verde.

#### Corretto

- **Favicon 404 zenzic-doc (Direttiva 084).** `docusaurus.config.ts` dichiarava
  `favicon: 'img/favicon.ico'` — un percorso inesistente in `static/`. Corretto in
  `'assets/favicon/png/zenzic-icon-32.png'` (file reale). Questo era esattamente
  il tipo di guasto infrastrutturale che Z404 è stato costruito per intercettare.
- **Completezza meta tag OG/Twitter (Direttiva 084).** Tre meta tag erano assenti:
  `twitter:image:alt`, `og:image:width` (1200), `og:image:height` (630). Aggiunti
  a `docusaurus.config.ts`. Asset social card confermato a 1200×630 px, 33 KB.
- **Release GitHub v0.6.1 marcata come superseded (Direttiva 085).** I titoli delle
  GitHub Release v0.6.1 di entrambi i repo (core e `zenzic-doc`) aggiornati a
  `[SUPERSEDED by v0.6.2]` con un callout `[!WARNING]` preposto alle note di rilascio.

---

### Passaggio Obsidian Integrity: Hardening UX e Audit della Verità (Direttive 076–079)

#### Aggiunto

- **Motore di Suggerimento Proattivo Z104 (Direttiva 077).** Quando un target di link
  non viene trovato (`Z104 FILE_NOT_FOUND`), Zenzic calcola ora il file più simile
  nel VSM usando `difflib.get_close_matches` (cutoff 0.6) e aggiunge un suggerimento
  `💡 Intendevi: '...'?` al messaggio di errore. Nessuna I/O su disco nel hot path —
  il diff viene eseguito sulla mappa `md_contents` in memoria costruita nel Pass 1.
- **Invariante del Perimetro README (Direttiva CEO 076).** Il file `zenzic.toml` del
  repository principale contiene ora un esplicito commento `⚠ PERIMETER INVARIANT`
  che documenta che `docs_dir = "."` è un invariante di sicurezza che mantiene
  `README.md` e `README.it.md` all'interno del perimetro di validazione. Modificare
  `docs_dir` senza re-aggiungere questi file creerebbe una falsa zona di sicurezza.

#### Modificato

- **Audit della Verità Standalone Mode (Direttiva 078).** Ogni descrizione
  user-facing della Standalone Mode dichiara ora esplicitamente che il rilevamento
  degli orfani (`Z402`) è disabilitato perché non esiste un contratto di navigazione.
  Sostituito "integrità strutturale" con "integrità dei file" per riflettere la
  capacità reale. `README.md`, `README.it.md` e tutti i file degli esempi aggiornati.
- **Engineering Ledger sostituisce Design Philosophy.** La sezione `## Design Philosophy`
  di `README.md` e `README.it.md` è stata ricostruita come HTML-table Engineering Ledger
  (tre contratti non negoziabili: Zero Assumptions, Subprocess-Free, Deterministic
  Compliance) con frammenti di codice reali come evidenza.
- **Purga Vanilla — esempi.** Tutti i file esempio `zenzic.toml` che usavano
  `engine = "vanilla"` ora usano `engine = "standalone"`. Interessati:
  `examples/vanilla/`, `examples/standalone-markdown/`, `examples/custom-dir-target/`,
  `examples/single-file-target/`. Il contenuto Markdown inline e i README all'interno
  di questi esempi sono stati riscritti di conseguenza.
- **Riferimenti di versione.** `pyproject.toml`, `src/zenzic/__init__.py` e
  `CITATION.cff` aggiornati da `0.6.1` a `0.6.2`. Data di rilascio: 2026-04-22.

#### Corretto

- **Tightening Sentinel Mesh — Link Diátaxis Obsoleti (Direttiva 079).** L'audit
  forense ha rivelato che `README.md` conteneva tre target di link diventati obsoleti
  dopo la ristrutturazione della documentazione Diátaxis:
  - `https://zenzic.dev/docs/usage/badges/` → `https://zenzic.dev/docs/how-to/add-badges/`
  - `https://zenzic.dev/docs/guides/ci-cd/` → `https://zenzic.dev/docs/how-to/configure-ci-cd/`
  - `https://zenzic.dev/docs/internals/architecture-overview/` → `https://zenzic.dev/docs/explanation/architecture/`
  Stesse tre corrette in `README.it.md` (prefisso `/it/docs/`).
- **Esclusione Blanket zenzic.dev Rimossa (Direttiva 079).** La voce `excluded_external_urls`
  `"https://zenzic.dev/"` era una soluzione temporanea aggiunta quando il sito di
  documentazione non era ancora distribuito. Era diventata un punto cieco permanente,
  silenziando la validazione `--strict` di tutti i link al portale anche mentre si
  deterioravano. La voce è stata rimossa. Un flag runtime
  (`--exclude-url https://zenzic.dev/`) è la valvola di sfogo corretta per i runner
  CI offline invece di un bypass nel file di configurazione.
- **README Developer zenzic-doc.** Prerequisito Node.js corretto da 20 a 24.
  Il testo della matrice CI aggiornato in "Node 22 e 24". La rotta i18n obsoleta
  `/docs/intro` sostituita con la corretta `/docs/` (indice radice) dopo la
  ristrutturazione Diátaxis.

---

## [0.6.1] — 2026-04-19 — Obsidian Glass [SUPERSEDED]

> ⚠ **[SUPERSEDED dalla v0.7.0]** — La versione 0.6.1 è deprecata a causa di problemi di allineamento con le specifiche Docusaurus e terminologia legacy. Tutti gli utenti devono aggiornare alla v0.7.0 "Obsidian Maturity".

### Modifiche che rompono la compatibilità

- **Standalone Engine sostituisce Vanilla (Direttiva 037).** `VanillaAdapter` e la
  keyword `engine = "vanilla"` sono stati rimossi. Tutti i progetti devono migrare a
  `engine = "standalone"`. Qualsiasi `zenzic.toml` che usa ancora `engine = "vanilla"`
  genera una `ConfigurationError [Z000]` all'avvio con un messaggio di migrazione chiaro.
  *Migrazione:* sostituire `engine = "vanilla"` con `engine = "standalone"` nel proprio
  `zenzic.toml` o nel blocco `[tool.zenzic]`.

### Aggiunto

- **Codici Finding (Zxxx) (Direttiva 036).** Ogni diagnostica emessa da Zenzic ora
  porta un identificatore univoco leggibile dalla macchina (es. `Z101 LINK_BROKEN`,
  `Z201 SHIELD_SECRET`, `Z401 MISSING_DIRECTORY_INDEX`). Il registro completo si trova
  in `src/zenzic/core/codes.py` — unica fonte di verità per tutti i codici.
- **Menu interattivo del Lab.** `zenzic lab` senza argomenti mostra ora l'indice degli
  atti per scegliere quale scenario esplorare. Eseguire `zenzic lab <N>` per avviare
  un atto specifico (0–8). L'opzione `--act` è stata sostituita da un argomento
  posizionale.
- **Identità Standalone Mode.** `StandaloneAdapter` è il motore no-op canonico per
  progetti Markdown puri. `zenzic init` ora scrive `engine = "standalone"` quando non
  viene rilevata nessuna configurazione di framework.

- **Flag `--offline` per la risoluzione URL Flat.** Disponibile su `check all`,
  `check links` e `check orphans`. Forza tutti gli adapter a produrre URL `.html`
  (es. `guida/install.md` → `/guida/install.html`) invece di slug in stile directory.
- **Supporto multi-versione Docusaurus v3.** `DocusaurusAdapter` ora identifica
  `versions.json`, `versioned_docs/` e le traduzioni versionate.
- **Proxy Trasparente Zensical.** Se viene dichiarato `engine = "zensical"` ma
  `zensical.toml` è assente, l'adapter crea automaticamente un ponte con il tuo
  `mkdocs.yml` esistente.
- **Ghost Routing consapevole delle versioni.** I percorsi della documentazione
  versionata sono automaticamente classificati come `REACHABLE`.
- **Risoluzione Alias @site/.** Aggiunto il supporto per l'alias di percorso `@site/`
  in `DocusaurusAdapter`, permettendo la corretta risoluzione dei link relativi al progetto.
- **Integrità dell'Indice di Directory.** Nuovo metodo `provides_index(path)` nel protocollo
  `BaseAdapter` per il rilevamento engine-aware delle directory prive di landing page.
  Il finding `MISSING_DIRECTORY_INDEX` (severità: `info`), emesso da `zenzic check all`,
  avvisa di ogni sottodirectory che contiene sorgenti Markdown ma nessun indice fornito
  dall'engine — prevenendo i 404 gerarchici prima del deploy.
- **Notifiche nel Banner Sentinel.** Nuovi messaggi di stato per l'attivazione della
  **Modalità Offline** e della **Modalità Proxy**.

### Corretto

- **Audit dei Guardiani: Allineamento Specifiche Ufficiali.**
  - **Versioning Docusaurus:** Corretta la mappatura URL della versione "latest" (prima voce
    in `versions.json`) per escludere il prefisso dell'etichetta di versione, allineandosi
    al comportamento ufficiale di Docusaurus. In precedenza ogni file versionato riceveva
    un prefisso `/versione/`, generando falsi positivi per tutte le pagine della versione latest.
  - **Slug Docusaurus:** Gli slug frontmatter assoluti (es. `slug: /mio-percorso`) sono
    ora correttamente preceduti dalla `routeBasePath` (es. `/docs/mio-percorso/`),
    allineandosi alla specifica Docusaurus `normalizeUrl([versionMetadata.path, docSlug])`.
  - **Collasso Intelligente dei File:** La logica `isCategoryIndex` ora rispecchia
    esattamente Docusaurus: `README.md`, `INDEX.md` (case-insensitive) e
    `{NomeCartella}/{NomeCartella}.md` collassano nell'URL della directory genitore,
    prevenendo falsi positivi per le convenzioni valide di landing page di categoria.
  - **Risoluzione Alias `@site/`:** `InMemoryPathResolver` ora risolve i link `@site/`
    rispetto al corretto confine `repo_root` invece di sfuggire tramite `../`,
    eliminando errori `PathTraversal` spuri per tutti i link relativi al progetto Docusaurus.
- **Integrità dei Metadati.** Corretto l'allineamento delle stringhe di versione in
  `CITATION.cff` e `pyproject.toml`.
- **Default routeBasePath Docusaurus.** Ripristinato `docs` come prefisso URL predefinito
  per i progetti Docusaurus per corrispondere al comportamento ufficiale dell'engine.

- **Parità Documentale Bilingue.** Copertura completa della documentazione EN/IT per
  tutte le feature della v0.6.1 nelle guide Architettura, Motori e Comandi.

## [0.6.1rc2] — 2026-04-16 — Obsidian Bastion (Hardened)

### SICUREZZA: Risultati Operation Obsidian Stress

- **Shield: bypass tramite caratteri Unicode di formato (ZRT-006).** Caratteri
  Unicode invisibili (ZWJ U+200D, ZWNJ U+200C, ZWSP U+200B) inseriti all'interno
  di un token potevano eludere il pattern matching. Il normalizzatore ora rimuove
  tutti i caratteri Unicode di categoria Cf prima della scansione.
- **Shield: bypass tramite offuscamento con entità HTML (ZRT-006).** I riferimenti
  a caratteri HTML (`&#65;&#75;` → `AK`) potevano nascondere i prefissi delle
  credenziali. Il normalizzatore ora decodifica le entità `&#NNN;`/`&#xHH;`
  tramite `html.unescape()`.
- **Shield: bypass tramite interleaving di commenti (ZRT-007).** Commenti HTML
  (`<!-- -->`) e commenti MDX (`{/* */}`) inseriti all'interno di un token
  potevano interrompere il pattern matching. Il normalizzatore ora rimuove
  entrambe le forme di commento.
- **Shield: rilevamento token spezzati tra righe (ZRT-007).** Aggiunto un buffer
  lookback di 1 riga tramite `scan_lines_with_lookback()` per rilevare segreti
  suddivisi su due righe consecutive (es. scalari YAML folded). I duplicati sono
  soppressi tramite il set di tipi già rilevati sulla riga precedente.

### Aggiunto

- **`--format json` sui comandi di controllo singoli.** `check links`, `check orphans`,
  `check snippets`, `check references` e `check assets` accettano ora `--format json`
  con uno schema uniforme `findings`/`summary`. I codici di uscita sono preservati in
  modalità JSON.
  ([#55](https://github.com/PythonWoods/zenzic/pull/55) — contributo di [@xyaz1313](https://github.com/xyaz1313))
- **Shield: rilevamento GitLab Personal Access Token.** Lo scanner di credenziali
  rileva ora i token `glpat-` (9 famiglie di credenziali in totale).
  ([#57](https://github.com/PythonWoods/zenzic/pull/57) — contributo di [@gtanb4l](https://github.com/gtanb4l))

### Corretto

- **Asimmetria exit-code JSON in `check orphans` e `check assets`.** Entrambi i comandi
  ora distinguono la severità `error` da `warning` prima di decidere il codice di uscita,
  in modo coerente con `check references` e `check snippets`. In precedenza, qualsiasi
  finding (inclusi i warning) attivava Exit 1 in modalità JSON.

## [0.6.1rc1] — 2026-04-15 — Obsidian Bastion

### Breaking Changes

- **Rimosso il comando `zenzic serve`.** Zenzic è ora 100% privo di sotto-processi,
  concentrandosi esclusivamente sull'analisi statica del sorgente. Per visualizzare
  la documentazione, usa il comando nativo del tuo engine: `mkdocs serve`,
  `docusaurus start`, o `zensical serve`. Questa rimozione elimina l'unica eccezione
  al Pillar 2 (Nessun Sottoprocesso) e completa la purezza architetturale del
  framework.
- **Plugin MkDocs spostato in `zenzic.integrations.mkdocs`** — In precedenza in
  `zenzic.plugin`. Aggiornare `mkdocs.yml` e reinstallare il pacchetto;
  il plugin viene ora auto-scoperto tramite l'entry point `mkdocs.plugins`.
  Richiede `pip install "zenzic[mkdocs]"`.

### Aggiunto

- **Layered Exclusion Manager** — Nuova gerarchia di esclusione a 4 livelli
  (Guardrail di Sistema > Inclusioni Forzate + VCS > Config > CLI). Parser
  gitignore pure-Python (`VCSIgnoreParser`) con pattern regex pre-compilati.
  Nuovi campi di configurazione: `respect_vcs_ignore`, `included_dirs`,
  `included_file_patterns`.
- **Discovery Universale** — Zero chiamate `rglob` nel codebase. Tutta
  l'iterazione sui file passa attraverso `walk_files` / `iter_markdown_sources`
  da `discovery.py`. Parametro `exclusion_manager` obbligatorio su tutti i punti
  d'ingresso di scanner e validator — nessun Optional, nessun fallback.
- **Flag CLI di Esclusione** — `--exclude-dir` e `--include-dir` ripetibili su
  tutti i comandi check, `score` e `diff`.
- **Cache Adapter** — Cache a livello di modulo con chiave `(engine, docs_root,
  repo_root)`. Singola istanziazione dell'adapter per sessione CLI.
- **F4-1 Protezione Jailbreak** — `_validate_docs_root()` rifiuta percorsi
  `docs_dir` che escono dalla radice del repository (Sentinella di Sangue
  Exit 3).
- **F2-1 Hardening Shield** — Le righe che superano 1 MiB vengono troncate
  silenziosamente prima del matching regex per prevenire ReDoS.
- **Namespace `zenzic.integrations`** — Plugin MkDocs spostato da `zenzic.plugin`
  a `zenzic.integrations.mkdocs`. Registrato come entry point ufficiale
  `mkdocs.plugins`. Il core è ora privo di import specifici per engine.
  Installa l'extra: `pip install "zenzic[mkdocs]"`.

### Modificato

- **BREAKING (Alpha):** il parametro `exclusion_manager` è ora obbligatorio su
  `walk_files`, `iter_markdown_sources`, `generate_virtual_site_map`,
  `check_nav_contract`, e tutte le funzioni dello scanner. Nessun default
  `None` retrocompatibile.

## [0.6.0a2] — 2026-04-13 — Obsidian Glass (Alpha 2)

### Aggiunto

- **Supporto Glob Pattern per `excluded_assets`** — Le voci di `excluded_assets`
  sono ora interpretate tramite `fnmatch` (sintassi glob: `*`, `?`, `[]`, `**`).
  I percorsi letterali continuano a funzionare come prima.  Questo allinea
  `excluded_assets` con `excluded_build_artifacts` e `excluded_file_patterns`,
  dando all'intera API di esclusione un linguaggio unico e coerente.
- **`base_url` in `[build_context]`** — Nuovo campo opzionale che permette di
  dichiarare esplicitamente la base URL del sito.  Quando impostato, l'adapter
  Docusaurus salta l'estrazione statica da `docusaurus.config.ts`, eliminando
  il warning di fallback "dynamic patterns" per le configurazioni che usano
  `async`, `import()` o `require()`.
- **Routing Guidato dai Metadati** — Nuovo dataclass `RouteMetadata` e metodo
  `get_route_info()` nel protocollo `BaseAdapter`. Tutti e quattro gli adapter
  (Vanilla, MkDocs, Docusaurus, Zensical) implementano la nuova API.
  `build_vsm()` preferisce il percorso metadata-driven quando disponibile,
  con fallback alla coppia legacy `map_url()` + `classify_route()` per gli
  adapter di terze parti.
- **Estrazione Centralizzata del Frontmatter** — Utility engine-agnostiche in
  `_utils.py`: `extract_frontmatter_slug()`, `extract_frontmatter_draft()`,
  `extract_frontmatter_unlisted()`, `extract_frontmatter_tags()`, e
  `build_metadata_cache()` per il harvesting eager single-pass del frontmatter
  YAML su tutti i file Markdown.
- **Dataclass `FileMetadata`** — Rappresentazione strutturata del frontmatter
  per file: `slug`, `draft`, `unlisted`, `tags`.
- **Shield IO Middleware** — `safe_read_line()` scansiona ogni riga del
  frontmatter attraverso lo Shield prima che qualsiasi parser la veda.
  L'eccezione `ShieldViolation` fornisce un errore strutturato con payload
  `SecurityFinding`.
- **Test di Conformità del Protocollo** — 43 nuovi test in
  `test_protocol_evolution.py`: validazione `runtime_checkable` del protocollo,
  invarianti `RouteMetadata`, test di contratto `get_route_info()` per tutti
  gli adapter, stress test Hypothesis con percorsi estremi, sicurezza pickle,
  estrazione frontmatter, middleware Shield, e operazione senza warning di
  VanillaAdapter.

### Modificato

- **BREAKING: `excluded_assets` usa fnmatch** — Tutte le voci sono ora
  interpretate come pattern glob.  I percorsi letterali continuano a
  funzionare (sono pattern validi), ma pattern come `**/_category_.json` o
  `assets/brand/*` sono ora supportati nativamente.  L'implementazione
  precedente basata sulla sottrazione di insiemi è stata rimossa.

### Corretto

- **Warning "dynamic patterns" di Docusaurus emesso due volte** — Quando
  `base_url` è dichiarato in `zenzic.toml`, l'adapter non chiama più
  `_extract_base_url()`, sopprimendo completamente il warning duplicato.

## [0.6.0a1] — 2026-04-12 — Obsidian Glass

> **Alpha 1 della serie v0.6.** Zenzic evolve da un linter MkDocs-aware a un
> **Analizzatore di Piattaforme Documentali**. Questo rilascio introduce
> l'adapter per il motore Docusaurus v3 — il primo adapter non-MkDocs/Zensical —
> e segna l'inizio della strategia di migrazione Obsidian Bridge.

### Aggiunto

- **Adapter Docusaurus v3 (Full Spec)**: Nuovo adapter engine-agnostico con
  parsing statico AST-like per `docusaurus.config.ts/js`. Adapter puro Python
  conforme al protocollo `BaseAdapter`. Gestisce file sorgente `.md` e `.mdx`,
  modalità sidebar auto-generata (tutti i file `REACHABLE`), geografia i18n
  Docusaurus (`i18n/{locale}/docusaurus-plugin-content-docs/current/`),
  rilevamento Ghost Route per le pagine indice delle locale, ed esclusione di
  file/directory con prefisso `_` (`IGNORED`). Registrato come adapter built-in
  con entry-point `docusaurus = "zenzic.core.adapters:DocusaurusAdapter"`.
  - **Estrazione `baseUrl`**: Parser statico multi-pattern che supporta
    `export default`, `module.exports` e pattern di assegnazione `const`/`let`.
    I commenti JS/TS vengono rimossi prima dell'estrazione. Nessun
    sottoprocesso Node.js (conformità Pilastro 2).
  - **Estrazione `routeBasePath`**: Rilevamento automatico di `routeBasePath`
    dai preset e blocchi plugin Docusaurus (es.
    `@docusaurus/preset-classic`). Supporta stringa vuota (docs alla radice
    del sito).
  - **Supporto Slug**: Gli override `slug:` nel frontmatter Markdown sono ora
    correttamente mappati nella VSM. Gli slug assoluti (`/custom-path`)
    sostituiscono l'URL completo; gli slug relativi sostituiscono l'ultimo
    segmento del percorso.
  - **Rilevamento Config Dinamica**: Rilevamento intelligente di config
    creator asincroni, chiamate `import()`/`require()` e export basati su
    funzione. Fallback a `baseUrl='/'` con warning utente — mai crash, mai
    assunzioni.
- **Hook factory `from_repo()`** per `DocusaurusAdapter`: Scopre automaticamente
  `docusaurus.config.ts` o `.js` e costruisce l'adapter con il `baseUrl` e
  `routeBasePath` corretti.
- **Topologia i18n Migliorata**: Mappatura nativa per la struttura delle
  directory `i18n/` di Docusaurus e risoluzione delle rotte specifiche per
  locale.

### Test

- **`tests/test_docusaurus_adapter.py` — 65 test in 12 classi di test.**
  Copertura completa del refactor dell'adapter Docusaurus: parsing config
  (CFG-01..07), estrazione `routeBasePath` (RBP-01), supporto slug
  frontmatter (SLUG-01), rilevamento config dinamica, rimozione commenti,
  integrazione `from_repo()`, regressione URL mapping e classificazione rotte.

## [0.5.0a5] — 2026-04-09 — Il Codex Sentinel

> **Rilascio Alpha 5.** Revisione del linguaggio visivo: Guida di Stile Sentinel,
> refactoring delle griglie a schede, normalizzazione di admonition e icone,
> 102 anchor ID strategici, effetti hover CSS per le schede, e pipeline di
> generazione screenshot completamente automatizzata. Rimosso template PDF legacy.
> Tracking changelog stabilizzato. Test E2E CLI di sicurezza aggiunti; bug
> `--exit-zero` corretto (exit 2/3 ora incondizionatamente non sopprimibili,
> conforme al contratto documentato).

### Aggiunto

- **Guida di Stile Sentinel** — riferimento canonico del linguaggio visivo
  (`docs/internal/style-guide-sentinel.md` + specchio italiano) che definisce
  griglie a schede, tipi di admonition, vocabolario icone e convenzioni
  anchor-ID.

- **Generazione screenshot automatizzata — SVG Blood & Circular.**
  `scripts/generate_docs_assets.py` ora genera tutti e cinque gli screenshot
  della documentazione. Gli SVG Blood Sentinel e Circular Link erano asset
  statici realizzati a mano; ora sono generati deterministicamente da fixture
  sandbox dedicate.

- **Tracking bumpversion CHANGELOG.it.md.** Il changelog italiano aggiunto a
  `[tool.bumpversion.files]` in `pyproject.toml`, garantendo la sincronizzazione
  delle intestazioni di versione durante le esecuzioni di `bump-my-version`.

### Corretto

- **`--exit-zero` non sopprime più gli exit di sicurezza in `check all`.**
  Gli exit code 2 (Shield breach) e 3 (Blood Sentinel) erano protetti da
  `not effective_exit_zero` in `check all`, in contraddizione con il contratto
  documentato. Le guardie sono state rimosse — exit 2 e 3 sono ora
  incondizionali.

### Test

- **`tests/test_cli_e2e.py` — 8 test E2E CLI di sicurezza.**
  Test full-pipeline (nessun mock) che verificano il contratto exit-code:
  Blood Sentinel (Exit 3), Shield Breach (Exit 2), `--exit-zero` non
  sopprime exit di sicurezza, priorità Exit 3 > Exit 2.
  Chiude gap: `docs/internal/arch_gaps.md` § "Security Pipeline Coverage".

### Modificato

- **Refactoring Griglie a Schede.** Pagine documentazione standardizzate con
  sintassi griglia Material for MkDocs.

- **Normalizzazione Admonition.** Stili callout ad-hoc sostituiti con tipi
  canonici (`tip`, `warning`, `info`, `example`).

- **Normalizzazione Icone.** Icone non-Material rimosse; standardizzate al set
  `:material-*:`.

- **102 Anchor ID Strategici** posizionati in 70 file di documentazione per
  deep-linking stabile.

- **Override CSS Schede.** Effetti hover e stile schede coerente via
  `docs/assets/stylesheets/`.

### Rimosso

- **`docs/assets/pdf_cover.html.j2`** — template Jinja2 copertina PDF legacy.
  Artefatto orfano senza riferimenti nella pipeline di build; rimosso per ridurre
  la superficie di manutenzione.

---

## [0.5.0a4] — 2026-04-08 — Il Sentinel Indurito: Sicurezza & Integrità

> **Rilascio Alpha 4.** Quattro vulnerabilità confermate chiuse (ZRT-001–004), tre
> nuovi pilastri di hardening aggiunti (Sentinella di Sangue, Integrità del Grafo,
> Scudo Esadecimale), e piena parità documentale bilingue raggiunta. In attesa di
> revisione manuale prima della promozione a Release Candidate.
>
> Branch: `fix/sentinel-hardening-v0.5.0a4`

### Aggiunto

- **Integrità del grafo — rilevamento link circolari.** Zenzic ora pre-calcola
  un registro dei cicli (Fase 1.5) tramite ricerca depth-first iterativa (Θ(V+E))
  sul grafo dei link interni risolti. Ogni link il cui target appartiene a un ciclo
  emette un finding `CIRCULAR_LINK` con severità `info`. I link di navigazione
  reciproca (A ↔ B) sono una struttura valida della documentazione; il finding è
  puramente informativo — non influisce mai sugli exit code in modalità normale o
  `--strict`. O(1) per query in Phase 2. Le Ghost Route (URL canonici generati da
  plugin senza file sorgente fisico) sono correttamente escluse dal grafo dei cicli.

- **`INTERNAL_GLOSSARY.toml`** — registro bilingue EN↔IT dei termini tecnici
  (15 voci) per un vocabolario coerente tra documentazione inglese e italiana. Copre
  i concetti principali: Porto Sicuro, Rotta Fantasma, Mappa del Sito Virtuale,
  Motore a Due Passaggi, Scudo, Sentinella di Sangue e altri. Mantenuto da S-0.
  Tutti i termini con `stable = true` richiedono un ADR prima della rinomina.

- **Parità documentale bilingue.** `docs/checks.md` e `docs/it/checks.md` aggiornati
  con le sezioni Sentinella di Sangue, Link Circolari e Scudo Esadecimale.
  `CHANGELOG.it.md` creato. Piena parità EN↔IT applicata per il Protocollo di
  Parità Bilingue.

### ⚠️ Sicurezza

- **Sentinella di Sangue — classificazione degli attraversamenti di percorso (Exit Code 3).**
  `check links` e `check all` ora classificano i finding di path-traversal per
  intenzione. Un href che esce da `docs/` e si risolve in una directory di sistema
  del SO (`/etc/`, `/root/`, `/var/`, `/proc/`, `/sys/`, `/usr/`) viene classificato
  come `PATH_TRAVERSAL_SUSPICIOUS` con severità `security_incident` e attiva
  l'**Exit Code 3** — un nuovo exit code dedicato riservato alle sonde del sistema
  host. L'Exit 3 ha priorità sull'Exit 2 (violazione credenziali) e non viene mai
  soppresso da `--exit-zero`. Gli attraversamenti fuori confine ordinari (es.
  `../../repo-adiacente/`) restano `PATH_TRAVERSAL` con severità `error` (Exit Code 1).

- **Scudo Esadecimale — rilevamento di payload hex-encoded.**
  Un nuovo pattern built-in dello Shield, `hex-encoded-payload`, rileva sequenze di
  tre o più escape hex `\xNN` consecutive (`(?:\\x[0-9a-fA-F]{2}){3,}`). La soglia
  `{3,}` evita falsi positivi sulle singole escape hex comuni nella documentazione
  delle regex. I finding escono con codice 2 (Shield, non sopprimibile) e si
  applicano a tutti i flussi di contenuto inclusi i blocchi di codice delimitati.

- **[ZRT-001] Shield Blind Spot — Bypass YAML Frontmatter (CRITICO).**
  `_skip_frontmatter()` veniva usato come sorgente di righe dello Shield,
  scartando silenziosamente ogni riga nel blocco YAML `---` del file prima che
  il motore regex girasse. Qualsiasi coppia chiave-valore (`aws_key: AKIA…`,
  `github_token: ghp_…`) era invisibile allo Shield.
  **Fix:** Il flusso Shield ora usa `enumerate(fh, start=1)` grezzo — ogni byte
  del file viene scansionato. Il flusso contenuto usa ancora `_iter_content_lines()`
  con salto del frontmatter per evitare falsi positivi da valori di metadati.
  Architettura **Dual-Stream**.

- **[ZRT-002] ReDoS + Deadlock ProcessPoolExecutor (ALTO).**
  Un pattern `[[custom_rules]]` come `^(a+)+$` superava il controllo
  `_assert_pickleable()` e veniva distribuito ai worker process senza timeout.
  **Due difese aggiunte:**
  — *Canary (prevenzione):* `_assert_regex_canary()` stress-testa ogni pattern
    `CustomRule` sotto un watchdog `signal.SIGALRM` di 100 ms. I pattern ReDoS
    sollevano `PluginContractError` prima della prima scansione.
  — *Timeout (contenimento):* `ProcessPoolExecutor.map()` sostituito con
    `submit()` + `future.result(timeout=30)`.

- **[ZRT-003] Bypass Shield Split-Token — Offuscamento Tabelle Markdown (MEDIO).**
  Il separatore `|` delle tabelle Markdown spezzava i token segreti su più celle.
  **Fix:** Le righe di tabella vengono de-pipe prima della scansione Shield.

- **[ZRT-004] Injection Path Traversal nei Link Reference (BASSO).**
  Link reference con href malevoli potevano sfuggire alla sandbox `docs/`.
  **Fix:** La validazione PATH_TRAVERSAL applicata ai link reference come ai link
  inline.

### Interno

- **Pipeline CI/CD corretta per Node.js 24.**
  `cloudflare/wrangler-action@v3` invoca `npx wrangler` senza il flag `--yes`;
  npm 10+ sui runner GitHub con Node.js 24 blocca i prompt non interattivi,
  causando il fallimento del deploy su Cloudflare Pages. Fix: pre-installazione
  globale di `wrangler@latest` prima dell'esecuzione dell'action, così npx trova
  il binario nel PATH senza scaricarlo. `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true`
  silenzia il warning di deprecazione di Node.js 20 prima della migrazione forzata
  di giugno 2026. Tracciato in `arch_gaps.md`.
  Branch: `fix/v050a4-infra-alignment`.

## [0.5.0a3] — 2026-03-28 — Il Sentinel: Plugin, Regole Adattive, Hooks Pre-commit

> Branch: `feat/sentinel-v0.5.0a3`

### Aggiunto

- **Sistema Plugin** — `[[custom_rules]]` in `zenzic.toml` per regole regex
  personalizzate. `PluginContractError` per la validazione contratto a boot.
- **Regex Canary** — watchdog SIGALRM 100 ms per backtracking catastrofico.
- **Hooks Pre-commit** — configurazione ufficiale per pipeline CI.
- **UI Sentinel** — palette colori, reporter a griglia, output Sentinel rinnovato.

## [0.5.0a1] — 2026-03-15 — Il Sentinel: Motore Adattivo delle Regole

> Branch: `feat/sentinel-v0.5.0a1`

### Aggiunto

- **AdaptiveRuleEngine** — motore di analisi estensibile con Phase 3.
- **Hybrid Adaptive Engine** — integrazione MkDocs + motore adattivo.
- **Pannelli Sentinel** — output strutturato per tutti i controlli.

## [0.4.0] — 2026-03-01 — Il Grande Disaccoppiamento

> Branch: `feat/engine-decoupling`

### Aggiunto

- **Factory entry-point dinamica** — `--engine` CLI flag; protocollo
  `has_engine_config`.
- **InMemoryPathResolver** — resolver agnostico rispetto al motore.
- **Tower of Babel Guard** — fallback i18n per ancora mancante nella locale.

## [0.3.0] — 2026-02-15 — Two-Pass Pipeline

### Aggiunto

- **Two-Pass Engine** — Phase 1 (I/O parallelo) + Phase 2 (validazione O(1)).
- **Virtual Site Map (VSM)** — proiezione logica del sito renderizzato.
- **Shield** — rilevamento segreti, Stream Dual, exit code 2.
- **Validazione anchor cross-lingua** — Tower of Babel Guard.
