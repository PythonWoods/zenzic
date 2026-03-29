---
icon: lucide/terminal
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Comandi CLI

Riferimento completo per ogni comando, flag e codice di uscita Zenzic.

---

## Controlli

```bash
# Controlli individuali
zenzic check links        # Link interni; aggiungi --strict per la validazione HTTP esterna
zenzic check orphans      # Pagine su disco mancanti dalla nav
zenzic check snippets     # Blocchi Python che non compilano
zenzic check placeholders # Pagine stub: basso conteggio parole o pattern vietati
zenzic check assets       # File media non referenziati da nessuna pagina
zenzic check references   # Reference-style link + Zenzic Shield (rilevamento credenziali)

# Tutti i controlli in sequenza
zenzic check all                    # Esegue tutti i controlli
zenzic check all --strict           # Valida anche gli URL esterni; tratta i warning come errori
zenzic check all --format json      # Output machine-readable
zenzic check all --exit-zero        # Segnala problemi ma esce sempre con codice 0
zenzic check all --engine mkdocs    # Sovrascrive il motore rilevato
```

### Flag `--strict`

| Comando | Effetto |
| :--- | :--- |
| `check links --strict` | Valida gli URL HTTP/HTTPS esterni via richieste di rete concorrenti |
| `check all --strict` | Valida gli URL esterni + tratta i warning come errori |
| `check references --strict` | Tratta le Dead Definitions (reference link non usati) come errori bloccanti |
| `score --strict` / `diff --strict` | Esegue il link check in modalità strict |

Puoi anche impostare `strict = true` in `zenzic.toml` per renderlo il default permanente.

### Flag `--exit-zero`

Esce sempre con codice `0` anche quando vengono trovati problemi. Tutti i problemi vengono
comunque stampati e inclusi nel punteggio — solo il codice di uscita viene soppresso. Utile per
pipeline di sola osservazione.

Puoi anche impostare `exit_zero = true` in `zenzic.toml` per renderlo il default permanente.

---

## Autofix & Cleanup

```bash
zenzic clean assets           # Elimina gli asset non utilizzati interattivamente (prompt per ognuno)
zenzic clean assets -y        # Elimina gli asset non utilizzati immediatamente (senza prompt)
zenzic clean assets --dry-run # Mostra cosa verrebbe eliminato senza farlo
```

`zenzic clean assets` rispetta `excluded_assets`, `excluded_dirs` e
`excluded_build_artifacts` da `zenzic.toml` — non eliminerà mai i file che corrispondono a
questi pattern.

---

## Server di sviluppo

```bash
zenzic serve                  # Avvia il server con pre-flight di qualità
zenzic serve --engine mkdocs  # Forza un motore specifico
zenzic serve --engine zensical
zenzic serve --port 9000      # Porta di partenza personalizzata (prova fino a 10 porte consecutive)
zenzic serve -p 9000
zenzic serve --no-preflight   # Salta il pre-flight e avvia il server immediatamente
```

`zenzic serve` rileva automaticamente il motore di documentazione dalla root del repository:

| File di config presente | Binario disponibile | Risultato |
| :--- | :--- | :--- |
| `zensical.toml` | `zensical` o `mkdocs` | Avvia il motore disponibile |
| `zensical.toml` | nessuno | Errore — installa un motore |
| solo `mkdocs.yml` | `mkdocs` o `zensical` | Avvia il motore disponibile |
| solo `mkdocs.yml` | nessuno | Errore — installa un motore |
| nessuno | qualsiasi | Server statico su `site/` (senza hot-reload) |

Prima di avviare il server, Zenzic esegue un pre-flight silenzioso (orfani, snippet,
placeholder, asset non usati). I problemi vengono stampati come warning ma non bloccano mai
l'avvio. La validazione dei link esterni è esclusa intenzionalmente dal pre-flight. Usa
`--no-preflight` per saltare il controllo qualità quando sei nel mezzo di una fix.

**Gestione della porta.** Zenzic individua una porta libera tramite socket probe prima di
avviare il subprocess dell'engine, poi passa `--dev-addr 127.0.0.1:{porta}` a mkdocs o
zensical. L'errore `Address already in use` non può mai provenire dall'engine.

---

## Codici di uscita

| Codice | Significato |
| :---: | :--- |
| `0` | Tutti i controlli selezionati sono passati (o `--exit-zero` era impostato) |
| `1` | Uno o più controlli hanno segnalato problemi |
| **`2`** | **SECURITY CRITICAL — Zenzic Shield ha rilevato una credenziale esposta** |

!!! danger "Il codice di uscita 2 è riservato agli eventi di sicurezza"
    Il codice 2 viene emesso esclusivamente da `zenzic check references` quando lo Shield
    rileva un pattern di credenziale noto incorporato in un URL di riferimento. Non viene mai
    usato per i fallimenti ordinari dei controlli. Se ricevi il codice di uscita 2, trattalo
    come un incidente di sicurezza bloccante e **ruota immediatamente la credenziale esposta**.

---

## Output JSON

Passa `--format json` a `check all` per output strutturato:

```bash
zenzic check all --format json | jq '.orphans'
zenzic check all --format json > report.json
```

Il report JSON contiene sette chiavi:

```json
{
  "links":         [],
  "orphans":       [],
  "snippets":      [],
  "placeholders":  [],
  "unused_assets": [],
  "references":    [],
  "nav_contract":  []
}
```

Ogni chiave contiene una lista di stringhe o oggetti con i problemi. Una lista vuota significa
che il controllo è passato. `nav_contract` valida i link `extra.alternate` in `mkdocs.yml`
rispetto alla Virtual Site Map — sempre vuoto per i progetti non MkDocs.

---

## Override dell'engine

Il flag `--engine` sovrascrive l'adapter del motore di build per una singola esecuzione senza
modificare `zenzic.toml`. Accettato da `check orphans` e `check all`:

```bash
zenzic check orphans --engine mkdocs
zenzic check all --engine zensical
zenzic check all --engine vanilla    # disabilita il controllo orfani indipendentemente dalla config
```

Se passi un nome di engine per cui non esiste un adapter registrato, Zenzic elenca gli adapter
disponibili ed esce con codice 1:

```text
ERROR: Unknown engine adapter 'hugo'.
Installed adapters: mkdocs, vanilla, zensical
Install a third-party adapter or choose from the list above.
```

Gli adapter di terze parti vengono scoperti automaticamente una volta installati — nessun
aggiornamento Zenzic richiesto. Vedi [Scrivere un Adapter](../developers/writing-an-adapter.md).

---

## Punteggio qualità

I controlli individuali rispondono a una domanda binaria: passa o fallisce. `zenzic score`
risponde a una diversa: *quanto è sana questa documentazione, e sta migliorando o peggiorando
nel tempo?*

```bash
zenzic score                   # Calcola punteggio 0–100
zenzic score --save            # Calcola e persiste snapshot in .zenzic-score.json
zenzic score --fail-under 80   # Esce con 1 se il punteggio è sotto la soglia
zenzic score --format json     # Report punteggio machine-readable

zenzic diff                    # Confronta punteggio attuale con snapshot salvato
zenzic diff --threshold 5      # Esce con 1 solo se il calo è superiore a 5 punti
zenzic diff --format json      # Report diff machine-readable
```

### Come è calcolato il punteggio

Ogni categoria di controllo porta un peso fisso che riflette il suo impatto sull'esperienza del
lettore:

| Categoria | Peso | Rationale |
| :--- | ---: | :--- |
| links | 35 % | Un link non valido è un vicolo cieco immediato per il lettore |
| orphans | 20 % | Le pagine irraggiungibili sono invisibili — potrebbero non esistere |
| snippets | 20 % | Esempi di codice non validi fuorviano attivamente gli sviluppatori |
| placeholders | 15 % | Il contenuto stub segnala una pagina incompiuta o abbandonata |
| assets | 10 % | Gli asset non usati sono spreco, ma non bloccano il lettore |

All'interno di ogni categoria, il punteggio decade linearmente: il primo problema costa il 20%
del peso della categoria, il secondo ne costa altri 20%, con un minimo di zero. Una categoria
con cinque o più problemi non contribuisce nulla al totale. I contributi ponderati vengono
sommati e arrotondati a un intero.

### Tracciare le regressioni

```bash
# Sul branch main — stabilisce o aggiorna il baseline
zenzic score --save

# Su ogni pull request — blocca le regressioni della documentazione
zenzic diff --threshold 5
```

`--threshold 5` dà ai collaboratori un margine di cinque punti. Impostalo a `0` per un gate
rigoroso dove qualsiasi regressione fa fallire la pipeline.

### Punteggio minimo

```bash
zenzic score --fail-under 80
```

Utile quando il team si è impegnato a mantenere un livello di qualità definito, indipendentemente
da quello che era il punteggio la settimana scorsa. Puoi anche impostare `fail_under = 80` in
`zenzic.toml` per renderlo persistente.

### Reporting soft

Per rendere visibile il punteggio senza bloccare la pipeline:

```bash
zenzic check all --exit-zero   # report completo, esce 0 comunque
zenzic score                   # mostra il punteggio per visibilità
```

---

## `uvx` vs `uv run` vs `zenzic` diretto

| Invocazione | Comportamento | Quando usare |
| :--- | :--- | :--- |
| `uvx zenzic ...` | Scarica ed esegue in un ambiente **isolato ed effimero** | Job una-tantum, pre-commit hook, CI senza fase di install del progetto |
| `uv run zenzic ...` | Esegue dal **virtual environment del progetto** (richiede `uv sync`) | Quando Zenzic è in `pyproject.toml` e serve comportamento version-pinned |
| `zenzic ...` (diretto) | Richiede Zenzic nel `$PATH` | Macchine developer con install globale |

!!! tip "Raccomandazione CI"
    Preferisci `uvx zenzic ...` per step CI che non installano già le dipendenze del progetto —
    evita di aggiungere Zenzic all'insieme delle dipendenze di produzione.
