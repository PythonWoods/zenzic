<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Red-Team Demo

This fixture deliberately triggers multiple Zenzic findings to demonstrate detection
capability across all supported engines. The attack vectors embedded in the subdirectory
files are: Z201 (Shadow Secret), Z105 (Absolute Path), Z502 (Short Content Ghost), and
Z401 (Missing Index). Run `zenzic check all` on this directory to see exit code 2 with
the Security Breach banner. No attack vectors are present in this root index file.
