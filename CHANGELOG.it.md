<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

Tutte le modifiche rilevanti a Zenzic sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Le versioni seguono il [Versionamento Semantico](https://semver.org/).

---

> **Storia di sviluppo (v0.1.0 – v0.8.0):** Vedi gli [Archivi Storici](./changelogs/README.md).

## [Unreleased]

### Added

- Lavoro iniziale sull'architettura Plugin SDK.
- **`zenzic score --stamp`:** Aggiornamento deterministico inline del badge. Aggiungi un marcatore `<!-- zenzic:badge -->` in qualsiasi file elencato in `badge_stamp_files` (config); eseguendo `zenzic score --stamp` viene sostituito l'URL del badge Shields.io sulla riga successiva con lo score corrente, con codifica colore del brand (`4f46e5` indaco per 100, `f59e0b` ambra per passing, `ef4444` rosso per fail/security breach). Elimina le dipendenze esterne (Gist, PAT token) e abilita i badge Time-Traveling: lo score viene cristallizzato in ogni commit.
- **Campo di configurazione `badge_stamp_files`:** Nuova chiave `[project_metadata]` che elenca i file aggiornati da `--stamp` (default: `["README.md"]`).
- **Domain-Aware Discovery (`CODE_ASSET_SUFFIXES`):** I file di codice sorgente (`.py`, `.pyi`, `.ts`, `.tsx`, `.rs`, `.go`, e 20+ altre estensioni) sono ora nativamente esenti dall'enforcement Z405 `UNUSED_ASSET` in `find_unused_assets`. I file sono ancora indicizzati dal motore di discovery per la risoluzione dei link attraverso il confine docs/source. Nessuna modifica di configurazione richiesta.
- **Parsing strict del TOML locale:** `.zenzic.local.toml` ora rifiuta le chiavi di primo livello sconosciute con un `ConfigurationError` fatale (`LOCAL-TOML-STRICT`).

### Changed

- **Modello di soppressione a costo fisso (Breaking Change):** Ogni soppressione inline o per-file ora deduce esattamente 1 punto dal DQS.
- **Eradicazione di `.zenzic.local.toml.example` (Phase 83):** Il file template statico è stato eliminato da tutti i repository. Usa `zenzic init --local` per generare un nuovo `.zenzic.local.toml`.
- **`zenzic init --local` aggiunto (Phase 83):** Nuovo flag che crea solo l'overlay locale senza toccare la configurazione condivisa.
- **Flag `--dev` rimosso da `zenzic init` (Phase 83):** Il flag deprecato no-op è stato eliminato.
- **Gate freshness badge in `just verify`:** La recipe `verify` ora esegue `zenzic score --stamp` poi `git diff --exit-code README.md README.it.md`, bloccando il push se il badge committato non riflette il punteggio effettivo.
- **Workflow CI rinominato `zenzic-audit` su tutta la flotta:** Il campo `name:` di GitHub Actions è ora `zenzic-audit` in tutti i repo, rendendo il badge CI nativo leggibile come `zenzic-audit | passing`.
- **Testo `alt` dei badge normalizzato a lowercase kebab:** I badge CI usano `alt="zenzic-audit"`, i badge Score usano `alt="zenzic-score"` in tutti i README.

### Fixed

- **SSoT `CodeDefinition`:** Severity, penalità DQS e categoria di scoring per ogni Z-code sono ora definiti una sola volta in `codes.py`.
- **ADR-031 Paradox Resolution:** Z103, Z111, Z113 integrati nella tabella delle penalità.
- **Bug CI Z114 corretto:** Z114 `LARGE_PAGINATION_SET` era erroneamente classificato come `severity="error"`.

### Removed

- **Badge Audit statico eradicato — Dual-Badge Telemetry:** Il badge "passing" hardcodato è stato sostituito su tutta la flotta dal badge nativo GitHub Actions CI. Zenzic espone ora due segnali ortogonali: stato CI (Pass/Fail, real-time, via GitHub Actions) e Score DQS (qualità del codice accettato, stampato inline via `--stamp`). Un badge rosso da `--stamp` in sviluppo locale è un feedback immediato e inequivocabile che il commit verrà respinto dalla CI — non raggiungerà mai main.
- **Breaking change — `--export-shields` rimosso da `zenzic score`.** Il workflow basato su Gist è eradicato. Sostituire con `zenzic score --stamp` (vedi Added). Rimuovere manualmente il secret `GIST_TOKEN` dalle impostazioni del repository.
- **Breaking change — `map_url()` e `classify_route()` rimossi dal protocollo `BaseAdapter`.**
- **Breaking change — API callback `find_orphans()` rimossa.**

---

## [0.8.0] — 2026-05-15 <!-- zenzic:ignore: Z601 release codename -->

### Added

- **Scoring Engine 2.0:** Valutazione matematica della qualità con pesi a tier e penalità Technical Debt.
- **Integrity Regression Check (`zenzic diff`):** Comando per confrontare lo stato della documentazione tra branch.
- **Config Genealogy (`zenzic explain`):** Comando di introspezione per tracciare l'origine delle regole.
- **Regola Z108 (EMPTY_LINK_TEXT):** Nuovo validatore per rilevare link con label vuote.
- **MDX-Native Suppressions:** Supporto per la sintassi JSX `{/* zenzic:ignore */}`.
- **Sovereign Audit Mode (`--audit`):** Flag globale per bypassare tutte le soppressioni.
- **Privacy Gate (Z204):** Supporto per `.zenzic.local.toml` per pattern vietati locali.
