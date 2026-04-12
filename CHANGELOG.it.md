<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Registro delle modifiche

Tutte le modifiche rilevanti a Zenzic sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Le versioni seguono il [Semantic Versioning](https://semver.org/).

---

## [Non rilasciato]

## [0.6.0a1] — 2026-04-12 — Obsidian Glass

> **Alpha 1 della serie v0.6.** Zenzic evolve da un linter MkDocs-aware a un
> **Analizzatore di Piattaforme Documentali**. Questo rilascio introduce
> l'adapter per il motore Docusaurus v3 — il primo adapter non-MkDocs/Zensical —
> e segna l'inizio della strategia di migrazione Obsidian Bridge.

### Aggiunto

- **Adapter Docusaurus v3** (`DocusaurusAdapter`): Supporto iniziale per il motore
  Docusaurus v3 — adapter puro Python conforme al protocollo `BaseAdapter`. Gestisce
  file sorgente `.md` e `.mdx`, modalità sidebar auto-generata (tutti i file
  `REACHABLE`), geografia i18n Docusaurus
  (`i18n/{locale}/docusaurus-plugin-content-docs/current/`), rilevamento Ghost Route
  per le pagine indice delle locale, ed esclusione di file/directory con prefisso `_`
  (`IGNORED`). Registrato come adapter built-in con entry-point
  `docusaurus = "zenzic.core.adapters:DocusaurusAdapter"`.
- **Estrazione `baseUrl`**: Estrazione chirurgica via regex di `baseUrl` da
  `docusaurus.config.ts` / `.js` — nessun sottoprocesso Node.js (conformità
  Pilastro 2).
- **Hook factory `from_repo()`** per `DocusaurusAdapter`: Scopre automaticamente
  `docusaurus.config.ts` o `.js` e costruisce l'adapter con il `baseUrl` corretto.

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
