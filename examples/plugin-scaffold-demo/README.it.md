<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# plugin-scaffold-demo

Scaffold per plugin generato da `zenzic init --plugin plugin-scaffold-demo`.
Questo è l'esempio di riferimento per scrivere plugin di regole custom per Zenzic.

## Cosa dimostra

| Funzionalità | Dove |
| --- | --- |
| Import SDK pubblico | `from zenzic.rules import BaseRule, RuleFinding` |
| Helper di test `run_rule()` | `tests/test_rules.py` |
| Registrazione entry-point | `pyproject.toml` `[project.entry-points]` |

## Avvio rapido

```bash
uv sync
uv pip install -e .
zenzic plugins list
```

## Testare la regola

```bash
pytest tests/test_rules.py -v
```

Il test usa `run_rule()` — un helper che crea un file Markdown virtuale, esegue
il motore delle regole e restituisce i risultati. Nessuna configurazione richiesta.

## Attivare in un progetto

Aggiungi a `zenzic.toml`:

```toml
plugins = ["plugin-scaffold-demo"]
```
