<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# 🪨 Zenzic v0.8.0 — Basalt (L'Era delle Fondamenta)

Basalt è la release di governance che blocca il contratto pubblico dei finding
prima della scalata dell'ecosistema. Chiude il ponte di migrazione dai namespace
legacy agli ID canonici v0.8.0 e rende immutabili gli exit di sicurezza.

## Snapshot del Contratto Basalt

- **Namespace Contract (ADR-012):** runtime ed esempi documentali attivi usano
 i codici canonici (`Z405`, `Z406`, `Z601`, `Z602`); i codici legacy restano
 solo come anchor di migrazione.
- **Superfici Frozen:** `FROZEN_CODES`, `NON_SUPPRESSIBLE_CODES` e
 `PLUGIN_FORBIDDEN_EXITS` diventano contratti di compatibilità espliciti.
- **Invariante sicurezza ZRT-007:** l'esecuzione regex in produzione è
 enforceata su RE2 con policy no-fallback.
- **Architettura developer (ADR-013):** Regex ACL formalizzato come boundary
 anti-corruzione tra ergonomia Python e garanzie runtime RE2.

## Conseguenze Operative

- CI e integrazioni plugin possono trattare i contratti Basalt come stabili.
- Gli exit di sicurezza restano non negoziabili ai confini di enforcement.
- La parità documentazione/runtime è obbligatoria per gli esempi dei finding.

---

## � Release Storica — v0.7.1 (Patch Infrastrutturale)

La v0.7.1 è una patch infrastrutturale silenziosa: allineamento CI/CD, correzione matrice Nox, e enforcement di default Zero-Config. Non porta significato architetturale o narrativo; tutti i risultati fondazionali appartengono esclusivamente a v0.7.0 (Quartz Maturity, Anno Zero).

**Versioni precedenti** a v0.7.0 sono ufficialmente deprecate e non seguono l'attuale architettura Diátaxis.

## 🚀 Verso il Futuro

Con questa release, Zenzic non è più solo un tool, ma una piattaforma di fiducia per l'ingegneria della documentazione.

---
**PythonWoods** <dev@pythonwoods.dev>
*Data di Rilascio: 2026-05-07*

---

## Riferimento operativo

Per dettagli tecnici storici e cronologia estesa, consultare anche
[RELEASE.md](RELEASE.md).
