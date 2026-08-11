# Roadmap Graph — a WIP proposal for how LunaFlow's roadmap is tracked

**Status: WIP — under active design, not ratified, not adopted anywhere in this project.** Nothing in
this folder changes how `CLAUDE.md`, `wiki-style.md`, `Documents/Roadmap/roadmap.md`, or the
handoff-ticket system actually work today. Everything here is a proposal under review. If it's
approved, [`migration-plan.md`](migration-plan.md) is how it would actually get adopted — nothing
adopts itself just by existing in this folder.

## What this is

A proposed replacement for the roadmap's flat phase-sequence model. Phase numbering has been
straining under real insertions and rework — `2.6.5`, `2.7.1`, and the `2.10`–`2.12` proposal batch
are all the same symptom, dependency order forced into a flat sequence that has no room for it. This
space reframes the roadmap as a dependency graph instead of a list: every unit of work is a node,
every real prerequisite is a declared edge, and "what's next" becomes a computed query instead of a
position in a line.

## Contents, in reading order

| Doc | What it covers |
| --- | --- |
| [`overview.md`](overview.md) | The brochure-level pitch — why this, and what it buys us |
| [`proposal.md`](proposal.md) | The full design: node kinds, lifecycle rules, dependency model, citation convention, governance |
| [`Specs/node-format-spec.md`](Specs/node-format-spec.md) | Buildable spec: what a node file looks like on disk |
| [`Specs/graph-tooling-spec.md`](Specs/graph-tooling-spec.md) | Buildable spec: the script that reads the graph and answers queries |
| [`Mockups/sample-generated-index.md`](Mockups/sample-generated-index.md) | Fake example of the generated, crawlable MD index |
| [`Mockups/sample-visualization.html`](Mockups/sample-visualization.html) | Fake example of the HTML graph visualization (open directly in a browser) |
| [`migration-plan.md`](migration-plan.md) | How adoption would actually happen, staged, with rollback at every point before cutover |

## Pilot data — real, not fictional

[`Documents/Roadmap/Nodes/`](../../Roadmap/Nodes/_index.md) now holds real nodes (Phase 2.6.5
through 2.12, ticket 0073, both convergence nodes) built as a Stage-1-style pilot against real,
in-flight project data rather than a synthetic graph — see the
[migration plan](migration-plan.md#stage-1--pilot-against-one-live-case). Still WIP, still nothing
adopted; the real tooling in [`Specs/graph-tooling-spec.md`](Specs/graph-tooling-spec.md) isn't built
yet, so every query against this pilot has been computed by hand so far.

## Two ideas worth knowing before reading further

**Two kinds of node, two different lifecycle rules.** A regular work node (a build, a fix, a stress
test) is terminal once resolved — its history never changes, corrections are new nodes, never a
reopening. A **convergence node** (a big milestone like "ROM Developer operational") makes a live
claim rather than a historical one, and can revert from `reached` back to `WIP` on real evidence of a
gap — without ever erasing the permanent record that it *was* reached before. See
[`proposal.md`](proposal.md) §4.

**Nothing about the ticket system changes.** Regular handoff tickets keep working exactly as
[`../Processes/handoff-tickets.md`](../Processes/handoff-tickets.md) already describes. This proposal
adds a small, separate, never-archived set of nodes for the subset of work that's actually
roadmap-load-bearing — it doesn't touch or replace the ticket ledger.

## Related pages

- [ClaudeWiki index](../index.md)
- [Supreme Leader (PM)](../Roles/supreme-leader.md)
- [Architect](../Roles/architect.md)
- [QA / Verification](../Roles/qa.md)
- [Handoff ticket process](../Processes/handoff-tickets.md) — the system this proposes to sit
  alongside, not replace
- [`Documents/Roadmap/roadmap.md`](../../Roadmap/roadmap.md) — the system this proposes to eventually
  supersede, per [`migration-plan.md`](migration-plan.md)
