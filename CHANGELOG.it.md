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

- **Sentinel Seal**: Sistema di validazione rigorosa a 4 stadi (`just verify`) integrato in
  ogni repository — pre-commit, test-cov e self-check eseguiti identicamente in locale e in CI.
- **Cross-Repo Governance**: Regola della Parità dei Branch per la sincronizzazione Core/Doc
  con fallback automatico su `main`. Configurazione VS Code Multi-Root Workspace per lo
  sviluppo unificato.
- **Z907 Parità I18N**: Scanner di parità traduzione language-agnostic con parallelismo
  adattivo, imposizione chiavi frontmatter e supporto Docusaurus multi-istanza.
- **Esportazione SARIF 2.1.0**: Tutti i comandi `check` supportano `--format sarif` per
  l'integrazione nativa con GitHub Code Scanning e annotazioni inline nelle PR.
- **Matrice CI Cross-Platform**: Matrice 3×3 (Ubuntu/Windows/macOS × Python 3.11/3.12/3.13).
- **Auto-Discovery del Motore**: `engine = "auto"` risolve automaticamente il framework di
  documentazione (Docusaurus → MkDocs → Zensical → Standalone).
- **Decoder Speculativo Base64**: Lo Shield rileva credenziali codificate in Base64 nel
  frontmatter YAML, sigillando il vettore d'attacco S2 dal Tribunale Quartz.
- **Z107 Ancora Circolare**, **Z505 Blocco Codice Senza Tag**, **Z905 Obsolescenza Brand**:
  Tre nuovi check basati su regole per integrità strutturale e del brand.
- **Z404 Integrità Asset di Configurazione**: Verifica i percorsi favicon e social card su
  tutti e tre i motori supportati (Docusaurus, MkDocs, Zensical).
- **Scoperta Navigazione Unificata**: Il rilevamento orfani Docusaurus aggrega le superfici
  sidebar, navbar e footer (Legge di Raggiungibilità UX R21).
- **Parser Sidebar Statico**: Parser regex pure-Python per `sidebars.ts`/`sidebars.js`.
- **GitHub Action Ufficiale**: Action composita `PythonWoods/zenzic-action` con upload SARIF
  e quality gate configurabili.
- **Invariante di Determinismo**: Contratto formale in `pyproject.toml` — Zenzic non
  distribuisce nessuna dipendenza AI/ML.

#### Modificato

- **Architettura Engine-Agnostic**: Plugin MkDocs rimosso permanentemente. Zenzic è ora una
  CLI Sovrana indipendente da qualsiasi framework di documentazione.
- **Ristrutturazione CLI**: Il monolite `cli.py` è stato suddiviso nel package coerente `cli/`.
  `zenzic plugins` sostituito da `zenzic inspect capabilities`.
- **Applicazione della Legge dei Layer**: `ui.py` → `core/ui.py`, `lab.py` → `cli/_lab.py`,
  `run_rule()` → `core/rules.py`. Il Core non importa mai dal layer CLI.
- **Hook Pre-commit**: `zenzic-check-all` sostituito da `zenzic-verify` (postura 4-Gates).
- **Formato Coverage**: Standardizzato in JSON (`coverage.json`) in justfile e noxfile.

#### Rimosso

- **Epurazione Brand Legacy**: Rimozione completa di ogni nomenclatura obsoleta e riferimento
  a piattaforme esterne dalla configurazione e documentazione attive.
- **Plugin MkDocs**: `zenzic.integrations.mkdocs` eliminato fisicamente. L'extra opzionale
  `[mkdocs]` non esiste più.
- **Comando `zenzic plugins`**: Eliminato completamente. Usare `zenzic inspect capabilities`.
- **`scripts/map_project.py`**: Superato; nessun chiamante residuo.

#### Sicurezza

- **[ZRT-001]** Shield Blind Spot — Bypass YAML Frontmatter sigillato (architettura Dual-Stream).
- **[ZRT-002]** ReDoS + Deadlock ProcessPoolExecutor — Prevenzione Canary + contenimento timeout 30s.
- **[ZRT-003]** Shield Bypass Split-Token — Pre-processore `_normalize_line_for_shield()`.
- **[ZRT-004]** Risoluzione VSM Context-Aware — Dataclass `ResolutionContext` per percorsi annidati.
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
