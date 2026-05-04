<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Archivio Changelog

Versioni storiche di Zenzic (v0.1.0 – v0.5.x) prima dell'era Obsidian.

Per la storia delle release correnti, consultare il [Changelog principale](CHANGELOG.it.md).

---

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
  — _Canary (prevenzione):_ `_assert_regex_canary()` stress-testa ogni pattern
    `CustomRule` sotto un watchdog `signal.SIGALRM` di 100 ms. I pattern ReDoS
    sollevano `PluginContractError` prima della prima scansione.
  — _Timeout (contenimento):_ `ProcessPoolExecutor.map()` sostituito con
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

---

## Cronologia di Sviluppo v0.7.0 (Archiviata)

> **Nota:** Questa sezione contiene la cronologia di sviluppo granulare della v0.7.0,
> archiviata per tracciabilità. Per le note di rilascio distillate, vedere il
> [Registro delle Modifiche principale](CHANGELOG.it.md).

## [0.7.0] — data prevista di rilascio 2026-05-05 — Quartz Maturity (Stable)

Zenzic v0.7.0 segna la transizione a un **Sovereign Knowledge System**. Dopo l'Assedio
Ossidianico e il Tribunale Quartz, questa release stabilisce lo **standard Quartz** per
precisione, sicurezza e integrità della documentazione. Il codebase raggiunge la maturità
strutturale: 1.342 test, copertura >80%, SARIF sovereignty dinamica, auto-discovery del motore
e Shield hardened con decodifica Base64 speculativa. Sostituisce v0.6.1.

> **Documentazione precedente:** Le versioni precedenti a v0.7.0 sono ufficialmente deprecate
> e non seguono l'attuale architettura Diátaxis. Per riferimento storico, vedere la
> [Release v0.6.1 su GitHub](https://github.com/PythonWoods/zenzic/releases/tag/v0.6.1).
> La fonte autorevole è [zenzic.dev](https://zenzic.dev).

## [Non rilasciato]

### Quartz Polish — Brand Purity & Hook Parity (2026-05-03)

#### Aggiunto

- **`📜 Log: v0.7.0 — Quartz Maturity`** patch-notes pubblicate sul blog
  ufficiale (specchio di `RELEASE.md` leggibile in 30 secondi).
- **Determinism Invariant** in `pyproject.toml` — contratto formale che
  Zenzic non spedisce nessuna dipendenza AI/ML.
- **Zero-Legacy Policy** — `forbidden_patterns` in `.zenzic.dev.toml`
  esteso con `Legacy Sovereign Engine`, `analisi strutturale`, `structural-map-check`,
  `Memoria Strutturale`, `Memoria Legacy` (firewall regression-proof).

#### Modificato — Breaking

- **`.pre-commit-hooks.yaml`** — l'id `zenzic-check-all` è stato
  rimosso (zero alias di compat) e sostituito da `zenzic-verify`
  (equivalente alla porzione Zenzic di `just verify`). Esempio `rev:`
  aggiornato da `v0.5.0a3` a `v0.7.0`. Entry: `--strict --quiet`.
  Migrazione per i downstream:

  ```diff
  -      - id: zenzic-check-all
  +      - id: zenzic-verify
  ```

- **README.md / README.it.md** — link "Zenzic Engineering Series" su
  Dev.to sostituito con il canonico
  `/blog/tags/engineering-chronicles`. La narrativa blog è ora
  auto-canonica.

#### Rimosso

- `scripts/map_project.py` — superato; nessun chiamante residuo in CI o
  `justfile`.
- `coverage.json` rimosso dal tracking (artefatto effimero; aggiunto a
  `.gitignore`).
- Riferimenti residui a `Legacy Sovereign Engine` in `src/zenzic/core/codes.py` e
  `src/zenzic/cli/_standalone.py` (scrub cosmetico — il CLI era già
  stato cancellato nel commit `41eaafc`).

### EPOCH 6 — Sovranità della Fiducia Cross-Instance (2026-05-03)

#### Aggiunto

- **Modello `LinkValidationConfig`** (`zenzic.models.config`) con il
  campo `absolute_path_allowlist: list[str]` — prefissi di percorso
  assoluto fidati che bypassano `Z105 ABSOLUTE_PATH` per riferimenti
  cross-plugin legittimi in setup Docusaurus multi-istanza.
- **Sezione di configurazione `[link_validation]`** in `zenzic.toml`.
  Vuota di default (zero variazioni di comportamento per i progetti
  esistenti).
- **Integrazione `DocusaurusAdapter`** — quando un prefisso di link
  assoluto matcha l'allowlist, il validator salta silenziosamente Z105
  e tratta l'URL come una Trusted Ghost Route.
- **5 test contrattuali** (`tests/test_docusaurus_adapter.py
  ::TestAbsolutePathAllowlist`):
  - 3 test happy-path che coprono allowlist hit, miss e configurazione mista.
  - 2 break-test distruttivi Team-D che dimostrano che l'allowlist non
    può silenziosamente degradare in catch-all (typo → emette ancora Z105;
    collisione `startswith` su prefisso bare documentata come invariante).

#### Documentazione (zenzic-doc, commit separato)

- **ADR-0011 "Cross-Instance Allowlist"** (EN+IT) inclusa la sezione
  "Soppressione vs Configurazione" che codifica la dottrina di
  ortogonalità: `absolute_path_allowlist` = contratto a livello di
  repository; `<!-- zenzic:ignore -->` = eccezione locale chirurgica.
  L'ADR vieta formalmente `<zenzic-ignore Z105>` per i link cross-plugin.
- **`/docs/how-to/manage-cross-site-links.mdx`** (EN+IT) — how-to
  Diátaxis user-facing.
- **`/docs/reference/configuration.mdx#link-validation`** (EN+IT) —
  reference dello schema.
- **`/developers/governance/technical-debt.mdx`** (EN+IT) — Z108
  STALE_ALLOWLIST_ENTRY rinviato esplicitamente a v0.8.0 "Basalt"
  (violazione del Pilastro 3 se implementato inline; richiede un
  comando dedicato `zenzic inspect config`).

#### Rinviato a v0.8.0

- **Z108 `STALE_ALLOWLIST_ENTRY`** — check di igiene della config che
  avvisa quando una voce dell'allowlist non corrisponde più ad alcun
  link cross-plugin reale. Il rinvio è intenzionale: implementarlo
  dentro il validator per-link violerebbe il Pilastro 3 (Pure Functions)
  introducendo stato mutabile condiviso attraverso la scansione. La sede
  corretta è un comando read-only separato `zenzic inspect config`.
  Tracciato nel Ledger del Debito Tecnico.

### EPOCH 5 — Z907 I18N_PARITY + Restructure Diátaxis Documentazione (2026-05-03)

#### Aggiunto

- **Z907 `I18N_PARITY`** — nuovo scanner core che verifica che ogni file
  di documentazione nella lingua base abbia un mirror in ciascuna root
  di lingua target configurata, più la parità opzionale delle chiavi di
  frontmatter (es. `title`, `description`). Language-agnostic: `base_lang`
  e `targets[]` sono dichiarati in config, nessun codice locale è
  cablato nel codice.
- **Sezione di configurazione `[i18n]`** in `zenzic.toml` (e l'equivalente
  `[tool.zenzic.i18n]` in `pyproject.toml`). Modelli: `I18nConfig`,
  `I18nSource`. Supporta `extra_sources` per repository con più root di
  documentazione (es. user-facing docs + developer docs).
- **Escape hatch `i18n-ignore: true` nel frontmatter** — file che non
  devono imporre la parità (bozze, guide lang-specific) si auto-escludono
  per-file.
- **Parallelismo adattivo** — quando la popolazione base supera
  `ADAPTIVE_PARALLEL_THRESHOLD` (50 file), Z907 distribuisce il lavoro
  per-file su un `ThreadPoolExecutor`, replicando il pattern del resto
  della pipeline scanner. Contratto pure-function preservato (Pillar 3).
- **Stress test Hypothesis** per Z907 — generatore property-based che
  copre nesting di directory profondo e segmenti unicode Latin Extended
  (es. `café/résumé`), così gli edge case vengono catturati prima di
  qualunque migrazione documentale big-bang.

### EPOCH 4 — Pipeline Qualità Unificata 4-Gates (2026-05-03)

#### Modificato (BREAKING per i contributor)

- **`just verify` è ora l'unico punto d'ingresso atomico** della pipeline
  qualità. Stesso comando in locale (via hook pre-push) e in GitHub
  Actions: locale ≡ remoto, niente drift.
- **`just test` riscritto** come inner loop TDD veloce: `pytest -n auto`
  senza coverage. Il Pillar 3 (Pure Functions) garantisce l'isolamento
  dei worker pytest-xdist.
- **`just test-cov` introdotto** per il run di audit: pytest seriale con
  coverage XML (allineato alla matrice CI). `just verify` invoca
  `test-cov` così la soglia `fail_under = 80` viene applicata prima di
  ogni push.
- **Nox declassato a "gestore di ambienti isolati"** — solo matrice
  multi-versione (3.11/3.12/3.13). Sessione `preflight` rimossa
  (logica duplicata con `just verify`).
- **`nox -s dev` ora installa entrambi gli hook pre-commit E pre-push**
  così la Final Guard (`just verify`) parte automaticamente su `git push`.

#### Aggiunto

- **`pytest-xdist>=3.6`** aggiunto al gruppo dipendenze `test`.
- **Stage pre-push in `.pre-commit-config.yaml`** — nuovo hook locale
  `just-verify` (id `just-verify`, stages `[pre-push]`) chiude il gap
  storico in cui `pre-commit install -t pre-push` installava un hook
  vuoto.
- **`.github/ISSUE_TEMPLATE/gate-bypass-postmortem.md`** — template
  protocollo Break-Glass (D7). Post-mortem blameless obbligatorio entro
  24h per ogni bypass `--no-verify` documentato.
- **Sezione "The 4-Gates Standard" in CONTRIBUTING.md** che documenta il
  flusso TDD → commit → push → CI + policy Emergency / Break-Glass.

#### Migrazione

I contributor devono rieseguire il bootstrap dopo il pull di questa modifica:

```bash
just sync
uvx pre-commit install              # stage commit (hook leggeri)
uvx pre-commit install -t pre-push  # 🛡️ Final Guard (just verify)
```

Ricetta `just preflight` rimossa; usare `just verify`.

### D097 — Applicazione CLOSING PROTOCOL (2026-05-01)

#### Aggiunto

- **Invariante ordinamento CHANGELOG (CEO-293)** codificato in `Legacy Sovereign Engine` [CLOSING PROTOCOL]
  Step 2. Lo sprint più recente va sempre in TESTA a `[Non rilasciato]`; ogni sprint è un heading
  `### Dxxx`; i gruppi CEO sono sub-heading `#### CEO-nnn`; `#### Test` con conteggio è obbligatorio
  e sempre l'ULTIMA sotto-sezione del blocco sprint.
- **`CONTRIBUTING.md` punto 4:** aggiornamento CHANGELOG obbligatorio nello stesso commit del codice —
  non rimandabile al giorno del rilascio. Chiude il gap strutturale che ha causato D096 incompleto
  su più commit.

#### Corretto

- **CHANGELOG.md / CHANGELOG.it.md struttura D096:** sezione `#### Test` duplicata rimossa;
  heading `### D095` ripristinato con separatore `---` corretto.

#### Test

- **1.452 superati · ≥83% copertura** (Python 3.11 / 3.12 / 3.13). Nessuna regressione.

---

### D096 — Quartz Discovery, SARIF Sovereignty & Curazione Strutturale (2026-04-30)

#### Aggiunto

- **`discover_engine(repo_root) -> str`** in `core/adapters/_factory.py`. `get_adapter()` risolve
  `engine="auto"` tramite `discover_engine()` prima della cache key. Priorità: `zensical.toml` →
  `docusaurus.config.ts/js` → `mkdocs.yml` → `"standalone"`.
- **Default `engine` cambiato** da `"mkdocs"` a `"auto"` in `models/config.py`.
- **Z906 NO_FILES_FOUND** registrato in `codes.py`. Livello note, exit 0, solo testo (Regola R20).
- **Regole SARIF generate dinamicamente** da `codes.py` in `cli/_shared.py`. Codici fantasma
  Z301/Z601/Z701 eliminati. `helpUri` per regola: `https://zenzic.dev/docs/reference/finding-codes#{codice.lower()}`.
- **Classe `ZenzicExitCode`** in `codes.py`: `SUCCESS=0`, `QUALITY=1`, `SHIELD=2`, `SENTINEL=3`.
- **`zenzic init` Template Quartz**: `_detect_init_engine()` delega a `discover_engine()`.
  Il `zenzic.toml` generato imposta `fail_under = 100` e `strict = true` come default attivi.
- **Trinity Mesh Awareness** in `scripts/map_project.py`: auditore Zone B (marcatori
  `<!-- ZONE_B_START -->` / `<!-- ZONE_B_END -->`, guardrail 400 righe, warning `[Z907] MEMORY_OVERFLOW`)
  - rilevamento repo sibling (blocco `[MESH STATUS]`).
- **Ristrutturazione Zone A/B** applicata a tutti e 3 i file pubblici `Legacy Sovereign Engine`
  (core, doc, action). Zone A = Costituzionale (Manifesto, Policy, ADR). Zone B = Operativa ([ACTIVE SPRINT]).
- **"The Zenzic Memory Contract"** aggiunto a `CONTRIBUTING.md` (CEO-237).
- **Testimonianza Contemporanea** (zenzic-doc): Z906 in `finding-codes.mdx` EN+IT; engine `"auto"`
  in `configuration-reference.mdx` EN+IT; blog aggiornato a 20 Acts + riga Atto 19.
- **ADR-015** (SARIF Sovereign Automation) e **ADR-016** (Quartz Auto-Discovery) aggiunti a
  `Legacy Sovereign Engine`.

#### Test

- **1.342 superati · 80,28% copertura** (Python 3.11 / 3.12 / 3.13). Nessuna regressione.

#### Cartografia Sovrana e Identity Gate (CEO-242–249)

- **`src/zenzic/core/cartography.py`** — scanner AST puro: `scan_python_sources`,
  `render_markdown_table`, `update_ledger`. Zero subprocess (Pillar 2).
- **`src/zenzic/cli/_structural.py`** — sotto-app `structural` (comando `map`): revisore Zona B,
  sonda Trinity Mesh, Master-Shadow Sync. Gated da PEP 610 Identity Gate (`_is_dev_mode()`).
  Gli utenti finali non possono scoprire il gruppo di comandi.
- **`just structural-map`** integrato in `verify` / `preflight`. Regola R24 Zero-Amnesia.
- **ADR-017** (Cartografia Sovrana & Identity Gate) aggiunto a `Legacy Sovereign Engine`.
- **CEO-249 Canary Hardening:** lunghezze `_CANARY_STRINGS` n=30→50 / n=25→40 / n=20→32,
  garantendo percorsi di backtracking O(2^50). `_CANARY_TIMEOUT_S` 0.1→0.05.
  Pattern di test `(a|aa)+` → `(a+)+` — ADR-018 documenta la motivazione SIGALRM.

#### Audit Gate Quartz (CEO-257–258)

- **`analisi strutturale --check`** — modalità audit sola lettura. Esce con 1 e `D001 MEMORY_STALE`
  se la [CODE MAP] non è sincronizzata con `src/`. Hook pre-commit `structural-map-check` aggiunto.

#### Sigillo di Integrità Developer + Porta Privacy Ambientale (CEO-259–283)

- **`cartography.py`** esteso: `load_dev_gate()`, `check_perimeter()` (letterale, no regex,
  sicuro da ReDoS), `check_sources_perimeter()`, `redact_perimeter()` (Redattore Sovrano),
  `render_json()` (AST leggibile da macchina). ADR-019.
- **Gate D002 a doppio spettro:** Fase A = Redattore Sovrano (silenzioso `[REDACTED_BY_SENTINEL]`).
  Fase B = audit sorgente VCS-Aware (`walk_files + LayeredExclusionManager`, `.py/.md/.mdx/.toml/.yml`).
  Immunità Sovrana: `.zenzic.dev.toml` sempre immune via `exclude=frozenset({dev_toml.resolve()})`.
- **Protocollo Test Sintetico (CEO-279):** token proibito mai su disco — assemblato a runtime
  dai frammenti `_PART_A` / `_PART_B`. Zero auto-violazione D002 Fase B.
- **Standard Perimetro Snello (CEO-280):** `forbidden_patterns` ridotto a 1 voce in tutti i repo.
- **Unified Vision Sweep (CEO-283):** `scan_python_sources` migrato da `rglob` a
  `walk_files + LayeredExclusionManager`. Zero `rglob` in qualsiasi modulo di produzione.

#### Sovranità Ambientale (CEO-252)

- **Flag `--no-external`** aggiunto a `check links` e `check all` (Simmetria CLI CEO-056).
  Salta il Passaggio 3 (richieste HTTP HEAD) indipendentemente da `--strict`. Lo Shield
  (Z201/Z202/Z203) si attiva sempre — opera sul contenuto grezzo del file, non sulla rete.
  Messaggio INFO di trasparenza in modalità testo (conforme Regola R20). Hook pre-commit
  dev aggiornato a `--strict --no-external` per il gate offline.
- **Parametro `check_external: bool = True`** propagato attraverso `validate_links_async()`,
  `validate_links()`, `validate_links_structured()`, `_collect_all_results()`.
- **R27 Sovranità Ambientale** codificato in `Legacy Sovereign Engine` [POLICIES].
- **`cli.mdx` EN+IT** aggiornato: tabelle del flag `--no-external` (zenzic-doc).

#### Test

- **1.452 superati · ≥83% copertura** (Python 3.11 / 3.12 / 3.13). Nessuna regressione.
  `test_structural.py`: 84 test. `test_validator.py::TestCheckExternalFlag`: 3 nuovi test.
  `test_cli.py`: test firma esistente aggiornato per `check_external=True`.

---

### D095 — Il Decoder Sentinella Base64 & Invariante Universale dei Percorsi

#### Aggiunto

- **Decoder Base64 speculativo in `shield.py` (CEO-194).** `_BASE64_CANDIDATE_RE` estrae
  token candidati da ogni riga normalizzata; `_try_decode_base64()` decodifica ciascuno
  come UTF-8; il testo decodificato viene ri-scansionato attraverso la tabella completa
  dei pattern `_SECRETS`. Questo sigilla il vettore di attacco S2 del Tribunale Quartz:
  un GitHub PAT codificato in Base64 nel frontmatter YAML ora attiva Z201 ed esce con 2.
  Guardia contro falsi positivi: lunghezza minima token 20 caratteri prima della decodifica.
  Nuovi import: `base64`, `binascii`.

- **Fix di portabilità `os.path.normcase` in `resolver.py` (CEO-203 / KL-002).** Il
  confronto del perimetro Shield ora applica `os.path.normcase` sia al percorso target che
  agli slot precomputati `_allowed_root_pairs_nc` / `_repo_root_nc_*`. Su Linux,
  `normcase` è l'identità — nessun cambio di comportamento. Su macOS (APFS) e Windows
  (NTFS), percorsi legittimi con case misto non producono più falsi positivi PathTraversal.
  Il `target_str` originale è preservato per la ricerca dei file. Tre nuovi `__slots__` aggiunti.

- **Atto 19 "The Base64 Shadow" in `zenzic lab`.** Dimostra il vettore di attacco S2
  sigillato da CEO-194. `expected_breach=True`. Sezione Scenari di Scoring estesa a
  `range(17, 20)`. Stringhe di errore in `parse_act_range` aggiornate da `0–18` → `0–19`.

- **Fixture `examples/scoring/security-base64/`** (2 file): `zenzic.toml` + `secret.md`
  con un GitHub PAT codificato in Base64 nel frontmatter YAML. Utilizzata dall'Atto 19.

- **`docs/explanation/audit-v070-quartz-siege.mdx`** (EN + IT) pubblicato in zenzic-doc.
  Pagina Explanation Diátaxis — "Il Tribunale Quartz" Libro Bianco che documenta l'audit
  di sicurezza AI-driven: 3 vettori di attacco, 7 bug sigillati, metriche di certificazione.

#### Corretto

- **README EN+IT:** Paragrafo Shield aggiornato — aggiunta frase sulla decodifica speculativa
  Base64.

- **`finding-codes.mdx` Z201 EN+IT:** Contesto Tecnico riscritto per descrivere la scansione
  multi-fase (grezza + normalizzata + decodifica Base64 speculativa).

#### Test

- `test_shield_obfuscation.py::TestBase64Bypass` — **sostituito** (era un placeholder per
  limitazione nota). 4 nuovi test: `test_base64_github_pat_detected` (vettore canonico
  CEO-201), `test_base64_aws_key_detected`, `test_base64_short_string_no_false_positive`,
  `test_base64_innocent_prose_no_false_positive`.

- `test_resolver.py::TestNormcasePortability` — 3 nuovi test che verificano il fix di
  portabilità KL-002: root con lettere maiuscole risolve correttamente; traversal con case
  misto ancora bloccato; normcase non apre gap tramite allowed roots extra.

- **1.307 superati · 0 falliti · 80,28% copertura** (Python 3.11 / 3.12 / 3.13).

---

### D091 — Integrità del Brand Quartz (Z107 · Z505 · Z905)

#### Aggiunto

- **`CircularAnchorRule` (Z107 CIRCULAR_ANCHOR).** Nuova sottoclasse `BaseRule` che rileva
  link ancora auto-referenziali (`[testo](#heading)` dove `heading` risolve alla stessa
  pagina). Calcola lo slug di tutti i heading e li confronta con i link ancora locali.
  Uscita 1, sopprimibile.

- **`UntaggedCodeBlockRule` (Z505 UNTAGGED_CODE_BLOCK).** Nuova sottoclasse `BaseRule`
  che rileva blocchi di codice recinzati privi di specificatore di linguaggio.
  Implementa l'invariante CommonMark: un fence di chiusura deve avere una info string
  vuota. Qualsiasi carattere non-spazio nella info string è trattato come apertura —
  i metadati Docusaurus (es. `` ```python title="file.py" showLineNumbers ``) sono
  gestiti correttamente. Uscita 1, sopprimibile.

- **`BrandObsolescenceRule` (Z905 BRAND_OBSOLESCENCE).** Nuova sottoclasse `BaseRule`
  che scansiona identificatori di release obsoleti. Configurata via `[project_metadata]`
  in `zenzic.toml`. Le righe con il token `[HISTORICAL]` vengono silenziosamente saltate.
  I pattern di file in `obsolete_names_exclude_patterns` (default: `CHANGELOG*.md`) sono
  completamente esenti. Uscita 1, sopprimibile. Pickle-safe.

- **Modello Pydantic `ProjectMetadata`** in `src/zenzic/models/config.py`.
  Campi: `release_name: str`, `obsolete_names: list[str]`,
  `obsolete_names_exclude_patterns: list[str]` (default: `["CHANGELOG*.md", "CHANGELOG*.archive.md"]`).
  Integrato in `ZenzicConfig` e `_HANDLED_SECTIONS`.

- **Z107, Z505, Z905 registrati** in `src/zenzic/core/codes.py`. Tutti e tre:
  `primary_exit=1, non_suppressible=False`.

- **`_build_rule_engine()` in `scanner.py`** aggiunge sempre `CircularAnchorRule` e
  `UntaggedCodeBlockRule`; aggiunge condizionalmente `BrandObsolescenceRule` quando
  `obsolete_names` è non vuoto.

- **`zenzic init`** — il template TOML include un blocco `[project_metadata]` commentato.

- **CEO-138 semantica info string.** `has_tag = bool(info.strip())` — qualsiasi carattere
  non-spazio nella info string del fence marca un blocco come etichettato.

- **CEO-140 invariante CommonMark fence di chiusura.** Un fence di chiusura richiede:
  stesso carattere dell'apertura, lunghezza ≥ apertura, **info string vuota** (`not info`).
  Questo ha eliminato 10 falsi positivi Z505 in architecture.mdx.

#### Test

- 18 nuovi test tra `TestCircularAnchorRule`, `TestUntaggedCodeBlockRule`,
  `TestBrandObsolescenceRule` (inclusi 3 casi limite CEO-138/140).
  **1 281 passati · 0 falliti · 80,81% di copertura.**

---

### D090 — La Legge di Raggiungibilità UX (Raccolta Navigazione Navbar + Footer)

#### Aggiunto

- **Scoperta Navigazione Unificata — Multi-Source Harvester Docusaurus.**
  `_parse_config_navigation()` aggiunta a `_docusaurus.py`. Legge
  `docusaurus.config.ts` tramite regex puro Python (Pillar 2 — nessun Node.js) ed
  estrae i valori `to:` e `docId:` sia da `themeConfig.navbar.items` **sia** da
  `themeConfig.footer.links`. I valori `to:` vengono risolti rimuovendo i prefissi
  `baseUrl` e `routeBasePath`, poi verificando l'esistenza del file `.md` / `.mdx`
  su disco. I link non-doc (blog, URL esterni) non corrispondono mai a nessun file
  e vengono ignorati silenziosamente.

- **`DocusaurusAdapter.get_nav_paths()` è ora un vero Aggregatore Multi-Sorgente.**
  Restituisce `sidebar_paths | navbar_paths | footer_paths`. Un file viene
  classificato `ORPHAN_BUT_EXISTING` solo se assente da tutte e tre le superfici
  di navigazione UI (sidebar, navbar, footer) — implementando la
  **Legge di Raggiungibilità UX (R21)**: _un file è REACHABLE se qualsiasi
  superficie cliccabile dall'utente lo dichiara_.

- **`_navbar_paths: frozenset[str]`** memorizzato preventivamente da `from_repo()`
  così che `get_nav_paths()` rimanga un aggregatore puro senza I/O.

- **Fixture Atto 7 espansa** (`docusaurus-v3-enterprise`):
  - `sidebars.ts` — sidebar esplicita (intro + guide/*, senza changelog o about).
  - `docs/changelog.mdx` — collegato solo dalla navbar → atteso REACHABLE.
  - `docs/about.mdx` — collegato solo dal footer → atteso REACHABLE.
  - `docusaurus.config.ts` — aggiornato con `themeConfig.navbar` e `themeConfig.footer`.

- **`engines.mdx`** — nuova sezione "Scoperta Navigazione Unificata" che documenta
  l'aggregazione a 3 sorgenti, la Legge di Raggiungibilità UX e il contratto
  `ORPHAN_BUT_EXISTING`. "Plugin sidebar dinamici" generalizzato a "Plugin nav dinamici".

#### Architettura

- **Risultato audit MCP registrato:** In Docusaurus, il routing è guidato dal
  filesystem — tutti i file in `docs/` ricevono un URL indipendentemente da
  sidebar/navbar/footer. Le superfici di navigazione sono costrutti di
  scopribilità UX. Il modello orfani di Zenzic è **basato sulla scopribilità**,
  non sull'esistenza dell'URL. Gli adapter MkDocs e Zensical confermati
  architetturalmente completi.

- **Purezza del Core mantenuta:** `validator.py` non contiene riferimenti a
  "navbar", "sidebar" o "footer". Il Core chiama solo `adapter.get_nav_paths()`.

#### Test

- 14 nuovi test: `TestParseConfigNavigation` (NCF-01..10) + `TestUnifiedNavigation` (NCI-01..04).
  **1 260 passing · 0 failing.**

---

### D085 — Full-Spec Alignment (Parser Sidebar Docusaurus + Chiusura #52)

#### Aggiunto

- **Parser statico sidebar Docusaurus — Issue #47 chiusa.**
  `DocusaurusAdapter.get_nav_paths()` ora legge `sidebars.ts` o `sidebars.js` tramite
  un parser regex puro Python (Pillar 2 — nessun Node.js). Se qualsiasi sidebar usa
  `type: 'autogenerated'`, tutti i file rimangono `REACHABLE` (comportamento attuale
  preservato). Con sidebar esplicita, solo gli ID doc elencati sono `REACHABLE`; le
  pagine non elencate vengono correttamente classificate come `ORPHAN_BUT_EXISTING`.
  Il rilevamento usa l'esistenza del file come verità — i falsi positivi da stringhe
  label vengono filtrati naturalmente. `from_repo()` rileva automaticamente
  `sidebars.ts` / `sidebars.js` nella root del repository.

#### Risolto / Chiuso

- **Issue #52 (output SARIF)** chiusa — già implementata nel sprint D081/D082.
  `_shared.py` contiene il formatter completo SARIF 2.1.0; `_check.py` espone
  `--format sarif` su tutti e cinque i comandi check. Nessuna ulteriore modifica necessaria.

#### Test

- 14 nuovi test: `TestParseSidebars` (SBP-01..10) + `TestFromRepoSidebar` (SBI-01..04).
  **1 246 passing · 0 failing.**

---

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

### Il Passaggio Quartz Mirror: Lab, Shield & Allineamento Docs (Direttive 082–086)

#### Aggiunto

- **Z404 CONFIG_ASSET_MISSING (Direttiva 085).** L'adapter Docusaurus analizza ora
  staticamente `docusaurus.config.ts` e verifica che ogni percorso `favicon:` e `image:`
  (OG social card) risolva in un file reale all'interno di `static/`. Implementato come
  `check_config_assets()` in `_docusaurus.py` — puro regex, zero subprocess. Codice
  registrato in `codes.py`; collegato tramite `_AllCheckResults.config_asset_issues` in
  `cli.py`. Severità: `warning` (promuovibile a Exit 1 via `--strict`).
- **Lab Sentinel Seal (Direttiva 086).** Ogni esecuzione `zenzic lab <N>` si chiude
  ora con un pannello **Sentinel Seal** dedicato (bordo indigo, colori Sentinel Palette)
  che mostra il conteggio file, tempo trascorso, throughput in file/s e un verdetto
  pass/fail per atto. I sommari di esecuzione completa mostrano un Sentinel Seal
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

### Passaggio Quartz Integrity: Hardening UX e Audit della Verità (Direttive 076–079)

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

### Espansione Enterprise CI (Direttive CEO 092–095)

#### Aggiunto

- **Esportazione SARIF 2.1.0 — `--format sarif` (Direttiva CEO 092).**
  Tutti i sotto-comandi `check` (`links`, `orphans`, `snippets`, `references`, `assets`, `all`)
  accettano ora `--format sarif`. Il formatter produce JSON SARIF 2.1.0 valido con l'URL
  SchemaStore nel campo `$schema` (`https://json.schemastore.org/sarif-2.1.0.json`),
  regole nominate e punteggi `properties.security-severity` (`9.5` per `security_breach`,
  `9.0` per `security_incident`). Il caricamento di `zenzic-results.sarif` su GitHub Code
  Scanning espone i risultati direttamente nei diff delle Pull Request e nella tab Security
  del repository — senza dover analizzare i log.
- **Matrice CI Cross-Platform — runner Windows e macOS (Direttiva CEO 093).**
  Il job `quality` in `.github/workflows/ci.yml` testa ora ogni commit su una matrice
  `3 × 3`: `os: [ubuntu-latest, windows-latest, macos-latest]` ×
  `python-version: ["3.11", "3.12", "3.13"]`. `fail-fast: false` garantisce che tutte
  e 9 le combinazioni vengano riportate. Il caricamento della copertura è limitato a
  `ubuntu-latest / 3.13`.
- **GitHub Action Ufficiale — `PythonWoods/zenzic-action` (Direttiva CEO 094).**
  Action composita scaffoldata nel repository `zenzic-action`. Installa Zenzic tramite
  `uv tool install`, esegue `check all --format sarif`, scrive `zenzic-results.sarif` e
  carica il file tramite `github/codeql-action/upload-sarif`. Input configurabili:
  `version`, `docs-dir`, `format`, `sarif-file`, `upload-sarif`, `strict`,
  `fail-on-error`. Elimina la necessità di invocazioni manuali `uvx zenzic` in CI.

---

### Sprint Sigillo Bilingue — Multi-Root Safe Harbor (D123–D128)

#### Aggiunto

- **Risoluzione Multi-Root dei Percorsi** (D124) — `InMemoryPathResolver` accetta ora
  `allowed_roots: list[Path]`. Quando vengono fornite le radici locale, i link
  relativi cross-locale (es. `i18n/it/intro.md` → `i18n/it/guide.md`) si
  risolvono correttamente invece di generare un falso positivo
  `PATH_TRAVERSAL_SUSPICIOUS`. L'invariante di sicurezza è preservata: i target
  al di fuori di tutte le radici autorizzate vengono comunque rifiutati.

- **Integrità delle Ancore i18n Obbligatoria** (D125) — La validazione delle
  ancore same-page è ora **sempre attiva** per i file nelle directory locale
  `i18n/`, indipendentemente dal flag di configurazione
  `validate_same_page_anchors`. Un traduttore che aggiorna `[link](#contesto)`
  lasciando il titolo come `{#context}` viene rilevato immediatamente.

- **Alias `@site/` espanso a `repo_root`** (D123) — `known_assets` ora scansiona
  `repo_root` invece del solo `docs_root`, in modo che i riferimenti alle
  immagini Docusaurus `@site/static/` all'interno dei file locale si risolvano
  correttamente.

- **Auto-rilevamento Docusaurus in `zenzic init`** (D128) — `zenzic init` ora
  rileva `docusaurus.config.ts` / `docusaurus.config.js` ed emette un template
  `[build_context]` espanso con commenti i18n e la nota Multi-Root Safe Harbor.
  URL di riferimento alla configurazione aggiornato a `zenzic.dev/docs/reference/`.

---

### Sprint Parità Codebase & Robustezza Cross-Platform (2026-04-24)

#### Corretto

- **Fallback asset case-sensitive su Windows / macOS** — `resolve_asset()` nei tre
  moduli adapter (`_mkdocs.py`, `_zensical.py`, `_docusaurus.py`) usava `Path.exists()`
  per testare i percorsi di fallback, che restituisce `True` sui filesystem
  case-insensitive indipendentemente dalla capitalizzazione. Sostituito con
  `case_sensitive_exists()` (nuovo helper in `_utils.py`, basato su `os.listdir()`)
  che impone la corrispondenza esatta su ogni piattaforma. Corregge una regressione CI
  rilevata sulle leg Windows e macOS della matrice cross-platform.

- **Commenti MDX / HTML esclusi dal conteggio parole dei placeholder** —
  `check_placeholder_content()` contava le parole nel sorgente Markdown grezzo,
  consentendo ai commenti `{/* … */}` MDX e `<!-- … -->` HTML di gonfiare il conteggio
  visibile. Un file sotto la soglia `placeholder_max_words` non veniva segnalato se
  conteneva un'intestazione di commento lunga. Introdotto `_visible_word_count(text)`
  che elimina frontmatter YAML, commenti MDX e commenti HTML prima della divisione.
  Aggiunto test di regressione `test_placeholder_mdx_comments_excluded_from_word_count`.

- **Guard di migrazione Z000 promosso da TODO a permanente** — `_factory.py` riportava
  `# TODO: Remove this migration guard in v0.7.0`, lasciando intendere che il controllo
  su `engine = "vanilla"` fosse temporaneo. Il guard è intenzionalmente permanente
  (vanilla è stato rimosso in v0.6.1); sostituito con un commento esplicativo.

- **Audit di parità documentazione** (zenzic-doc) — Tredici riferimenti rimasti alla
  classe rimossa `VanillaAdapter` sostituiti con `StandaloneAdapter` (locale EN + IT).
  Esempi JSON in `cli.mdx` e `configure-ci-cd.mdx` usavano il codice inesistente
  `"BROKEN_LINK"`; corretto in `"Z104"` con il formato messaggio canonico. L'entry Z000
  in `finding-codes.mdx` ora documenta esplicitamente che è un'eccezione
  `ConfigurationError` assente dall'output `--format json`. Il diagramma ASCII dello
  scanner dei riferimenti in `checks.mdx` sostituito con un `flowchart LR` Mermaid
  con i colori ObsidianPalette.

#### Sicurezza

- **CVE-2026-3219 — gestione archivi poliglotti da pip** — `pip 26.0.1` è affetto da
  CVE-2026-3219 (archivi tar + ZIP concatenati trattati come ZIP indipendentemente dal
  nome file; nessuna release corretta su PyPI). Zenzic usa `uv` per tutta la gestione
  dei pacchetti e non invoca mai pip programmaticamente; pip è una dipendenza dev-only
  transitiva di pip-audit. Tutti i pacchetti sono bloccati in `uv.lock`. Aggiunto
  `--ignore-vuln CVE-2026-3219` alla sessione `nox security` con promemoria di rimozione.

---

### Sprint Copertura Test & Mutation Testing (2026-04-24)

#### Aggiunto

- **`tests/test_cache.py`** (29 test) — copertura completa di `src/zenzic/core/cache.py`.
  Helper hash puri (`make_content_hash`, `make_config_hash`, `make_vsm_snapshot_hash`,
  `make_file_key`) e operazioni in-memory e I/O di `CacheManager` (`get`, `put`, `load`,
  `save`). Copre scrittura atomica, creazione directory parent, fallback JSON corrotto e
  pulizia OSError tramite monkeypatching di `json.dump`.

- **`tests/test_reporter.py`** (12 test) — copertura di `_read_snippet` e `_strip_prefix`
  in `src/zenzic/core/reporter.py`. Verifica la guardia `or`/`and` nel caso file vuoto /
  line_no non valido, il clamping del context-window a inizio e fine file, e la semantica
  dello strip del prefisso (bypass linea 0, ritenzione corrispondenza parziale).

- **`TestToCanonicalUrlMutantKill`** (15 test) aggiunto a `tests/test_rules.py` — targeta
  `VSMBrokenLinkRule._to_canonical_url`. Uccide le mutazioni `rstrip(None)` / `lstrip("/")`,
  normalizzazione backslash, strip `index.md` → directory padre, risoluzione `..`
  context-aware, inversioni della logica di guardia `source_dir`/`docs_root` e caso limite
  path relativo `"."`.

- **`TestObfuscateSecretMutantKill`** (7 test) aggiunto a `tests/test_redteam_remediation.py`
  — targeta `_obfuscate_secret` in `reporter.py`. Uccide le mutazioni boundary `<= 8` → `< 8`,
  `<= 8` → `<= 9` e la mutazione di larghezza prefisso `raw[:4]` → `raw[:5]`. Verifica che
  il conteggio asterischi sia `len(raw) - 8` e che la lunghezza totale sia sempre preservata.

- **`TestNormalizeLineForShieldMutantKill`** (4 test) aggiunto a
  `tests/test_shield_obfuscation.py` — uccide la sostituzione commento MDX → `"XXXX"`
  (mutmut_22), pipe tabella → `"XX XX"` (mutmut_40) e join spazio → `"XX XX".join`
  (mutmut_42).

- **Run di mutation testing `mutmut`** su `rules.py`, `shield.py`, `reporter.py` — run
  completata. Oltre 200 mutanti sopravvissuti analizzati; i mutanti logici ad alto impatto
  in `_to_canonical_url`, `_obfuscate_secret` e `_normalize_line_for_shield` uccisi dai
  nuovi test. I mutanti sopravvissuti restanti classificati come equivalenti (variazioni di
  stringhe template in `SentinelReporter.render`, asserzioni difensive, o mutazioni
  `encoding="UTF-8"` / `errors="REPLACE"` con comportamento runtime identico).

---

### Sprint Integrità Sentinel & Codificazione della Conoscenza (D041–D047 — 2026-04-25)

#### Corretto

- **Falso positivo Blood Sentinel — target esterni espliciti (Direttiva CEO 043 — "The Sentinel's Sanity Pass").**
  `zenzic check all ../percorso-esterno` lanciava Exit 3 (Blood Sentinel) quando il target
  esplicito si trovava fuori dalla radice del repository CWD. La guardia `_validate_docs_root`
  (F4-1) trattava qualsiasi `docs_root` esterna a `repo_root` come un attacco path traversal,
  indipendentemente dal fatto che l'utente avesse fornito esplicitamente quel percorso come
  argomento CLI.
  **Fix (ADR-007 — Sovereign Sandbox):** Dopo la risoluzione di `docs_root`, se
  `docs_root.relative_to(repo_root)` lancia `ValueError`, si riassegna `repo_root = docs_root`.
  Il target utente esplicito diventa la sandbox sovrana; il Blood Sentinel sorveglia le fughe
  _da_ quel target, non la _posizione_ di esso.
  Test di integrazione `test_check_all_external_docs_root_not_blocked_by_sentinel` aggiunto a
  `tests/test_cli.py`.

- **Banner Zenzic assente sulle uscite fatali precoci (Direttiva CEO 043).**
  `_ui.print_header(__version__)` veniva chiamato dentro il blocco di rendering text-format,
  dopo tutta la validazione. Qualsiasi uscita fatale precedente (config mancante, rifiuto Blood
  Sentinel, Shield breach) produceva output privo di banner. **Fix:** banner anticipato all'inizio
  di `check_all`, protetto da `not quiet and output_format == "text"`.

#### Documentazione

- **Integrità frontmatter confermata — audit ZRT-001 (Direttiva CEO 041).**
  Confermato che `check_shield()` scansiona tramite `enumerate(fh, start=1)` — ogni linea,
  incluso il frontmatter YAML — prima di qualsiasi passata sul contenuto filtrato. Il fix
  `_visible_word_count()` (Sprint Parità Codebase) elimina il frontmatter solo per il conteggio
  parole Z502 e non ha alcun impatto sulla copertura dello Shield. Nessuna modifica al codice
  richiesta.

- **Zenzic Ledger delle istruzioni agente (Direttive CEO 046–047 — "The Knowledge Refactoring" / "The Knowledge Trinity").**
  Tutti e tre i file `.github/copilot-instructions.md` dei repository riscritti secondo lo schema
  Zenzic Ledger: `[MANIFESTO] → [POLICIES] → [ARCHITECTURE] → [ADR] → [CHRONICLES] → [SPRINT LOG]`.
  Correzioni architetturali applicate: struttura del package `cli/`, `core/ui.py`, `cli/_lab.py`,
  11 Atti (0–10), Z504 `QUALITY_REGRESSION` documentato per la prima volta. `zenzic-action`
  riceve il suo primo file di istruzioni agente (directory `.github/` creata da zero).

- **Memory Law codificata (Direttiva CEO 042).**
  Sezione 9 — "Documenting Evolution (The Memory Law)" — aggiunta a entrambi i file di istruzioni
  agente `zenzic` e `zenzic-doc`. Gli agenti devono codificare tutte le innovazioni dello sprint
  prima che una direttiva venga chiusa.

- **Invariante strutturale bilingue codificato (Direttiva CEO 045 — "Codifying the Symmetry").**
  La Legge del Mirroring Italiano formalmente codificata in entrambi i file di istruzioni agente:
  qualsiasi `git mv` in `docs/` deve essere accompagnato da un corrispondente `git mv` in
  `i18n/it/` **nello stesso commit**. Audit di simmetria (comando diff) eseguito e confermato
  con zero asimmetrie.

---

### Sprint Legge della Memoria Quartz & Rifinitura di Precisione (D048–D049 — 2026-04-25)

#### Corretto

- **Puntatore Z502 `SHORT_CONTENT` puntava al frontmatter (Direttiva CEO 048 — Bug 1).**
  `check_placeholder_content` aveva `line_no=1` cablato nel `PlaceholderFinding` short-content,
  causando il puntamento della freccia diagnostica `❱` sull'apertura `---` del frontmatter YAML
  — non sulla prima riga di contenuto. **Fix:** `_first_content_line(text)` usa
  `_FRONTMATTER_RE.match()` per contare le righe nel blocco frontmatter e restituisce il numero
  della prima riga post-frontmatter. Test: `test_short_content_pointer_skips_frontmatter`.

- **Gli errori Z503 YAML riportano la riga relativa invece di quella assoluta (Direttiva CEO 048 — Bug 2).**
  Il gestore YAML in `check_snippet_content` usava `line_no=fence_line + 1` incondizionatamente,
  scartando l'offset `exc.problem_mark.line` del parser YAML. Un errore di sintassi alla riga 3
  dello snippet (riga 183 del file) veniva segnalato come riga 181 invece che 183.
  **Fix:** `offset = (mark.line + 1) if mark is not None else 1`.
  Test: `test_check_snippet_yaml_absolute_line_no`.

- **I cursori `^^^^` si disallineano dopo il wrapping di riga nel terminale (Direttiva CEO 048 — Bug 3).**
  `_render_snippet` usava una soglia cablata `col_start + caret_len <= 60` senza tenere conto
  della larghezza del terminale. Le righe sorgente molto lunghe (200+ caratteri) andavano a capo
  nel terminale, spostando la riga dei cursori sulla riga visiva sbagliata.
  **Fix:** `shutil.get_terminal_size(fallback=(120, 24)).columns` determina `max_src`. Le righe
  sorgente vengono troncate a `max_src` con suffisso `…`. I cursori vengono renderizzati solo se
  `col_start + caret_len <= max_src`.

- **Gli snippet YAML multi-documento generano falso positivo Z503 (Direttiva CEO 048 — Bug 4).**
  `yaml.safe_load(snippet)` rifiutava gli snippet YAML contenenti separatori di documento `---`
  con "expected a single document in the stream". La documentazione Docusaurus mostra
  frequentemente esempi di frontmatter usando `---` all'interno dei blocchi di codice.
  **Fix:** `list(yaml.safe_load_all(snippet))` — il generatore viene consumato per forzare il
  parsing completo accettando stream YAML multi-documento.

#### Documentazione

- **`[CLOSING PROTOCOL]` — Legge della Memoria Quartz codificata (Direttiva CEO 049 — "The Quartz Memory Law").**
  Tutti e tre i file di istruzioni agente ricevono una sezione `[CLOSING PROTOCOL]`, posizionata
  subito dopo `[MANIFESTO]`. Definisce una checklist obbligatoria per repo (aggiornare
  istruzioni, aggiornare changelog, eseguire audit di obsolescenza, eseguire gate di verifica).
  Saltare qualsiasi passo è una violazione di Classe 1 (Technical Debt). Risolve il "Paradosso
  del Custode senza Memoria". La Memory Law in `[POLICIES]` aggiornata a "The Custodian's
  Contract" con la clausola di violazione Classe 1 e l'invariante esplicito "Definition of Done".

---

### Sprint del Perimetro Intelligente (D050 — 2026-04-25)

#### Corretto

- **Falsi positivi Z903 su file di configurazione engine e infrastruttura (BUG-009 — Direttiva CEO 050 "The Intelligent Perimeter").**
  Eseguire `zenzic check all .` dalla root del progetto generava avvisi Z903 (Asset Non Utilizzato)
  su `docusaurus.config.ts`, `package.json`, `pyproject.toml` e altri file toolchain — gli stessi
  file che Zenzic legge per operare. La causa: `find_unused_assets()` non aveva guardrail a livello
  di file; ogni file non-Markdown in `docs_root` non referenziato veniva segnalato.

  **Fix — Sistema di guardrail a due livelli (L1a + L1b):**

  - **L1a — `SYSTEM_EXCLUDED_FILE_NAMES` / `SYSTEM_EXCLUDED_FILE_PATTERNS`** in
    `src/zenzic/models/config.py`: file toolchain universali (`package.json`, `pyproject.toml`,
    `yarn.lock`, `tsconfig.json`, `uv.lock`, `eslint.config.*`, `.prettierrc*`, ecc.) sono
    guardrail di sistema immutabili, non sovrascrivibili da config utente o flag CLI.
  - **L1b — `BaseAdapter.get_metadata_files() -> frozenset[str]`**: ogni adapter dichiara i file
    di configurazione engine che consuma (`docusaurus.config.ts` / `sidebars.ts` per Docusaurus;
    `mkdocs.yml` per MkDocs; `zensical.toml` per Zensical). `LayeredExclusionManager` li memorizza
    e li applica in `should_exclude_file()`. `find_unused_assets()` applica entrambi i livelli
    prima di costruire l'insieme degli asset. `_build_exclusion_manager` propaga i metadata
    dell'adapter al gestore delle esclusioni al momento della costruzione.

  Regola R13 (CEO-050) codificata in `[POLICIES]`: _"Non chiedere mai all'utente di escluderli manualmente."_

#### Test

- `tests/test_exclusion.py::TestSystemFileGuardrails` — 5 nuovi test: esclusione per nome esatto,
  esclusione per pattern glob (`eslint.config.mjs`), pattern `*.lock`, metadata adapter L1b, e
  non-esclusione di file doc legittimi.
- `tests/test_scanner.py::test_find_unused_assets_skips_system_infrastructure_files` — L1a end-to-end.
- `tests/test_scanner.py::test_find_unused_assets_skips_adapter_metadata_files` — L1b end-to-end.

---

### Sprint Documentazione come Invariante (D051 — 2026-04-25)

#### Modificato

- **`[CLOSING PROTOCOL]` Step 3 rinominato "Staleness & Testimony Audit" in tutti e tre gli Zenzic Ledger.**
  Aggiunte checklist trigger per-repo: ogni funzione modificata deve essere incrociata con la
  pagina `.mdx` corrispondente prima della chiusura dello sprint.

- **Legge sulla Documentazione — "The Quartz Testimony" aggiunta a `[POLICIES]` in tutti e tre gli Zenzic Ledger.**
  Trigger obbligatori: I/O o logica di esclusione modificata → `configuration.mdx`; struttura
  UI/CLI/modulo modificata → `architecture.mdx`; finding `Zxxx` modificato → `finding-codes.mdx`;
  adapter discovery modificata → `configure-adapter.mdx`. Uno sprint senza Testimony check non è chiuso.

- **`docs/reference/finding-codes.mdx` (EN + IT) — aggiornamenti di precisione Z502 e Z503 (zenzic-doc).**
  Il Contesto Tecnico di Z502 documenta che il conteggio parole è puramente semantico: frontmatter,
  commenti MDX e HTML vengono esclusi. Il Contesto Tecnico di Z503 documenta che il numero di riga
  riportato è assoluto (relativo al file sorgente, non allo snippet), abilitando la navigazione immediata.

- **`docs/reference/configuration.mdx` (EN + IT) — Nuova sezione "Protezioni di Sistema (Esclusioni di Livello 1)" (zenzic-doc).**
  Documenta l'elenco completo delle esclusioni L1a (infrastruttura universale) e L1b (config engine
  dichiarate dall'adapter). La nota su `_category_.json` in `excluded_assets` è aggiornata: non più
  necessaria per i progetti Docusaurus (guardrail L1b). Le voci esistenti sono silenziosamente deduplicate.

- **`docs/how-to/configure-adapter.mdx` (EN + IT) — Tip box L1b aggiunto (zenzic-doc).**
  Dopo la tabella di adapter discovery, un tip box informa gli utenti che i file di configurazione
  engine sono automaticamente esclusi da Z903. Nessuna voce manuale in `excluded_assets` necessaria.

---

### Correzione della Root Sovrana (D052 — 2026-04-25)

#### Corretto

- **BUG-010: Context Hijacking tramite percorso esterno.**
  Eseguire `zenzic check all /percorso/altro-repo` dall'interno di un repository diverso causava
  il caricamento del `zenzic.toml` del chiamante invece di quello del target. Causa: `find_repo_root()`
  cercava sempre verso l'alto da `Path.cwd()`, ignorando il target esplicito.
  Correzione: `find_repo_root()` accetta ora il parametro `search_from: Path | None`; `check_all()`
  lo deriva dal percorso target risolto. "La configurazione segue il target, non il chiamante." — ADR-009.

- **Guardrail root sovrana in `_apply_target()`.**
  Quando il target esplicito coincideva con la root del progetto, `_apply_target()` sovrascriveva
  `docs_dir` con `"."` — causando la scansione dell'intera root del progetto (inclusi `blog/`, `scripts/`)
  invece di rispettare il `docs_dir` configurato. Correzione: quando `target == repo_root`, la
  configurazione viene restituita con il `docs_dir` preservato.

#### Test Aggiunti

- `tests/test_remote_context.py` — 9 test di regressione: isolamento root con `find_repo_root(search_from=...)`,
  guardrail root sovrana di `_apply_target`, e isolamento configurazione end-to-end (scenario "The Stranger").

---

### L'Invariante di Portabilità (D053 — 2026-04-25)

#### Corretto

- **Link assoluti in `configure-adapter.mdx` (EN + IT) introdotti da D051.**
  D051 usava percorsi assoluti in stile Docusaurus (`/docs/reference/configuration#system-guardrails`)
  che violano la regola Z105 di Zenzic stesso. Corretti in percorsi MDX relativi:
  `../reference/configuration.mdx#system-guardrails`.

#### Aggiunto

- **Regola R14 — La Portabilità è Indipendente dall'Esecuzione.**
  Codificata in `[POLICIES]`: i link assoluti (che iniziano con `/`) sono errori bloccanti (Z105)
  incondizionatamente — anche quando il file target esiste su disco. Z105 è un gate pre-risoluzione
  che scatta prima di qualsiasi controllo del filesystem. Motivazione: i link assoluti rompono la
  portabilità quando il sito è ospitato in una sottodirectory.

- **Test di regressione CEO-053.**
  `tests/test_validator.py::TestAbsolutePathProhibition::test_z105_fires_even_when_target_file_exists_on_disk`
  — crea un file reale, lo referenzia con un link assoluto, verifica che `error_type == "ABSOLUTE_PATH"`.

---

### La Legge del Perimetro Rigido (D054 — 2026-04-25)

#### Diagnosi

Il CEO ha rilevato Z104 su `../assets/brand/svg/zenzic-badge-shield.svg` scansionando zenzic-doc
dall'esterno del repository. L'indagine forense ha determinato: il link è valido (il file esiste
in `docs/assets/brand/svg/zenzic-badge-shield.svg`, dentro `docs_root`), il resolver Shield
applicava già correttamente la scope integrity (PathTraversal Z202 scatta per link fuori perimetro),
e il Z104 era interamente un artefatto CEO-052. La fix CEO-052 (già applicata) elimina il falso
Z104 nella scansione remota.

#### Corretto

- **BUG-011: il default documentato di `excluded_dirs` includeva erroneamente `"assets"` (zenzic-doc).**
  `docs/reference/configuration.mdx` (EN + IT) riportava il default come
  `["includes", "assets", "stylesheets", "overrides", "hooks"]`. Il default effettivo nel codice
  (`models/config.py` riga 152) è `["includes", "stylesheets", "overrides", "hooks"]` — senza
  `"assets"`. Correzione: default aggiornato + tip box che spiega perché `"assets"` è
  intenzionalmente assente.

#### Aggiunto

- **Regola R15 — Integrità del Perimetro.** Codificata in `[POLICIES]`: un link risolto è valido
  solo se il suo target è all'interno del perimetro consentito del motore (`docs_root` + directory
  statiche dichiarate dall'adapter). L'esistenza del file sul filesystem host al di fuori di questo
  perimetro è irrilevante — il resolver Shield (PathTraversal Z202) lo applica incondizionatamente.

- **Firma del comando `clean assets` allineata con `check all`.**
  Aggiunti: argomento `PATH` (fix sovrana CEO-052), `--engine`, `--exclude-dir`, `--include-dir`,
  `--quiet`. Supporto completo per i file di metadati adapter (guardrail L1b).

---

### La Calibrazione di Precisione (D055 — 2026-04-25)

#### Corretto

- **Z502: il conteggio parole inflazionato dal commento MDX SPDX prima del frontmatter.**
  `_visible_word_count()` eseguiva `_FRONTMATTER_RE` (ancorato a `\A`) prima di rimuovere i
  commenti MDX a blocco (`{/* … */}`). I file MDX che si aprono con un'intestazione SPDX/copyright
  prima del blocco `---` causavano il mancato riconoscimento del frontmatter da parte della regex,
  perdendo tutte le coppie chiave-valore del frontmatter nel conteggio prosa. Fix: rimuovere prima
  i commenti MDX e HTML, poi eseguire la regex frontmatter. Funzione pura; testo originale invariato.

- **Z105: falso positivo sui link `pathname:///` (Diplomatic Courier Docusaurus).**
  `urlsplit("pathname:///assets/file.html")` → `scheme="pathname"`, `path="/assets/file.html"`.
  Il gate Z105 (`parsed.path.startswith("/")`) scattava sulla `/` iniziale del componente path URI
  — un artefatto convenzionale, non un riferimento alla radice del server. Fix: gate condizionato
  su `not parsed.scheme`. Qualsiasi URL con schema non vuoto è un protocollo engine, non un percorso
  assoluto. Regola R16 "Consapevolezza dei Protocolli" codificata.

#### Aggiunto

- Test di regressione in `tests/guardians/test_precision.py` (5 test).
- Nota Nox di sviluppo aggiunta a `CONTRIBUTING.md` (EN) e `CONTRIBUTING.it.md` (IT).

---

### Consapevolezza Universale dei Percorsi (D056 — 2026-04-25)

#### Aggiunto

- **`zenzic score [PATH]` — argomento posizionale opzionale.**
  Quando fornito, `score` applica il fix sovrano CEO-052: `find_repo_root(search_from=target)`
  deriva la root del repo dal percorso target, non dalla CWD. Banner stampato immediatamente prima
  dell'analisi. Suggerimento `Scoring: <path>` mostrato per target non-CWD.

- **`zenzic diff [PATH]` — argomento posizionale opzionale.**
  Stessa semantica sovrana di `score`. Percorso snapshot derivato automaticamente da `repo_root`
  (non dalla CWD). Suggerimento `Comparing: <path>` mostrato per target non-CWD.

- Regola R17 "Simmetria CLI" codificata: `score` e `diff` accettano lo stesso argomento PATH
  opzionale di `check all`, con identica semantica sovrana e di sandbox.

---

### L'Audit di Precedenza (D058 — 2026-04-25)

#### Modificato

- **Documentazione della priorità di configurazione aggiornata da 3 a 4 livelli.**
  `README.md` e `README.it.md` ora elencano esplicitamente i flag CLI come sorgente a massima
  priorità. La formulazione precedente ometteva completamente i flag CLI. La catena autoritativa:
  flag CLI > `zenzic.toml` > `[tool.zenzic]` in `pyproject.toml` > valori predefiniti integrati.

---

### La Legge della Testimonianza Contemporanea (D059 — 2026-04-25)

#### Modificato

- **Legge della Testimonianza Contemporanea codificata come politica operativa obbligatoria.**
  Tutti e tre gli Zenzic Ledger (`.github/copilot-instructions.md` in core, zenzic-doc e
  zenzic-action) aggiornati con la nuova legge: codice e documentazione sono un'unica unità
  indivisibile di lavoro. Step 0 "Pre-Task Alignment" aggiunto al [CLOSING PROTOCOL]. Step 3
  migliorato con bullet "Contemporary Check" che coprono flag CLI, valori predefiniti, bug
  architetturali, codici di finding e comportamento degli adapter.

---

### Simmetria CLI Totale (D060 — 2026-04-25)

#### Aggiunto

- **Argomento PATH su tutti i sotto-comandi `check`.**
  `check links`, `check orphans`, `check snippets`, `check placeholders`, `check assets` e
  `check references` accettano ora un argomento posizionale opzionale `PATH` con semantica
  sovereign root identica a `check all`. Zenzic carica la configurazione dalla destinazione,
  non dalla CWD del chiamante — abilitando l'uso cross-progetto e monorepo senza cambiare
  directory.

- **Modalità Nomad per `init`.**
  `zenzic init <percorso>` tratta il percorso indicato come root del progetto di destinazione.
  La directory viene creata (`mkdir -p`) se non esiste. La CWD del chiamante non viene
  modificata. Il rilevamento automatico dell'engine opera sulla directory di destinazione.

#### Test

- `test_init_nomad_writes_to_target_not_cwd` — verifica che `zenzic.toml` sia creato nella
  destinazione, non nella CWD.
- `test_init_nomad_creates_target_directory` — verifica che un percorso nidificato non
  esistente venga creato.

---

### L'Applicazione del Genesis Nomad (D062 — 2026-04-25)

#### Aggiunto

- **Banner & Hint Sync.** Tutti e 6 i sotto-comandi `check` stampano
  `Scanning: <target-risolto>` dopo l'intestazione Sentinel quando `PATH` viene fornito.
  `init` stampa `Target: <percorso-risolto>` in modalità Genesis Nomad. Gli operatori hanno
  ora conferma visiva della sovereign root attiva prima che i risultati vengano visualizzati.

- **Documentazione Protocollo Sovereign Root** (`docs/explanation/architecture.mdx` EN + IT).
  Nuova sezione che documenta il protocollo di sovranità in tre passi (`find_repo_root` →
  `_apply_target` → guardia sandbox CEO-043), la tabella degli invarianti Genesis Nomad e il
  racconto problema/soluzione del Context Hijacking.

---

### La Narrativa della Maturità (D061 — 2026-04-25)

#### Modificato

- **Articolo di lancio del blog** (`blog/2026-04-22-beyond-the-siege-zenzic-v070.mdx`) revisionato
  come caso studio di maturità ingegneristica (EN + IT simultaneamente).
  Nuove sezioni: "Trattare la Documentazione come Input Non Fidato" (inquadramento), "Il Sprint
  di Precisione" (narrativa dei falsi positivi Z502 BUG-012 + Z105 BUG-013), "Simmetria CLI
  Totale: Il Protocollo Sovereign Root" (copertura D060/D062 con esempi di output terminale),
  "La Legge della Testimonianza Contemporanea" (CEO-059). Tabella delle funzionalità aggiornata
  con nuove righe. Conteggio test aggiornato 1.195 → 1.225. CTA modificato da
  `pip install zenzic; zenzic check all` a `uvx zenzic lab`.

---

### L'Igiene Ossidiana (D063 — 2026-04-25)

#### Modificato

- **Debito tecnico zero confermato.** Grep forense su tutto il codice sorgente di produzione
  (`src/zenzic/`) per marcatori `TODO`, `FIXME` e `HACK`. Ogni corrispondenza era logica di
  produzione intenzionale: il rilevatore Z501 (`if "TODO" in line:`), docstring delle regole,
  o stringhe di esempio nei messaggi di errore. Nessun marcatore rimosso; nessuno esisteva.
  Il codebase "Stable" v0.7.0 è privo di debito tecnico.

---

### Laboratorio Matrix Operazione (D064 — 2026-04-25)

#### Aggiunto

- **`examples/os/unix-security/`** — Esercitazione Red/Blue team: catene `../` multi-hop che
  puntano a `/etc/passwd`, `/root/.ssh/`, `/etc/shadow`, combinate con esposizione di
  credenziali in tabelle, blockquote, titoli di link, parametri URL e blocchi di codice
  delimitati. Esercita Z202 (PATH_TRAVERSAL) + Z201 (rilevamento credenziali Shield).
  `check all` esce con codice 2.

- **`examples/os/win-integrity/`** — Rilevamento di percorsi assoluti stile Windows: `/C:/`,
  `/D:/`, `/Z:/`, `/UNC/server/share/` e target di link `file:///`. Tutti attivano Z105
  (ABSOLUTE_LINK) — dipendenti dall'ambiente e non portabili. `check links` esce con
  codice 1.

- **`examples/rules/z100-link-graph/`** — Test di stress sul grafo dei link: rete circolare
  di anchor non funzionanti su 5 nodi (Z102 ×13) e due link a file inesistenti (Z104 ×2).
  `check links` esce con codice 1.

- **`examples/rules/z200-shield/`** — Estrema offuscazione dello Shield: pattern di credenziali
  codificati in Base64, percent-encoded (singolo e doppio passaggio) e con maiuscole/minuscole
  miste. Lo Shield normalizza prima della corrispondenza — tutte e tre le tecniche vengono
  rilevate. `check references` esce con codice 2 (BREACH).

- **`examples/rules/z400-seo/`** — Lacune nella copertura SEO: tre sottodirectory con contenuto
  ma senza `index.md` (Z401 ×3) e una pagina orfana senza link in entrata (Z402 ×1).
  `check seo` esce con codice 1.

- **`examples/rules/z500-quality/`** — Stress del quality gate: tre pagine stub (meno di 50
  parole, marcatore `TODO`, marcatore `FIXME`) che attivano Z501 e una pagina con un
  `@include` a uno snippet inesistente che attiva Z503. `check quality` esce con codice 1.

- **Atti 11–16 aggiunti a `zenzic lab`.**
  - Atto 11 — Unix Security Probe (`os/unix-security`, `expected_breach=True`)
  - Atto 12 — Windows Path Integrity (`os/win-integrity`, `expected_pass=False`)
  - Atto 13 — Link Graph Stress (`rules/z100-link-graph`, `expected_pass=False`)
  - Atto 14 — Shield Extreme (`rules/z200-shield`, `expected_breach=True`)
  - Atto 15 — SEO Coverage (`rules/z400-seo`, `expected_pass=False`)
  - Atto 16 — Quality Gate (`rules/z500-quality`, `expected_pass=False`)

- **UI di `zenzic lab` rifattorizzata in quattro sezioni Rich.**
  `_print_act_index()` ora raggruppa gli atti per sezione tematica con intestazione icona:
  🛡 Guardrail OS & Ambiente (Atti 0–3),
  🔗 Integrità Strutturale & SEO (Atti 4–6),
  🏢 Adattatori Enterprise & Migrazione (Atti 7–10),
  🔴 Matrice Red/Blue Team (Atti 11–16).
  Ogni sezione viene renderizzata come una tabella Rich `ROUNDED` separata.

- **`examples/run_demo.sh` aggiornato.** Aggiunto commenti di banner di sezione (quattro
  sezioni tematiche). Aggiunti gli Atti 9 e 10 (presenti in `_lab.py` ma assenti dallo
  script). Aggiunti gli Atti 11–16 con i codici di uscita attesi corretti (uscita 2 per
  gli atti BREACH).

---

### Il Protocollo Range Master (D069 — 2026-04-25)

#### Modificato

- **Tipo argomento `zenzic lab` cambiato da `int` a `str`.**
  L'argomento `ATTO` accetta ora un intero (`3`), un intervallo inclusivo (`11-16`), o il
  valore speciale `all`. Una nuova funzione pura `parse_act_range(raw: str) -> list[int]`
  esegue la validazione e restituisce un elenco ordinato di ID degli atti.

#### Aggiunto

- **Esecuzione a intervalli.** `zenzic lab 11-16` esegue tutti e sei gli atti della
  Matrice Red/Blue Team in sequenza e produce la tabella riassuntiva di esecuzione
  multipla tramite `_print_summary()`. Sintassi di intervallo non valida (es. `1-x`) e
  numeri di atto fuori range producono un pannello `ObsidianUI.print_exception_alert()`
  con un messaggio descrittivo.

- **Scorciatoia `zenzic lab all`.** Esegue tutti i 17 atti (0–16) in ordine crescente.

- **Intestazione di sequenza.** Quando è selezionato più di un atto, il Lab stampa un
  banner `LAB SEQUENCE: Running Acts N through M …` prima dell'esecuzione.

- **Sezione `zenzic lab` aggiunta a `docs/reference/cli.mdx` (EN + IT).**
  Documenta la sintassi di selezione degli atti (singolo, intervallo, `all`), le quattro
  sezioni tematiche, il significato delle etichette di esito ed esempi d'uso. Soddisfa la
  Legge della Testimonianza Contemporanea (CEO-059).

---

### Il Fix del Contenuto Fantasma (D072 — 2026-04-25)

#### Corretto

- **Il puntatore Z502 non si ancora più sulle intestazioni di licenza SPDX.**
  `_first_content_line()` era implementata come un'unica chiamata `_FRONTMATTER_RE.match(text)`
  ancorata a `\A`. Quando un file apriva con commenti HTML `<!-- SPDX-FileCopyrightText: … -->`
  (pratica REUSE standard), la regex del frontmatter falliva nel match — causando il fallback a
  riga 1 e la freccia diagnostica `❱` puntata all'intestazione di licenza invece della prima
  parola di prosa.

  `_first_content_line()` è ora un walker riga per riga in tre fasi:
  1. Salta i commenti HTML (`<!-- … -->`) e MDX (`{/* … */}`) iniziali, incluse le varianti
     multi-riga.
  2. Salta il blocco frontmatter YAML (`--- … ---`), se presente dopo i commenti.
  3. Salta le righe vuote tra quanto sopra e la prima parola di prosa.

  La logica di conteggio parole in `_visible_word_count()` era già corretta (commenti rimossi
  prima del frontmatter per D055); solo il puntatore era guasto.

#### Test

- **`test_short_content_pointer_skips_spdx_comments`** — "La Trappola SPDX": 5 righe di
  commenti HTML SPDX iniziali + 10 righe di frontmatter YAML + parola singola `FINE`. Verifica
  che `line_no` risolva alla riga contenente `FINE`, non a commenti o delimitatori di frontmatter.

---

### D073 — La Legge della Curation Evolutiva (2026-04-25)

#### Governance

- **Tutti e tre gli Zenzic Ledger refactorizzati da "diari storici" a "manuali operativi".**
  La sezione [CHRONICLES] (14 post-mortem di bug) rimossa dal ledger core; le lezioni già
  distillate nelle regole [POLICIES] (R11–R18) e nelle voci ADR rimangono. [SPRINT LOG]
  sostituito da [ACTIVE SPRINT] (finestra a 2 sprint) in tutti e tre i repo.
  Legge della Curation Evolutiva codificata in [POLICIES]: questo file è un Contesto di
  Lavoro, non un archivio storico. Guardrail dimensionale: avviare curation quando il file
  supera 400 righe.

- **Regola R19 — Nessuna Esclusione a Livello di Dominio (nuova).**
  `excluded_external_urls` in `zenzic.toml` deve puntare a URL o prefissi specifici, non a
  interi domini. Un'esclusione di dominio generico (es. `"https://zenzic.dev/"`) crea un
  angolo buio permanente che sopravvive alle ristrutturazioni dei contenuti. Solo governance;
  nessuna validazione a runtime. Documentata nel ledger core [POLICIES] e nel riferimento
  di configurazione di `zenzic-doc`.

- **ADR-006 esteso con il corollario BUG-014 SPDX.**
  `_first_content_line()` applica lo stesso skip in tre fasi (commenti HTML → frontmatter →
  righe vuote) stabilito in D072. La lezione è ora catturata permanentemente in ADR-006.

---

### D074+D075 — Iron Gate della Copertura + Testimonianza R19 (2026-04-25)

#### Test — D074

- **Tre unit test mirati per i percorsi di commenti multi-riga di `_first_content_line()`.**
  L'implementazione del walker in tre fasi di D072 aveva rami di continuazione non coperti.
  Il test di regressione esistente esercitava solo commenti HTML su singola riga.

  Nuovi test:
  - `test_short_content_pointer_skips_multiline_html_comment` — `<!-- … -->` su più righe;
    verifica che il puntatore atterri sulla prosa, non su righe di commento.
    Copre il percorso di continuazione `in_html=True` (righe 209–213, 221 in scanner.py).
  - `test_short_content_pointer_skips_multiline_mdx_comment` — `{/* … */}` su più righe;
    verifica che il puntatore atterri sulla prosa, non su righe di commento.
    Copre il percorso di continuazione `in_mdx=True` (righe 214–218, 226 in scanner.py).
  - `test_short_content_pointer_unclosed_frontmatter` — frontmatter senza `---` di chiusura;
    verifica assenza di crash e `line_no ≥ 1`.
    Copre il ramo False di `if i < n:` (riga 239 → 243 in scanner.py).

  Copertura test complessiva: **79,82% → 80,00%** (Python 3.11, 3.12, 3.13).

#### Documentazione — D075

- **Admonition `:::warning` Regola R19 aggiunta a `configuration-reference.mdx` (EN + IT).**
  La sezione `excluded_external_urls` ora porta un avvertimento permanente contro le
  esclusioni a livello di dominio. Legge della Testimonianza Contemporanea soddisfatta:
  R19 (codificata in D073) è ora visibile nel punto d'uso nella documentazione di riferimento
  ufficiale.

---

### D077 — Il Silenzio Macchina-Macchina (2026-04-25)

#### Corretto

- **`_print_no_config_hint()` stava contaminando l'output SARIF/JSON su stdout (Regola R20).**
  Quando `zenzic check all --format sarif` veniva eseguito su un progetto senza `zenzic.toml`,
  il pannello informativo Rich (il suggerimento "no config") veniva scritto su stdout prima
  del JSON SARIF, producendo un file che iniziava con `╭` — JSON non valido che causava
  il crash di GitHub Code Scanning con `Unexpected token '╭'`.

  Fix: `_print_no_config_hint(output_format: str = "text")` in `_shared.py` ora controlla
  `_MACHINE_FORMATS = frozenset({"json", "sarif"})` — ritornando immediatamente senza
  alcuna scrittura su stdout per i formati macchina. Cinque call site in `_check.py`
  aggiornati per passare il formato corrente. L'output stdout di `check all --format sarif`
  inizia ora con `{`.

  **Regola R20 — Silenzio Macchina** codificata in [POLICIES]: qualsiasi formato
  machine-readable (json/sarif) impone la soppressione totale di banner e pannelli Rich
  su stdout.

#### Action (zenzic-action)

- **`github/codeql-action/upload-sarif@v3` → `@v4`** (fix deprecazione).
- **`astral-sh/setup-uv@v7` → `@v8`** (miglioramenti cache).
- **Default input `version` modificato da `latest` → `0.7.0`** (default orientato alla stabilità).
  Chi vuole aggiornamenti continui può impostare esplicitamente `version: latest`.

---

### D084 — Audit di Neutralità Quartz (2026-04-26)

#### Modificato — `docs/reference/engines.mdx` (EN + mirror IT)

- **Sottosezione MkDocs `### Risoluzione degli URL di route` aggiunta.** Documenta che Zenzic
  valida i link relativi a livello sorgente, rendendo la correttezza dei link immune alla
  modalità `use_directory_urls`. I link assoluti (`/percorso/`) restano sempre segnalati come
  `Z105 ABSOLUTE_PATH`.

- **Sezione Proxy Trasparente Zensical riscritta ed elevata.**
  - `:::warning[Regola del Custode Strutturale]` sostituito con `:::tip[Strategia di migrazione]`
    — inquadramento corretto da "rete di sicurezza" a "feature distintiva di migrazione".
  - Aggiunto anchor `{#zensical-transparent-proxy}` per deep-linking.
  - Tabella di mappatura del ponte: 4 campi di `mkdocs.yml` → utilizzo da parte di
    `ZensicalAdapter` (`docs_dir`, `nav`, `plugins.i18n.languages`, `theme.favicon`/`theme.logo`).

- **Sottosezione Zensical `### Limitazioni` aggiunta.** Copre nav generata da plugin,
  analisi TOML statica e scope di rilevamento di `zensical.toml`.

- **Sezione Standalone espansa da stub 17 righe a sezione completa (~43 righe).** Quattro
  sottosezioni: `### Quando usare Standalone` (3 casi d'uso), `### Configurazione minimale`
  (blocco TOML), `### Capacità` (controlli a piena potenza elencati), `### Limitazioni`
  (controllo orphan disabilitato, pattern di soppressione locale).

#### Aggiunto

- **`README.md`: HN Hook.** Link diretto a `https://zenzic.dev/blog/beyond-the-siege-zenzic-v070`
  aggiunto nella sezione "The Zenzic Chronicles".

---

### D083 — Iron Gate & Automazione dei Satelliti (2026-04-26)

#### Aggiunto — Porta di Ferro della Copertura

- **3 test CLI mirati in `tests/test_cli.py`** che portano la copertura totale all'**80.07%** (1232 test):
  - `test_inspect_capabilities_shows_bypass_table` — verifica che la Sezione C della tabella bypass
    sia renderizzata con `"Engine-specific Link Bypasses"`, `"pathname:"`, `"docusaurus"` e `"R21"`.
  - `test_score_perfect_shows_obsidian_seal` — simula score=100; verifica `"OBSIDIAN SEAL"` e
    `"Every check passed"` nell'output.
  - `test_score_low_uses_error_style` — simula score=30; copre la linea 132 (ramo `STYLE_ERR`);
    verifica che l'Sentinel Seal NON appaia.

#### Aggiunto — Automazione dei Satelliti

- **`zenzic-doc/noxfile.py`** — 5 sessioni nox: `lint` (TypeScript + Markdown), `typecheck`,
  `build` (build Docusaurus produzione), `reuse` (REUSE/SPDX), `preflight` (pipeline completa).
  Fornisce un punto d'ingresso unificato `nox -s preflight` che rispecchia il repo Core.

- **`zenzic-action/noxfile.py`** — 3 sessioni nox: `reuse`, `check` (auto-audit Zenzic),
  `preflight`. Dà all'Action la stessa disciplina di automazione del Core.

- **`zenzic-action/justfile`** — 5 comandi: `bump`, `reuse`, `check`, `preflight`, `clean`.

- **`zenzic-action/scripts/bump-version.sh`** — Script Bash per sincronizzare la versione
  Zenzic predefinita in `action.yml` con un singolo comando (`just bump 0.7.1`). Valida il
  formato della versione; idempotente; produce un riepilogo chiaro delle modifiche.

#### Risolto — Conformità REUSE di `zenzic-action`

- Aggiunti `LICENSES/Apache-2.0.txt`, `.reuse/dep5` (copre `package.json` e asset SVG),
  e intestazione SPDX su `.github/copilot-instructions.md`. Ora 12/12 file conformi.

---

### D082 — La Finitura Quartz Finale (2026-04-26)

#### Aggiunto

- **`zenzic inspect capabilities`: Sezione C "Bypass di Schemi Link per Engine".**
  Nuova terza tabella che mostra quale engine dichiara quali bypass URI via
  `get_link_scheme_bypasses()`. Righe: `docusaurus` → `pathname:` (escape hatch per asset statici),
  `mkdocs` / `zensical` / `standalone` → `(nessuno)`. Nota footer Regola R21 aggiunta.
  Help del comando aggiornato per includere i bypass engine-specifici.

- **`zenzic score`: Pannello Sentinel Seal a 100/100.**
  Quando `report.score == 100`, il comando score visualizza lo stesso pannello celebrativo
  dell'Atto Lab 0 — `Group` con intestazione scudo `ObsidianPalette.BRAND` e riga di successo
  che conferma l'integrità della documentazione. Pannello soppresso in modalità `--format json`.

#### Verificato Completo

- **`docs/how-to/add-badges.mdx` (EN) righe 73-111** già documentano il flusso completo del badge
  dinamico: `zenzic score --save` → `.zenzic-score.json` → GitHub Actions con
  `dynamic-badges-action` → endpoint Shields.io. Nessuna modifica necessaria.

---

### D081 — La War Room (2026-04-26)

#### Aggiunto — Matrice di Validazione Cross-Engine

- **`examples/matrix/red-team/` — tre fixture con vettori d'attacco (standalone, mkdocs, zensical).**
  Ogni fixture contiene vettori d'attacco identici: Z201 (Shadow Secret — `aws_access_key_id` nel
  frontmatter YAML), Z105 (Absolute Trap — tre link con percorso assoluto), Z502 (Short Content Ghost
  — quattro file sotto le 50 parole), Z501 (Ghost File — `draft: false`), Z401 (Missing Index —
  quattro sottodirectory senza `index.md`). Tutti e tre producono findings identici.
  **Exit code: 2 (SECURITY BREACH).**

- **`examples/matrix/blue-team/` — tre fixture di documentazione pulita (standalone, mkdocs, zensical).**
  Versioni corrette: link relativi, prosa ≥50 parole, `index.md` in ogni sottodirectory, nessuna
  credenziale, campo `draft:` rimosso. Tutti e tre ottengono l'Sentinel Seal.
  **Exit code: 0 (Sentinel Seal ✨).** Parità confermata: zero asimmetrie tra engine.

#### Documentazione (zenzic-doc)

- **`architecture.mdx` (EN+IT): sottosezioni "Sovranità del Protocollo" e "Parità di Validazione Cross-Engine"**
  aggiunte dopo la tabella Adapter Built-in. Documenta `get_link_scheme_bypasses()`, la Regola R21,
  e la garanzia di parità D079 con tabella per-adapter. Riferimento a `examples/matrix/` come prova vivente.

- **`implement-adapter.mdx` (EN+IT): Step 6 "Dichiarare i Bypass per gli Schemi Link" aggiunto;**
  elemento 11 del Contratto Adapter per `get_link_scheme_bypasses()` aggiunto.

- **`first-audit.mdx` (EN+IT): Step 2 ristrutturato in "L'Assedio e lo Scudo".**
  Mostra prima `uvx zenzic lab 2` (banner Security Breach), poi `uvx zenzic lab 0` (Sentinel Seal).
  Implementa la Regola R22 (Fall-before-Redemption): il contrasto emotivo è la lezione.

#### Governance

- **Regola R22 (Fall-before-Redemption) codificata in [POLICIES]:** il contenuto tutorial deve
  mostrare prima lo stato compromesso (L'Assedio), spiegare la correzione, poi mostrare lo stato
  corretto (L'Sentinel Seal).

---

### D079+D080 — L'Assedio Agnostico + Sovranità del Protocollo (2026-04-26)

#### Refactoring — D080: Sovranità del Protocollo

- **Core Leak rimosso da `validator.py` — introdotto `BaseAdapter.get_link_scheme_bypasses()`.**
  `validator.py` conteneva due riferimenti hardcoded a `"docusaurus"` che esponevano
  l'escape hatch `pathname:` tramite confronto sulla stringa del nome motore.
  Per la Direttiva CEO 080 (Protocol Sovereignty), il Core deve essere agnostico al motore —
  conosce il Protocollo, non gli attori.

  **Modifiche:**
  - Costante `_DOCUSAURUS_SKIP_SCHEMES = ("pathname:",)` rimossa da `validator.py`.
  - `get_link_scheme_bypasses() -> frozenset[str]` aggiunto al protocollo `BaseAdapter` (`_base.py`).
  - Tutti i quattro adapter implementano il nuovo metodo:
    - `DocusaurusAdapter`: restituisce `frozenset({"pathname"})` — preserva l'escape hatch `pathname:///` (Regola R16, CEO-055).
    - `MkDocsAdapter`, `ZensicalAdapter`, `StandaloneAdapter`, `ZensicalLegacyProxy`: restituiscono `frozenset()`.
  - `validate_links_async()` deriva `_bypass_schemes` da `adapter.get_link_scheme_bypasses()` subito dopo l'istanziazione dell'adapter. `_effective_skip` è costruito come `_SKIP_SCHEMES + tuple(f"{s}:" for s in _bypass_schemes)`.
  - Controllo Z105: `if parsed.path.startswith("/") and parsed.scheme not in _bypass_schemes:` — nessun nome di motore nel codice Core.

  **Invariante:** Aggiungere un nuovo adapter domani non richiede **zero modifiche** a `validator.py`.

#### Lab — D079: L'Assedio Agnostico (Matrice di Parità Cross-Engine)

- **Tre demo repo esterni creati in `/dev/PythonSandbox/`:**
  `zenzic-demo-standalone/`, `zenzic-demo-mkdocs/`, `zenzic-demo-zensical/` — ciascuno
  con quattro vettori d'attacco deliberatamente costruiti sulla stessa documentazione.

  **Risultati Matrice di Parità (da dir demo + Sovereign Scan dal repo core):**

  | Motore | Z201 | Z105 | Z502 | Z401 |
  |---|---|---|---|---|
  | standalone | ✅ exit 2 | ✅ 3× | ✅ 4 file | ✅ 4× info |
  | mkdocs | ✅ exit 2 | ✅ 3× | ✅ 4 file | ✅ 4× info |
  | zensical | ✅ exit 2 | ✅ 3× | ✅ 4 file | ✅ 4× info |

  **Verdetto: ZERO asimmetrie.** Tutti e tre i motori producono conteggi e severità
  di finding identici per la stessa documentazione. Sovereign Root Protocol confermato.

  **Scoperta bonus:** Z501 (testo segnaposto) scatta su `draft: false` nel frontmatter di
  `architecture.md` — la keyword `draft` corrisponde al pattern segnaposto di default.
  Coerente su tutti e tre i motori (by design: è una regola di contenuto, non di motore).

---## [0.6.1] — 2026-04-19 — Obsidian Glass [SUPERSEDED]

> ⚠ **[SUPERSEDED dalla v0.7.0]** — La versione 0.6.1 è deprecata a causa di problemi di allineamento con le specifiche Docusaurus e terminologia legacy. Tutti gli utenti devono aggiornare alla v0.7.0 "Obsidian Maturity".

---

### Modifiche che rompono la compatibilità

- **Standalone Engine sostituisce Vanilla (Direttiva 037).** `VanillaAdapter` e la
  keyword `engine = "vanilla"` sono stati rimossi. Tutti i progetti devono migrare a
  `engine = "standalone"`. Qualsiasi `zenzic.toml` che usa ancora `engine = "vanilla"`
  genera una `ConfigurationError [Z000]` all'avvio con un messaggio di migrazione chiaro.
  _Migrazione:_ sostituire `engine = "vanilla"` con `engine = "standalone"` nel proprio
  `zenzic.toml` o nel blocco `[tool.zenzic]`.

---

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

---

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

---

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

---

### Aggiunto

- **`--format json` sui comandi di controllo singoli.** `check links`, `check orphans`,
  `check snippets`, `check references` e `check assets` accettano ora `--format json`
  con uno schema uniforme `findings`/`summary`. I codici di uscita sono preservati in
  modalità JSON.
  ([#55](https://github.com/PythonWoods/zenzic/pull/55) — contributo di [@xyaz1313](https://github.com/xyaz1313))
- **Shield: rilevamento GitLab Personal Access Token.** Lo scanner di credenziali
  rileva ora i token `glpat-` (9 famiglie di credenziali in totale).
  ([#57](https://github.com/PythonWoods/zenzic/pull/57) — contributo di [@gtanb4l](https://github.com/gtanb4l))

---

### Corretto

- **Asimmetria exit-code JSON in `check orphans` e `check assets`.** Entrambi i comandi
  ora distinguono la severità `error` da `warning` prima di decidere il codice di uscita,
  in modo coerente con `check references` e `check snippets`. In precedenza, qualsiasi
  finding (inclusi i warning) attivava Exit 1 in modalità JSON.

## [0.6.1rc1] — 2026-04-15 — Obsidian Bastion

---

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

---

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

---

### Modificato

- **BREAKING (Alpha):** il parametro `exclusion_manager` è ora obbligatorio su
  `walk_files`, `iter_markdown_sources`, `generate_virtual_site_map`,
  `check_nav_contract`, e tutte le funzioni dello scanner. Nessun default
  `None` retrocompatibile.

## [0.6.0a2] — 2026-04-13 — Obsidian Glass (Alpha 2)

---

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

---

### Modificato

- **BREAKING: `excluded_assets` usa fnmatch** — Tutte le voci sono ora
  interpretate come pattern glob.  I percorsi letterali continuano a
  funzionare (sono pattern validi), ma pattern come `**/_category_.json` o
  `assets/brand/*` sono ora supportati nativamente.  L'implementazione
  precedente basata sulla sottrazione di insiemi è stata rimossa.

---

### Corretto

- **Warning "dynamic patterns" di Docusaurus emesso due volte** — Quando
  `base_url` è dichiarato in `zenzic.toml`, l'adapter non chiama più
  `_extract_base_url()`, sopprimendo completamente il warning duplicato.

## [0.6.0a1] — 2026-04-12 — Obsidian Glass

> **Alpha 1 della serie v0.6.** Zenzic evolve da un linter MkDocs-aware a un
> **Analizzatore di Piattaforme Documentali**. Questo rilascio introduce
> l'adapter per il motore Docusaurus v3 — il primo adapter non-MkDocs/Zensical —
> e segna l'inizio della strategia di migrazione Obsidian Bridge.

---

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

---

### Test

- **`tests/test_docusaurus_adapter.py` — 65 test in 12 classi di test.**
  Copertura completa del refactor dell'adapter Docusaurus: parsing config
  (CFG-01..07), estrazione `routeBasePath` (RBP-01), supporto slug
  frontmatter (SLUG-01), rilevamento config dinamica, rimozione commenti,
  integrazione `from_repo()`, regressione URL mapping e classificazione rotte.
