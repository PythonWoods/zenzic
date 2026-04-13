// SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
// SPDX-License-Identifier: Apache-2.0
//
// Minimal Docusaurus v3 config — used by Zenzic to extract baseUrl.
// This file is never executed by Node.js. Zenzic reads it as plain text.

const config = {
  title: "Docusaurus Example",
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
