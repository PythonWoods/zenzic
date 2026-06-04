<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

Tutte le modifiche rilevanti a Zenzic sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Le versioni seguono il [Versionamento Semantico](https://semver.org/).

---

## [Unreleased]

### Fixed

- **Gli URL di loopback non vengono più segnalati come link esterni:** Gli URL `http://localhost`, `http://127.0.0.1`, `http://0.0.0.0` e `http://::1` (su qualsiasi porta) vengono ora ignorati silenziosamente dal validatore. In precedenza venivano raccolti come link esterni e provocavano un ping di rete o un errore `EXTERNAL_LINK` spurio, rendendo inutilizzabile la validazione in ambienti Docker che referenziano URL di servizi locali negli esempi di configurazione.
- **`Z109 EXTERNAL_LINK_BROKEN` — nuovo codice canonico per URL esterni non raggiungibili:** Gli errori su link esterni (stato HTTP di errore, timeout, errore di rete) vengono ora riportati con il codice `Z109` invece della stringa non standard `EXTERNAL_LINK`. Il codice è registrato in `codes.py` con severità `error`, penalità DQS `3.0` e categoria `structural`.
- **`Z501 PLACEHOLDER` — default sicuri contro il problema di Scunthorpe:** `placeholder_patterns` usa ora pattern RE2 con word boundaries `\b` invece di stringhe letterali compilate con `re.escape()`. Pattern come `wip` non corrispondono più a "wipe"; `stub` non corrisponde più a "Istanbul". I 12 pattern troppo generici o basati su frasi (`draft`, `placeholder`, `to do`, `coming soon`, ecc.) sono rimossi dal set predefinito. I pattern definiti dall'utente vengono compilati senza `re.escape()` e devono essere regex RE2 valide; `re.IGNORECASE` viene applicato automaticamente in fase di compilazione.
- **`MkDocsAdapter.get_metadata_files()` — `.pages` vincolato alla dichiarazione del plugin:** I file `.pages` vengono ora inclusi nel set di file di metadati esclusi dall'analisi solo quando `awesome-pages` o `mkdocs-awesome-pages-plugin` è dichiarato in `mkdocs.yml`. Nei progetti privi del plugin awesome-pages, i file `.pages` non vengono più esclusi silenziosamente dall'analisi degli asset inutilizzati Z405.
- **`zenzic init` — chiarezza dell'output:** Il pannello di conferma principale (verde) elenca ora esplicitamente entrambi i file creati: `.zenzic.toml` e `.zenzic.local.toml will be scaffolded next (machine-local, gitignored)`. La riga engine riporta `(auto-detected)` o `(manually specified via --engine)` per distinguere i due percorsi.
- **`zenzic init --pyproject` — non interrompe più se `pyproject.toml` è assente:** Invece di terminare con un errore, il comando crea ora un file `pyproject.toml` minimale e vi appende la sezione completa `[tool.zenzic]`. Questo rende `--pyproject` utilizzabile anche su progetti greenfield.

### Added

- **`zenzic init --engine ENGINE`:** Nuovo flag per specificare esplicitamente l'adapter engine (`mkdocs`, `zensical`, `docusaurus`, `standalone`) senza affidarsi all'auto-detection. Equivalente al flag `--engine` già disponibile in `check` e `clean`. I valori non validi vengono rifiutati con un errore chiaro che elenca le opzioni valide.
- **Parità di qualità del template `[tool.zenzic]`:** Il template pyproject.toml generato da `zenzic init --pyproject` raggiunge ora la qualità didattica di `.zenzic.toml`: commenti per chiave, exclusion zones, snippet CI/CD, custom rules, spiegazione dei vincoli ortogonali e tutte le sezioni di governance.

### Changed

- **Help text di `zenzic init --local`:** Aggiornato da "Scaffold only .zenzic.local.toml (machine-local overlay). Skips main config creation." a una descrizione orientata al contributor che indica il caso d'uso primario: clonare un repo che ha già `.zenzic.toml` committato.

### Changed

- **La validazione degli snippet gestisce i blocchi Python indentati:** `textwrap.dedent()` viene ora applicato a ciascuno snippet prima della compilazione AST, così i blocchi Python inseriti in elementi di lista, citazioni o altri contesti indentati vengono analizzati correttamente senza generare segnalazioni spurie di `IndentationError`.

---

## [0.9.1] - 2026-06-02

### Added

- Copertura di test con engine nativo, fixture, lab e validazione per `Z107 CIRCULAR_ANCHOR` (link ancora auto-referenziale) e `Z104 FILE_NOT_FOUND`.

### Changed

- **Pipeline unificata delle esclusioni del punteggio:** Refactoring dei calcoli di `zenzic score` (`_run_all_checks` in `_standalone.py`) per eseguire la stessa pipeline `_collect_all_results` → `_to_findings` usata da `check all`. Le esclusioni per soppressione (`per_file_ignores` e `directory_policies`) vengono ora applicate in modo identico per garantire che il DQS sia allineato con i risultati del linter.
- **Risoluzione dei path relativi al repository:** Refactoring della mappatura dei path nello scanner del motore (`scanner.py`), nei comandi CLI di verifica (`_check.py`), nel reporter dei risultati (`reporter.py`) e nel filtro di governance (`_governance.py`) per risolvere tutti i path relativi delle segnalazioni rispetto a `repo_root` invece di `docs_root`, eliminando le incoerenze.
- **Risoluzione del path per il badge stamp:** Corretta la risoluzione del path in `score --stamp` e `score --check-stamp` affinché i path configurati in `badge_stamp_files` siano risolti rispetto a `repo_root` del progetto target invece della directory di lavoro del processo.

### Fixed

- Correzione dell'integrazione dello scanner per `Z403 MISSING_ALT_TEXT` per allineare la copertura delle fixture ai path di scansione in produzione.
- Correzione dei numeri di riga nelle fixture dei test per mantenere deterministiche e stabili le posizioni delle segnalazioni.

---

## [0.9.0] - 2026-05-31

### Added

- `zenzic score --stamp`: stamping deterministico inline del badge per la telemetria del punteggio.
- `zenzic score --check-stamp`: gate di freschezza config-aware per i badge di punteggio stampati.
- Chiave di metadati di progetto `badge_stamp_files` per dichiarare i target di stamp.
- Esenzioni di discovery domain-aware per asset di codice sorgente nell'analisi degli asset inutilizzati.
- Comando `zenzic lab`: sandbox gallery empirica con copertura del 100% degli Z-code (20 scenari).
- 15 nuove directory sandbox sotto `examples/` (z102 fino a z505), ognuna con `.zenzic.toml`, `README.md` e un albero `docs/` minimale che innesca in modo affidabile la regola target.
- Gate di validazione `zenzic lab all`: tutti i 20 scenari emettono il codice di uscita atteso.

### Changed

- Modello di debito di soppressione migrato a punteggio a costo fisso (un punto per soppressione).
- Comportamento di `suppression_cap` chiarito come gate di hard-fail indipendente.
- Parsing dell'overlay locale rafforzato con rifiuto strict delle chiavi sconosciute.
- `just verify` standardizzato a una sequenza operativa in cinque passi (hook, test, strict check, stamp, freshness gate).
- **Performance — Z204 (FORBIDDEN_TERM):** `scan_line_for_forbidden_terms` accetta ora una regex union RE2 precompilata. `ZenzicConfig` costruisce la union una volta sola tramite `_recompile_forbidden_patterns()`. Complessità ridotta da O(N_lines × N_patterns) a O(N_lines).
- **Performance — Z601 (BRAND_OBSOLESCENCE):** `BrandObsolescenceRule` sostituisce `list[RegexPattern]` per pattern con un unico pattern union RE2 compilato in `__init__`. Stessa riduzione a O(N_lines).

### Removed

- Metodi legacy dell'adapter `map_url()` e `classify_route()` dal contratto pubblico.
- Path di export del punteggio legacy `--export-shields` in favore della telemetria nativa stamp/check-stamp.

---

## Versioni precedenti

- Archivio v0.8.x: [changelogs/v0.8.md](./changelogs/v0.8.md)
- Indice archivi v0.1.x–v0.7.x: [changelogs/README.md](./changelogs/README.md)
