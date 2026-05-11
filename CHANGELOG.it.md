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

### Added

- **Decreto Epoch 8:** «Epoch 8: Basalt – The Sovereign Transition. Introducing Suppression CAP, Local Sanctuary, and Avion-Grade Governance.»
- **Fase 2 (The Truth-Seeker) consegnata:** aggiunta la modalità Audit
  Sovrano con `zenzic check all --audit` (bypassa `zenzic-ignore` inline e
  `[governance].per_file_ignores` per i finding sopprimibili), oltre ai
  comandi Secret Guard nativi (`zenzic guard scan`, `zenzic guard init`)
  alimentati dalle signature Shield per enforcement pre-commit.
- **Stability Contract in `codes.py`:** aggiunte le superfici immutabili
  `FROZEN_CODES`, `NON_SUPPRESSIBLE_CODES` e `PLUGIN_FORBIDDEN_EXITS` per la
  linea v0.8.0 Basalt.
- **Tier model formalizzato nel registro pubblico:** ownership
  Core/Structure/Governance esplicita nelle mappature canoniche.
- **Mappa di migrazione legacy:** aggiunta `LEGACY_TO_CODE` per mappare
  `Z903`→`Z405`, `Z904`→`Z406`, `Z905`→`Z601`, `Z907`→`Z602`.
- **ADR-013 (Regex ACL) pubblicata nelle developer docs EN/IT:** definisce la
  strategia anti-corruption layer e l'enforcement RE2 senza fallback.

### Changed

- **Contratto namespace ADR-012 finalizzato per v0.8.0:** runtime/docs/esempi
  usano i codici canonici (`Z405`, `Z406`, `Z601`, `Z602`) e mantengono codici
  legacy solo come anchor diagnostiche di migrazione.

### Fixed

- **Gap di parità registro per `Z000` (`UNSUPPORTED_ENGINE`) chiuso:**
  aggiunto a `CODE_NAMES`, `CODE_DESCRIPTIONS` e `CODE_SARIF_LEVELS` con
  allineamento enciclopedia codici.
- **Regressione di performance in `VSMBrokenLinkRule.check_vsm` corretta
  (implementazione ZRT-007):** Il facade RE2 `zenzic.core.regex` non ha cache
  interna dei pattern; ogni chiamata `re.sub/search` con stringa raw ricompilava
  il pattern da zero. 12 call-site inline in 5 file sorgente (`rules.py`,
  `validator.py`, `scanner.py`, `adapters/_docusaurus.py`, `adapters/_utils.py`,
  `cli/_standalone.py`) sostituite con 11 costanti pre-compilate a livello di
  modulo. Aggiunto fast path in `_to_canonical_url` per href relativi semplici.
  `TestAdaptiveRuleEngineTortureTest` (N=10 000 link): `1,18 s → 0,78 s`
  (soglia < 1,0 s). 1 500 test superati.

### Security

- **Hardening ZRT-007 completato nel codice runtime:** eliminato l'uso di
  `re` stdlib nei percorsi di produzione, sostituito con ACL RE2.
- **Policy regex no-fallback enforceata:** costrutti non supportati falliscono
  esplicitamente sotto RE2, senza degradazione silenziosa a stdlib.
- **Lint gate anti-regressione:** Ruff banned API blocca la reintroduzione di
  import diretti `re` nei sorgenti protetti.

---
