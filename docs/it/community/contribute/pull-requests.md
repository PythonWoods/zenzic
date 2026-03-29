---
icon: lucide/git-pull-request-create
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Pull Request

Il processo e i requisiti che descriviamo di seguito fungono da importanti linee guida
essenziali per la gestione di un progetto Open Source e ci aiutano a prevenire sprechi
di lavoro e a garantire l'integrità del codebase.

## Setup per lo sviluppo locale

Clona il repository e installa Zenzic in modalità editabile in modo che le
modifiche locali si riflettano immediatamente senza reinstallare.

=== ":simple-astral: uv (raccomandato)"

    ```bash
    git clone https://github.com/PythonWoods/zenzic.git
    cd zenzic
    uv venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    uv pip install -e .
    ```

    [`uv`](https://docs.astral.sh/uv/) risolve le dipendenze molto più velocemente di pip e produce un
    ambiente riproducibile tramite `uv.lock`. Preferito per tutto il lavoro di
    sviluppo.

=== ":simple-pypi: pip"

    ```bash
    git clone https://github.com/PythonWoods/zenzic.git
    cd zenzic
    python -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -e .
    ```

Con un'installazione editabile, il binario `zenzic` nel tuo `PATH` esegue
sempre il sorgente su cui stai lavorando. Puoi validare la documentazione del
repository in qualsiasi momento:

```bash
zenzic check all            # tutti e sei i controlli
zenzic check references     # include la valutazione delle [[custom_rules]]
pytest                      # suite di test completa
```

!!! note "Utenti finali vs contributori"

    **Gli utenti finali** eseguono `uvx zenzic check all` — nessun clone,
    nessuna installazione, zero attrito. È il punto di ingresso documentato
    nelle guide rivolte agli utenti.

    **I contributori** clonano il repo e installano in modalità editabile come
    mostrato sopra. Il binario `zenzic` nel virtualenv attivato è quello da
    usare — non `uvx`, che scaricherebbe la versione PyPI pubblicata.

## Prima di iniziare

Prima di iniziare a lavorare su una pull request (PR), ti chiediamo di aprire un'issue
e discuterla con noi, così sappiamo su cosa stai lavorando e possiamo concordare
l'approccio da adottare. Questo ti evita di dedicare tempo a una funzionalità che
potrebbe non allinearsi con gli obiettivi del progetto. Nella tua PR farai quindi
riferimento al numero dell'issue per collegare la nostra discussione.

## Stile e linting

È importante che le tue modifiche producano commit puliti che possano essere revisionati
rapidamente e senza distrazioni causate da diff spuri. Il progetto utilizza i seguenti
strumenti di stile e linting:

| Linguaggio | Strumento | Note                              |
| :--------- | :-------- | :-------------------------------- |
| Python     | [ruff]    | Linting e formattazione del codice |
| Python     | [mypy]    | Type checking                     |

  [ruff]: https://docs.astral.sh/ruff/
  [mypy]: https://www.mypy-lang.org/

Utilizziamo anche un file [.editorconfig] che configura gli editor compatibili per
comportarsi in modo coerente per operazioni come la rimozione degli spazi finali o
l'applicazione degli stili di indentazione.

  [.editorconfig]: https://editorconfig.org/

## Commit verificati

Per garantire l'integrità del nostro progetto, richiediamo [commit verificati]
crittograficamente firmati. Segui le istruzioni su GitHub per utilizzare keypair
[gpg], [ssh] o [s/mime].

  [commit verificati]: https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification
  [gpg]: https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification#gpg-commit-signature-verification
  [ssh]: https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification#ssh-commit-signature-verification
  [s/mime]: https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification#smime-commit-signature-verification

## Developer Certificate of Origin

Per garantire l'integrità legale del nostro progetto, richiediamo a tutti i
contributori di _firmare_ i propri commit, accettando così il Developer Certificate
of Origin. Questo certifica che hai il diritto di inviare il codice sotto la licenza
del progetto.

Aggiungi una riga `Signed-off-by` a ogni commit usando il flag `-s`:

```bash
git commit -s -m "<tipo>: <sommario> (#<numero issue>)"
```

## Uso dell'Intelligenza Artificiale Generativa

La programmazione assistita da AI può essere utile, ma l'inclusione acritica di codice
generato da AI può causare danni. Firmando i commit, attesti di aver scritto tutto il
codice tu stesso o di aver revisionato e compreso appieno qualsiasi codice generato.

I contributi di codice che contengono codice generato da AI che non sei in grado di
spiegarci completamente verranno rifiutati.

## Standard per i messaggi di commit

Seguiamo la specifica [Conventional Commits]. Ogni messaggio di commit deve seguire
questa struttura:

```text
<tipo>: <descrizione sommaria> (#<numero issue>)

Signed-off-by: ...
```

  [Conventional Commits]: https://www.conventionalcommits.org/

<figure markdown>

| Tipo          | Descrizione                                         |
| :------------ | :-------------------------------------------------- |
| `feat`        | Implementa una nuova funzionalità                   |
| `fix`         | Corregge un bug                                     |
| `perf`        | Migliora le prestazioni                             |
| `refactor`    | Migliora il codice senza cambiarne il comportamento |
| `build`       | Modifica il sistema di build o CI                   |
| `docs`        | Aggiunge o migliora la documentazione               |
| `style`       | Apporta solo modifiche stilistiche (es. whitespace) |
| `test`        | Aggiunge o migliora i test                          |
| `chore`       | Aggiorna il processo di build, prepara release, ecc.|

  <figcaption>Tipi di commit accettati</figcaption>
</figure>
