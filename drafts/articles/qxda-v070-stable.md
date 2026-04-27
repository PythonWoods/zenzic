<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->

<!-- SPDX-License-Identifier: Apache-2.0 -->

# [DRAFT] v0.7.0 Stable — QXDA Engineering Abstract

## Title

How We Built a Subprocess-Free Documentation Analyzer and Survived an AI Siege

## Positioning

Target: power users, infrastructure-minded engineers, readers who care about architecture more than launch copy.

## Core Thesis

Zenzic is not a markdown formatter. It is a static analysis framework that treats documentation as untrusted input. The differentiator is not a prettier report — it is the architectural refusal to execute the build engine while trying to secure it.

## The Hook

Most documentation tooling trusts the build system to reveal what is broken. That is already too late. The build sees rendered output. Zenzic inspects the raw source, builds a Virtual Site Map in memory, and enforces the security perimeter before the engine gets a turn.

## Talking Points

- Zero subprocesses: no `subprocess.run`, no `os.system`, no Node.js evaluation for Docusaurus config.
- Virtual Site Map (VSM): links and routes validated against an in-memory projection of the site, not against hopeful filesystem assumptions.
- Sovereign Root Protocol: configuration follows the target repository, not the caller's current working directory.
- AI siege aftermath: Unicode, entity, frontmatter, and navigation edge cases forced architectural hardening instead of surface patches.
- Purity Protocol: the Core never hardcodes engine names; adapters declare engine-specific behavior.

## Suggested Structure

1. The build-dependency trap
2. Why zero subprocesses is a security decision
3. VSM: O(1) route validation without running the site
4. Sovereign Root and monorepo-safe scanning
5. What the AI siege taught us about documentation as attack surface
6. Why v0.7.0 Stable is an architecture milestone, not just a release

## Closing Angle

The point of Zenzic is not to lint prettier Markdown. The point is to make documentation analyzable with the same rigor we already demand from source code.

## Canonical References

- Product site: <https://zenzic.dev>
- Canonical article path: <https://zenzic.dev/blog/beyond-the-siege-zenzic-v070-new-standard>
- Supporting background: Virtual Site Map, Sovereign Root, UX-Discoverability
