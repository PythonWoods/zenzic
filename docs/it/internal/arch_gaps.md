<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic - Architectural Gaps & Technical Debt

> *"Ciò che non è documentato, non esiste; ciò che è documentato male, è un'imboscata."*
>
> Questo documento traccia i gap architetturali e il debito tecnico identificati durante lo sviluppo, che necessitano di risoluzione prima di traguardi specifici (come la rc1).

---

## Target: v0.5.0rc1 (The Bastion)

### 1. Automazione del Versioning (Noxfile)

**Identificato in:** v0.5.0a4 (`fix/sentinel-hardening`)
**Componente:** `noxfile.py`
**Descrizione:** Il noxfile attualmente supporta solo bump di `patch`, `minor` e `major`. Durante le iterazioni alpha/beta, non è possibile eseguire il bump prerelease direttamente tramite il framework di automazione (`nox -s bump -- prerelease`).
**Azione Richiesta:** Il noxfile deve essere aggiornato per estrarre e supportare la gestione dei tag alpha/beta pre-release (bump `pre_l` e `pre_n`) interfacciandosi correttamente con `bump-my-version`, per permettere l'iterazione rapida delle release di testing senza bypassare l'automazione.

### 2. Copertura della Pipeline di Sicurezza (Integrazione CLI)

**Identificato in:** v0.5.0a4 (`fix/sentinel-hardening`)
**Componente:** `zenzic/cli.py`
**Descrizione:** Lo scanner e il reporter dispongono ora di mutation test completi che proteggono l'efficacia dello Shield (The Sentinel's Trial). Tuttavia, la mutazione del silenziatore (`findings.append(...) -> pass`) all'interno di `cli.py` non viene coperta dalla suite attuale perché essa salta la CLI per interfacciarsi con il proxy.
**Azione Richiesta:** Un test end-to-end (e2e) che attivi l'intera CLI e verifichi l'uscita con exit code 2 e la presenza del reporter per assicurare che il routing non sia vulnerabile ad amnesie (Commit 4b o successivi).
