---
icon: lucide/play
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Per iniziare

Zenzic legge direttamente dal filesystem e funziona con qualsiasi progetto basato su Markdown.
Usalo in locale, come hook di pre-commit, nelle pipeline CI o per audit una-tantum.

## Esempi canonici

Il repository include fixture mantenuti e allineati ai contratti documentati:

- `examples/mkdocs-basic/` — baseline MkDocs 1.6 (nav annidata, link nav esterno,
  tag YAML tolleranti come `!ENV` e `!relative`).
- `examples/i18n-standard/` — gold standard bilingue in strict mode.
- `examples/zensical-basic/` — baseline Zensical v0.0.31+ (`[project].nav`).
- `examples/broken-docs/` — errori intenzionali (exit 1).
- `examples/security_lab/` — fixture sicurezza (Shield exit 2).

!!! tip "Vuoi eseguirlo subito?"

    ```bash
    uvx zenzic check all
    ```

    Nessuna installazione richiesta. `uvx` scarica ed esegue Zenzic in un ambiente temporaneo.

---

## Installazione

### Temporanea — nessuna installazione richiesta

=== ":simple-astral: uv"

    ```bash
    uvx zenzic check all
    ```

    `uvx` risolve ed esegue Zenzic da PyPI in un ambiente temporaneo. Nulla viene installato sul
    sistema. La scelta giusta per audit una-tantum, `git hooks` e job CI dove si vuole evitare di
    fissare una dipendenza dev.

=== ":simple-pypi: pip"

    ```bash
    pip install zenzic
    zenzic check all
    ```

    Installazione standard nell'ambiente attivo. Usa all'interno di un virtual environment per
    mantenere pulito il Python di sistema.

### Strumento globale — disponibile in ogni progetto

=== ":simple-astral: uv"

    ```bash
    uv tool install zenzic
    zenzic check all
    ```

    Installa una volta, usa in qualsiasi progetto. Il binario è disponibile nel `PATH` senza
    attivare un virtual environment.

=== ":simple-pypi: pip"

    ```bash
    python -m venv ~/.local/zenzic-env
    source ~/.local/zenzic-env/bin/activate   # Windows: .venv\Scripts\activate
    pip install zenzic
    ```

    Installa in un virtual environment dedicato, poi aggiungi la directory `bin/` al `PATH`.

### Dipendenza dev del progetto — versione fissata per progetto

=== ":simple-astral: uv"

    ```bash
    uv add --dev zenzic
    uv run zenzic check all
    ```

    Installa Zenzic nel virtual environment del progetto e fissa la versione in `uv.lock`.
    La scelta giusta per progetti di team e pipeline CI che installano le dipendenze del progetto
    prima di eseguire i controlli.

=== ":simple-pypi: pip"

    ```bash
    python -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install zenzic
    zenzic check all
    ```

    Pattern standard da dipendenza dev con virtual environment locale al progetto.

### L'extra `zenzic[docs]` — per il rendering, non per il linting

Zenzic legge `mkdocs.yml` come YAML semplice tramite il proprio `_PermissiveYamlLoader`
(una sottoclasse di `yaml.SafeLoader` che ignora silenziosamente i tag specifici degli
engine come `!ENV`). **Non importa `mkdocs`, `mkdocs-material` né alcun pacchetto plugin**
per analizzare la configurazione. PyYAML è una dipendenza core — nessun extra necessario.

L'extra `[docs]` (`mkdocs-material`, `mkdocstrings`, `mkdocs-minify-plugin`,
`mkdocs-static-i18n`) è lo stack di build usato per **renderizzare il sito di
documentazione di Zenzic stesso**. È una dipendenza per i contributori, non per gli utenti:

- **Fare il lint del tuo progetto MkDocs:** installa solo `zenzic`.
- **Buildare il sito di documentazione di Zenzic localmente:** installa `zenzic[docs]`.

```bash
# Fare il lint di qualsiasi progetto MkDocs — nessun extra necessario
uvx zenzic check all

# Buildare il sito docs di Zenzic (solo workflow contributori)
uv add --dev "zenzic[docs]"
mkdocs serve
```

!!! note "Adapter di terze parti"
    Gli adapter di terze parti (es. un ipotetico `zenzic-hugo-adapter`) sono pacchetti
    installabili separati — non extra di `zenzic` stesso. Nessun extra è richiesto per
    `VanillaAdapter` (cartelle Markdown semplici).

---

## Workflow Init → Config → Check

Il workflow standard per adottare Zenzic in un progetto:

### 1. Init — scaffolding del file di configurazione

Crea un `zenzic.toml` con un singolo comando. Zenzic rileva automaticamente il motore di
documentazione e preimposta `[build_context]` di conseguenza:

```bash
zenzic init
```

**Esempio di output quando è presente `mkdocs.yml`:**

```text
Created zenzic.toml
  Engine pre-set to mkdocs (detected from mkdocs.yml).

Edit the file to enable rules, adjust directories, or set a quality threshold.
Run zenzic check all to validate your documentation.
```

Se non viene rilevato alcun file di configurazione engine, `zenzic init` produce uno scaffold
engine-agnostico (modalità Vanilla). In entrambi i casi, tutte le impostazioni sono commentate
per default — decommenta e modifica solo i campi di cui hai bisogno.

Eseguendo Zenzic senza un `zenzic.toml`, Zenzic utilizza i valori predefiniti e mostra un
pannello Helpful Hint che suggerisce `zenzic init`:

```text
╭─ 💡 Zenzic Tip ─────────────────────────────────────────────────────╮
│ Using built-in defaults — no zenzic.toml found.                      │
│ Run zenzic init to create a project configuration file.              │
│ Customise docs directory, excluded paths, engine adapter, and rules. │
╰──────────────────────────────────────────────────────────────────────╯
```

### 2. Config — personalizza per il tuo progetto

Modifica il `zenzic.toml` generato per silenziare il rumore e impostare soglie appropriate:

```toml
# zenzic.toml — nella root del repository
excluded_assets = [
    "assets/favicon.svg",      # referenziato da mkdocs.yml, non da nessuna pagina .md
    "assets/social-preview.png",
]
placeholder_max_words = 30     # le pagine di reference tecnico sono intenzionalmente brevi
fail_under = 70                # stabilisce un quality floor iniziale
```

Consulta la [Guida alla Configurazione](../configuration/index.md) per l'elenco completo dei campi.

### 3. Check — esegui in modo continuativo

Con il baseline stabilito, esegui Zenzic su ogni commit e pull request:

```bash
# Hook pre-commit o step CI
# --strict: valida URL esterni + tratta i warning come errori
zenzic check all --strict

# Salva il baseline (punto di riferimento) qualità sul branch main
zenzic score --save

# Blocca le PR che regrediscono il baseline di più di 5 punti
zenzic diff --threshold 5
```

---

## Modalità engine

Zenzic opera in una di due modalità a seconda che riesca a trovare un file di configurazione
del motore di build:

### Modalità Engine-aware

Quando `mkdocs.yml` (MkDocs/Zensical) o `zensical.toml` (Zensical) è presente nella root del
repository, Zenzic carica l'**adapter** corrispondente che fornisce:

- **Consapevolezza della nav** — il controllo orfani sa la differenza tra "non nella nav" e "non
  dovrebbe essere nella nav" (ad esempio i file di locale i18n).
- **Fallback i18n** — i link cross-locale vengono risolti correttamente invece di essere
  segnalati come non validi.
- **Soppressione directory locale** — i file sotto `docs/it/`, `docs/fr/`, ecc. non vengono
  segnalati come orfani.

### Modalità Vanilla

Quando non viene trovata alcuna configurazione del motore di build, Zenzic ricade su
`VanillaAdapter`. In questa modalità:

- **Il controllo orfani viene saltato.** Senza una dichiarazione di nav, ogni file sembrerebbe
  un orfano.
- **Tutti gli altri controlli vengono eseguiti normalmente** — link, snippet, placeholder, asset
  e riferimenti.

La modalità Vanilla è la scelta giusta per wiki Markdown semplici, repository GitHub-wiki o
qualsiasi progetto dove la navigazione è implicita.

!!! tip "Forza una modalità specifica"
    Usa `--engine` per sovrascrivere l'adapter rilevato per una singola esecuzione:

    ```bash
    zenzic check all --engine vanilla    # salta il controllo orfani
    zenzic check all --engine mkdocs     # forza l'adapter MkDocs
    ```

---

**Prossimi passi:**

- [Riferimento comandi CLI](commands.md) — ogni comando, flag e codice di uscita
- [Funzionalità avanzate](advanced.md) — integrità dei riferimenti, Shield, utilizzo programmatico
- [Integrazione CI/CD](../ci-cd.md) — GitHub Actions, pre-commit hook, gestione del baseline
