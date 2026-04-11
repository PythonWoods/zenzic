<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Guida di Stile Sentinel {#sentinel-style-guide}

> *"Il rigore della Sentinella nel codice deve estendersi a ogni pixel che l'utente vede."*

Questo documento codifica il **Sentinel Visual Language** — le regole
vincolanti per tutte le pagine della documentazione Zenzic. Ogni
contributore deve seguirle. I revisori devono rifiutare le PR che le violano.

**Direttiva:** ZRT-DOC-002

---

## 1. Regola delle Card (High-Density UX) {#card-rule}

Le card di navigazione orientano. **Non** sostituiscono la barra laterale.

### Struttura

Ogni card in un blocco `<div class="grid cards" markdown>` deve avere esattamente:

1. Un'**icona** (Lucide o Octicons — vedi §3).
2. Un **titolo in grassetto**.
3. Una **descrizione** di massimo due righe.
4. Un **unico link d'azione** con prefisso freccia.

### Esempio canonico

```markdown
- :lucide-play: &nbsp; **Guida Utente**

    Tutto ciò che serve per installare, configurare e integrare Zenzic
    nel tuo workflow CI/CD.

    [:octicons-arrow-right-24: Esplora la Guida](../usage/index.md)
```

### Pattern vietati

| Pattern | Motivo |
| :--- | :--- |
| Catene di link orizzontali (separati da `·`) | Crea un muro di testo; impossibile da scansionare |
| Liste `<li>` annidate dentro una card | Rompe l'uniformità dell'altezza delle card |
| Separatori `---` dentro una card | Aggiunge rumore visivo senza guadagno informativo |
| Card senza action link | Vicolo cieco; l'utente non ha dove andare |

### Eccezione

**Card di presentazione** (es. demo "Sentinel in Action" nella homepage)
possono omettere l'action link perché il loro scopo è la dimostrazione
visiva, non la navigazione. Devono comunque avere il CSS delle card
(bordo, hover, transizione).

---

## 2. Tassonomia delle Admonition {#admonition-taxonomy}

Ogni tipo di admonition ha un — e un solo — ruolo semantico.

| Tipo | Ruolo | Quando usare |
| :--- | :--- | :--- |
| `!!! tip` | **Quick Win** | Comandi one-liner eseguibili immediatamente |
| `!!! example` | **Output Sentinel** | Blocchi di output CLI e campioni di report Sentinel |
| `!!! danger` | **Security Gate** | Solo Exit Code 2 (credenziali) e Exit Code 3 (path traversal) |
| `!!! warning` | **Vincolo di Design** | Regole architetturali, policy per contributori, caveat "usare con parsimonia" |
| `!!! note` | **Chiarimento** | Fatti specifici del motore, onboarding contributori, guide multi-step |
| `!!! abstract` | **Ponte Cross-Reference** | Link dalla sezione corrente al prossimo step operativo |
| `!!! info` | **CTA Comunità** | Chiamate di engagement ("Aiutaci a crescere", "Unisciti alla discussione") |
| `!!! quote` | **Filosofia** | Visione del progetto, manifesto di design, credo della Sentinella |

### Applicazione

Se un blocco non rientra in nessuna delle categorie sopra, riscrivilo come
prosa. Le admonition non sono decorazione.

---

## 3. Legge dell'Iconografia (ZRT-DOC-003) {#iconography}

### Gerarchia

| Priorità | Set | Ambito | Esempio |
| :---: | :--- | :--- | :--- |
| 1 | **Lucide** (`:lucide-*:`) | Tutte le icone UI e di navigazione | `:lucide-play:`, `:lucide-book:` |
| 2 | **Octicons** (`:octicons-*:`) | Concetti GitHub / workflow di sviluppo | `:octicons-arrow-right-24:`, `:octicons-mark-github-24:` |
| 3 | **Simple Icons** (`:simple-*:`) | Logo di brand di terze parti **esclusivamente** | `:simple-pypi:`, `:simple-astral:` |
| — | ~~Material~~ (`:material-*:`) | **VIETATO** | — |

### Regole

- **Coerenza semantica:** se un'icona rappresenta "Contribuisci" in una pagina,
  deve essere la stessa icona in ogni pagina.
- **Nessun mix:** una singola griglia di card non deve combinare icone di set
  diversi (eccezione: freccia Octicons nei link d'azione accanto a icone
  titolo Lucide).

---

## 4. Protocollo Anchor ID (ZRT-DOC-004) {#anchor-ids}

### Quando aggiungere ID espliciti

Aggiungere `{#id}` a un heading quando soddisfa **una qualsiasi** di:

1. È un **titolo H1 di pagina**.
2. È referenziato da un link cross-pagina (`[testo](pagina.md#ancora)`).
3. Compare nelle voci `nav` di `mkdocs.yml` che puntano a una sezione specifica.

### Invariante i18n

L'ID canonico è sempre lo **slug inglese**. Le pagine italiane (e di ogni
futura lingua) devono usare lo stesso valore `{#id}`:

```markdown
<!-- EN -->
## Getting Started {#getting-started}

<!-- IT -->
## Inizia Ora {#getting-started}
```

Questo garantisce che il resolver VSM e i link cross-lingua non si
rompano mai a causa della generazione di slug dipendente dalla traduzione.

### Formato heading

```markdown
## Titolo Sezione {#section-title}
```

Non aggiungere ID a heading che non vengono mai linkati esternamente.
Ogni ID esplicito è un contratto di manutenzione.

---

## 5. Regola dei Blocchi di Codice {#code-blocks}

Ogni fence di apertura **deve** avere un tag di linguaggio:

| Fence | Verdetto |
| :--- | :---: |
| ` ```python ` | ✓ |
| ` ```bash ` | ✓ |
| ` ```toml ` | ✓ |
| ` ```text ` | ✓ (output senza formattazione) |
| ` ``` ` | ✗ **VIETATO** |

Usare `text` per output senza syntax highlighting. I fence nudi danneggiano
gli strumenti di accessibilità e i syntax highlighter.

**Specificità del Gutter:** per l'output CLI mostrato nei blocchi
`!!! example`, preferire sempre il tag `text` per evitare che
l'evidenziatore di sintassi generi colori casuali su stringhe di log
o percorsi di file.

---

## 6. Header SPDX {#spdx-header}

Ogni file `.md` deve iniziare con:

```html
<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
```

I file con frontmatter YAML posizionano il blocco SPDX immediatamente dopo
il `---` di chiusura.

---

## 7. Checklist di Coerenza Visiva {#checklist}

Prima di sottomettere una PR, verificare:

- [ ] Ogni griglia di card segue §1 (singolo action link).
- [ ] Ogni admonition corrisponde al suo ruolo §2.
- [ ] Nessuna icona `:material-*:` rimane (§3).
- [ ] Gli heading cross-referenziati hanno `{#id}` esplicito (§4).
- [ ] Nessun code fence nudo esiste (§5).
- [ ] L'header SPDX è presente (§6).
- [ ] Il mirror italiano è strutturalmente identico all'inglese.
