# Avvio rapido

Questo documento è la traduzione IT dell'esempio Z602 I18N_PARITY.
Contiene tre sezioni. La sezione "Configurazione avanzata" presente
nel documento EN è intenzionalmente assente — Zenzic emette Z602 I18N_PARITY.

## Installazione

Installa Zenzic tramite pip o uv:

```bash
pip install zenzic
# oppure
uv add zenzic
```

## Utilizzo di base

Esegui il controllo completo dalla root del progetto:

```bash
zenzic check all
```

## Configurazione

Crea `zenzic.toml` nella root del progetto. Campi minimi richiesti:

```toml
docs_dir = "docs"

[build_context]
engine = "standalone"
```

<!-- Z602: "Configurazione avanzata" / "Advanced Configuration" absent from this locale. -->
