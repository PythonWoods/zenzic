# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Backwards-compatible alias for ``zenzic.core.adapters``.

All symbols are re-exported from the ``zenzic.core.adapters`` package.
Import from ``zenzic.core.adapters`` for new code.
"""

from zenzic.core.adapters import *  # noqa: F401, F403
from zenzic.core.adapters import (  # noqa: F401
    BaseAdapter,
    MkDocsAdapter,
    StandaloneAdapter,
    ZensicalAdapter,
    _collect_nav_paths,
    _extract_i18n_fallback_to_default,
    _extract_i18n_locale_dirs,
    _extract_i18n_locale_patterns,
    _load_doc_config,
    _load_zensical_config,
    _PermissiveYamlLoader,
    _validate_i18n_fallback_config,
    find_config_file,
    find_zensical_config,
    get_adapter,
    list_adapter_engines,
)
