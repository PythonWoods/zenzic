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
(`src/zenzic/core/adapters/_base.py`). I sette metodi richiesti:

| Metodo | Domanda |
|---|---|
| `is_locale_dir(part)` | Questa directory è una locale non-default? |
| `resolve_asset(missing_abs, docs_root)` | Esiste un fallback default-locale per questo asset mancante? |
| `resolve_anchor(resolved_file, anchor, anchors_cache, docs_root)` | Questo anchor miss deve essere soppresso perché l'ancora esiste nel file default-locale equivalente? |
| `is_shadow_of_nav_page(rel, nav_paths)` | Questo file è il mirror locale di una pagina nella nav? |
| `get_ignored_patterns()` | Quali glob di filename deve saltare il controllo orfani? |
| `get_nav_paths()` | Quali percorsi `.md` sono dichiarati nella nav di questo motore? |
| `has_engine_config()` | È stato trovato un file di config del motore? (Controlla l'attivazione del controllo orfani.) |

```python
from pathlib import Path
from typing import Any


class MyEngineAdapter:
    def __init__(self, config: dict[str, Any], docs_root: Path) -> None:
        self._config = config
        self._docs_root = docs_root

    def is_locale_dir(self, part: str) -> bool:
        return part in self._config.get("locales", [])

    def resolve_asset(self, missing_abs: Path, docs_root: Path) -> Path | None:
        return None  # nessun fallback i18n

    def resolve_anchor(
        self, resolved_file: Path, anchor: str,
        anchors_cache: dict[Path, set[str]], docs_root: Path,
    ) -> bool:
        return False  # nessun fallback i18n per le ancore

    def is_shadow_of_nav_page(self, rel: Path, nav_paths: frozenset[str]) -> bool:
        if not rel.parts or not self.is_locale_dir(rel.parts[0]):
            return False
        return Path(*rel.parts[1:]).as_posix() in nav_paths

    def get_ignored_patterns(self) -> set[str]:
        return set()

    def get_nav_paths(self) -> frozenset[str]:
        paths = {e for e in self._config.get("nav", [])
                 if isinstance(e, str) and e.endswith(".md")}
        return frozenset(p.lstrip("/") for p in paths)

    def has_engine_config(self) -> bool:
        return bool(self._config)

    @classmethod
    def from_repo(cls, context: Any, docs_root: Path, repo_root: Path) -> "MyEngineAdapter":
        """Carica la configurazione dalla root del repository."""
        import tomllib
        config_path = repo_root / "myengine.toml"
        config: dict[str, Any] = {}
        if config_path.exists():
            with config_path.open("rb") as f:
                config = tomllib.load(f)
        return cls(config, docs_root)
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

!!! abstract "Passaggi Successivi"
     Collega il lavoro sull'adapter alla verità operativa del progetto:

     1. Registra l'identità engine in configurazione tramite `[build_context] engine`
         (vedi [Adapter e Configurazione del Motore](../configuration/adapters-config.md)).
     2. Valida il comportamento adapter in policy Sentinel strict:
         `zenzic check all --engine myengine --strict`.
         Per i controlli di run, vedi [Comandi CLI: Flag globali](../usage/commands.md#flag-globali).
     3. Se il tuo engine genera route locali sintetiche, mappa esplicitamente le Ghost Route
        rispetto al riferimento VSM:
         [VSM Engine — Esempio D: Ghost Route](../arch/vsm_engine.md#esempio-d-ghost-route-raggiungibile-senza-file).

---

Per la documentazione completa del protocollo, gli esempi di test e la checklist di conformità,
consulta la guida inglese: [Writing an Adapter](../../developers/writing-an-adapter.md).
