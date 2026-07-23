// SPDX-FileCopyrightText: 2026 PythonWoods
//
// SPDX-License-Identifier: Apache-2.0

// Dynamically import plugins so they use the standard loader.
const typescriptEslint = (await import('@typescript-eslint/eslint-plugin')).default;
const typescriptParser = (await import('@typescript-eslint/parser')).default;
const js = (await import('@eslint/js')).default;

export default [
  js.configs.recommended,
  {
    files: ['src/**/*.ts'],
    languageOptions: {
      parser: typescriptParser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: 'module',
      },
    },
    plugins: {
      '@typescript-eslint': typescriptEslint,
    },
    rules: {
      ...typescriptEslint.configs.recommended.rules,
      // B2 fix: no-undef is off because TypeScript's type system covers this
      // comprehensively; keeping both active produces duplicate noise.
      'no-undef': 'off',
      // B2 fix: downgraded from 'off' to 'warn' — unused vars are a signal of
      // stale code; 'warn' surfaces them without blocking CI.
      '@typescript-eslint/no-unused-vars': 'warn',
      // B2 fix: downgraded from 'off' to 'warn' — any usage should be reviewed;
      // if intentional, suppress per-site with an inline eslint-disable comment.
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
    },
  },
];
