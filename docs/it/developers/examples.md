---
icon: lucide/folder-open
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Progetti di Esempio

La directory `examples/` alla root del repository contiene quattro progetti
auto-contenuti. Ognuno è un fixture eseguibile: naviga nella directory e lancia
`zenzic check all` per vederne l'output.

```bash
git clone https://github.com/PythonWoods/zenzic
cd zenzic/examples/<nome>
zenzic check all
```

---

## broken-docs — Fixture di Fallimenti Intenzionali

**Scopo:** Attivare ogni controllo Zenzic almeno una volta. Utile per testare un
nuovo controllo o verificare che un messaggio di errore sia formattato correttamente.

**Risultato atteso:** `FAILED` — molteplici fallimenti, codice di uscita 1.

| Controllo | Cosa lo attiva |
| --- | --- |
| Link | File mancante, ancora morta, path traversal, percorso assoluto, i18n rotto |
| Orfani | `api.md` esiste su disco ma è assente dalla `nav` |
| Snippet | Blocco Python con `SyntaxError` (due punti mancanti) |
| Placeholder | `api.md` ha solo 18 parole e un marcatore di task |
| Asset | `assets/unused.png` è su disco ma mai referenziato |
| Regole custom | Pattern `ZZ-NOFIXME` in `zenzic.toml` |

```bash
cd examples/broken-docs
zenzic check all              # uscita 1
zenzic check all --exit-zero  # uscita 0 (modalità soft-gate)
```

Motore: `mkdocs`. Contiene anche un `zensical.toml` per dimostrare lo stesso
fixture con il motore Zensical.

---

## i18n-standard — Progetto Bilingue Gold Standard

**Scopo:** Dimostrare un progetto bilingue perfettamente pulito con punteggio 100/100.
Usa questo come template di riferimento per un nuovo progetto multilingua.

**Risultato atteso:** `SUCCESS` — tutti i controlli passano, punteggio 100/100.

Pattern chiave dimostrati:

- **Suffix-mode i18n** — le traduzioni vivono come file `pagina.it.md` nella stessa
  cartella, mai in un sottoalbero `docs/it/`
- **Simmetria dei percorsi** — `../../assets/brand-kit.zip` si risolve identicamente
  da `pagina.md` e `pagina.it.md`
- **Esclusione build artifact** — `excluded_build_artifacts` permette a Zenzic di
  validare i link a file generati senza che siano presenti su disco
- **`fail_under = 100`** — qualsiasi regressione rompe il gate

```bash
cd examples/i18n-standard
zenzic check all --strict   # uscita 0, punteggio 100/100
```

Motore: `mkdocs` con plugin `i18n` in modalità `docs_structure: suffix`.

---

## security_lab — Fixture di Test per lo Shield

**Scopo:** Verificare il sottosistema Shield — rilevamento credenziali e
classificazione del path traversal — prima dei rilasci.

**Risultato atteso:** `FAILED` — codice di uscita 2 (evento Shield; non sopprimibile).

| File | Cosa attiva |
| --- | --- |
| `traversal.md` | `PathTraversal`: `../../etc/passwd` sfugge a `docs/` |
| `attack.md` | `PathTraversal` + sette pattern fake di credenziali (tutte le famiglie Shield) |
| `absolute.md` | Percorsi assoluti (`/assets/logo.png`, `/etc/passwd`) |
| `fenced.md` | Credenziali fake dentro blocchi delimitati senza etichetta e con etichetta `bash` |

```bash
cd examples/security_lab
zenzic check links --strict   # uscita 1 (path traversal)
zenzic check references       # uscita 2 (Shield: credenziali fake)
zenzic check all              # uscita 2 (Shield ha la priorità)
```

> Le credenziali in `attack.md` e `fenced.md` sono completamente sintetiche —
> corrispondono alla forma regex ma non sono token validi per nessun servizio.

Motore: `mkdocs`.

---

## vanilla — Gate di Qualità Agnostico rispetto all'Engine

**Scopo:** Mostrare Zenzic in esecuzione senza nessun motore di build. Nessun
`mkdocs.yml`, nessun `zensical.toml`, nessuna config Hugo. Solo
`engine = "vanilla"` in `zenzic.toml`.

**Risultato atteso:** `SUCCESS` — tutti i controlli applicabili passano.

Cosa funziona in modalità Vanilla:

- Link, snippet, placeholder e asset sono verificati completamente
- Le `[[custom_rules]]` si attivano identicamente a qualsiasi altra modalità
- `fail_under` impone un punteggio di qualità minimo
- Il **controllo orfani è saltato** — senza nav dichiarata non esiste un insieme di riferimento

```bash
cd examples/vanilla
zenzic check all   # uscita 0
```

Usa la modalità Vanilla per Hugo, Docusaurus, Sphinx, Astro, Jekyll, wiki GitHub
o qualsiasi progetto che non usa MkDocs o Zensical.

---

## Eseguire la suite completa degli esempi

Dalla root del repository, verifica che tutti gli esempi producano i codici di
uscita attesi:

```bash
# Gold standard e vanilla: devono essere puliti
(cd examples/i18n-standard && zenzic check all --strict)
(cd examples/vanilla        && zenzic check all)

# Broken: deve fallire con uscita 1
(cd examples/broken-docs    && zenzic check all); [ $? -eq 1 ]

# Security lab: deve uscire con codice 2 (Shield)
(cd examples/security_lab   && zenzic check all); [ $? -eq 2 ]
```
