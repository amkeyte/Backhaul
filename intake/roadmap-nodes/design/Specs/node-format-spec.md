# Spec: RM node file format

> **WIP — draft complete, part of an unratified proposal.** See
> [`../../index.md`](../../index.md) for this space's status. Nothing here is buildable against yet —
> this spec exists to be reviewed alongside [`../proposal.md`](../proposal.md) and
> [`graph-tooling-spec.md`](graph-tooling-spec.md), not implemented on its own.

**Companion to:** [`../proposal.md`](../proposal.md) §4 (core model) and §6 (tooling) —
read those first for rationale. **Consumed by:** [`graph-tooling-spec.md`](graph-tooling-spec.md).

## Purpose

Defines exactly what an RM node file contains, so the graph-tooling script has something precise to
parse and a human has something precise to write. One file per node, plain markdown with a small,
fixed set of machine-readable fields at the top — same shape discipline the existing handoff-ticket
template already holds authors to, extended with the fields a graph needs that a flat ticket list
never did (`DependsOn`, `Kind`, and a reversible status for convergence nodes).

## Location and naming

`Documents/Roadmap/Nodes/RM-NNNN-slug.md` — a new folder, parallel to `Documents/Roadmap/Proposals/`,
deliberately **separate from** `Documents/ClaudeWiki/Processes/Handoffs/`. Reasoning: the Handoffs
index is explicitly allowed to be archived and sharded once it grows too long to skim
(`index-archive.md`, `index-archive-2.md` already exist for exactly this reason) — that's fine for
routine findings-and-asks tickets, but fatal for something load-bearing enough to gate a convergence
node. RM nodes need a home that's small enough, and important enough, to never need that treatment.

`NNNN` is monotonic, assigned at creation, never reused — identical discipline to ticket numbers,
just a separate counter. `slug` is a short kebab-case description, same as ticket filenames today.

**`Nodes/_index.md` — a flat numeric ledger, same shape as
[`Handoffs/_index.md`](../../Processes/Handoffs/_index.md).** One row per node: ID, Kind, Status,
Owner, one-line summary — same columns, same discipline (update the row when the node changes,
Kofi reconciles drift same as with tickets). This is not a stand-in for §6's `render` query: `render`
computes the dependency structure and the actionable frontier fresh every time, which is exactly the
kind of derived truth that shouldn't be hand-maintained. The flat index does a narrower, cheaper job
`render` doesn't: giving node creation an authoritative "what's the next number" lookup, and giving a
human something to skim before the real tooling exists at all. Once `render` exists, the two coexist
the same way `roadmap.md`'s table and the generated index coexist during
[migration Stage 3](../migration-plan.md#stage-3--run-both-systems-in-parallel) — the flat index isn't
retired just because a smarter view showed up.

## Required fields

Every node file opens with a fixed block, in this order:

```markdown
# RM-0042 — <short title>

**Kind:** work | convergence
**Status:** <see below, depends on Kind>
**Created:** <date>
**Owner:** <role — Kofi, Amara, Juno, Baraka, Nadia, or Lothar>
**DependsOn:** [RM-0012](RM-0012-slug.md), [RM-0031](RM-0031-slug.md)
**Visualize:** <a href="<path-to-viz>?focus=RM-0042" target="_blank" rel="noopener">Open in graph view ↗</a>
```

Link, don't reference bare — a dependency you can't click is one more thing to grep for by hand. Same
folder, so a plain relative filename (no `../` needed, node files are all siblings). The bracket text
stays the bare `RM-NNNN` form so parsing doesn't care whether a tool reads the link target or the
link text — either resolves the same ID.

- **Kind** is set once at creation and never changes. A work node that turns out to be more
  significant than expected doesn't get promoted — a new convergence node is created that depends on
  it instead. (Mirrors the project's own rule against generalizing a mechanism from a single
  consumer — don't reclassify retroactively on a hunch, wait for a second real reason.)
- **DependsOn** is a flat list of RM-IDs, each written as a markdown link to that node's file (see
  the header block above). Empty list is valid (a node with no prerequisites is actionable from
  creation). Malleable while the node is `open`/`WIP`; changing it after the node is `resolved`
  requires a dated note in the node's own body, not a silent edit — same discipline ticket
  Resolution sections already follow.
- **Owner** is whichever role's judgment call closes the node — not necessarily who created it,
  mirroring the ticket system's opened-by/for split.
- **Ticket** (optional): `**Ticket:** [NNNN](path) — <its current ticket status>`, once work has
  actually started. Pure cross-reference — points at whichever handoff ticket is doing the day-to-day
  work, so a reader lands on the live conversation instead of hunting for it. Carries no weight in any
  query below; see the note under Status vocabulary for why.
- **Visualize** — a raw HTML anchor (`target="_blank"` so it opens the graph in a new tab rather than
  navigating away from the node), always the last line of the header block. Plain markdown link syntax
  can't set `target`, hence the raw `<a>` tag — every renderer in play here passes inline HTML through
  (CommonMark allows it by default), so this isn't a special case to support. See "Visualize — computed,
  not stored" below for what it's for and why it lives in the header rather than at the bottom next to
  Required By.

## Status vocabulary

**Deliberately no "in progress" status.** A node's own status only answers one question — does the
deliverable exist yet — and stays `open` for as long as that's not yet true, whether that means
"nobody's touched it" or "it's in-review and nearly done." The finer-grained question, *is someone
actively on this right now*, is already answered by the linked ticket's own `open → in-review →
resolved` lifecycle — that mechanism already exists, already works, and doesn't need a parallel one
bolted onto the node. `frontier` (§6 of the proposal) will keep listing an in-review node as
actionable, and that's correct, not a gap: actionable means "dependencies are satisfied, this could be
picked up," never "unclaimed." Whether it's already claimed is one click away, same as it is today.

**Work nodes** — terminal once left `open`:

| Status | Meaning | Reversible? |
| --- | --- | --- |
| `open` | Not yet resolved. Actionable if `DependsOn` is fully satisfied (computed, see below). | — |
| `resolved` | Done. Historical fact, permanent. | No — corrections are a new node, never reopening this one. |
| `superseded` | Wrong, or replaced by a better answer. Must carry `**Superseded by:** RM-XXXX`. | No — same rule as `resolved`. |

**Convergence nodes** — the one place status is genuinely reversible:

| Status | Meaning | Reversible? |
| --- | --- | --- |
| `WIP` | The milestone isn't currently claimed solid. Initial state, and the state a `reached` node returns to if reopened. | — |
| `reached` | The milestone currently holds, backed by an independent QA verdict. | **Yes** — can revert to `WIP`. Requires QA authority per [`../proposal.md`](../proposal.md) §7. |

Convergence nodes additionally carry a `ReachedLog` — append-only, never edited or pruned once an
entry is written:

```markdown
## ReachedLog

- 2026-08-04 — reached, verdict [phase-2-10-verdict.md](../../../QA/phase-2-10-verdict.md)
- 2026-09-02 — reverted to WIP, see RM-0058 (gap found in Poisoned's cross-session persistence)
- 2026-09-20 — reached again, verdict [...]
```

This is the part that never gets erased even when current `Status` flips back to `WIP` — the record
that it *was* reached, when, and on what evidence, stays exactly as true as it always was. Only the
*current* claim changes.

## What's stored vs. what's computed

Stored (an author writes it, changes only by explicit edit): `Kind`, `Status`, `DependsOn`, `Owner`,
`Created`, `ReachedLog`, `Superseded by`.

**Never stored, always computed by the tooling:** whether a node is *actionable*. No field for it,
no human sets it — it's derived fresh every time as "status permits starting, and every `DependsOn`
entry is `resolved` or `reached`." Same reasoning `wiki-style.md` already applies to phase status:
don't let a claim of readiness be asserted when it can be derived from evidence instead. A stored
"actionable: true" field would just be a second place for the truth to drift away from, the exact
failure this whole proposal exists to stop introducing elsewhere.

## Required By — computed, not stored

The mirror of `DependsOn`, shown at the bottom of a node's rendered view for reading flow: `DependsOn`
at the top tells you what this needs, **Required By** at the bottom tells you what needs this. Direct
(one-hop) reverse edges only — for node X, everything Y where X appears in Y's `DependsOn`. Not the
full transitive closure; that's a different question, already served by `downstream` (§6 of the
proposal / `graph-tooling-spec.md`'s `dependents`/`downstream` queries).

**Never hand-authored.** If RM-0007 lists RM-0002 in `DependsOn`, RM-0002's Required By already
*is* RM-0007 — writing that into RM-0002's own file too would be a second, independently-editable copy
of a fact that's only real once, the same dual-write risk `wiki-style.md` already warns against
everywhere else. **Real tooling now exists** —
[`scripts/roadmap/roadmap_graph.py`](../../../../scripts/roadmap/roadmap_graph.py)'s `dependents`
query computes this directly — but it isn't wired into the node files themselves yet (the script is
read-only by design, see `graph-tooling-spec.md`'s Scope). Every real node's own "## Required By"
section is still hand-written prose asserting the tool's answer, kept honest by cross-checking against
`dependents <RM-ID>` rather than by the tool writing it in automatically.

## Visualize — computed, not stored

Same discipline as Required By: a link to the HTML graph view, deep-linked and focused on this node —
mechanically derived from the node's own ID, never a fact an author invents or maintains by hand.
Convention: append `?focus=RM-NNNN` to the visualization's URL — the consumer highlights the matching
node and scrolls/pans it into view.

**Different placement than Required By, on purpose.** Required By lives at the bottom, mirroring
`DependsOn` at the top for a reading flow (what this needs / what needs this). Visualize lives in the
header block instead, as the last line — it's not part of that mirror, it's a jumping-off point: "see
this node in context" is something a reader wants *before* reading the body, not after, and putting it
next to `Ticket` keeps every quick-action link in one place at the top rather than split across the
file.

**Working today, against real data.** [`../Mockups/sample-visualization.html`](../Mockups/sample-visualization.html)
implements `?focus=RM-NNNN`, and as of 2026-08-08 its 11 nodes are the real pilot under
`Documents/Roadmap/Nodes/` — not an illustrative placeholder set. A link like
[`sample-visualization.html?focus=RM-0007`](../Mockups/sample-visualization.html?focus=RM-0007) is a
genuinely correct, live link today, and every real node under `Documents/Roadmap/Nodes/` now carries
its own `Visualize` line pointing at exactly this, focused on itself. It's still a hand-built page, not
real tooling output — if the node files change, this page drifts until someone updates it by hand, same
as the flat index.

`export-json` itself now exists and produces exactly this data — see
[`scripts/roadmap/roadmap_graph.py`](../../../../scripts/roadmap/roadmap_graph.py) — but nothing yet
consumes that JSON to render an actual graph view; `sample-visualization.html` remains hand-built.
Once a real HTML consumer exists and renders the graph fresh from `export-json`'s output
([`graph-tooling-spec.md`](graph-tooling-spec.md)), this hand-built page retires. The
`Visualize` link's *target* changes at that point; its `?focus=RM-NNNN` contract doesn't.

## Body content

Below the required block, a node file reads like any other wiki page — purpose, context, whatever
narrative the work needs. No fixed template beyond the header block above; work nodes can borrow the
existing ticket template's Context/Ask/Response/Resolution shape wholesale where that fits (most
will, since most RM nodes *are* build tickets that also happen to be roadmap-load-bearing — see
[`../migration-plan.md`](../migration-plan.md) on how the two relate day to day).

**A note on the example IDs below:** `RM-9001` and `RM-9058` — deliberately outside the `RM-0001`...
`RM-0011` range the real pilot occupies, so nothing here is mistakable for, or collides with, a real
node. (An earlier draft of this spec reused `RM-0007`/`RM-0058` for these examples, back when the
mockup's graph was itself illustrative and those numbers were safely fictional. Once the mockup was
rebuilt against real pilot data, `RM-0007` became a real node — reusing it here would have made this
example's `Visualize` link resolve to the wrong, real thing.)

## Example — a convergence node

```markdown
# RM-9001 — ROM Developer operational

**Kind:** convergence
**Status:** reached
**Created:** 2026-07-15
**Owner:** Kofi
**DependsOn:** [RM-9010](RM-9010-slug.md), [RM-9011](RM-9011-slug.md), [RM-9012](RM-9012-slug.md), [RM-9013](RM-9013-slug.md)
**Visualize:** <a href="../Mockups/sample-visualization.html?focus=RM-9001" target="_blank" rel="noopener">Open in graph view ↗</a> *(illustrative only — `RM-9001` is a placeholder ID, not a real pilot node, so this particular link isn't live; see "Visualize — computed, not stored" above for one that is)*

The point at which a third party could author a new ROM against `Capability`/`IRom`/
`ComponentRegistry` without touching engine internals, with the toolbox proven across three real
ROMs (GridMap, D20System, Loot) plus a fourth relay case (Reputation).

## ReachedLog

- 2026-08-04 — reached, verdict phase-2-10-verdict.md

## Required By

*(computed — this example has no dependents yet; a convergence node often won't, since not much sits
downstream of "operational")*
```

## Example — a work node citing a live design question

```markdown
# RM-9058 — Evaluate Roslyn removal from the rule-compilation pipeline

**Kind:** work
**Status:** open
**Created:** 2026-08-04
**Owner:** Amara
**DependsOn:** *(empty — no prerequisites)*
**Visualize:** <a href="../Mockups/sample-visualization.html?focus=RM-9058" target="_blank" rel="noopener">Open in graph view ↗</a> *(illustrative only — same placeholder caveat as the example above)*

Roslyn compiles 1.d20's rule groups at ~14x the cost of the NRules Rete-build it feeds. Findings and
charted options in `rule-pipeline-compilation-cost.md`. See handoff ticket 0073 for the original
finding — this node exists because whichever option gets ruled on may retroactively affect anything
that cited "Roslyn compiles rule groups" as a stated fact (§5's citation convention is what makes
that list computable instead of remembered).

## Required By

*(computed — [RM-9080](RM-9080-slug.md), "GM Overlay operational," once the live-reload cost model
depends on this ruling)*
```

(The real Roslyn-evaluation node in the pilot is [`RM-0009`](../../../Roadmap/Nodes/RM-0009-ticket-0073-roslyn-evaluation.md) — narrower in scope than this example, no Required By yet. This example is deliberately a bit more elaborate to show the citation convention in context.)

## Related pages

- [RoadmapGraph space index](../../index.md)
- [Full proposal](../proposal.md)
- [Graph tooling spec](graph-tooling-spec.md)
- [Migration plan](../migration-plan.md)
