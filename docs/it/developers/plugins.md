---
icon: lucide/puzzle
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Scrivere Regole Plugin {#writing-plugin-rules}

Zenzic supporta regole di linting esterne scritte in Python. Una regola plugin è
una sottoclasse di `BaseRule` distribuita come un normale pacchetto Python e
scoperta a runtime tramite il gruppo di entry-point `zenzic.rules`.

---

## Il Contratto della Regola

Ogni regola plugin deve soddisfare tre requisiti non negoziabili. Questi vengono
verificati al momento della costruzione del motore — una regola che viola uno
qualsiasi di essi viene rifiutata con `PluginContractError` prima che il primo
file venga scansionato.

### 1. Definita a livello di modulo

La classe deve essere importabile per nome da un modulo. Le classi definite
all'interno di funzioni o closure non possono essere pickled e **verranno
rifiutate**.

```python
# ✓ corretto — importabile come my_rules.NoDraftRule
class NoDraftRule(BaseRule): ...

# ✗ errato — non serializzabile; solleverà PluginContractError al caricamento
def make_rule():
    class NoDraftRule(BaseRule): ...
    return NoDraftRule()
```

### 2. Serializzabile via pickle

L'`AdaptiveRuleEngine` serializza le regole tramite `pickle` prima di
inviarle ai processi worker. Ogni attributo memorizzato su `self` deve essere
serializzabile.

Attributi sicuri: stringhe, numeri, pattern `re.compile()`, dataclass frozen,
oggetti `Path`, tuple di tipi sicuri.

Attributi non sicuri: file handle aperti, connessioni a database, funzioni
lambda, `threading.Lock`, oggetti generator, o qualsiasi oggetto che definisce
`__reduce__` incorrettamente.

```python
# ✓ regex compilata è serializzabile
class NoDraftRule(BaseRule):
    _pattern = re.compile(r"(?i)\bDRAFT\b")   # attributo di classe

# ✓ funziona anche come attributo di istanza impostato in __init__
class NoDraftRule(BaseRule):
    def __init__(self) -> None:
        self._pattern = re.compile(r"(?i)\bDRAFT\b")
```

### 3. Pura e deterministica

`check()` e `check_vsm()` devono:

- **Mai** aprire file, fare richieste di rete, o chiamare sottoprocessi.
- **Sempre** restituire lo stesso output per lo stesso input — nessuna casualità,
  nessuna dipendenza da stato globale mutabile.
- **Non** mutare i propri argomenti (`file_path`, `text`, `vsm`, `anchors_cache`).

!!! warning "Evitare lo stato globale mutabile"
    Una regola che scrive su un contatore globale sembrerà funzionare in
    modalità sequenziale, ma produrrà risultati **non deterministici e
    silenziosamente errati** in modalità parallela.  I processi worker
    ricevono ciascuno una copia pickle indipendente del motore — le mutazioni
    sono locali al worker e vengono scartate al completamento.  Tutto lo
    stato deve essere restituito come oggetti `RuleFinding`.

---

## Esempio minimale

```python
# my_org_rules/rules.py
import re
from pathlib import Path
from zenzic.rules import BaseRule, RuleFinding


class NoInternalHostnameRule(BaseRule):
    """Segnala le occorrenze dell'hostname interno nella documentazione pubblica."""

    _pattern = re.compile(r"internal\.corp\.example\.com", re.IGNORECASE)

    @property
    def rule_id(self) -> str:
        return "MYORG-001"

    def check(self, file_path: Path, text: str) -> list[RuleFinding]:
        findings = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            if self._pattern.search(line):
                findings.append(
                    RuleFinding(
                        file_path=file_path,
                        line_no=lineno,
                        rule_id=self.rule_id,
                        message="L'hostname interno non deve apparire nella documentazione pubblica.",
                        severity="error",
                        matched_line=line,
                    )
                )
        return findings
```

---

## Pacchettizzazione e registrazione

Esponi la regola tramite il gruppo di entry-point `zenzic.rules` nel
`pyproject.toml` del tuo pacchetto:

```toml
[project.entry-points."zenzic.rules"]
no-internal-hostname = "my_org_rules.rules:NoInternalHostnameRule"
```

Il nome dell'entry-point (`no-internal-hostname`) è il **plugin ID** che gli
utenti referenziano in `zenzic.toml` (vedi [Abilitare i plugin](#enabling-plugins)
qui sotto).

Installa il tuo pacchetto insieme a Zenzic:

```bash
uv add my-org-rules            # oppure: pip install my-org-rules
```

Dopo l'installazione, esegui `zenzic plugins list` per confermare che la regola venga
scoperta:

```bash
zenzic plugins list
# Installed plugin rules (2 found)
#   broken-links          Z001       (core)          zenzic.core.rules.VSMBrokenLinkRule
#   no-internal-hostname  MYORG-001  (my-org-rules)  my_org_rules.rules.NoInternalHostnameRule
```

---

## Fast-Track: da zero a plugin in 30 secondi

Usa il comando di scaffolding per generare un pacchetto plugin pronto da modificare:

```bash
zenzic init --plugin plugin-scaffold-demo
```

Struttura generata:

```text
plugin-scaffold-demo/
    pyproject.toml
    README.md
    zenzic.toml
    docs/
        index.md
    src/
        plugin_scaffold_demo/
            __init__.py
            rules.py
```

Lo scaffold include:

- un entry-point `zenzic.rules` pre-configurato in `pyproject.toml`
- un template di classe `BaseRule` a livello modulo in `rules.py`
- una fixture docs minima, cosi `zenzic check all` passa subito

Verifica rapida:

```bash
cd plugin-scaffold-demo
uv pip install -e .
zenzic plugins list
zenzic check all
```

---

## Abilitare i plugin {#enabling-plugins}

Le regole core (registrate sotto `zenzic.rules` da Zenzic stesso) sono sempre
attive. Le regole plugin esterne devono essere esplicitamente abilitate in
`zenzic.toml` sotto la chiave `plugins`:

```toml
# zenzic.toml
[build_context]
engine = "mkdocs"

plugins = ["no-internal-hostname"]
```

Solo i plugin elencati qui verranno caricati. L'installazione di un pacchetto
che registra regole sotto `zenzic.rules` senza elencarlo in `plugins` non ha
effetto — questo è il comportamento intenzionale del **Safe Harbor**: sai sempre
esattamente quali regole sono attive nel tuo progetto.

---

## Regole VSM-aware

Le regole che devono validare i link contro la tabella di routing devono
sovrascrivere `check_vsm` invece di (o in aggiunta a) `check`. Il motore chiama
`check_vsm` quando una VSM e `anchors_cache` sono disponibili:

```python
from collections.abc import Mapping
from zenzic.core.rules import BaseRule, RuleFinding
from zenzic.models.vsm import Route


class NoOrphanLinkRule(BaseRule):
    @property
    def rule_id(self) -> str:
        return "MYORG-002"

    def check(self, file_path, text):
        return []   # nessun controllo autonomo; richiede contesto VSM

    def check_vsm(self, file_path, text, vsm: Mapping[str, Route], anchors_cache):
        # vsm mappa URL canonico → Route; consulta vsm[url].status
        ...
        return []   # restituisce list[Violation]
```

Vedi [`BaseRule`][api-baserule] nella reference API per l'interfaccia completa.

---

## Testare le regole

Usa il test helper `run_rule` per validare una regola con una singola chiamata —
nessuna configurazione dell'engine richiesta:

```python
from zenzic.rules import run_rule
from my_org_rules.rules import NoInternalHostnameRule


def test_hostname_interno_rilevato():
    findings = run_rule(
        NoInternalHostnameRule(),
        "Visita internal.corp.example.com per i dettagli.",
    )
    assert len(findings) == 1
    assert findings[0].rule_id == "MYORG-001"
    assert findings[0].severity == "error"


def test_contenuto_pulito_passa():
    findings = run_rule(NoInternalHostnameRule(), "Tutto contenuto pubblico.")
    assert findings == []
```

`run_rule` crea internamente un `AdaptiveRuleEngine`, esegue la regola e
restituisce la lista dei finding. Accetta un argomento opzionale `file_path`
per l'etichettatura (default: `test.md`).

---

## Isolamento degli errori

Se una regola plugin solleva un'eccezione inaspettata all'interno di `check()`
o `check_vsm()`, il motore la cattura, emette un singolo finding `"error"` con
`rule_id="RULE-ENGINE-ERROR"`, e continua la scansione. Un plugin difettoso non
può interrompere la scansione dell'intero albero della documentazione.

Se una regola plugin fallisce la **validazione pickle anticipata** al momento
del caricamento (cioè non è serializzabile), Zenzic solleva `PluginContractError`
immediatamente e si rifiuta di avviarsi. Correggi la regola prima di eseguire
Zenzic.

---

## Checklist prima della pubblicazione

- [ ] Classe definita a livello di modulo (non all'interno di una funzione o lambda).
- [ ] Tutti gli attributi `self.*` sono serializzabili via pickle.
- [ ] `check()` è pura: nessun I/O, nessun effetto collaterale, stesso output per stesso input.
- [ ] `rule_id` è una stringa stabile e univoca (includi un prefisso org, es. `"MYORG-001"`).
- [ ] Entry-point registrato sotto `zenzic.rules` nel `pyproject.toml`.
- [ ] Plugin ID elencato nel `zenzic.toml` del progetto sotto `plugins`.

!!! abstract "Passaggi Successivi"
     Collega la regola dal codice al flusso Sentinel in produzione:

     1. Registra e abilita il plugin ID nel `zenzic.toml` sotto `plugins`
         (vedi [Abilitare i plugin](#enabling-plugins)).
     2. Valida la regola in semantica pipeline strict:
         `zenzic check all --strict`.
         Per i controlli di run, vedi [Comandi CLI: Flag globali](../usage/commands.md#global-flags).
     3. Se la regola è nav-aware, mappa il comportamento atteso delle Ghost Route rispetto
         al modello VSM:
         [VSM Engine — Esempio D: Ghost Route](../arch/vsm_engine.md#example-d-ghost-route-reachable-without-a-file).

[api-baserule]: ../../reference/api.md
