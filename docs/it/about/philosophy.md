---
icon: lucide/lightbulb
---

# Il Manifesto di Zenzic {#philosophy}

## La Certezza Matematica della Qualità

La documentazione è il veicolo definitivo della verità tecnica. Eppure, viene spesso trattata come codice di seconda classe, assoggettata a fragili script regex o controlli link incompleti.

In Zenzic, crediamo che lo stato di salute della documentazione debba essere misurabile, deterministico e rigorosamente garantito. Immaginiamo un mondo in cui un link interrotto, un'immagine mancante o una credenziale esposta all'interno di un file Markdown vengano intercettati con la stessa ineluttabile certezza matematica di un errore di sintassi nel codice sorgente.

### Il Paradigma Agnostico

Technical writer e sviluppatori migrano continuamente tra vari framework — da MkDocs a Zensical,
da Hugo (Go) a Docusaurus (Node.js), o tra sistemi di documentazione di qualsiasi tipo. Strumenti
di garanzia della qualità non dovrebbero diventare zavorra obsoleta durante questi passaggi.

La visione di Zenzic è radicata in un **costrutto rigorosamente engine-agnostic**. Separando l'I/O
dalla logica, trattiamo il Markdown grezzo come l'unica e vera fonte di verità. Non ci interessa
come esegui il rendering del tuo HTML né in quale linguaggio è scritto il tuo generatore di siti;
ci interessa l'integrità strutturale del tuo documento sorgente.

Zenzic è uno strumento Python — ma la sua portata attraversa i confini dell'ecosistema. Il sistema
di adapter a entry-point consente di validare documentazione MkDocs (Python), Zensical (Python),
Hugo (Go), Docusaurus (Node.js) o Jekyll (Ruby) con lo stesso strumento, gli stessi controlli, lo
stesso punteggio deterministico. Questo paradigma garantisce che Zenzic rimanga il quality-gate
definitivo della tua pipeline di deployment, indipendentemente dal generatore di siti che adotterai
domani.

### Safe Harbor e resilienza a MkDocs 2.0

Il ruolo di Zenzic e essere il punto stabile quando il framework cambia. Se il futuro di
MkDocs 2.0 introduce rotture incompatibili, i progetti MkDocs 1.x non devono perdere il
proprio quality gate.

Per questo Zenzic mantiene tre garanzie operative:

- continua a validare `mkdocs.yml` come contratto sorgente, senza dipendere dal binario;
- non esegue plugin e non richiede il runtime del motore per produrre findings;
- tratta in modo tollerante chiavi e tag YAML sconosciuti, preservando la continuita
 della validazione durante le transizioni.

In sintesi: puoi rimandare una migrazione senza rimandare la qualita.

### La Sentinella Silenziosa

Un linter vale l'accuratezza con cui evita i falsi positivi. Quando gli strumenti sollevano allarmi ingiustificati, gli sviluppatori imparano a ignorarli.

Il nostro DNA architetturale — costruito interamente su funzioni pure deterministiche e algoritmi multi-pass in memoria — è stato progettato esattamente per sradicare alla radice la piaga dei falsi positivi. La vision di Zenzic è quella di agire come una **sentinella priva di attriti**: totalmente silenziosa quando i tuoi documenti sono impeccabili, e chirurgicamente precisa e irriducibile quando non lo sono.

Dal risolvere i complessi forward reference fino a proteggere il tuo ecosistema con lo `Shield` nativo contro le credenziali esposte, Zenzic trasforma il deploy della documentazione. Non è un salto nel buio. È una certezza calcolata

---

*Zenzic è un progetto orgogliosamente sviluppato e mantenuto da PythonWoods, un'organizzazione dedicata alla creazione di strumenti solidi e resilienti per l'ecosistema Python.*
