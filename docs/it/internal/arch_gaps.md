<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic - Architectural Gaps & Technical Debt {#architectural-gaps}

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

---

## Risolti

### ZRT-005 — Bootstrap Paradox

**Identificato in:** v0.5.0a3
**Componente:** `zenzic/cli.py`, `zenzic/core/scanner.py`
**Descrizione:** `zenzic init` crashava con un errore di configurazione quando veniva invocato in una directory vuota (senza `zenzic.toml` esistente). Il comando di bootstrap assumeva erroneamente che un contesto di progetto valido fosse già presente prima ancora di crearlo.
**Risoluzione:** Implementata una sequenza di inizializzazione a due fasi: (1) scrittura del file `zenzic.toml` tramite template isolato dal resolver di contesto, (2) avvio del ciclo di validazione solo se il file di configurazione esiste già. Il resolver ora tollera la directory vuota e delegamente l'amorcage al comando `init`. Verificato con il Genesis Test: `zenzic init` in directory completamente vuota genera correttamente `zenzic.toml` con il blocco Shield commentato.
**Chiuso in:** v0.5.0a4 (`fix/sentinel-hardening`) — commit `38be6f1`

### CI-001 — Node.js 24 / npx Prompt Non Interattivo (Cloudflare Pages)

**Identificato in:** v0.5.0a4 (`fix/v050a4-infra-alignment`)
**Componente:** `.github/workflows/deploy-docs.yml`
**Descrizione:** `cloudflare/wrangler-action@v3` (ultima versione stabile) invoca
`npx wrangler` senza il flag `--yes`. npm 10+ sui runner GitHub con Node.js 24
blocca l'installazione non interattiva dei pacchetti, interrompendo il deploy con:
`"npx canceled due to missing packages and no YES option: [wrangler@4.81.0]"`.
**Risoluzione:** Pre-installazione globale di `wrangler@latest` tramite `npm install -g`
prima dello step dell'action. npx trova il binario già nel PATH e salta il download
interattivo. `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` aggiunto per sopprimere il
warning di deprecazione di Node.js 20. Rimuovere lo step di pre-installazione solo
quando `wrangler-action` rilascia una versione che passa `--yes` a npx nativamente.
**Chiuso in:** v0.5.0a4 (`fix/v050a4-infra-alignment`)
