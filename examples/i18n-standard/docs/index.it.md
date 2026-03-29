<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# i18n Standard — Il Gold Standard

Benvenuto nell'esempio **Zenzic Gold Standard**. Questo sito dimostra una struttura
di documentazione bilingue perfetta che ottiene **100/100** con `zenzic check all --strict`.

## Perché questo è lo standard

| Regola | Come questo sito è conforme |
| --- | --- |
| **Suffix Mode** | Le traduzioni sono file `pagina.it.md` nella stessa cartella, mai in `docs/it/` |
| **Zero link assoluti** | Ogni link interno è relativo (`../`, `./`) |
| **Simmetria dei percorsi** | Un link `../assets/brand-kit.zip` si risolve identicamente da `.md` e `.it.md` |
| **Integrità degli asset** | Tutti gli asset referenziati esistono su disco; nessun file ireferenziato |
| **Nessun segnaposto** | Ogni pagina ha contenuto reale, nessun stub TODO |

## Esplora la struttura

- [Indice delle guide](guides/index.md) — inizia qui per il tour guidato
- [Setup avanzato](guides/advanced/setup.md) — annidamento profondo, link relativi a tre livelli
- [Riferimento API](reference/api.md) — interfaccia programmatica

## Download

Il brand kit completo è disponibile come archivio ZIP:
[Scarica brand-kit.zip](assets/brand-kit.zip)

Il manuale utente (generato al momento del build):
[Scarica manual.pdf](assets/manual.pdf)
