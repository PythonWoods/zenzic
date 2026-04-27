<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->

<!-- SPDX-License-Identifier: Apache-2.0 -->

# [DRAFT] v0.7.0 Stable — Dev.to Community Victory

## Title

Obsidian Maturity: How an AI Siege Made Our Docs Pipeline Stronger

## Positioning

Target: open-source developers, maintainers, Dev.to readers who want a technical story with a human arc.

## Narrative Hook

We did not reach v0.7.0 by polishing a changelog. We got there by attacking our own assumptions. AI agents found edge cases in the Shield, exposed weak spots in frontmatter handling and discoverability, and forced us to turn a linter into a real documentation safety system.

## Story Arc

Part 3 ended with the siege. This piece is the emotional and technical payoff.

- The siege proved the threat model was real.
- The fixes could not be local patches; they had to become policy and architecture.
- v0.7.0 Stable is the moment where those lessons became product guarantees.

## Key Beats

1. The AI siege did not break confidence — it removed illusion.
2. Unicode and frontmatter edge cases taught us that parsers fail at boundaries, not at headlines.
3. UX-Discoverability changed the orphan rule: invisible pages are broken even if they exist on disk.
4. The Lab became a teaching surface, not just a demo.
5. SARIF and CI integration turned documentation quality into a team habit.

## Suggested Structure

1. The day we let AI attack the Shield
2. The bugs that mattered because they were subtle
3. Why v0.7.0 Stable is called Obsidian Maturity
4. UX-Discoverability and the human-eye definition of reachability
5. What changed for maintainers and contributors
6. Try it now: `uvx zenzic check all .`

## Closing Angle

Open source wins when the scary lessons become shared infrastructure. v0.7.0 Stable is the version where Zenzic stopped being just our tool and became a reproducible discipline.

## Canonical References

- Canonical article path: <https://zenzic.dev/blog/zenzic-v070-obsidian-maturity-stable>
- Prior saga context: <https://zenzic.dev/blog/ai-driven-siege-shield-postmortem>
