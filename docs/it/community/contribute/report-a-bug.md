---
icon: lucide/bug
tags:
  - Community
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Segnalazioni di Bug

Zenzic è un progetto attivamente mantenuto che cerchiamo costantemente di migliorare.
Con un progetto di questa dimensione e complessità, possono verificarsi dei bug. Se pensi
di aver scoperto un bug, puoi aiutarci inviando un'issue nel nostro [issue tracker] pubblico,
seguendo questa guida.

  [issue tracker]: https://github.com/PythonWoods/zenzic/issues

## Prima di creare un'issue

Puntiamo a mantenere basso il numero di issue aperte affrontando i bug tempestivamente.
Prima di inviare una nuova issue, completa i seguenti passaggi.

### Aggiorna all'ultima versione

È probabile che il bug che hai scoperto sia già stato corretto in una versione successiva.
Prima di segnalare un'issue, assicurati di utilizzare l'[ultima versione] di Zenzic.

!!! warning "I fix dei bug non vengono backportati"

    Verranno risolti solo i bug che si verificano nell'ultima versione di Zenzic.

  [ultima versione]: https://github.com/PythonWoods/zenzic/releases

### Cerca soluzioni

Prima di creare una segnalazione di bug, fai una ricerca:

1. [Cerca nella documentazione][Cerca nella documentazione] e cerca sezioni
   correlate al tuo problema.

2. [Cerca nel nostro issue tracker][issue tracker], poiché un altro utente potrebbe
   aver già segnalato lo stesso problema.

__Tieni traccia di tutti i <u>termini di ricerca</u> e i <u>link pertinenti</u>:
ti serviranno nella segnalazione del bug.__

  [Cerca nella documentazione]: ?q=

---

## Template dell'issue

Il nostro template per le issue è composto dalle seguenti sezioni:

- [Titolo]
- [Contesto] <small>opzionale</small>
- [Descrizione del bug]
- [Link correlati]
- [Riproduzione]
- [Passi per riprodurre]
- [Checklist]

  [Titolo]: #titolo
  [Contesto]: #contesto
  [Descrizione del bug]: #descrizione-del-bug
  [Link correlati]: #link-correlati
  [Riproduzione]: #riproduzione
  [Passi per riprodurre]: #passi-per-riprodurre
  [Checklist]: #checklist

### Titolo

Un buon titolo è breve e descrittivo — un riassunto esecutivo in una frase dell'issue.

| <!-- --> | Esempio |
| -------- | ------- |
| :material-check:{ style="color: #4DB6AC" } __Chiaro__ | `validate_same_page_anchors` genera falso positivo su heading auto-generati |
| :material-close:{ style="color: #EF5350" } __Vago__ | La validazione degli anchor non funziona |
| :material-close:{ style="color: #EF5350" } __Inutile__ | Aiuto |

### Contesto <small>opzionale</small> { #contesto }

Fornisci contesto aggiuntivo per aiutarci a capire cosa stavi cercando di fare. Non
descrivere qui il bug.

### Descrizione del bug

Fornisci un riassunto chiaro, focalizzato e conciso del bug. Segui questi principi:

- __Spiega il <u>cosa</u>, non il <u>come</u>__ — concentrati sul problema
    e sul suo impatto, non su come riprodurlo.

- __Sii breve e conciso__ — una o due frasi è l'ideale.

- __Un bug alla volta__ — crea issue separate per bug non correlati.

### Link correlati

Condividi link a tutte le sezioni della documentazione rilevanti per il bug, oltre a
qualsiasi issue correlata trovata durante la ricerca.

### Riproduzione

Una riproduzione minimale è il cuore di ogni buona segnalazione di bug. Ci permette di
ricreare istantaneamente le condizioni necessarie per trovare la causa principale.

Dopo aver creato la riproduzione, allega il file `.zip` direttamente all'issue.

!!! warning "Non condividere link a repository."

    Allega una riproduzione `.zip` invece di linkare a un repository.

### Passi per riprodurre

Elenca i passaggi specifici da seguire quando esegui la riproduzione per osservare il
bug. Mantieni i passaggi concisi e completi.

### Checklist

Grazie per aver seguito la guida e aver creato una segnalazione di bug di alta qualità.
La checklist assicura che tu abbia letto questa guida e ci abbia fornito tutto il
necessario per aiutarti.

__Pensiamo a tutto noi.__
