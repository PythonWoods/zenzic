---
icon: lucide/plug
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Scrivere un Adapter

Questa pagina descrive come scrivere un adapter Zenzic per un motore di documentazione di
terze parti. Per la guida completa in inglese, consulta
[Writing an Adapter](../../developers/writing-an-adapter.md).

---

## Il protocollo `BaseAdapter`

Ogni adapter deve implementare il protocollo `BaseAdapter`
(`src/zenzic/core/adapters/_base.py`). Le cinque funzioni richieste:

```python
class MyEngineAdapter:
    def nav_paths(self) -> list[str]:
        """Restituisce tutti i percorsi file dichiarati nella nav, relativi a docs_dir."""
        ...

    def locale_dirs(self) -> list[str]:
        """Restituisce i nomi delle directory locale non-default (es. ['it', 'fr'])."""
        ...

    def asset_fallback(self, path: str, locale: str) -> str:
        """Risolve un path asset relativo a una pagina locale nel path canonico."""
        ...

    def has_engine_config(self) -> bool:
        """Restituisce True quando è stato trovato e caricato un file di config del motore."""
        ...

    @classmethod
    def from_repo(cls, context, docs_root, repo_root) -> "MyEngineAdapter":
        """Fabbrica che carica la configurazione dalla root del repository."""
        ...
```

---

## Registrazione via entry-point

Registra il tuo adapter nel `pyproject.toml` del tuo pacchetto Python:

```toml
[project.entry-points."zenzic.adapters"]
myengine = "mypackage.adapter:MyEngineAdapter"
```

Dopo `uv pip install mypackage` (o `pip install mypackage`), il tuo adapter è disponibile come:

```bash
zenzic check all --engine myengine
```

---

## Regole custom con adapter personalizzati

Le `[[custom_rules]]` dichiarate in `zenzic.toml` si attivano identicamente con qualsiasi adapter
— incluso il tuo. Non è richiesta alcuna integrazione speciale.

---

Per la documentazione completa del protocollo, gli esempi di test e la checklist di conformità,
consulta la guida inglese: [Writing an Adapter](../../developers/writing-an-adapter.md).
