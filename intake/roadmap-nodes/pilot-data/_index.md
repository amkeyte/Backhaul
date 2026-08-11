# RM Node Index

> **WIP — pilot data, part of an unratified proposal.** See
> [`../../ClaudeWiki/RoadmapGraph/index.md`](../../ClaudeWiki/RoadmapGraph/index.md) for this space's
> status. These are real project nodes (not fictional mockup data) built as a Stage-1-style pilot —
> see the proposal's [migration plan](../../ClaudeWiki/RoadmapGraph/migration-plan.md). Not adopted;
> `roadmap.md`'s phase table is still the live source of truth.

Flat numeric ledger, same shape and discipline as
[`Handoffs/_index.md`](../../ClaudeWiki/Processes/Handoffs/_index.md) — not the dependency/frontier
view (that's `render`'s output, now real — see below). This index exists for the "what's the next
number" lookup and for skimming the node set without running the tool. Update a row when its node
changes; Kofi reconciles drift, same as with tickets.

**Real tooling exists now (2026-08-08).**
[`scripts/roadmap/roadmap_graph.py`](../../../scripts/roadmap/roadmap_graph.py) implements
`graph-tooling-spec.md` against this real folder — `validate`, `frontier`, `dependents`,
`downstream`, `blocking`, `render`, `export-json`, all passing their acceptance criteria and
cross-checked against this ledger's own data. Run `python3 scripts/roadmap/roadmap_graph.py frontier`
(etc.) from the repo root rather than trusting a hand-computed answer. This doesn't change this
index's own job (still a hand-maintained flat lookup) or this proposal's ratification status (still
unadopted) — it just means the dependency/frontier view is no longer hypothetical.

**Visualize links still hand-built, not yet tool-generated.**
[`sample-visualization.html`](../../ClaudeWiki/RoadmapGraph/Mockups/sample-visualization.html) holds
this real node set (not illustrative data), so each node's own `Visualize` line deep-links correctly
with `?focus=RM-NNNN` — but it's still a hand-built page, not `export-json`'s output. If a node here
changes and the mockup isn't updated to match, it will drift. Real, tool-generated deep-linking
replaces it once an HTML consumer is built against `export-json`, per
[`graph-tooling-spec.md`](../../ClaudeWiki/RoadmapGraph/Specs/graph-tooling-spec.md#deep-link-contract-for-the-future-html-consumer)
— the script itself deliberately doesn't build that part (see the spec's Scope section).

| Node | Kind | Status | Owner | Summary |
| --- | --- | --- | --- | --- |
| [RM-0001](RM-0001-phase-2-6-5.md) | work | resolved | Kofi | Phase 2.6.5 — ROM identity & cross-ROM interop |
| [RM-0002](RM-0002-phase-2-7.md) | work | resolved | Kofi | Phase 2.7 — Multi-ROM composition |
| [RM-0003](RM-0003-phase-2-7-1.md) | work | resolved | Kofi | Phase 2.7.1 — Loot ROM & content expansion |
| [RM-0004](RM-0004-phase-2-8.md) | work | resolved | Kofi | Phase 2.8 — World Module extraction |
| [RM-0005](RM-0005-phase-2-9.md) | work | resolved | Kofi | Phase 2.9 — Lua World Module authoring |
| [RM-0006](RM-0006-phase-2-10.md) | work | resolved | Kofi | Phase 2.10 — Content coverage stress test |
| [RM-0007](RM-0007-phase-2-11.md) | work | resolved | Kofi | Phase 2.11 — Capability mechanism stress test (QA gate 0080 — PASS) |
| [RM-0008](RM-0008-phase-2-12.md) | work | open | Kofi | Phase 2.12 — Lua World Module stress test (still proposal-stage) |
| [RM-0009](RM-0009-ticket-0073-roslyn-evaluation.md) | work | open | Amara | Evaluate Roslyn removal from the rule-compilation pipeline (ticket 0073) |
| [RM-0010](RM-0010-rom-developer-operational.md) | convergence | reached | Kofi | ROM Developer operational |
| [RM-0012](RM-0012-rulebook-tier-established.md) | work | resolved | Kofi | OneD20 established as the Rulebook tier (backfilled, no ticket) |
| [RM-0013](RM-0013-rulebook-author-operational.md) | convergence | reached | Kofi | Rulebook Author operational (single-case proof — see caveat in the node) |
| [RM-0014](RM-0014-phase-2-11-1.md) | work | open | Kofi | Phase 2.11.1 — Rulebook content extraction (ticket 0082, open) — optional, dead-end |
| [RM-0011](RM-0011-world-builder-operational.md) | convergence | WIP | Kofi | World Builder operational — blocked on RM-0007, RM-0008 |

## Related pages

- [RoadmapGraph proposal space](../../ClaudeWiki/RoadmapGraph/index.md)
- [Node format spec](../../ClaudeWiki/RoadmapGraph/Specs/node-format-spec.md)
- [Handoff Ticket Index](../../ClaudeWiki/Processes/Handoffs/_index.md) — the equivalent ledger this mirrors
