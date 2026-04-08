<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Registro delle modifiche

Tutte le modifiche rilevanti a Zenzic sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Le versioni seguono il [Semantic Versioning](https://semver.org/).

---

## [Non rilasciato]

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
