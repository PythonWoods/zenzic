<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Registro delle modifiche

Tutte le modifiche rilevanti a Zenzic sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Le versioni seguono il [Semantic Versioning](https://semver.org/).

---

> **Cronologia di sviluppo (v0.1.0 – v0.7.1):** Consultare l'[Archivio Changelog](CHANGELOG.it.archive.md).

## [Non Rilasciato]

### Modificato (Breaking)

- **Refactor del namespace per ownership dei codici (ADR-012, Batch 1):** I
  finding di governance e struttura sono stati rinumerati in bande dedicate.
  - `Z903` → `Z405` (`UNUSED_ASSET`)
  - `Z904` → `Z406` (`NAV_CONTRACT`)
  - `Z905` → `Z601` (`BRAND_OBSOLESCENCE`)
  - `Z907` → `Z602` (`I18N_PARITY`)
  La banda `Z9xx` resta focalizzata sui diagnostici engine/system.

### Aggiunto

- **Costanti dello Stability Contract in `codes.py`:** Aggiunte
  `FROZEN_CODES`, `NON_SUPPRESSIBLE_CODES` e `PLUGIN_FORBIDDEN_EXITS`
  come superfici contrattuali esplicite e immutabili per la v0.8.0.
- **Tier Model formalizzato nel registro pubblico:** ownership
  Core/Structure/Governance esplicita nelle mappature e documentata per la
  migrazione.
- **Mappa di migrazione legacy per diagnostica:** aggiunta `LEGACY_TO_CODE`
  per collegare riferimenti legacy (`Z903`, `Z904`, `Z905`, `Z907`) ai
  rispettivi codici canonici v0.8.0.

### Aggiunto

- **DX guard `_check-hooks`:** Aggiunta recipe nascosta `_check-hooks` come prima dipendenza
  di `just verify`. Emette un avviso se l’hook Final Guard pre-push (`pre-commit install
  -t pre-push`) non è installato localmente, senza bloccare l’esecuzione della verifica.- **Recipe `version`:** `just version` stampa la versione corrente del progetto direttamente
  tramite `bump-my-version`. Alternativa rapida alla lettura manuale di `pyproject.toml`.
- **Flag `--short` per `release-dry`:** `just release-dry patch --short` filtra l'output
  verbose di bump-my-version alle tre righe essenziali: versione corrente, nuova versione
  e conferma dry-run. Il comportamento predefinito (diff verbose completo) è invariato.
- **DX guard `release-contracts`:** Nuova recipe che impone i contratti architetturali sul
  justfile: presenza obbligatoria delle recipe `version`, `release` e `release-dry`;
  `--allow-dirty` deve comparire solo in `release-dry`, mai in `release`. Inclusa in
  `just verify` come controllo strutturale che fallisce immediatamente in caso di violazione.

### Modificato

- **Matrice di test — Boundary Testing (parità CI):** `PYTHONS` di Nox aggiornato da
  `["3.11", "3.12", "3.13"]` a `["3.10", "3.14"]`, specchiando la CI Pillar Matrix
  (Floor 3.10 / Peak 3.14). Elimina la divergenza "verde in locale ≠ verde in remoto".
- **Sessioni a versione fissa pinnate al Peak 3.14:** Le sessioni `lint`, `format`,
  `fmt`, `typecheck`, `reuse`, `security`, `mutation` e `bump` aggiornate da
  `python="3.11"` a `python="3.14"`.
- **Floor Mypy abbassato a 3.10:** `[tool.mypy] python_version` modificato da `"3.11"` a
  `"3.10"`, imponendo la compatibilità al floor dichiarato `requires-python = ">=3.10"`.
  Il guard `tomllib` / `tomli` (`sys.version_info >= (3, 11)`) e la dipendenza runtime
  `tomli>=2.0.0; python_version < '3.11'` erano già in posto.

### Corretto

- **`Z000` aggiunto al registro dei codici (`codes.py`):** `Z000` (UNSUPPORTED_ENGINE)
  era già documentato nello schema nel docstring di `codes.py` e in `finding-codes.mdx`,
  ma mancava dai dizionari `CODE_NAMES`, `CODE_DESCRIPTIONS` e `CODE_SARIF_LEVELS`.
  Il registro conta ora 34 codici canonici. La sessione `verify-codes-parity` include
  Z000 come voce completa dell’enciclopedia con anchor `{#z000}`.

---
