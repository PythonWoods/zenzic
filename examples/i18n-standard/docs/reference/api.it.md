<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Riferimento API

Questa pagina documenta l'interfaccia programmatica esposta dall'esempio i18n Standard.
È volutamente semplice — l'obiettivo è dimostrare una pagina di riferimento valida con
link incrociati funzionanti, non documentare una vera API.

## `check_links(docs_dir)`

Valida tutti i link interni nella directory docs specificata.

**Parametri:**

- `docs_dir` (`str`) — percorso della root della documentazione, relativo alla root del repository.

**Ritorna:** codice di uscita `0` in caso di successo, `1` per errori di link, `2` per violazioni di sicurezza.

## `score()`

Restituisce il punteggio di qualità della documentazione corrente (0–100).

## Pagine correlate

- [Setup avanzato](../guides/advanced/setup.md) — riferimento alla configurazione
- [Ottimizzazione delle prestazioni](../guides/advanced/tuning.md) — guida all'ottimizzazione
- [Home](../index.md)
