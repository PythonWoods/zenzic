<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z602 Guide — Advanced Configuration

This is the English guide that has no Italian mirror.
Its absence in `docs/it/` triggers **Z602 I18N_PARITY**.

## i18n Setup

Enable i18n parity checking in `.zenzic.toml`:

```toml
[build_context]
default_locale = "en"
locales        = ["it"]

[i18n]
enabled = true
```

## Parity Rules

Zenzic compares the file structure between the default locale and each
non-default locale. Any file present in the default locale but absent
from a non-default locale emits Z602.
