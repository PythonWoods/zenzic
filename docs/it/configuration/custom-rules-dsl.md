---
icon: lucide/regex
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# DSL Regole Custom

`[[custom_rules]]` permette di dichiarare regole lint specifiche del progetto direttamente in
`zenzic.toml`. Ogni regola applica un'espressione regolare riga per riga a ogni file `.md`. Nessun
Python richiesto — il DSL è puro TOML.

---

## Sintassi

```toml
[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Rimuovere il marker DRAFT prima della pubblicazione."
severity = "warning"

[[custom_rules]]
id       = "ZZ-NOINTERNAL"
pattern  = "internal\\.corp\\.example\\.com"
message  = "L'hostname interno non deve apparire nella documentazione pubblica."
severity = "error"
```

Ogni header `[[custom_rules]]` aggiunge una regola alla lista (sintassi TOML array-of-tables).

---

## Campi

| Campo | Tipo | Richiesto | Descrizione |
| :--- | :--- | :---: | :--- |
| `id` | stringa | ✓ | Identificatore univoco stabile mostrato nei risultati |
| `pattern` | stringa | ✓ | Espressione regolare applicata a ogni riga di contenuto |
| `message` | stringa | ✓ | Spiegazione leggibile mostrata nel risultato |
| `severity` | `"error"` \| `"warning"` \| `"info"` | — | Default: `"error"` |

---

## Comportamento della severità

| Severità | Blocca la pipeline | Con `--strict` |
| :--- | :---: | :---: |
| `"error"` | Sì (exit code 1) | Sì |
| `"warning"` | No | Sì |
| `"info"` | No | No |

---

## Formato dell'output

Quando una regola custom scatta, Zenzic mostra il problema con uno snippet visivo della riga
incriminata:

```text
[ZZ-NODRAFT] docs/guide/install.md:14 — Rimuovere il marker DRAFT prima della pubblicazione.
  │ > DRAFT: sezione in costruzione
```

Per la severità `"error"` l'ID della regola viene mostrato in rosso; per `"warning"` in giallo.
La riga `│` mostra la riga sorgente esattamente come appare nel file.

Le regole con `severity = "info"` vengono stampate senza lo snippet `│`.

---

## Indipendenza dall'adapter

**Le regole custom sono indipendenti dall'adapter.** Una regola che cerca `DRAFT` si attiva
identicamente che il progetto usi `MkDocsAdapter`, `ZensicalAdapter` o `VanillaAdapter`. Questo
significa che le regole scritte per un progetto MkDocs non richiedono modifiche dopo la
[migrazione a Zensical](../../guide/migration.md).

---

## Posizionamento TOML

Inserisci tutti i blocchi `[[custom_rules]]` **prima** della sezione `[build_context]`.
`[build_context]` deve essere l'ultima sezione in `zenzic.toml`.

```toml
docs_dir = "docs"

[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Rimuovere il marker DRAFT prima della pubblicazione."
severity = "warning"

[build_context]          # ← sempre per ultimo
engine = "mkdocs"
```

---

## Performance

**I pattern vengono compilati una volta sola** al caricamento della configurazione, non per ogni file. Non c'è penalità di performance nell'avere molte regole. Pattern regex non validi sollevano un `ConfigurationError` all'avvio con il pattern incriminato e il messaggio di errore della regex.

---

## Suggerimenti per i pattern

| Obiettivo | Pattern |
| :--- | :--- |
| Corrispondenza case-insensitive | `(?i)\\bDRAFT\\b` |
| Punto letterale (hostname) | `internal\\.corp\\.example\\.com` |
| Corrispondenza ovunque sulla riga | `TODO` (non servono ancore — il matching è per riga) |
| Escludere falsi positivi | Usa i word boundary `\\b` per evitare di matchare `TODOS` cercando `TODO` |

Tutti i pattern vengono applicati con Python `re.search` — una corrispondenza ovunque sulla riga attiva il finding. Usa `^` e `$` solo quando devi vincolare all'inizio o alla fine della riga.
