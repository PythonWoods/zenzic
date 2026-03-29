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

## Indipendenza dall'adapter

**Le regole custom sono indipendenti dall'adapter.** Una regola che cerca `DRAFT` si attiva
identicamente che il progetto usi `MkDocsAdapter`, `ZensicalAdapter` o `VanillaAdapter`. Questo
significa che le regole scritte per un progetto MkDocs non richiedono modifiche dopo la
[migrazione a Zensical](../../guides/migration.md).

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
