<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->

<!-- SPDX-License-Identifier: Apache-2.0 -->

# [DRAFT] v0.7.0 Stable — Medium Thought Leadership

## Title

Why We Treat Documentation as Untrusted Input

## Positioning

Target: Tech Leads, engineering managers, documentation leaders. Less code, more strategic framing.

## Thesis

Most teams protect source code with discipline and protect documentation with optimism. That asymmetry is a governance failure. Documentation contains credentials, operational instructions, architecture decisions, and user-facing truth. It deserves a Sentinel before the build, not a post-mortem after production.

## Strategic Frame

Zenzic exists because documentation pipelines quietly became part of the software supply chain. They ingest untrusted contributions, run in CI, and publish globally. If you only validate the rendered site, you are trusting the engine to reveal what the source should have prevented.

## Suggested Structure

1. The blind spot in modern software governance
2. Why documentation belongs inside supply-chain thinking
3. What changes when you treat docs as untrusted input
4. Zero subprocesses as a trust-boundary decision
5. From local discipline to CI policy: how teams operationalize the Safe Harbor
6. Why v0.7.0 Stable matters to managers, not just toolsmiths

## Key Messages

- Build engines are delivery tools, not trust boundaries.
- Security findings must be non-suppressible when credentials or path traversal are involved.
- The best moment to catch a docs failure is while the author is still writing, not after a failed deployment.
- Documentation quality becomes scalable when it is expressed as policy, code, and CI output.

## Closing Angle

The real product is not a linter. It is peace of mind for teams who can no longer afford to treat their documentation as harmless text.

## Canonical References

- Product site: <https://zenzic.dev>
- Strategic anchor article: <https://zenzic.dev/blog/hardening-the-documentation-pipeline>
- Stable release article: <https://zenzic.dev/blog/zenzic-v070-obsidian-maturity-stable>
