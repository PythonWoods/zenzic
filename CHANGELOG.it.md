<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Changelog

Tutti i cambiamenti degni di nota a questo progetto sono documentati in questo file.
Il formato si basa su [Keep a Changelog][keep-a-changelog].
Le versioni seguono il [Versionamento Semantico][semver].

---

## [Non rilasciato]

---

## [0.4.0-rc3] — 2026-03-29 — Fix i18n Ancore, Snippet Multilingua & Shield Deep-Scan

> **Sprint 7.** Il gap di fallback i18n per `AnchorMissing` è chiuso. Codice morto eliminato.
> Utility condivisa per la rimappatura dei percorsi locale estratta. Visual Snippets per i
> rilevamenti delle regole custom. Documentazione usage suddivisa in tre pagine dedicate.
> Schema JSON stabilizzato a 7 chiavi. Validazione snippet multilingua (Python/YAML/JSON/TOML)
> e Shield deep-scan sull'intero file aggiunti.

### Aggiunto

- **Validazione snippet multilingua** — `check_snippet_content` valida ora i blocchi di codice
  delimitati per quattro linguaggi usando parser puri in Python (nessun sottoprocesso):
  `python`/`py` → `compile()`; `yaml`/`yml` → `yaml.safe_load()`; `json` → `json.loads()`;
  `toml` → `tomllib.loads()`. I blocchi con tag di linguaggio non supportati (es. `bash`) vengono
  silenziosamente saltati. `_extract_python_blocks` rinominato in `_extract_code_blocks`.

- **Shield deep-scan — credenziali nei blocchi delimitati** — Lo scanner di credenziali opera
  ora su ogni riga del file sorgente, incluse le righe nei blocchi di codice delimitati (con o
  senza etichetta). In precedenza `_iter_content_lines` alimentava sia lo Shield che l'harvester
  dei riferimenti, rendendo il contenuto nei fence invisibile allo Shield. Un nuovo generatore
  `_skip_frontmatter` fornisce un flusso grezzo di righe (solo senza frontmatter); `harvest()`
  esegue ora due pass indipendenti — Shield sul flusso grezzo, ref-def + alt-text sul flusso
  filtrato dei contenuti. Link e definizioni di riferimento nei blocchi delimitati rimangono
  ignorati per prevenire falsi positivi.

- **Shield esteso a 7 famiglie di credenziali** — Aggiunte chiavi live Stripe
  (`sk_live_[0-9a-zA-Z]{24}`), token Slack (`xox[baprs]-[0-9a-zA-Z]{10,48}`), chiavi API
  Google (`AIza[0-9A-Za-z\-_]{35}`) e chiavi private PEM generiche
  (`-----BEGIN [A-Z ]+ PRIVATE KEY-----`) in `core/shield.py`.

- **Metodo `resolve_anchor()` nel protocollo `BaseAdapter`** — Nuovo metodo adapter che
  restituisce `True` quando un anchor miss su un file locale deve essere soppresso perché
  l'ancora esiste nel file equivalente della locale di default. Implementato in
  `MkDocsAdapter`, `ZensicalAdapter` (tramite `remap_to_default_locale()`) e `VanillaAdapter`
  (restituisce sempre `False`).

- **`adapters/_utils.py` — utility pura `remap_to_default_locale()`** — Estrae la logica di
  rimappatura dei percorsi locale che era duplicata indipendentemente in `resolve_asset()` e
  `is_shadow_of_nav_page()` in entrambi gli adapter. Funzione pura: riceve
  `(abs_path, docs_root, locale_dirs)`, restituisce il `Path` equivalente nella locale di
  default o `None`. Nessun I/O.

- **Visual Snippets per i rilevamenti `[[custom_rules]]`** — Le violazioni delle regole custom
  mostrano ora la riga sorgente incriminata sotto l'intestazione del rilevamento, preceduta
  dall'indicatore `│` nella colore della severity del rilevamento. I rilevamenti standard non
  sono interessati.

- **`strict` e `exit_zero` come campi di `zenzic.toml`** — Entrambi i flag sono ora campi
  di prima classe in `ZenzicConfig` (tipo `bool | None`, sentinella `None` = non impostato).
  I flag CLI sovrascrivono i valori TOML. Abilita default a livello di progetto.

- **Schema output JSON — 7 chiavi stabili** — `--format json` emette:
  `links`, `orphans`, `snippets`, `placeholders`, `unused_assets`, `references`, `nav_contract`.

- **Suddivisione documentazione usage** — `docs/usage/index.md` suddivisa in tre pagine
  dedicate: `usage/index.md` (install + workflow), `usage/commands.md` (riferimento CLI),
  `usage/advanced.md` (pipeline tre-pass, Shield, API programmatica, multilingua).
  Mirror italiani (`docs/it/usage/`) a piena parità. Nav `mkdocs.yml` aggiornata.

### Risolto

- **`AnchorMissing` non aveva la soppressione tramite fallback i18n** — Il ramo `AnchorMissing`
  in `validate_links_async` riportava incondizionatamente. I link a intestazioni tradotte in
  file locale generavano falsi positivi. Fix: il ramo `AnchorMissing` ora chiama
  `adapter.resolve_anchor()`. Cinque nuovi test di integrazione in `TestI18nFallbackIntegration`.

### Rimosso

- **`_should_suppress_via_i18n_fallback()`** — Codice morto. Era definita in `validator.py`
  ma non veniva mai chiamata. Rimossa permanentemente.
- **`I18nFallbackConfig` NamedTuple** — Struttura dati interna per la funzione eliminata.
  Rimossa.
- **`_I18N_FALLBACK_DISABLED`** — Costante sentinella per la funzione eliminata. Rimossa.
- **`_extract_i18n_fallback_config()`** — Anch'essa codice morto. Era testata da
  `TestI18nFallbackConfig` (6 test), anch'essa rimossa. Totale: ~118 righe da `validator.py`.

### Test

- 5 nuovi test di integrazione anchor fallback in `TestI18nFallbackIntegration`.
- `TestI18nFallbackConfig` (6 test per le funzioni eliminate) rimossa.
- 8 nuovi test di validazione snippet (YAML valido/non valido, alias `yml`, JSON valido/non
  valido, accuratezza numero di riga JSON, TOML valido/non valido).
- 5 nuovi test Shield deep-scan: segreto in fence senza etichetta, segreto in fence `bash`,
  segreto in fence senza creazione ref-def, blocco codice pulito senza findings.
- **446 test passano.** `nox preflight` — tutti i gate verdi: ruff ✓ mypy ✓ pytest ✓
  reuse ✓ mkdocs build --strict ✓ zenzic check all --strict ✓.

---

## [0.4.0-rc2] — 2026-03-28 — Il Grande Disaccoppiamento

> **Sprint 6.** Zenzic cessa di possedere i propri adapter. Gli adapter di terze parti si
> installano come pacchetti Python e vengono scoperti a runtime tramite entry-point. Il Core
> non importa più nessun adapter concreto. La documentazione viene promossa a knowledge base
> strutturata con piena parità i18n.

### Aggiunto

- **Scoperta Dinamica degli Adapter** (`_factory.py`) — `get_adapter()` non importa più
  direttamente `MkDocsAdapter` o `ZensicalAdapter`. La factory interroga
  `importlib.metadata.entry_points(group="zenzic.adapters")` a runtime. Installando un
  pacchetto che si registra in questo gruppo, il suo adapter è immediatamente disponibile
  come `--engine <nome>` — nessun aggiornamento di Zenzic richiesto. Gli adapter built-in
  (`mkdocs`, `zensical`, `vanilla`) sono registrati in `pyproject.toml`:

  ```toml
  [project.entry-points."zenzic.adapters"]
  mkdocs   = "zenzic.core.adapters:MkDocsAdapter"
  zensical = "zenzic.core.adapters:ZensicalAdapter"
  vanilla  = "zenzic.core.adapters:VanillaAdapter"
  ```

- **Pattern classmethod `from_repo()`** — Gli adapter gestiscono il proprio caricamento della
  configurazione e contratto di enforcement. La factory chiama
  `AdapterClass.from_repo(context, docs_root, repo_root)` se presente.

- **Metodo di protocollo `has_engine_config()`** (`BaseAdapter`) — Sostituisce il precedente
  controllo `isinstance(adapter, VanillaAdapter)` in `scanner.py`. Lo scanner è ora
  completamente disaccoppiato da tutti i tipi di adapter concreti.

- **`list_adapter_engines() -> list[str]`** — Funzione pubblica che restituisce la lista
  ordinata dei nomi degli engine adapter registrati.

- **Flag `--engine ENGINE` su `check orphans` e `check all`** — Sovrascrive
  `build_context.engine` per una singola esecuzione senza modificare `zenzic.toml`. I nomi
  sconosciuti producono un errore amichevole con le scelte disponibili:

  ```text
  ERROR: Unknown engine adapter 'hugo'.
  Installed adapters: mkdocs, vanilla, zensical
  Install a third-party adapter or choose from the list above.
  ```

- **DSL `[[custom_rules]]`** — Regole lint specifiche del progetto in `zenzic.toml` come
  array-of-tables TOML puro. Indipendenti dall'adapter: si attivano identicamente con
  `mkdocs`, `zensical` e `vanilla`. Pattern compilati una volta al caricamento. Pattern
  non validi sollevano `ConfigurationError` all'avvio. Vedi
  [DSL Regole Custom](docs/configuration/custom-rules-dsl.md).

- **Contratto di enforcement `ZensicalAdapter.from_repo()`** — Quando è dichiarato
  `engine = "zensical"`, `zensical.toml` deve esistere. `from_repo()` solleva
  `ConfigurationError` immediatamente se assente. Nessun fallback silenzioso.

- **Tracciamento `MkDocsAdapter.config_file_found`** — `from_repo()` registra se
  `mkdocs.yml` è stato trovato su disco (indipendentemente dal parsing). `has_engine_config()`
  restituisce `True` quando il file esisteva.

- **Comando `zenzic init`** — Scaffolding di `zenzic.toml` con rilevamento automatico
  dell'engine. Rileva `mkdocs.yml` → preimposta `engine = "mkdocs"`; rileva `zensical.toml`
  → preimposta `engine = "zensical"`; nessun file rilevato → scaffold Vanilla. Tutte le
  impostazioni sono commentate per default. `--force` sovrascrive un file esistente.

- **Pannello UX "Helpful Hint"** — Quando un comando `check` viene eseguito senza
  `zenzic.toml`, Zenzic mostra un pannello informativo Rich che suggerisce `zenzic init`.
  Il pannello viene soppresso automaticamente una volta che `zenzic.toml` esiste. Pilotato
  dal nuovo flag `loaded_from_file: bool` restituito da `ZenzicConfig.load()`.

- **`ZenzicConfig.load()` restituisce `tuple[ZenzicConfig, bool]`** — Il secondo elemento
  (`loaded_from_file`) è `True` quando `zenzic.toml` è stato trovato e analizzato, `False`
  quando si usano i default integrati.

- **Documentazione — Suddivisione configurazione** —
  [Panoramica](docs/configuration/index.md) ·
  [Impostazioni di Base](docs/configuration/core-settings.md) ·
  [Adapter e Motore](docs/configuration/adapters-config.md) ·
  [DSL Regole Custom](docs/configuration/custom-rules-dsl.md)

- **Documentazione — Parità italiana** — `docs/it/` rispecchia la struttura inglese completa:
  `it/configuration/` (4 pagine), `it/developers/writing-an-adapter.md`,
  `it/guides/migration.md`.

- **Documentazione — Guida scrittura Adapter** (`docs/developers/writing-an-adapter.md`).

- **Documentazione — Guida migrazione MkDocs → Zensical** (`docs/guides/migration.md`) —
  Workflow in quattro fasi con approccio baseline/diff/gate.

### Modificato

- **Engine sconosciuto → `VanillaAdapter`** (breaking change rispetto a v0.3) — Prima:
  fallback a `MkDocsAdapter`. Ora: `VanillaAdapter` (controllo orfani no-op).

- **`scanner.py` ora è solo-protocollo** — rimossa importazione di `VanillaAdapter`;
  sostituito `isinstance(adapter, VanillaAdapter)` con `not adapter.has_engine_config()`.

- **Parametro `output_format`** (era `format`) — Rinominato in `check_all`, `score` e `diff`
  per evitare l'oscuramento del built-in Python `format`.

### Risolto (Sprint 6 — v0.4.0-rc2)

- **`check all` esegue ora 7/7 controlli** — La pipeline di integrità delle reference
  (`scan_docs_references_with_links`) non veniva mai invocata da `check all`. I link
  dangling e gli eventi Shield potevano superare il gate globale in silenzio. Fix:
  `_collect_all_results` ora chiama la pipeline delle reference. `_AllCheckResults`
  aggiunge i campi `reference_errors` e `security_events`. Exit code `2` dello Shield
  è imposto incondizionatamente. L'output JSON acquista la chiave `"references"`.

- **File fantasma `docs/it/configuration.md`** — La god-page italiana della configurazione
  non era stata eliminata dopo la suddivisione in `docs/it/configuration/`. Il controllo
  orphan salta correttamente i sottoalberi locale per design; il file era un fantasma fisico.
  Fix: file eliminato.

- **`rule_findings` scartati silenziosamente in `check references`** — `IntegrityReport.rule_findings`
  veniva popolato dallo scanner ma mai iterato nel loop di output CLI di `check references`.
  Le violazioni delle regole personalizzate erano invisibili agli utenti. Fix: aggiunta
  iterazione su `report.rule_findings` nel percorso di output.

### Risolto (Sprint 5 — v0.4.0-rc1)

- **Marcatore radice `find_repo_root()`** — da `mkdocs.yml` a `.git` o `zenzic.toml`.
- **Letture O(N)** — eliminato il collo di bottiglia della doppia lettura con
  `_scan_single_file()`.
- **Pre-compilazione regex `[[custom_rules]]`** — `model_post_init` compila una volta.
- **Salto del frontmatter YAML** — `_iter_content_lines()` salta il blocco `---` iniziale.
- **Falsi positivi riferimenti immagine** — `(?<!!)` lookbehind in `_RE_REF_LINK`.
- **Scansione Shield nel testo** — `scan_line_for_secrets` nel ciclo `harvest()`.
- **Nomi file percent-encoded** — `unquote()` applicato prima di `normpath`.

### Sicurezza

- **Shield come firewall nel testo** (hardening CVE-2026-4539) — Scanner su ogni riga
  non-definizione durante il Pass 1. Exit code `2` non sopprimibile da nessun flag.

### Test

- 435 test passano. `zenzic check all` — 7/7 OK (self-dogfood, parità i18n verificata).

---

## [0.4.0-rc1] — 2026-03-27 — Lo Sprint di Consolidamento RC1

> **Sprint 5.** Undici fix di livello produzione applicati a `0.4.0-alpha.1`.

### Aggiunto

- **`validate_same_page_anchors`** — campo booleano in `zenzic.toml` (default `false`).
- **`excluded_external_urls`** — campo lista in `zenzic.toml` (default `[]`).
- **`excluded_build_artifacts`** e **`excluded_asset_dirs`** — nuovi campi in `zenzic.toml`.
- **Sezione Community** — Get Involved, FAQ, Contributing, Bug Report, Docs Issue, Change
  Request, Pull Request.

### Modificato

- **`find_repo_root()`** — da `mkdocs.yml` a `.git` + `zenzic.toml`.
- **`check_all` refactoring** — `_AllCheckResults` + `_collect_all_results()`.
- **`format` → `output_format`** — elimina ruff A002.
- **`placeholder_patterns` predefiniti** — 23 convenzioni stub EN/IT.

### Risolto

- **Ancore esplicite MkDocs Material** in `slug_heading()`.
- **Tag HTML** rimossi prima della slugificazione.
- **Output `check_references`** relativizzato a `docs_root`.

### Test

- 405 test passano. `zenzic check all` — 6/6 OK.

---

## [0.4.0-alpha.1] — 2026-03-26 — L'Architettura Sovrana

> Breaking release candidate. Introduce la Pipeline degli Adapter.

### Breaking Changes

- **Migrazione i18n Folder Mode** — da Suffix Mode a Folder Mode (`docs/it/`).
- **`[build_context]` deve essere dichiarato per ultimo** in `zenzic.toml`.

### Aggiunto

- **Modello `BuildContext`** — nuova sezione `[build_context]` in `zenzic.toml`.
- **`MkDocsAdapter`** — tre metodi agnostici: `is_locale_dir()`, `resolve_asset()`,
  `is_shadow_of_nav_page()`.
- **Factory `get_adapter()`** — unico punto di ingresso per la selezione dell'adapter.
- **Fallback automatico a `mkdocs.yml`** quando `build_context.locales` è vuoto.

### Risolto

- Falsi positivi orfani (14 file `docs/it/**/*.md`).
- Falsi positivi link non raggiungibili negli asset di `docs/it/`.
- Tag SPDX `header.html` con whitespace-stripping Jinja2.

### Test

- 384 test passano. `zenzic check all` — 6/6 OK.

---

## [0.3.0-rc3] — 2026-03-25 — The Bulldozer Edition

> **Nota:** Si basa su `0.3.0-rc2`. Aggiunge la Trinità degli Esempi (Gold Standard,
> Broken Docs, Security Lab), il controllo ISO 639-1 nel rilevamento dei suffissi e
> 20 test chaos. Questa è la Release Candidate finale prima del tag stabile `0.3.0`.

### Aggiunto

- **Trinità degli Esempi** — tre directory di riferimento in `examples/` che coprono
  lo spettro completo dell'integrità documentale:
  - `examples/i18n-standard/` — il Gold Standard: gerarchia profonda, suffix mode,
    ghost artifacts (`excluded_build_artifacts`), zero link assoluti, 100/100.
  - `examples/broken-docs/` — aggiornato con violazione di link assoluto e link i18n
    rotto per dimostrare il Portability Enforcement Layer e la validazione cross-locale.
  - `examples/security_lab/` — aggiornato con `traversal.md` e `absolute.md`;
    quattro trigger distinti di Shield e Portability, tutti verificati.
- **`examples/run_demo.sh` Philosophy Tour** — orchestratore in tre atti:
  Atto 1 Standard (deve passare), Atto 2 Broken (deve fallire), Atto 3 Shield (deve bloccare).
- **Demo Ghost Artifact** — `examples/i18n-standard/` referenzia `assets/manual.pdf`
  e `assets/brand-kit.zip` tramite `excluded_build_artifacts`. Zenzic ottiene verde
  senza i file su disco — prova vivente della Build-Aware Intelligence.

### Modificato

- **Guardia ISO 639-1** — `_extract_i18n_locale_patterns` ora valida le stringhe locale
  con `re.fullmatch(r'[a-z]{2}', locale)`. Tag di versione (`v1`, `v2`), tag di build
  (`beta`, `rc1`), stringhe numeriche, codici BCP 47 e valori maiuscoli vengono
  rifiutati silenziosamente. Solo i codici di due lettere minuscole producono pattern
  `*.locale.md`.

### Test

- **`tests/test_chaos_i18n.py`** — 20 scenari chaos (guardia ISO 639-1 × 11,
  orphan check patologico × 9). 367 passati, 0 falliti.

---

## [0.3.0-rc2] — 2026-03-25 — The Agnostic Standard

> **Nota:** Si basa su `0.3.0-rc1`. Aggiunge il Portability Enforcement Layer (divieto di link
> assoluti) e migra la documentazione del progetto al Suffix Mode i18n engine-agnostico.
> La validazione i18n di Zenzic funziona ora con qualsiasi motore di documentazione senza dipendenze da plugin.

### Aggiunto

- **Divieto di Link Assoluti** — I link che iniziano con `/` generano ora un errore bloccante.
  I percorsi assoluti sono dipendenti dall'ambiente: si rompono quando la documentazione è
  ospitata in una sottocartella (es. `sito.io/docs/`). Zenzic impone l'uso di percorsi relativi
  (`../` o `./`) per rendere la documentazione portabile in qualsiasi contesto di hosting. Il
  messaggio di errore include un suggerimento esplicito per la correzione.
- **i18n Agnostico a Suffisso** — Supporto per il pattern di traduzione non annidato
  (`pagina.locale.md`). Zenzic rileva i suffissi locale dai nomi dei file indipendentemente
  da qualsiasi plugin del motore di build. Questo rende la validazione i18n compatibile con
  Zensical, MkDocs, Hugo o una semplice cartella di file Markdown senza richiedere plugin specifici.

### Risolto

- **Integrità della navigazione i18n** — La documentazione del progetto è stata migrata da
  Folder Mode (`docs/it/pagina.md`) a Suffix Mode (`docs/pagina.it.md`). Il Suffix Mode elimina
  l'ambiguità di profondità degli asset: i file tradotti sono nella stessa cartella degli
  originali, quindi tutti i percorsi relativi sono simmetrici tra le lingue. Risolve la perdita
  di contesto durante il cambio lingua e i 404 degli asset cross-locale (doppio slash generato
  dai percorsi assoluti in folder mode).
- **Simmetria dei percorsi asset** — Uniformata la profondità dei link per i file originali e
  tradotti. Tutti i percorsi relativi nei file `.it.md` sono ora strutturalmente identici alle
  loro controparti `.md`, rendendo la manutenzione delle traduzioni semplice e priva di errori.

### Modificato

- **Portability Enforcement Layer** — Stadio di pre-risoluzione aggiunto a `validate_links_async`
  che rifiuta i percorsi interni assoluti prima che `InMemoryPathResolver` venga consultato.
  Eseguito incondizionatamente indipendentemente dal motore, dal plugin o dalla configurazione locale.

---

## [0.3.0-rc1] — 2026-03-25 — The Build-Aware Candidate

> **Nota:** Questa Release Candidate sostituisce il tag stabile 0.3.0 (ritirato) e incorpora
> tutto il lavoro dello Sprint 4 Fase 1 e Fase 2. È la baseline di riferimento per la linea v0.3.x.

### Aggiunto

- **Intelligenza Build-Aware (i18n)** — Zenzic comprende ora il plugin `i18n` di MkDocs in
  modalità `folder`. Quando `fallback_to_default: true` è impostato in `mkdocs.yml`, i link
  a pagine non tradotte vengono risolti nel locale di default prima di essere segnalati come
  rotti. Nessun falso positivo per le traduzioni parziali.
- **`excluded_build_artifacts`** — nuovo campo in `zenzic.toml` che accetta pattern glob
  (es. `["pdf/*.pdf"]`) per asset generati al momento del build. I link a percorsi corrispondenti
  vengono soppressi in fase di lint senza richiedere il file fisico sul disco.
- **Validazione dei link in stile riferimento** — i link `[testo][id]` vengono ora risolti
  attraverso la pipeline completa di `InMemoryPathResolver` (incluso il fallback i18n).
  In precedenza invisibili al link checker; ora cittadini di prima classe accanto ai link inline.
- **`I18nFallbackConfig`** — `NamedTuple` interno che codifica la semantica del fallback i18n
  (`enabled`, `default_locale`, `locale_dirs`). Progettato per l'estensione: qualsiasi regola
  futura locale-aware può consumare questa config senza ri-analizzare `mkdocs.yml`.
- **Suite Tower of Babel** (`tests/test_tower_of_babel.py`) — 20 scenari che coprono la
  matrice completa della modalità i18n folder: pagine completamente tradotte, traduzioni parziali,
  link fantasma, link diretti cross-locale, collisioni case-sensitivity, percorsi annidati,
  esclusione orfani, guard `ConfigurationError` e link in stile riferimento tra locali.
- **Core engine-agnostico** — Zenzic è una CLI standalone pura, utilizzabile con qualsiasi
  framework di documentazione (MkDocs, Zensical o nessuno). Zero dipendenze da plugin.
- **`InMemoryPathResolver`** — resolver di link deterministico e engine-agnostico in
  `zenzic.core`. Risolve i link Markdown interni rispetto a una mappa di file precostituita
  in memoria. Zero I/O dopo la costruzione; supporta link relativi, assoluti al sito e a frammento.
- **Zenzic Shield** — protezione integrata contro gli attacchi di path traversal durante la
  scansione dei file. `PathTraversal` emerge come esito distinto ad alta gravità.
- **Configurazione gerarchica** — nuovo campo `fail_under` in `zenzic.toml` (0–100) con
  precedenza: flag CLI `--fail-under` > `zenzic.toml` > default `0` (modalità osservazionale).
- **Dynamic Scoring v2** — `zenzic score --save` persiste uno snapshot JSON `ScoreReport`
  (`.zenzic-score.json`) con `score`, `threshold`, `status` e breakdown per categoria,
  pronto per l'automazione dei badge shields.io tramite `dynamic-badges-action`.
- **Documentazione bilingue** — documentazione EN/IT sincronizzata su tutte le sezioni.

### Risolto

- **Falsi positivi file orfani** — `find_orphans()` non segnala più come orfani i file nelle
  sottocartelle dei locali (es. `docs/it/`) quando il plugin i18n è configurato in modalità
  `folder`.
- **Validazione asset non deterministica** — `validate_links_async()` chiamava in precedenza
  `Path.exists()` per ogni link nel percorso critico, producendo risultati dipendenti dall'I/O
  in CI. Il Pass 1 costruisce ora una pre-mappa `known_assets: frozenset[str]`; il Pass 2
  usa appartenenza al set O(1) con zero I/O su disco.
- **Iterazione YAML null-safe** — `languages: null` in `mkdocs.yml` è ora gestito correttamente
  da tutti gli helper i18n (pattern guard `or []`). In precedenza sollevava `TypeError` quando
  la chiave era presente con valore null.
- **Entry point** — `pyproject.toml` corretto in `zenzic.main:cli_main`, che inizializza il
  logging prima di passare il controllo a Typer.
- **Type safety** — risolto il `TypeError` (`MagicMock > int`) nei test dello scorer causato
  da un mock di configurazione non tipizzato.
- **Integrità degli asset** — la generazione degli artefatti di build (`.zip`) è automatizzata
  in `run_demo.sh`, `nox -s preflight` e CI, garantendo uno score 100/100 coerente.
- **Coercizione del tipo `BUILD_DATE`** — formato cambiato da `%Y-%m-%d` a `%Y/%m/%d` per
  impedire a PyYAML di convertire automaticamente la stringa data in `datetime.date`.
- **CVE-2026-4539 (Pygments ReDoS)** — rischio accettato e documentato: il ReDoS in
  `AdlLexer` di Pygments non è raggiungibile nel threat model di Zenzic (Zenzic non elabora
  input ADL; Pygments è usato solo per il syntax highlighting statico della documentazione).
  Esenzione aggiunta a `nox -s security` in attesa di una patch upstream. Tutte le altre
  vulnerabilità restano pienamente auditate.

### Modificato

- **Interfaccia CLI** — rimossi tutti i riferimenti residui al plugin MkDocs; l'API pubblica
  è esclusivamente l'interfaccia a riga di comando. La selezione del generatore (`mkdocs.yml`)
  è rilevata automaticamente a runtime.
- **Self-check `zenzic.toml`** — `excluded_build_artifacts = ["pdf/*.pdf"]` aggiunto alla
  configurazione del repository, eliminando il requisito di pre-generare i PDF prima di
  eseguire `zenzic check all` in locale.
- **Zenzic Shield** — protezione Path Traversal ora integrata nel core di `InMemoryPathResolver`,
  sostituendo il precedente controllo ad-hoc nel wrapper CLI.

---

## [0.3.0] — 2026-03-24 — [RITIRATO]

> Sostituito da `0.3.0-rc1`. Questo tag è stato creato prima del merge del lavoro
> Build-Aware Intelligence (i18n folder-mode, mapping asset O(1), link in stile riferimento).
> Usare `0.3.0-rc1`.

---

## [0.2.1] — 2026-03-24

### Rimosso

- **Supporto `zensical.toml`** — Zensical legge ora `mkdocs.yml` nativamente;
  un `zensical.toml` separato non è più richiesto né supportato come file di
  configurazione del build. Il fixture `examples/broken-docs/zensical.toml` è
  mantenuto solo come asset di test.
- **Dipendenza runtime `mkdocs`** — `mkdocs>=1.5.0` rimosso da
  `[project.dependencies]`. I pacchetti dei plugin MkDocs (`mkdocs-material`,
  `mkdocs-minify-plugin`, `mkdocs-with-pdf`, `mkdocstrings`, `mkdocs-static-i18n`)
  rimangono in `[dependency-groups.dev]` in attesa degli equivalenti nativi
  Zensical per le funzionalità social, minify e with-pdf.
- **Entry-point plugin MkDocs** — `[project.entry-points."mkdocs.plugins"]`
  rimosso. Zenzic non si registra più come entry-point `mkdocs.plugins`.
  Usa `zenzic check all` nella CI invece del plugin.

### Modificato

- **`find_config_file()`** — cerca solo `mkdocs.yml`; logica di preferenza
  `zensical.toml` rimossa.
- **`find_repo_root()`** — risale fino a `mkdocs.yml` o `.git`; non controlla
  più `zensical.toml`.
- **`find_orphans()`** — ramo TOML rimosso; legge sempre `mkdocs.yml` via
  `_PermissiveYamlLoader`. Ramo di fallback localizzazione i18n rimosso.
- **`_detect_engine()`** — semplificato: `mkdocs.yml` è il singolo trigger di
  configurazione; `zensical` viene tentato prima (legge `mkdocs.yml`
  nativamente), poi `mkdocs`. L'euristica `zensical.toml`-first è rimossa.
- **`noxfile.py`** — sessioni `docs` e `docs_serve` usano `zensical
  build/serve`; `preflight` usa `zensical build --strict`.
- **`justfile`** — target `build`, `serve` e `build-release` usano
  `zensical`; `live` è ora un alias per `serve`.
- **`deploy-docs.yml`** — step di build usa `uv run zensical build --strict`.
- **`zenzic.yml`** — trigger path ridotti a `docs/**` e `mkdocs.yml` soltanto.
- **`mkdocs.yml`** — versione aggiornata a `0.2.1`; commento aggiornato per
  indicare la lettura nativa di Zensical.
- **`pyproject.toml`** — override mypy per `mkdocs.*` rimosso (non più
  dipendenza runtime).

### Aggiunto

- **Ristrutturazione documentazione** — nuova sezione `docs/about/` con
  `index.md`, `vision.md`, `license.md` (EN + IT); nuova sezione
  `docs/reference/` con `index.md` e `api.md` (EN + IT).
- **Nav `mkdocs.yml`** — riflette il nuovo layout `about/` e `reference/`
  con le funzionalità Material `navigation.indexes` e `navigation.expand`.

---

## [0.2.0-alpha.1] — 2026-03-23

### Aggiunto

#### Two-Pass Reference Pipeline — `zenzic check references`

- **`ReferenceMap`** (`zenzic.models.references`) — registro stateful per-file per le definizioni di reference link `[id]: url`. CommonMark §4.7 first-wins: la prima definizione di qualsiasi ID nell'ordine del documento vince; le definizioni successive vengono ignorate e tracciate in `duplicate_ids`. Le chiavi sono case-insensitive (`lower().strip()`). Ogni voce memorizza `(url, line_no)` come metadati per report di errore precisi. La proprietà `integrity_score` restituisce `|used_ids| / |definitions| × 100`; protetta da ZeroDivisionError — restituisce `100.0` quando non esistono definizioni.
- **`ReferenceScanner`** (`zenzic.core.scanner`) — scanner stateful per-file che implementa una pipeline in tre fasi: (1) **Harvesting** (`harvest()`) legge le righe tramite generator `_iter_content_lines()` (O(1) RAM per riga), popola la `ReferenceMap` ed esegue lo Zenzic Shield su ogni URL; (2) **Cross-Check** (`cross_check()`) risolve ogni utilizzo `[testo][id]` rispetto alla mappa completamente popolata, emettendo `ReferenceFinding(issue="DANGLING")` per ogni Dangling Reference; (3) **Integrity Report** (`get_integrity_report()`) calcola l'`integrity_score`, segnala le Dead Definitions (`issue="DEAD_DEF"`) e consolida tutti i finding con gli errori prima.
- **`scan_docs_references` / `scan_docs_references_with_links`** — orchestratori di alto livello che eseguono la pipeline su ogni file `.md` in `docs/`. Contratto Shield-as-firewall: il Pass 2 (Cross-Check) viene saltato interamente per qualsiasi file con eventi `SECRET`. Deduplicazione URL globale opzionale tramite `LinkValidator` quando è richiesto `--links`.
- **Zenzic Shield** (`zenzic.core.shield`) — motore di rilevamento segreti che scansiona ogni URL di riferimento durante l'Harvesting usando pattern pre-compilati con quantificatori a lunghezza esatta (nessun backtracking, O(1) per riga). Tre famiglie di credenziali: OpenAI API key (`sk-[a-zA-Z0-9]{48}`), GitHub token (`gh[pousr]_[a-zA-Z0-9]{36}`), AWS access key (`AKIA[0-9A-Z]{16}`). Qualsiasi rilevamento causa l'interruzione immediata con **Exit Code 2**; nessuna richiesta HTTP viene emessa per documenti contenenti credenziali esposte.
- **`LinkValidator`** (`zenzic.core.validator`) — registro di deduplicazione URL globale sull'intero albero della documentazione. `register_from_map()` registra tutti gli URL `http/https` da una `ReferenceMap`. `validate()` emette esattamente una richiesta HEAD per URL unico, indipendentemente da quanti file vi fanno riferimento. Riutilizza il motore asincrono `_check_external_links` esistente (semaphore(20), fallback HEAD→GET, 401/403/429 trattati come vivi).
- **Comando CLI `zenzic check references`** — attiva la pipeline completa in tre fasi. Flag: `--strict` (le Dead Definitions diventano errori bloccanti), `--links` (validazione HTTP asincrona di tutti gli URL di riferimento, 1 ping per URL unico). Exit Code 2 riservato esclusivamente agli eventi Zenzic Shield.
- **Controllo accessibilità alt-text** (`check_image_alt_text`) — funzione pura che segnala sia immagini inline `![](url)` che tag HTML `<img>` senza alt text. `is_warning=True`; promosso a errore con `--strict`. Non blocca mai i deploy per default.
- **Modulo `zenzic.models.references`** — nuova posizione canonica per `ReferenceMap`, `ReferenceFinding`, `IntegrityReport`. `zenzic.core.models` diventa uno shim di re-export per retrocompatibilità.

#### Documentazione

- `docs/architecture.md` — sezione "Two-Pass Reference Pipeline (v0.2.0)": tabella comparativa stateless→document-aware, problema dei forward reference, diagramma ASCII del ciclo di vita, razionale dello streaming tramite generator, invarianti di `ReferenceMap` (first-wins, case-insensitivity, metadati numero di riga), design Shield-as-firewall, diagramma deduplicazione URL globale, gentle nudge accessibilità, riepilogo completo del flusso dati con formula LaTeX dell'integrità.
- `docs/usage.md` — riscrittura completa per v0.2.0: content tab `uv`/`pip` per ogni livello di installazione, `check references` con `--strict`/`--links`, sezione Reference Integrity con formula LaTeX, sezione CI/CD integration (tabella `uvx` vs `uv run`, workflow GitHub Actions, gestione Exit Code 2), sezione Programmatic Usage con esempi API `ReferenceScanner`.
- `README.md` — stile Reference Link ovunque, sezione `## 🛡️ Zenzic Shield`, `> [!WARNING]` per Exit Code 2, tabella dei controlli aggiornata con `check references`.
- Tutti i file di localizzazione italiana (`*.it.md`) sincronizzati con il sorgente inglese secondo la direttiva Parità Documentale.

### Modificato

- Modello di scansione: da **stateless** (riga per riga, senza memoria delle righe precedenti) a **document-aware** (Three-Phase Pipeline con stato `ReferenceMap` per-file).
- Modello di memoria: il generator `_iter_content_lines()` sostituisce `.read()` / `.readlines()` nella pipeline di riferimento — la RAM al picco scala con la dimensione della `ReferenceMap`, non con la dimensione del file.
- Deduplicazione URL globale estesa alla pipeline di riferimento: `LinkValidator` deduplica al momento della registrazione sull'intero albero della documentazione — una sola richiesta HTTP per URL unico indipendentemente dal conteggio dei riferimenti.

### Corretto

- **Forward Reference Trap** — gli scanner single-pass producono falsi errori di Dangling Reference quando `[testo][id]` appare prima di `[id]: url` nello stesso file. Risolto per design nell'architettura Two-Pass: il Cross-Check viene eseguito solo dopo che l'Harvesting ha completamente popolato la `ReferenceMap`.
- Normalizzazione ID di riferimento: gli spazi iniziali/finali e il casing misto vengono rimossi dentro `add_definition()` e `resolve()` — le voci duplicate per ID che differiscono solo per casing o spaziatura sono impossibili per costruzione.

### Sicurezza

- **Exit Code 2** — riservato esclusivamente agli eventi Zenzic Shield. Se `zenzic check references` esce con codice 2, è stato rilevato un pattern di credenziale incorporato in un URL di riferimento. La pipeline si interrompe immediatamente; tutte le richieste HTTP e l'analisi Cross-Check vengono saltate. **Ruota la credenziale esposta immediatamente.**

---

## [0.1.0-alpha.1] — 2026-03-23

### 🚀 Funzionalità

#### Validatore di link nativo — nessun sottoprocesso, nessuna dipendenza MkDocs

- `zenzic check links` — completamente riscritto come validatore Markdown nativo in due pass. Il pass 1 legge tutti i file `.md` in memoria e pre-calcola i set di ancore dalle intestazioni ATX. Il pass 2 estrae i link inline e le immagini tramite `_MARKDOWN_LINK_RE`, risolve i percorsi interni rispetto alla mappa di file in memoria, valida le ancore `#frammento` e rifiuta i path traversal fuori da `docs/`. Il pass 3 (solo `--strict`) esegue il ping degli URL esterni in modo concorrente tramite `httpx` con concorrenza limitata (`asyncio.Semaphore(20)`), deduplicazione URL e degradazione controllata per risposte 401/403/429. MkDocs non è più richiesto per la validazione dei link.

#### Punteggio qualità e rilevamento regressioni

- `zenzic score` — aggrega tutti i risultati dei cinque controlli in un intero ponderato da 0 a 100. Pesi: `links` 35%, `orphans` 20%, `snippets` 20%, `placeholders` 15%, `assets` 10%. Supporta `--format json`, `--save` (persiste snapshot in `.zenzic-score.json`) e `--fail-under <n>`.
- `zenzic diff` — confronta il punteggio corrente con il baseline `.zenzic-score.json`; esce con codice non-zero quando il punteggio regredisce oltre `--threshold` punti.
- `zenzic check all --exit-zero` — produce il report completo ma esce sempre con codice 0; pensato per pipeline CI soft-fail e sprint di miglioramento della documentazione.

#### Server di sviluppo engine-agnostico con pre-flight

- `zenzic serve` — rileva automaticamente il motore di documentazione dalla root del repository e lo avvia con `--dev-addr 127.0.0.1:{porta}`. Fallback a server di file statici su `site/` quando nessun binario del motore è installato. Risoluzione porta tramite socket probe prima del subprocess. Esegue un pre-flight silenzioso prima dell'avvio; usa `--no-preflight` per saltarlo.

#### Configurazione

- Campo `excluded_assets` in `ZenzicConfig` — lista di percorsi asset esclusi dal controllo asset non usati.
- Campo `excluded_file_patterns` in `ZenzicConfig` — lista di pattern glob di nomi file esclusi dal controllo orfani.

### 🛡️ Qualità e Test

- **98,4% di copertura test** su `zenzic.core.*` e wrapper CLI.
- **`PermissiveYamlLoader`** in `scanner.py` — gestisce i tag `!ENV` di MkDocs che altrimenti causavano la segnalazione di tutte le pagine come orfane.

### 📦 DevOps

- **Pubblicazione PyPI via OIDC** — workflow `release.yml` pubblica su PyPI usando OpenID Connect trusted publishing; nessun token API a lunga durata.
- **Backend di build hatch** — `pyproject.toml` migrato a `hatchling`; versione ottenuta dai tag git tramite `hatch-vcs`.
- **`zensical` come extra opzionale** — dipendenza `zensical` spostata in `optional-dependencies[zensical]`.
- **Documentazione multilingua (EN/IT)** — tutte le pagine rivolte all'utente disponibili in inglese e italiano.

## [0.1.0] — 2026-03-18

### Aggiunto

- `zenzic check links` — rilevamento di link non validi e ancore mancanti via `mkdocs build --strict`
- `zenzic check orphans` — rileva file `.md` assenti dalla `nav`
- `zenzic check snippets` — controlla la sintassi di tutti i blocchi Python delimitati
- `zenzic check placeholders` — segnala pagine stub e pattern di testo vietati
- `zenzic check assets` — rileva immagini e asset non utilizzati
- `zenzic check all` — esegue tutti i controlli con un solo comando; supporta `--format json` per l'integrazione CI/CD
- Generazione PDF professionale — plugin `with-pdf` integrato con copertina Jinja2 brandizzata e timestamp dinamico
- File di configurazione `zenzic.toml` con modelli Pydantic v2; tutti i campi opzionali con valori predefiniti sensati
- `justfile` — task runner integrato per lo sviluppo rapido (sync, lint, dev, build-release)
- `examples/broken-docs/` — repository di documentazione intenzionalmente rotta per tutti i cinque tipi di controllo
- `noxfile.py` — task runner per sviluppatori: `tests`, `lint`, `format`, `typecheck`, `reuse`, `security`, `docs`, `preflight`, `screenshot`, `bump`
- `scripts/generate_screenshot.py` — screenshot SVG riproducibile del terminale tramite Rich `Console(record=True)`
- Piena conformità REUSE 3.3 / SPDX su tutti i file sorgente
- GitHub Actions — `ci.yml`, `release.yml`, `sbom.yml`, `secret-scan.yml`, `security-posture.yml`, `dependabot.yml`
- Suite documentazione — index, architettura, riferimento controlli e riferimento configurazione
- Pre-commit hook — ruff, mypy, reuse, self-check di Zenzic

---

<!-- ─── Reference link definitions ──────────────────────────────────────────── -->

[keep-a-changelog]: https://keepachangelog.com/en/1.1.0/
[semver]:           https://semver.org/
[0.3.0]:            https://github.com/PythonWoods/zenzic/compare/v0.2.1...v0.3.0
[0.3.0-rc1]:        https://github.com/PythonWoods/zenzic/compare/v0.2.1...v0.3.0-rc1
[0.2.1]:            https://github.com/PythonWoods/zenzic/compare/v0.2.0-alpha.1...v0.2.1
[0.2.0-alpha.1]:    https://github.com/PythonWoods/zenzic/compare/v0.1.0-alpha.1...v0.2.0-alpha.1
[0.1.0-alpha.1]:    https://github.com/PythonWoods/zenzic/compare/v0.1.0...v0.1.0-alpha.1
[0.1.0]:            https://github.com/PythonWoods/zenzic/releases/tag/v0.1.0
