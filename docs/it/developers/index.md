---
icon: lucide/code
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Guida per Sviluppatori

Benvenuti nella comunità tecnica di Zenzic. Costruiamo strumenti che colmano il
divario tra la documentazione umana e la verità eseguibile. Il nostro codice segue
standard rigorosi per prestazioni, sicurezza dei tipi (`mypy --strict`) e
accessibilità.

Questa sezione copre tutto il necessario per estendere, adattare o contribuire a
Zenzic.

---

## In questa sezione

- [Scrivere Regole Plugin](plugins.md) — implementa sottoclassi `BaseRule`,
  registrale tramite `entry_points` e soddisfa il contratto pickle / purezza.
- [Scrivere un Adapter](writing-an-adapter.md) — implementa il protocollo
  `BaseAdapter` per insegnare a Zenzic a gestire un nuovo motore di documentazione.
- [Progetti di Esempio](examples.md) — quattro fixture eseguibili auto-contenuti che
  dimostrano configurazioni Zenzic corrette e non.

---

## Contribuire

Le linee guida complete per contribuire, le convenzioni del codice, le Core Laws e la
checklist pre-PR si trovano in
[`CONTRIBUTING.md`](https://github.com/PythonWoods/zenzic/blob/main/CONTRIBUTING.md)
su GitHub (in inglese).

Quando apri una pull request, GitHub carica automaticamente la
[checklist PR](https://github.com/PythonWoods/zenzic/blob/main/.github/PULL_REQUEST_TEMPLATE.md)
— verifica tutte le voci prima di richiedere una revisione.
