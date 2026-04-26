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

  themeConfig: {
    // navbar: 'changelog' is NOT in sidebars.ts — Zenzic must mark it REACHABLE
    // via config navigation (UX-Discoverability Law, D090).
    navbar: {
      items: [
        { to: '/docs/intro', label: 'Docs', position: 'left' },
        { to: '/docs/changelog', label: 'Changelog', position: 'right' },
      ],
    },
    // footer: 'about' is NOT in sidebars.ts or navbar — Zenzic must mark it REACHABLE
    // because a user can click it from the footer.
    footer: {
      links: [
        {
          title: 'Company',
          items: [
            { label: 'About', to: '/docs/about' },
          ],
        },
      ],
    },
  },

  i18n: {
    defaultLocale: "en",
    locales: ["en", "it"],
  },
};

export default config;
