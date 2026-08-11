# Migration plan: from `roadmap.md` to the dependency graph

> **WIP — draft complete, part of an unratified proposal.** See [`../index.md`](../index.md) for this
> space's status. Nothing below has been executed. This plan only becomes real if
> [`proposal.md`](proposal.md) is approved.

**Companion to:** [`proposal.md`](proposal.md) §8 (relationship to what exists today) and §9 (open
questions this plan resolves).

## Principle: no big-bang rewrite, no history loss

Everything in `Documents/Roadmap/` and `Documents/ClaudeWiki/Processes/Handoffs/` stays exactly as it
is throughout this migration until the specific step that says otherwise. At every stage, the old
system keeps working — this is an addition running alongside the current process until it's proven,
not a cutover done on faith.

## Stage 0 — build against a copy, touch nothing live — **done, 2026-08-08**

Implemented at [`scripts/roadmap/roadmap_graph.py`](../../../scripts/roadmap/roadmap_graph.py),
Python stdlib only. All seven of `graph-tooling-spec.md`'s acceptance criteria pass — see
[`scripts/roadmap/test_roadmap_graph.py`](../../../scripts/roadmap/test_roadmap_graph.py), nine
tests, synthetic fixtures for every criterion, plus one that copies the real pilot data to a temp dir
and diffs before/after to confirm read-only behavior. `python3 -m unittest
scripts.roadmap.test_roadmap_graph -v` from the repo root to re-run.

Went a step further than this stage strictly required: also ran every query (`validate`, `frontier`,
`downstream`, `blocking`, `render`, `export-json`) against the real 13-node pilot under
`Documents/Roadmap/Nodes/` (via a temp copy, never the live files) and cross-checked the output
against everything hand-computed during the pilot exercise — exact match throughout (frontier =
RM-0007/RM-0008/RM-0009; no cycles; `downstream RM-0010` returns all eight nodes past it). That's
Stage 1-and-beyond validation happening inside what was scoped as a synthetic-only stage — noted
honestly rather than quietly relabeled as "Stage 0 complete" and left at that.

## Stage 1 — pilot against one live case — **already happened, out of order**

This stage as originally scoped (write exactly one real node, for ticket 0073 alone, prove the tool
survives contact with one messy real case before trusting it further) never ran as its own discrete
step. Instead, a separate pilot exercise (Arryn: *"let's mock up the note system... let's see what
stage 0 gets us"*) produced real node files for the *entire* Phase 2.6.5–2.12 history plus 0073 plus
two convergence-tier nodes, all before this script existed. The tool was then built and pointed at
that already-existing real data, rather than the data being built incrementally against an
already-working tool the way this stage assumed.

Practical effect: no harm done — the acceptance-criteria tests using isolated synthetic fixtures give
the same confidence this stage was meant to provide, and the cross-check against real data (Stage 0's
note, above) is strictly more validation than "one node" would have been. But the *order* in the plan
and the order in reality diverged, and this section is being left here, marked as such, rather than
quietly rewritten to look like the plan was followed — same "supersede, don't delete" instinct this
project applies everywhere else.

## Stage 2 — backfill existing history, once — **already happened, same pilot exercise**

The 13 real nodes under `Documents/Roadmap/Nodes/` already cover this stage's scope: `phase-2-6-5.md`
through `phase-2-12.md` converted to `resolved`/`open` work nodes (`RM-0001`–`RM-0009` for the phase
history plus the 0073 evaluation), and the convergence points decided as three tiers, not the single
"ROM Developer operational" this stage originally anticipated — `RM-0010` (ROM Developer, `reached`,
real 3-ROM evidence), `RM-0012`/`RM-0013` (Rulebook tier, `reached`, single-case evidence, honestly
flagged as weaker in `RM-0013`'s own body), and `RM-0011` (World Builder, `WIP`, blocked on
RM-0007/RM-0008). Every backfilled node still cites the real QA verdict or ticket behind it, per this
stage's original rule — nothing about *what happened* was changed, only that it now also has a
graph-shaped record. What's genuinely still open from this stage's original scope: `phase-0.md`
through `phase-2-6.md` (pre-pilot history) were never backfilled — the pilot's own root node,
`RM-0001`, says so explicitly rather than implying full coverage.

**What doesn't get backfilled, confirmed still true:** superseded/archived material (`phase-3.md`, the
two Handoffs archive pages) stayed out of the graph, per this stage's original rule.

## Stage 3 — run both systems in parallel

`roadmap.md`'s phase table keeps being the source of truth. The generated index
(`render`'s output) runs alongside it, visible, but informational — anyone can compare the two and
flag a mismatch. This stage has no fixed length; it ends when the generated index has been trusted
enough, long enough, that nobody's finding daylight between the two.

## Stage 4 — cut over

`roadmap.md`'s phase-sequence table is replaced with a short pointer to the generated index, the same
way `Documents/ApiReference/` already replaced hand-written type documentation — generated,
regenerated on demand, not hand-maintained. The existing phase docs (`phase-2-10.md` etc.) aren't
deleted; they become the "body" a node file points at, the same relationship a ticket file already
has to its one-line row in `Handoffs/_index.md` today.

## Stage 5 — retire the manual table

Once Stage 4 has held for a while with nobody needing the old table, mark the phase-sequence table's
last hand-maintained version as historical per the usual supersession convention — banner, pointer to
the generated index, not deleted.

## What never changes, at any stage

- `Documents/ClaudeWiki/Processes/Handoffs/` — untouched. Regular tickets keep working exactly as
  `handoff-tickets.md` describes, forever, independent of whether this proposal is adopted.
- Every existing QA verdict, ticket resolution, and phase doc — none of it is rewritten. The graph
  only ever adds a structured pointer to what already exists; it never becomes the sole copy of a
  fact that used to live only in prose.
- Authority — who can mark what, per [`proposal.md`](proposal.md) §7 — is unchanged by migration
  staging; it's a proposal-approval question, not a rollout question.

## Rollback

Trivial through Stage 3: stop generating the index, keep using `roadmap.md` exactly as today, delete
the `Nodes/` folder if desired — nothing outside it was ever touched. Rollback gets genuinely costly
only after Stage 4's cutover, which is exactly why Stage 3 has no fixed timebox — it ends on
confidence, not on a calendar.

## Related pages

- [RoadmapGraph space index](index.md)
- [Full proposal](proposal.md)
- [Node format spec](Specs/node-format-spec.md)
- [Graph tooling spec](Specs/graph-tooling-spec.md)
- [Ticket 0073](../Processes/Handoffs/0073-rule-compilation-cost-and-runtime-mode.md) — Stage 1's pilot case
