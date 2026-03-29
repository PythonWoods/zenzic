<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ottimizzazione delle Prestazioni

Per alberi di documentazione di grandi dimensioni, l'`InMemoryPathResolver` di Zenzic
costruisce una mappa completa dei file all'avvio. Questa pagina descrive le opzioni
di tuning che mantengono i tempi di lint sotto i 100 ms anche per repository con
migliaia di file Markdown.

## Principi chiave

1. **Risoluzione asset O(1)** — Zenzic pre-costruisce un `frozenset` di percorsi
   noti nel Pass 1. Ogni ricerca di link nel Pass 2 è un controllo di appartenenza
   al set a tempo costante. Nessun I/O su filesystem avviene dopo la costruzione.

2. **Rilevamento suffissi senza plugin** — Il resolver identifica `pagina.it.md`
   come traduzione di `pagina.md` dal solo nome del file. Nessun plugin MkDocs,
   nessuna configurazione Hugo, nessun config Zensical richiesto.

3. **`excluded_build_artifacts`** — elenca qui i file generati in modo che Zenzic
   non tenti mai di verificarli su disco durante il lint. Vedi [setup](setup.md)
   per un esempio.

## Navigazione

- [Torna all'Avanzato](setup.md)
- [Torna alle Guide](../index.md)
- [Home](../../index.md)
