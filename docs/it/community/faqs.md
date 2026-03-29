---
icon: lucide/circle-question-mark
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Domande Frequenti

Questa pagina raccoglie le risposte alle domande più frequenti degli utenti di Zenzic. Sfoglia le sezioni
qui sotto o usa la barra di ricerca per trovare ciò di cui hai bisogno.

!!! info "Aiutaci a far crescere questa pagina"

    Hai una domanda a cui non è stata data risposta? [Apri un'issue](https://github.com/PythonWoods/zenzic/issues)
    e la aggiungeremo.

## Generale

**Cos'è Zenzic?**

Zenzic è un linter di documentazione di livello ingegneristico per siti MkDocs e Zensical. Rileva
link interrotti, pagine orfane, stub placeholder, asset mancanti e altro ancora — a livello sorgente,
prima che venga eseguita la build.

**Zenzic è gratuito?**

Sì. Zenzic è Open Source con licenza Apache-2.0. Puoi usarlo, modificarlo e distribuirlo liberamente,
anche in contesti commerciali.

**Quali versioni di Python sono supportate?**

Zenzic richiede Python 3.11 o superiore.

## Installazione e utilizzo

**Come si installa Zenzic?**

Il modo più semplice è usare `uvx` per eseguirlo direttamente senza installazione:

```bash
uvx zenzic check all
```

Oppure installalo nel progetto con `uv add --dev zenzic` (raccomandato) o `pip install zenzic`.

**Devo creare un file `zenzic.toml`?**

No. Zenzic funziona con configurazione zero — i valori predefiniti coprono la maggior parte dei
progetti MkDocs standard. Il file `zenzic.toml` è necessario solo per personalizzare il comportamento,
ad esempio per escludere directory, asset o URL esterni specifici.

**Posso usare Zenzic con un progetto non-MkDocs?**

Attualmente Zenzic supporta MkDocs e Zensical. Il supporto per altri engine è pianificato.
Consulta la guida [Motori](../guides/engines.md) per i dettagli.

## Checks e risultati

**Qual è la differenza tra `zenzic check all` e `zenzic score`?**

`zenzic check all` esegue tutti i controlli e restituisce un risultato pass/fail binario.
`zenzic score` calcola un punteggio di qualità pesato da 0 a 100 con dettaglio per categoria,
utile per il monitoraggio continuo e i badge.

**Cosa significa "orphan page"?**

Una pagina orfana è un file Markdown presente nella directory `docs/` ma assente dalla
navigazione (`nav:`) in `mkdocs.yml`. Le pagine orfane non sono raggiungibili dagli utenti
ma occupano spazio e creano confusione. Zenzic le segnala per tenerti in controllo.

**Il check dei link esterni è lento. Posso disabilitarlo?**

Puoi escludere URL specifici con `excluded_external_urls` in `zenzic.toml`. Per saltare
completamente il controllo dei link esterni usa `zenzic check links --no-external`.

**Zenzic controlla anche i link nelle immagini?**

Sì. Il check dei link analizza tutti i riferimenti Markdown: link testuali, immagini,
link di definizione e anchor interni (se `validate_same_page_anchors: true`).

## CI/CD

**Come integro Zenzic in GitHub Actions?**

```yaml
- name: Lint documentation
  run: uvx zenzic check all --strict
```

Per la configurazione completa con badge dinamici e rilevamento regressioni, consulta la
guida [CI/CD](../ci-cd.md).

**Cosa fa il flag `--strict`?**

In modalità strict, qualsiasi warning diventa un errore. È consigliato nelle pipeline CI
per garantire che nessuna issue passi inosservata.

**Cos'è il Zenzic Shield (exit code 2)?**

Exit code `2` indica che il check dei riferimenti ha rilevato un pattern che assomiglia a
una credenziale (API key, token, password) in un URL o in un testo. Ruota immediatamente
la credenziale se ricevi questo codice.

**Perché Zenzic segnala `DANGLING_REFERENCE` se ho definito il link a fondo pagina?**

La definizione del reference link è probabilmente cancellata silenziosamente da un altro
strumento nella pipeline. `markdownlint --fix` (un hook pre-commit comune) rimuove le
definizioni bare `[id]: url` quando si trovano in certe posizioni — dopo blocchi HTML,
tag `<figure>` o prima del primo heading — senza segnalare quale regola ha scatenato la
rimozione. La riga semplicemente scompare.

**Soluzione:** Usa link inline (`[testo](url)`) invece dei link reference-style
(`[testo][id]` + `[id]: url` a fondo pagina). I link inline sono immuni a questa classe
di interferenze dei linter e sono il formato raccomandato per repository con pipeline di
linting aggressive.
