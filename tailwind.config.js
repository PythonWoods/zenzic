// SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
// SPDX-License-Identifier: Apache-2.0

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class', '[data-md-color-scheme="slate"]'],
  content: [
    "./docs/**/*.md",
    "./overrides/**/*.html",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
