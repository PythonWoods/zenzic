---
icon: lucide/book-open-text
hide:
  - toc
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Documentazione {#documentation}

Zenzic è un **linter di documentazione CI-first** per qualsiasi progetto basato su Markdown. Analizza i file sorgente grezzi — mai l'HTML generato — e intercetta il degrado della documentazione prima che raggiunga i tuoi utenti.

!!! tip "Zero installazione — eseguilo ora"

    ```bash
    uvx --pre zenzic check all
    ```

    `uvx` scarica ed esegue Zenzic in un ambiente temporaneo. Nessuna installazione richiesta.

---

## Il problema che Zenzic risolve

La documentazione degrada in silenzio. Uno sviluppatore rinomina una pagina e dimentica di aggiornare il nav. Un esempio di codice che funzionava sei mesi fa ora contiene un errore di sintassi. Un'immagine viene eliminata ma il Markdown che la referenzia rimane. Una pagina contrassegnata come «coming soon» non viene mai scritta.

Nessuno di questi è un errore grave che rompe la build. Sono **fallimenti silenziosi** — si accumulano inosservati finché un utente non segue un link morto, copia del codice non funzionante, o atterra su una pagina che dice «TODO». A quel punto il danno è fatto.

Poiché Zenzic analizza file Markdown sorgente grezzi — mai l'HTML generato — è **agnostico rispetto al generatore e indipendente dalla versione**. Funziona in modo identico con MkDocs, Zensical o qualsiasi generatore futuro. Aggiornare il motore di documentazione non rompe il quality gate.

Oltre alla pura reportistica, Zenzic fornisce **utility di autofix** (come `zenzic clean assets`) per pulire automaticamente il repository dai file non utilizzati, rendendolo un partecipante proattivo alla salute del tuo progetto.

> Il tuo generatore costruisce la documentazione. Zenzic ne garantisce la qualità.

---

## Cosa trovi in questa documentazione

<div class="grid cards" markdown>

- :lucide-play: &nbsp; **Guida Utente**

    Tutto ciò che serve per installare, configurare e integrare Zenzic nel tuo workflow CI/CD.

    [:octicons-arrow-right-24: Esplora la Guida](../usage/index.md)

- :lucide-book: &nbsp; **Guida Sviluppatore**

    Architettura interna, design della pipeline e documentazione API auto-generata.

    [:octicons-arrow-right-24: Architettura e API](../architecture.md)

- :lucide-users: &nbsp; **Comunità**

    Segnala problemi, richiedi funzionalità, migliora i docs o apri una pull request.

    [:octicons-arrow-right-24: Partecipa](../community/index.md)

</div>

---

## Costruito con fiducia

Zenzic impone un **gate di branch-coverage ≥ 80 %** tramite `pytest-cov`, affiancato da mutation testing (mutmut) che verifica l'efficacia dei test oltre la semplice copertura di riga. Ogni controllo, ogni caso limite nel parser a macchina a stati e ogni percorso di codice asincrono nel validatore di link ha un test dedicato. `ruff` garantisce la qualità del codice nell'intero codebase.

Un linter che individua i problemi della tua documentazione deve essere esso stesso corretto. Questi numeri non sono una metrica di vanità — sono ciò che ti permette di fidarti dell'output di Zenzic nelle pipeline automatizzate.
