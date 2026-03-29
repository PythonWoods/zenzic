---
icon: lucide/hand-platter
tags:
  - Community
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Richieste di Modifica

Zenzic è uno strumento potente per il linting della documentazione. Miriamo a supportare
un'ampia gamma di casi d'uso e le richieste di modifica sono un meccanismo essenziale per
garantire che il software soddisfi le esigenze della nostra community.

!!! warning "Come gestiamo le richieste di modifica"

    Diamo grande valore a ogni idea o contributo della nostra community e ti chiediamo
    gentilmente di leggere le seguenti linee guida prima di inviare la tua richiesta nel
    nostro [issue tracker] pubblico. Prima di inviare una nuova idea, leggi
    [come gestiamo le richieste di modifica].

  [issue tracker]: https://github.com/PythonWoods/zenzic/issues

## Prima di creare un'issue

Prima di investire tempo nella compilazione di una richiesta di modifica, rispondi alle
seguenti domande preliminari per valutare se la tua idea è adatta a Zenzic.

### Non è un bug, è una funzionalità

Le richieste di modifica servono per suggerire piccole modifiche, proporre idee per nuove
funzionalità o fornire input sulla direzione del progetto. **Non** sono destinate alla
segnalazione di bug — consulta la nostra [guida alla segnalazione di bug] per quello.

  [guida alla segnalazione di bug]: report-a-bug.md

### Cerca fonti di ispirazione

Se hai visto la tua idea implementata in un altro strumento, raccogli informazioni
sufficienti sulla sua implementazione prima di inviarla, poiché questo ci aiuterà a
valutarne la compatibilità più rapidamente.

**Tieni traccia di tutti i <u>termini di ricerca</u> e i <u>link pertinenti</u>, ti
serviranno nella richiesta di modifica.**

## Template dell'issue

Il nostro template per le richieste di modifica è composto dalle seguenti sezioni:

- [Titolo]
- [Contesto] <small>opzionale</small>
- [Descrizione]
- [Link correlati]
- [Casi d'uso]
- [Elementi visivi] <small>opzionale</small>
- [Checklist]

  [Titolo]: #titolo
  [Contesto]: #contesto
  [Descrizione]: #descrizione
  [Link correlati]: #link-correlati
  [Casi d'uso]: #casi-duso
  [Elementi visivi]: #elementi-visivi
  [Checklist]: #checklist

### Titolo

Un buon titolo è breve e descrittivo — un riassunto esecutivo in una frase dell'idea,
così che l'impatto e il beneficio potenziale possano essere dedotti a colpo d'occhio.

### Contesto <small>opzionale</small> { #contesto }

Fornisci contesto aggiuntivo per aiutarci a capire cosa stai cercando di ottenere.
Non descrivere qui la richiesta di modifica.

> **Perché potrebbe essere utile**: alcune idee potrebbero riguardare solo impostazioni
> specifiche o casi limite. Il contesto ci aiuta a stabilire le priorità con maggiore
> precisione.

### Descrizione

Fornisci una descrizione dettagliata e precisa della tua idea. Spiega perché è
rilevante specificamente per Zenzic.

- **Spiega il <u>cosa</u>, non il <u>perché</u>** — concentrati nel descrivere
    precisamente la modifica proposta. I benefici appartengono ai [Casi d'uso].

- **Sii breve** — vai dritto al punto.

- **Un'idea alla volta** — apri richieste di modifica separate per idee non correlate.

### Link correlati

Fornisci link pertinenti a issue o sezioni della documentazione correlate alla tua
richiesta di modifica, incluse eventuali discussioni precedenti nella community.

### Casi d'uso

Spiega come la tua richiesta di modifica funzionerebbe dalla prospettiva di un autore
e di un utente — qual è l'impatto atteso, chi ne beneficerà e potrebbe potenzialmente
interrompere funzionalità esistenti?

### Elementi visivi <small>opzionale</small> { #elementi-visivi }

Se hai schizzi, screenshot, mockup o esempi da altri strumenti, condividili qui.
Puoi trascinare e rilasciare file nell'area di testo o includere link.

### Checklist

Grazie per aver seguito la guida e aver creato una richiesta di modifica di alta
qualità. La checklist assicura che tu abbia letto questa guida e ci abbia fornito
tutto il necessario per esaminare la tua idea.

**Pensiamo a tutto noi.**

---

## Come gestiamo le richieste di modifica

Le richieste di modifica vengono inviate come issue nel nostro [issue tracker] pubblico.
Ecco come le gestiamo:

1. Leggiamo e esaminiamo la richiesta per comprendere l'idea.
2. Potremmo lasciare commenti per chiarire l'intento o suggerire alternative.
3. Se l'idea è fuori ambito, chiuderemo la richiesta spiegandone il motivo.
4. Se l'idea si allinea con la visione del progetto, la sposteremo nel backlog.
5. Altrimenti, chiudiamo la richiesta per mantenere l'issue tracker focalizzato sui bug.

## Richieste rifiutate

**La tua richiesta di modifica è stata rifiutata? Ce ne dispiace.** Capiamo che possa
essere frustrante, ma come maintainer dobbiamo sempre considerare le esigenze dell'intera
community.

I seguenti principi (in nessun ordine particolare) costituiscono la base delle nostre
decisioni:

- [ ] Allineamento con la visione e gli obiettivi del progetto
- [ ] Compatibilità con le funzionalità esistenti
- [ ] Sforzo di implementazione e manutenzione
- [ ] Utilità per la maggioranza degli utenti
- [ ] Semplicità e facilità d'uso

Se non sei sicuro del motivo per cui la tua richiesta di modifica è stata rifiutata,
non esitare a chiedere chiarimenti.
