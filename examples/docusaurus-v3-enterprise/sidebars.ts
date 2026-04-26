// SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
// SPDX-License-Identifier: Apache-2.0
//
// Explicit sidebar — does NOT list changelog (navbar-only) or about (footer-only).
// Zenzic must classify those two files as REACHABLE via config navigation, not sidebar.

export default {
  main: [
    'intro',
    {
      type: 'category',
      label: 'Guide',
      items: ['guide/index', 'guide/deploy'],
    },
  ],
};
