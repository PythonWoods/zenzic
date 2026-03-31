<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Guida (Italian)

TRAP (benign): i18n shadow page — exists in `it/` but not in nav.

When MkDocs i18n plugin is configured, this page is a valid shadow of
`guide/get-started.md`. Without the plugin declared, it is an orphan.

This sandbox does NOT declare i18n plugin → ORPHAN_BUT_EXISTING.
Links to this page from Italian locale files would emit UNREACHABLE_LINK.
