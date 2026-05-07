<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Registro delle modifiche

Tutte le modifiche rilevanti a Zenzic sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Le versioni seguono il [Semantic Versioning](https://semver.org/).

---

> **Cronologia di sviluppo (v0.1.0 – v0.6.x):** Consultare l'[Archivio Changelog](CHANGELOG.it.archive.md).

## [0.7.0] — 2026-05-XX (Target) — Quartz Maturity (Stable)

> **Documentazione precedente:** Le versioni precedenti a v0.7.0 sono ufficialmente deprecate
> e non seguono l'attuale architettura Diátaxis. Per riferimento storico, vedere la
> [Release v0.6.1 su GitHub](https://github.com/PythonWoods/zenzic/releases/tag/v0.6.1).
> La fonte autorevole è [zenzic.dev](https://zenzic.dev).

### 💎 Era del Quarzo (Release Iniziale)

Questa release segna l'Anno Zero dell'ecosistema Zenzic, stabilendo un nuovo standard di
maturità deterministica e integrità formale. Il codebase raggiunge la maturità strutturale:
1.342+ test, copertura branch >80%, e una pipeline di sicurezza blindata.

#### Aggiunto

- **Z204 FORBIDDEN_TERM — Enterprise Privacy Gate (Sprint D100)**: Nuova regola Shield che
  scatena Exit 2 quando un termine proibito del progetto compare in qualsiasi file di
  documentazione. I pattern (stringhe semplici o regex ancorate) sono dichiarati nel file
  locale e git-ignorato `.zenzic.local.toml`, mantenendo il vocabolario sensibile del
  progetto permanentemente fuori da `git log`. Architettura a due layer:
  `scan_line_for_forbidden_terms()` in `shield.py` esegue la scansione dei termini;
  `_apply_local_toml()` in `config.py` unisce i pattern in modo additivo al caricamento.
- **Scaffolding init di `.zenzic.local.toml` (Sprint D100)**: `zenzic init` (e `--dev`)
  crea sempre `.zenzic.local.toml` e lo aggiunge automaticamente a `.gitignore`, così i
  pattern privati sono git-ignorati fin dal primo commit.

- **EPOCH 7a.1 — Sovranità Zero-Config (`absolute_path_allowlist` epurato)**: Lo
  schema TOML `[link_validation]` e il campo `absolute_path_allowlist` sono
  rimossi. I prefissi URL multi-instance di Docusaurus (`/docs/`, `/developers/`,
  ogni ulteriore istanza `@docusaurus/plugin-content-docs`) vengono ora
  auto-rilevati da `DocusaurusAdapter.get_absolute_url_prefixes(repo_root)` —
  nuovo metodo del Protocol `BaseAdapter`. Due passi puramente Python preservano
  l'invariante Zero Subprocess: parsing statico via regex su
  `docusaurus.config.{ts,js,mjs,cjs}` per ogni tupla
  `@docusaurus/plugin-content-docs` e l'estrazione del relativo `routeBasePath`,
  più un'euristica filesystem che accoppia `<repo>/<id>/` con
  `i18n/<locale>/docusaurus-plugin-content-docs-<id>/` quando la config è
  dinamica. Z105 `ABSOLUTE_PATH` rispetta i prefissi rilevati senza alcuna
  duplicazione TOML lato utente. **Industry-grade — nessuno shim di
  compatibilità**: `LinkValidationConfig` viene rimossa integralmente; le
  configurazioni che ancora dichiarano `[link_validation]` falliranno la
  validazione TOML.
- **Default Zero-Config per gli Asset (Direttiva CEO — Cimitero degli Asset)**:
  I file di toolchain universali sono promossi a Layer 1 in
  `SYSTEM_EXCLUDED_FILE_NAMES` e `SYSTEM_EXCLUDED_FILE_PATTERNS` — `*.toml`,
  `*.yaml`, `*.yml`, `*.json`, `*.cfg`, `*.ini`, `*.cff`, `*.code-workspace`,
  `LICENSE`, `LICENSE.txt`, `LICENSE.md`, `NOTICE`, `NOTICE.txt`, `COPYING`,
  `Dockerfile`, `noxfile.py`, `.gitignore`, `.gitattributes`, `.coverage`. I
  repo "Prose-only Maintenance" (engine `standalone` con `docs_dir = "."`) non
  devono più ripeterli in `excluded_assets`.
- **Default Zero-Config per le Directory (Direttiva CEO — Cimitero delle Dir)**:
  Le directory universali di build / artefatti temporanei sono promosse a
  `SYSTEM_EXCLUDED_DIRS` — `build`, `dist`, `temp`, `tmp`, `mutants` (`.tox`
  era già presente). Ogni build di wheel Python, bundler JS e toolchain di
  mutation testing è ora onorato Zero-Config.
- **EPOCH 7a — Multi-Root Discovery (VSM Blindness sigillata)**: Il VSM non è
  più vincolato a `docs_dir`. Gli adapter possono dichiarare radici di contenuto
  aggiuntive tramite l'hook opzionale `get_extra_content_roots(repo_root) -> list[ContentRoot]`
  (rilevato con `hasattr()`, replicando la convenzione di `get_locale_source_roots` —
  non-breaking per gli adapter di terze parti). L'adapter Docusaurus auto-rileva il
  plugin `blog/` in due passaggi puramente di parsing (regex statico su
  `docusaurus.config.{ts,js,mjs,cjs}` con fallback per convenzione) — l'invariante Zero
  Subprocess è preservato. Quattro stadi della pipeline (Discovery, VSM, Validator,
  Scanner Z903/Z104) cooperano affinché i post del blog siano contenuto di prima classe:
  link rotti dentro `blog/` e link cross-tree da `docs/` verso `blog/` sono ora
  intercettati da `zenzic check all --strict` invece di sfuggire a `docusaurus build`.
  Un test di invariante Reverse-Mapping
  (`tests/test_docusaurus_blog_vsm.py::TestEpoch7aReverseMapping`) verifica che ogni
  `Route.source` di blog risalga a un file fisico, bloccando il contratto che le rotte
  virtuali di EPOCH 7b (tag, paginazione, autori) erediteranno. La Discovery usa
  `walk_files` (lo stesso motore `os.walk` esistente), non `rglob` — il determinismo è
  preservato.
- **EPOCH 7b — Virtual Routes e `zenzic inspect routes` (La JSON API)**: Le pagine generate
  dal motore — pagine di tag Docusaurus (`/blog/tags/{slug}/`), indice dei tag (`/blog/tags/`),
  indici paginati e profili autore — sono ora cittadini di prima classe nella VSM, con
  l'Invariante di Reverse-Mapping applicata al momento della costruzione: una `VirtualRoute`
  con `source_files=frozenset()` solleva immediatamente `ValueError`, impedendo che un URL
  non tracciato raggiunga la VSM. Tre nuovi codici di finding: **Z111 VIRTUAL_ROUTE_BROKEN**
  (error) quando un link in docs punta a un URL di tag che nessun post del blog attiva,
  **Z113 AUTHOR_KEY_COLLISION** (error) per chiavi autore duplicate, **Z114 LARGE_PAGINATION_SET**
  (info) quando il set di paginazione supera 200 pagine. Il generatore di tag di
  `DocusaurusAdapter` applica la normalizzazione Unicode NFKD + slugification `re.ASCII`
  (replicando l'algoritmo di Docusaurus) e gestisce i tag puramente CJK restituendo
  `"untagged"`. Il nuovo comando CLI `zenzic inspect routes [--kind physical|virtual|all]
  [--json]` esporta la mappa completa del sito in formato JSON deterministico con `url`,
  `kind`, `source_files` (path POSIX repo-relative) e `digest`
  (`sha256(url + ":" + ",".join(sorted(source_files)))`) per rotta.
  **Invariante di Purezza JSON**: quando `--json` è attivo, `stdout` contiene
  esclusivamente JSON valido — nessun codice ANSI, nessun banner. Questa funzionalità
  è progettata per essere consumata da tool esterni: script Bash custom, dashboard di
  CI/CD, o agenti di Intelligenza Artificiale che necessitano di contesto architetturale.
- **Sentinel Seal**: Sistema di validazione rigorosa a 4 stadi (`just verify`) integrato in
  ogni repository — pre-commit, test-cov e self-check eseguiti identicamente in locale e in CI.
- **Cross-Repo Governance**: Branch Parity Rule per la sincronizzazione Core/Doc
  con fallback automatico su `main`. Configurazione VS Code Multi-Root Workspace per lo
  sviluppo unificato.
- **Z907 I18N_PARITY**: Scanner di parità traduzione language-agnostic con parallelismo
  adattivo, imposizione chiavi frontmatter e supporto Docusaurus multi-istanza.
- **Esportazione SARIF 2.1.0**: Tutti i comandi `check` supportano `--format sarif` per
  l'integrazione nativa con GitHub Code Scanning e annotazioni inline nelle PR.
- **Matrice CI Cross-Platform**: Matrice 3×3 (Ubuntu/Windows/macOS × Python 3.11/3.12/3.13).
- **Auto-Discovery del Motore**: `engine = "auto"` risolve automaticamente il framework di
  documentazione (Docusaurus → MkDocs → Zensical → Standalone).
- **Decoder Speculativo Base64**: Lo Shield rileva credenziali codificate in Base64 nel
  frontmatter YAML, sigillando il vettore d'attacco S2 dal Quartz Tribunal.
- **Z107 Ancora Circolare**, **Z505 Blocco Codice Senza Tag**, **Z905 Obsolescenza Brand**:
  Tre nuovi check basati su regole per integrità strutturale e del brand.
- **Z404 Integrità Asset di Configurazione**: Verifica i percorsi favicon e social card su
  tutti e tre i motori supportati (Docusaurus, MkDocs, Zensical).
- **Scoperta Navigazione Unificata**: Il rilevamento orfani Docusaurus aggrega le superfici
  sidebar, navbar e footer (Legge di Raggiungibilità UX R21).
- **Parser Sidebar Statico**: Parser regex pure-Python per `sidebars.ts`/`sidebars.js`.
- **GitHub Action Ufficiale**: Action composita `PythonWoods/zenzic-action` con upload SARIF
  e quality gate configurabili.
- **Determinism Invariant**: Contratto formale in `pyproject.toml` — Zenzic non
  distribuisce nessuna dipendenza AI/ML.
- **Flag CLI `--exclude-url`** (`check all`, `check links`): Soppressione a runtime della
  validazione degli URL esterni per prefissi specifici. Ripetibile; i valori vengono uniti
  a `excluded_external_urls` in `zenzic.toml`. Pensato per i paradossi di deployment
  CI/CD — es. sopprimere una Release GitHub non ancora pubblicata al momento dell'esecuzione
  della pipeline.

#### Modificato

- **Architettura Engine-Agnostic**: Plugin MkDocs rimosso permanentemente. Zenzic è ora una
  CLI Sovrana indipendente da qualsiasi framework di documentazione.
- **Scudo Unicode Windows nel bootstrap CLI**: `cli_main()` invoca ora
  `bootstrap_unicode()` prima dell'inizializzazione di Rich traceback e logging,
  forzando stdio UTF-8 (`errors='replace'`) su Windows per prevenire crash
  `UnicodeEncodeError` causati dalle code page della console.
- **Ristrutturazione CLI**: Il monolite `cli.py` è stato suddiviso nel package coerente `cli/`.
  `zenzic plugins` sostituito da `zenzic inspect capabilities`.
- **Applicazione della Legge dei Layer**: `ui.py` → `core/ui.py`, `lab.py` → `cli/_lab.py`,
  `run_rule()` → `core/rules.py`. Il Core non importa mai dal layer CLI.
- **Hook Pre-commit**: `zenzic-check-all` sostituito da `zenzic-verify` (postura 4-Gates).
- **Formato Coverage**: Standardizzato in JSON (`coverage.json`) in justfile e noxfile.
- **Parità CI e automazione cross-platform**: `.github/workflows/ci.yml` ora
  esegue `just verify` su matrice Ubuntu/Windows (`fail-fast: false`) e il
  `justfile` del core è esplicitamente Bash-first (`set shell := ["bash", "-c"]`)
  per comportamento uniforme delle recipe sui runner Windows di GitHub.

#### Rimosso

- **`.zenzic.dev.toml` (D002 Environmental Privacy Gate) — rimosso definitivamente**: Il file
  non esiste più per il motore Zenzic. Non viene scansionato, non viene caricato, non riceve
  warning. L'unica fonte di verità per i pattern locali del Privacy Gate è
  `.zenzic.local.toml`. `_scaffold_dev_toml()` rimosso; `zenzic init --dev` chiama
  direttamente `_scaffold_local_toml()`.

- **Schema TOML `[link_validation]` (EPOCH 7a.1)**: Il modello Pydantic
  `LinkValidationConfig` e il campo `absolute_path_allowlist: list[str]`
  vengono rimossi da `zenzic.models.config`. Le configurazioni che dichiarano
  ancora `[link_validation]` sollevano un errore di validazione TOML.
  **Migrazione:** elimina il blocco — il `DocusaurusAdapter` rileva i prefissi
  URL plugin Zero-Config.
- **Percorsi fantasma stantii in `excluded_build_artifacts`**:
  `docs/configuration/*.md` e `docs/adr/*.md` rimossi da `zenzic.toml` — le
  directory sottostanti erano state estirpate in EPOCH precedenti; le voci
  erano ormai morte.
- **Epurazione Brand Legacy**: Rimozione completa di ogni nomenclatura obsoleta e riferimento
  a piattaforme esterne dalla configurazione e documentazione attive.
- **Plugin MkDocs**: `zenzic.integrations.mkdocs` eliminato fisicamente. L'extra opzionale
  `[mkdocs]` non esiste più.
- **Comando `zenzic plugins`**: Eliminato completamente. Usare `zenzic inspect capabilities`.
- **`scripts/map_project.py`**: Superato; nessun chiamante residuo.

#### Sicurezza

- **[D100] Z204 FORBIDDEN_TERM — Brand Integrity Shield**: Architettura Privacy Gate a due
  layer che sigilla il vocabolario sensibile del progetto (codename, endpoint interni, PII)
  al layer Shield (Exit 2). I pattern sono dichiarati nel `.zenzic.local.toml` locale e
  git-ignorato. `.zenzic.dev.toml` è rimosso definitivamente: non riconosciuto dal motore,
  mai scansionato, mai caricato.
- **[ZRT-001]** Shield Blind Spot — Bypass YAML Frontmatter sigillato (architettura Dual-Stream).
- **[ZRT-002]** ReDoS + Deadlock ProcessPoolExecutor — Prevenzione Canary + contenimento timeout 30s.
- **[ZRT-003]** Shield Bypass Split-Token — Pre-processore `_normalize_line_for_shield()`.
- **[ZRT-004]** Risoluzione VSM Context-Aware — Dataclass `ResolutionContext` per percorsi annidati.
- **[ZRT-007] La Rivoluzione DFA — Motore Google RE2** (`core/rules.py`, `core/shield.py`): Migrazione
  integrale al motore DFA **Google RE2**. I pattern `CustomRule` hanno ora complessità garantita $O(n)$
  — il rischio ReDoS è eliminato per design, non tramite timeout.
  * **Breaking Change**: pattern che usano backreference (`\1`), lookahead (`(?=...)`, `(?!...)`)  
    o lookbehind (`(?<=...)`) vengono rifiutati al caricamento con `PluginContractError`.
  * `timeout.py` e la sua dipendenza da `signal.SIGALRM` eliminati: Zenzic è ora nativamente
    identico su Linux e Windows.
  * `shield.py` migrato a `re2`: lo Shield è ora completamente DFA-Pure.
  * Alias legacy `Z001` e `Z009` rimossi: i finding emettono ora direttamente `Z101` (LINK_BROKEN)
    e `Z902` (ANALYSIS_TIMEOUT) alla sorgente.
- **Decoder speculativo Base64** sigilla il vettore d'attacco delle credenziali codificate.
- **Fix di portabilità `os.path.normcase`** per confronto perimetro Shield cross-platform.
- **Standard 4-Gates**: pre-commit → test-cov → self-check, applicato ad ogni push.

#### Migrazione

I contributor devono rieseguire il bootstrap dopo il pull di questa release:

```bash
just sync
uvx pre-commit install              # hook stage commit
uvx pre-commit install -t pre-push  # 🛡️ Final Guard (just verify)
```

Sostituire `zenzic plugins list` con `zenzic inspect capabilities`.
Sostituire `pip install "zenzic[mkdocs]"` con `pip install zenzic`.

#### Corretto

- **[ZRT-006] Bypass VSM: Link con Slug Assoluti Saltati Silenziosamente** (`core/validator.py`):
  Due bug coordinati causavano l'assenza di finding quando un link assoluto puntava allo
  slug sbagliato di un post del blog Docusaurus — mentre `docusaurus build` falliva con un
  errore di link non trovato.

  1. **Ordinamento del ciclo di vita** — `DocusaurusAdapter.set_slug_map(md_contents)` non
     veniva mai chiamato durante `validate_links_async()`. La mappa degli slug era vuota al
     momento della costruzione della VSM, quindi i post con un campo `slug:` nel frontmatter
     venivano instradati tramite derivazione dal filename (es. `2026-04-29-post.mdx` →
     `/blog/2026-04-29-post/`) anziché tramite l'URL dello slug dichiarato. Fix:
     `set_slug_map()` viene ora chiamato tramite guardia `hasattr` immediatamente prima di
     `build_vsm()` — sicuro cross-engine, non-breaking per gli adapter MkDocs / Standalone /
     Zensical che non implementano il metodo.

  2. **Lookup VSM con scope** — La soppressione Z105 `ABSOLUTE_PATH` per i prefissi di
     proprietà del progetto (es. `/blog/`) era implementata con un `continue` nudo, che
     usciva dal ciclo per-link prima di qualsiasi lookup nella VSM, rendendo impossibile
     a `FILE_NOT_FOUND` di attivarsi su quei link. Fix: un nuovo discriminatore
     `_scanned_vsm_prefixes` separa i prefissi *completamente scansionati* (quelli con ≥1
     route nella VSM) dai *plugin sorella non scansionati* (es. `/developers/` il cui
     markdown è fuori dallo scope di scansione). I link che puntano a un prefisso scansionato
     ricevono ora un lookup `dict.get()` e riportano Z104 `FILE_NOT_FOUND` quando la route
     esatta è assente. I prefissi non scansionati mantengono il bypass incondizionato —
     invariante Zero-Config preservata.

- **Lock di regressione** — `tests/test_docusaurus_blog_vsm.py::TestAbsoluteSlugMismatch`
  (2 nuovi test):
  - `test_absolute_broken_blog_link_is_detected` — slug sbagliato solleva `FILE_NOT_FOUND`
  - `test_correct_absolute_slug_link_is_clean` — slug corretto non produce finding

**Suite di test: 1480 passati, 0 falliti.**
