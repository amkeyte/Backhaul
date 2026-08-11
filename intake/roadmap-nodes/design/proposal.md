# Proposal: a dependency-graph roadmap for LunaFlow

> **WIP — proposal under active design, not ratified.** This document is the full design behind
> [`overview.md`](overview.md)'s pitch. Nothing here is adopted process. See
> [`../index.md`](../index.md) for this space's status and [`migration-plan.md`](migration-plan.md)
> for how adoption would actually happen if this is approved.

**Author:** Kofi (PM), from a working design conversation with Arryn.
**Status:** draft, first full write-up.

## 1. Problem statement

`Documents/Roadmap/roadmap.md` encodes two different things in one number: *creation order* and
*dependency order*. Those two properties don't actually correlate, and forcing them into one flat
sequence has already broken three times — `2.6.5` (ROM identity work that couldn't wait for a
whole-number slot), `2.7.1` (content work wedged the same way), and the `2.10`–`2.12` batch (three
siblings from one proposal, numbered as though they were the tenth through twelfth things to happen).
Each decimal insertion is a symptom, not a one-off. The next one is already visible: ticket
[0073](../Processes/Handoffs/0073-rule-compilation-cost-and-runtime-mode.md) may rule that Roslyn
should be removed from the rule-compilation pipeline entirely — a change wide enough to touch
multiple existing phases' assumptions, with no clean slot to insert it into a linear sequence and no
mechanical way to know everything that would need re-checking if it happens.

## 2. Goals

- Let new work be declared without renumbering anything that already exists.
- Make "what can I actually start right now" a computed answer, not a memorized one.
- Make deprecating or reworking something produce a computed list of what else might be affected,
  instead of relying on whoever's holding the most context that week.
- Preserve history exactly as it is today — nothing about this proposal deletes or rewrites a past
  record. `wiki-style.md`'s "supersede, don't delete" rule holds throughout.
- Cost nothing extra for the common case. Most work today is a routine ticket between two roles and
  should stay exactly that — this proposal only adds structure to the subset of work that's actually
  roadmap-load-bearing.

## 3. Non-goals

- This does **not** replace the handoff ticket system. Tickets keep their numbering, lifecycle, and
  index exactly as `handoff-tickets.md` describes today.
- This does **not** propose real-time collaborative editing or concurrent-writer conflict resolution
  (the LexoRank/fractional-indexing class of tools solves that problem; we don't have it — one PM,
  git-tracked files, serialized edits). We take the *insight* — decouple identity from position —
  without importing machinery sized for a problem we don't have.
- This does **not** decide, in this document, whether Roslyn should actually be removed. Ticket 0073
  is a live example used throughout to pressure-test the model, not a ruling made here.

## 4. Core model

**Nodes.** Every roadmap-load-bearing unit of work — a build, a design ruling, a stress-test finding,
a migration — is a node with a stable ID, assigned once at creation, never reused, never renumbered.
Same discipline the ticket ledger already proves out over 76 tickets.

**Edges.** A node declares `DependsOn: [other node IDs]` — the set of things that must be true before
this one can be considered actionable. Edges are malleable on an open node (understanding a
dependency correctly is part of the work) and require an explicit, dated amendment to change on a
resolved one (never a silent rewrite).

**Two kinds of node, with different lifecycle rules:**

- **Work nodes** — a build ticket, a spec, a fix, a stress-test phase. Terminal once resolved.
  History never changes: "this passed QA on this date" stays true forever, even if something built
  on top of it later reveals a gap. Corrections happen by adding a new node, never by reopening the
  old one. States: `open` → `resolved`, or `open` → `superseded` (wrong, or replaced — points at what
  replaced it).
- **Convergence nodes** — the big milestones: "ROM Developer operational," "World Builder
  operational." These make a *live* claim, not a historical one — "the ground underneath this is
  currently solid enough to build the next tier on" — and that claim has to be revocable, or it stops
  doing its job. States: `WIP` ↔ `reached`, freely reversible in either direction, plus a permanent,
  append-only `ReachedLog` recording every time it was reached and by what evidence — that part never
  gets erased, even when the current status reverts.

See [`Specs/node-format-spec.md`](Specs/node-format-spec.md) for the exact fields.

**Actionable is computed, never stored.** A node is actionable exactly when its own status permits
starting (`open`, or `WIP` for a convergence node) and every node in its `DependsOn` list is
`resolved` or `reached`. Nobody hand-sets "actionable" — that would let a claim of readiness drift
from the graph's actual truth, the same failure mode `wiki-style.md` already guards against by
requiring an independent QA verdict before a phase moves to `done`. Here, the check is mechanical
instead of a verdict, but the principle — don't let status be asserted when it can be derived — is
the same one.

## 5. Citations, for prose that isn't a node

A node is a discrete, dated thing with edges. A sentence in `engine-core.md` or `rule-pipeline.md`
is not — it's prose stating a fact about how the system works, and prose doesn't have edges. That gap
is exactly where "an agent falls back on a false fact" lives: the graph can tell you every *node*
that depended on a deprecated one, but it can't natively tell you that paragraph four of some design
doc quietly assumed the same thing.

The fix: any design-doc prose stating a load-bearing external fact cites the node that established
it, gathered in a references list at the bottom of the document (not inline — keeps the prose
readable; this project's design docs already end with "Related documents" sections, this is that
same convention held to a stricter bar). Deprecating a node then becomes: run the impact query
(§6) for every *node* that depends on it, **and** grep `Documents/` for citations of its ID to find
every *document* that does. Same mechanism, extended from nodes into text that isn't graph-shaped.

No citation, no claim — that's the actual writing discipline this introduces. It doesn't apply to
node files themselves (they're already dated, already habitually cite each other inline, and aren't
prone to silently going stale the way a standing design claim is).

## 6. Tooling

One script, one loaded graph, several queries — not four separate scripts each re-implementing graph
load. Full spec in [`Specs/graph-tooling-spec.md`](Specs/graph-tooling-spec.md); summary:

- **`frontier`** — every actionable node right now. This is the "menu" that replaces the linear plan.
- **`downstream <ID>`** — full transitive closure of everything that depends on `<ID>`, direct or
  indirect, in dependency order. This is the deprecation-impact query: point it at a node about to be
  superseded or a convergence node about to revert, and it hands back everything that needs a human
  to judge "still stands on its own merits" versus "actually needs to change too" — the same query
  serves both trigger events, because reverting a convergence node and deprecating a work node raise
  the identical question: what else was resting on this.
- **`blocking <ID>`** — the reverse: what's currently unsatisfied that's keeping `<ID>` from being
  actionable. Answers "why can't I start this yet" without manual chain-walking.
- **`validate`** — cycle detection over the whole graph, same shape as `ComponentRegistry.Validate()`.
  Fails loud rather than producing a nonsensical frontier.
- **`render`** — generates the crawlable MD index: actionable frontier at top, names-only dependency
  structure below. See [`Mockups/sample-generated-index.md`](Mockups/sample-generated-index.md).
- **`export-json`** — the same graph, structured, for the HTML visualization to consume later without
  re-deriving the parsing layer. See [`Mockups/sample-visualization.html`](Mockups/sample-visualization.html).

The tool is read-only against node files — it computes and reports, it never edits a node or makes a
judgment call. Deciding whether a downstream node survives a deprecation is always a human ruling,
same as today.

## 7. Governance — mapped onto roles that already exist

Nothing here invents new authority; it gives existing authority a mechanical place to land.

- **Opening a work node / cutting a build ticket** — Kofi, same as today's build-ticket process.
- **Ratifying a convergence node's existence** (deciding "ROM Developer operational" is a real
  milestone worth tracking) — Kofi + Amara, same act-then-report-or-propose-first split that already
  governs structural roadmap changes.
- **Marking a convergence node `reached`** — requires an independent QA verdict, exactly the existing
  hard rule (`wiki-style.md`'s "Where status lives") that a phase doesn't move to done on the PM's own
  read of ticket close-outs.
- **Reverting a convergence node to `WIP`** — this is QA's existing authority, just newly mechanized.
  `qa.md` already states Lothar "can reopen any ticket or phase whose acceptance criteria aren't
  actually met." Today that's a vague gesture with no defined downstream consequence. Under this
  model it's a status flip that mechanically freezes every convergence node depending on it — the
  authority isn't new, the blast radius is just no longer something Kofi has to remember to go check.
- **Ruling a dependency edge is wrong or ambiguous** — Amara, same as any spec-vs-reality question
  today.
- **Deciding whether a downstream node survives a deprecation** — whoever owns that node's domain
  (Kofi for scope questions, Amara for framework questions, Juno for content questions) — the impact
  query produces the list, it doesn't make the call.

## 8. Relationship to what exists today

- `Documents/Roadmap/roadmap.md`'s phase table becomes, eventually, a generated view rather than a
  hand-maintained one — see the migration plan for how that cutover happens without a big-bang
  rewrite.
- `Documents/ClaudeWiki/Processes/Handoffs/` and its numbering are untouched. RM nodes are a separate,
  smaller, never-archived series precisely because they can't afford to fall out of the visible
  window the way a ticket-index page eventually does.
- `wiki-style.md`'s "supersede, don't delete" and "where status lives" conventions are the ancestors
  of this proposal's node-lifecycle rules, not replacements for them.

## 9. Open questions

- ~~Exact node-ID prefix and file location~~ — **settled** by
  [`Specs/node-format-spec.md`](Specs/node-format-spec.md): `Documents/Roadmap/Nodes/RM-NNNN-slug.md`,
  monotonic `NNNN`, flat `_index.md` ledger alongside it.
- Whether `render`'s output ever replaces `roadmap.md` outright, or the two coexist indefinitely —
  deferred to the migration plan, since it's a rollout-sequencing question, not a design one.
- What happens to phase docs that already exist (`phase-0.md` through `phase-2-11.md`) — addressed in
  the migration plan as a backfill pass, not a rewrite.
- **New, from the Stage-1 pilot:** the roadmap's own tier list (`CLAUDE.md`: Engine → Rules → ROM →
  Rulebook) and the project's three named roles (`glossary.md`: ROM Developer, Rulebook Author, World
  Builder) imply a three-checkpoint chain, not two — the pilot added `RM-0012`/`RM-0013` to model
  this. Whether that third checkpoint belongs in the ratified model, or was a pilot-only backfill, is
  undecided. Related: `RM-0013` is `reached` on a single case (OneD20 only) — real multi-Rulebook
  reusability is untested and explicitly deferred per `phase-2-7-1.md`/`non-goals.md`, so this
  convergence node's evidentiary bar is weaker than its siblings'. Worth a real governance answer
  (§7) before ratification, not just a pilot footnote.
- **New, from the same pilot:** non-goals (`Documents/design/non-goals.md`) deliberately stay out of
  the graph rather than being modeled as parked/deferred nodes — `frontier`'s `open` status has no way
  to express "known, scoped, explicitly not actionable yet" without either misrepresenting them as
  pickable or inventing a new status value nothing else here needed. Decided against for now; revisit
  only if a real case makes the omission actively costly, same trigger-based discipline `non-goals.md`
  already holds everything else to.

## Related pages

- [RoadmapGraph space index](../index.md)
- [Overview / brochure](overview.md)
- [Node format spec](Specs/node-format-spec.md)
- [Graph tooling spec](Specs/graph-tooling-spec.md)
- [Migration plan](migration-plan.md)
- [Supreme Leader (PM)](../Roles/supreme-leader.md), [Architect](../Roles/architect.md), [QA](../Roles/qa.md)
- [Ticket 0073](../Processes/Handoffs/0073-rule-compilation-cost-and-runtime-mode.md) — the live case
  this proposal keeps testing itself against
