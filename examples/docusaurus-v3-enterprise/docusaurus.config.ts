// SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
// SPDX-License-Identifier: Apache-2.0
//
// Docusaurus v3 Enterprise config — Zenzic reads this as plain text.
// Node.js is never invoked.

const config = {
  title: "Enterprise Docs",
  url: "https://example.com",
  baseUrl: "/",

  presets: [
    [
      "@docusaurus/preset-classic",
      {
        docs: {
          routeBasePath: "docs",
          sidebarPath: "./sidebars.ts",
        },
      },
    ],
  ],

  i18n: {
    defaultLocale: "en",
    locales: ["en", "it"],
  },
};

export default config;
