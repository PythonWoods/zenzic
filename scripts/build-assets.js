#!/usr/bin/env node
// SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
// SPDX-License-Identifier: Apache-2.0

// Prebuild asset packager.
// Zips static/assets/brand/ and static/assets/social/ into static/assets/brand/brand-kit.zip.
// Overwrites on every run so users always download the latest assets.
// Silent on success; writes to stderr on error.

'use strict';

const AdmZip = require('adm-zip');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const OUTPUT = path.join(ROOT, 'static', 'assets', 'brand', 'brand-kit.zip');

/** Folders to include. Each entry maps a real directory to a zip prefix. */
const SOURCES = [
  { dir: path.join(ROOT, 'static', 'assets', 'brand'),    prefix: 'brand'  },
  { dir: path.join(ROOT, 'static', 'assets', 'social'),   prefix: 'social' },
];

try {
  const zip = new AdmZip();
  let hasContent = false;

  for (const { dir, prefix } of SOURCES) {
    if (!fs.existsSync(dir)) continue;
    zip.addLocalFolder(dir, prefix);
    hasContent = true;
  }

  if (!hasContent) {
    process.stderr.write('build-assets: no source folders found — brand-kit.zip not generated.\n');
    process.exit(0);
  }

  // Ensure output directory exists (static/assets/ should always be present,
  // but be defensive during first-time setup).
  const outputDir = path.dirname(OUTPUT);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  zip.writeZip(OUTPUT);
} catch (err) {
  process.stderr.write(`build-assets: failed to generate brand-kit.zip — ${err.message}\n`);
  process.exit(1);
}
