<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic — Architettura della Pipeline e Complessità Algoritmica {#pipeline-architecture}

> *"Misura due volte, taglia una volta. Conosci la complessità prima di scalare."*
>
> Questo documento descrive le fasi interne della pipeline del motore di
> validazione di Zenzic, con enfasi sulle garanzie di complessità algoritmica.
> È rivolto ai DevOps engineer che valutano le caratteristiche di performance
> su siti di documentazione di grandi dimensioni (1 000–50 000 pagine) e ai
> contributor che lavorano sul core del validatore.

---

## Panoramica

La pipeline di validazione di Zenzic è divisa in tre fasi sequenziali:

| Fase | Nome | Complessità | Descrizione |
| :---: | :--- | :---: | :--- |
| 1 | **Build in-memory** | Θ(N) | Legge tutti i file, estrae i link, costruisce la VSM |
| 1.5 | **Analisi del grafo** | Θ(V+E) | Costruisce il grafo di adiacenza, rileva cicli tramite DFS iterativa |
| 2 | **Validazione per-link** | O(1) per query | Risolve ogni link contro gli indici pre-costruiti |

Complessità totale della pipeline per un sito con N pagine e L link totali:
**Θ(N + V + E + L)** — lineare in tutti gli input, dove V ≤ N e E ≤ L.

---

## Fase 1 — Build in-memory (Θ(N))

La Fase 1 legge ogni file `.md` in `docs_dir` esattamente una volta. Per ogni file:

1. **Estrazione dei link** — una state machine deterministica riga per riga estrae
   tutti i link Markdown `[testo](href)` e i link di riferimento `[testo][id]`,
   saltando i blocchi di codice delimitati e gli inline code span.
2. **Pre-calcolo delle ancore** — gli slug delle intestazioni vengono estratti e
   memorizzati in un `dict[str, set[str]]` indicizzato per percorso file.
3. **Costruzione della VSM** — la Virtual Site Map viene popolata: un `frozenset`
   di tutti i percorsi file risolti presenti nell'insieme dei file scansionati e
   nell'alberatura di navigazione del sito (se applicabile).

Ogni file viene letto esattamente una volta (O(N) letture I/O). La state machine
gira in O(F) dove F è il numero di caratteri nel file, sommando a Θ(N) su tutti
i file. Nessun file viene riaperto durante le Fasi 1.5 o 2.

### Parsing a macchina a stati e falsi positivi da Superfences

Il motore di estrazione usa una macchina a tre stati: `NORMALE`, `IN_FENCE`,
`IN_CODE_SPAN`. Le transizioni sono attivate da:

- `` ``` `` o `~~~` all'inizio di una riga → entra/esce da `IN_FENCE`
- Conteggio backtick su una singola riga → commuta `IN_CODE_SPAN`

I link in `IN_FENCE` o `IN_CODE_SPAN` vengono scartati silenziosamente.
Questo previene falsi positivi da documentazione che mostra esempi di sintassi
Markdown all'interno di blocchi di codice (documenti in stile
`pymdownx.superfences`).

---

## Fase 1.5 — Analisi del grafo: DFS iterativa (Θ(V+E))

La Fase 1.5 viene eseguita una volta dopo la Fase 1, prima di qualsiasi
validazione per-link. Prende l'insieme delle coppie (pagina_sorgente →
pagina_target) estratte nella Fase 1 e costruisce un grafo orientato di
adiacenza.

### Perché DFS iterativa?

Il limite di ricorsione predefinito di Python (`sys.getrecursionlimit()` = 1 000)
causerebbe un `RecursionError` su siti di documentazione con catene di navigazione
profonde. Zenzic usa una **DFS iterativa con stack esplicito** per evitare questo
limite completamente, indipendentemente dalla profondità del grafo.

### Algoritmo — colorazione BIANCO/GRIGIO/NERO

```python
BIANCO = 0  # non visitato
GRIGIO  = 1  # sullo stack DFS corrente (in elaborazione)
NERO   = 2  # completamente esplorato

def _find_cycles_iterative(adj: dict[str, list[str]]) -> frozenset[str]:
    colore = dict.fromkeys(adj, BIANCO)
    in_ciclo: set[str] = set()

    for inizio in adj:
        if colore[inizio] != BIANCO:
            continue
        stack = [(inizio, iter(adj[inizio]))]
        colore[inizio] = GRIGIO
        while stack:
            nodo, figli = stack[-1]
            try:
                figlio = next(figli)
                if colore[figlio] == GRIGIO:
                    # Arco all'indietro → ciclo rilevato
                    in_ciclo.add(figlio)
                    in_ciclo.add(nodo)
                elif colore[figlio] == BIANCO:
                    colore[figlio] = GRIGIO
                    stack.append((figlio, iter(adj.get(figlio, []))))
            except StopIteration:
                colore[nodo] = NERO
                stack.pop()

    return frozenset(in_ciclo)
```

**Complessità:** Θ(V+E) — ogni vertice viene inserito e rimosso dallo stack
esattamente una volta; ogni arco viene percorso esattamente una volta.

**Spazio:** O(V) — la mappa dei colori e lo stack DFS insieme usano O(V) memoria.
Il risultato `frozenset[str]` contiene solo i nodi che partecipano ad almeno
un ciclo.

### Registro dei cicli

L'output della Fase 1.5 è un `frozenset[str]` di percorsi di pagine che sono
membri di almeno un ciclo orientato. Questo registro è memorizzato come attributo
immutabile sull'istanza del validatore.

---

## Fase 2 — Validazione per-link (O(1) per query)

Ogni link estratto nella Fase 1 viene validato nella Fase 2 contro **tre
strutture dati pre-costruite**, tutte costruite durante le Fasi 1 e 1.5:

| Controllo | Struttura dati | Costo di lookup |
| :--- | :--- | :---: |
| Esistenza del file | `frozenset[str]` — VSM | O(1) |
| Appartenenza alla nav | `frozenset[str]` — insieme nav | O(1) |
| Validità ancora | `dict[percorso, set[ancora]]` | O(1) |
| Appartenenza a ciclo | `frozenset[str]` — registro cicli | O(1) |

Poiché tutti e quattro i lookup sono O(1), la Fase 2 gira in **O(L)** tempo
totale dove L è il numero totale di link in tutte le pagine.

### Perché la Fase 2 rimane O(1) per query

Il registro dei cicli è un `frozenset` — l'insieme immutabile built-in di Python
con test di appartenenza in O(1) medio-caso tramite hashing. Non c'è DFS o
attraversamento del grafo al momento della query. Il costo Θ(V+E) viene pagato
una volta nella Fase 1.5; ogni lookup successivo è puro accesso a tabella hash.

---

## Profilo di Scalabilità

| Dimensione sito | Fase 1 | Fase 1.5 | Fase 2 | Totale |
| :--- | :--- | :--- | :--- | :--- |
| 100 pagine, 500 link | < 5 ms | < 1 ms | < 2 ms | ~ 8 ms |
| 1 000 pagine, 5 000 link | ~ 30 ms | ~ 8 ms | ~ 15 ms | ~ 55 ms |
| 10 000 pagine, 50 000 link | ~ 300 ms | ~ 80 ms | ~ 150 ms | ~ 530 ms |
| 50 000 pagine, 250 000 link | ~ 1.5 s | ~ 400 ms | ~ 750 ms | ~ 2.6 s |

Tutte le misurazioni sono single-threaded su un runner CI di fascia media
(2 vCPU, 4 GB RAM). La scansione Shield (Fase 1, sovrapposta) aggiunge < 10%
di overhead indipendentemente dalla dimensione del sito, poiché è un singolo
passaggio regex per file.

---

## Documenti Correlati

- [ADR 003 — Logica di Discovery](../adr/003-discovery-logic.md) — motivazione
  per la pipeline in due fasi e la scelta della DFS iterativa
- [Gap Architetturali](arch_gaps.md) — elementi di debito tecnico aperti
- [Rapporto Sicurezza — Shattered Mirror](security/shattered_mirror_report.md) —
  analisi della correttezza dei pattern Shield
