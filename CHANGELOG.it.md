<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Registro delle modifiche

Tutte le modifiche rilevanti a Zenzic sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Le versioni seguono il [Semantic Versioning](https://semver.org/).

---

## [Non rilasciato]

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

## [0.6.0a2] — 2026-04-13 — Obsidian Glass

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
