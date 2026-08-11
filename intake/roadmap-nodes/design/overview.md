# The Roadmap, Rebuilt: From a List to a Map

> **WIP — this is a proposal under active design, not a ratified process.** Nothing here changes
> how `CLAUDE.md`, `wiki-style.md`, `roadmap.md`, or the ticket system actually work today. See
> [`../index.md`](../index.md) for this space's status and [`proposal.md`](proposal.md) for the full
> design this brochure summarizes.

## The problem, in one sentence

The phase number was carrying two jobs at once — "when this was created" and "what order it
happens in" — and the second job kept breaking the first. 2.6.5. 2.7.1. Three siblings crammed into
2.10–2.12 because a proposal happened to land after 2.9. Every one of those is the same symptom:
dependency order doesn't actually fit in a flat sequence, and we kept forcing it to anyway.

## The pitch

Stop planning a line. Plan a map.

Every unit of work — a build ticket, a design ruling, a fix — becomes a node. Every real dependency
between nodes is declared explicitly, and revised the moment our understanding of it improves.
Nothing gets a position in a sequence. Everything just connects to what it actually needs.

## What that buys us

**Insertion is free.** Need to redo something three phases back? Add a node, point its dependency
where it belongs, done. Nothing else moves. Nothing else renumbers. No cascading edits through docs
that were already closed out.

**"What's next" becomes a query, not a debate.** At any moment, the actionable menu is exactly the
set of nodes whose dependencies are already satisfied — no more scanning a sequence table trying to
remember whether the next phase secretly needs something from a sibling that hasn't shipped yet.

**The big milestones fall out for free.** "ROM Developer operational." "World Builder operational."
These aren't a separate tier bolted on top of the graph — they're just nodes with a lot of edges
pointing into them, converging from everything underneath. We call these **convergence nodes**, and
they're the same kind of thing as any other node, just with more weight resting on them.

**It matches how the architecture already works.** This isn't a new philosophy grafted onto the
project — it's the same dependency discipline `ComponentRegistry` already enforces on ROMs, one
level up. A Rulebook can't touch the Engine directly; "World Builder operational" can't be reached
before "ROM Developer operational" is — same reason, same shape. We're not inventing a principle
here, we're finally writing down the one the codebase already runs on.

**Fixes gravitate to where they actually belong.** When something breaks, the graph gives us a real
question to ask before touching anything: what's the least invasive node this can be repaired at,
before escalating up toward a tier boundary? That's not a new rule — it's what already happened the
last time a cross-ROM dependency problem surfaced. Now it's a stated principle instead of a lucky
accident.

**Claims stay traceable, without cluttering the prose.** Any design doc stating a load-bearing fact
about the system — "the rule pipeline compiles through Roslyn," say — cites the node that established
it, gathered in a references list at the bottom of the doc rather than inline. When that node is
later deprecated, finding everything that assumed it true is a search, not a memory test.

**Convergence nodes can un-converge, on purpose.** A regular node's history never changes — "this
build passed QA on this date" stays true forever, even if a later stress test finds a gap underneath
it. But a convergence node isn't a historical record, it's a live claim: "the ground here is
currently solid enough to build the next tier on." If that stops being true, the node has to be able
to say so — reverting to work-in-progress, which mechanically freezes whatever depends on it, without
erasing the permanent record of when it was reached before. A milestone that can never un-converge
isn't a gate, it's a plaque.

## What doesn't change

- Tickets still work exactly like they do today — same numbering, same lifecycle, same index. Most
  of them stay exactly what they already are: a conversation between two roles about one finding.
- The graph sits alongside that, as its own small, separately-numbered set of nodes marking what's
  actually roadmap-load-bearing. It never gets buried the way a ticket-index page eventually does
  once it's grown too long to skim.
- One script does the reading — not four. Whether the question is "what's actionable right now,"
  "what breaks if I deprecate this," or "what's blocking this from starting," it's the same graph,
  walked in a different direction.

## What's coming

A generated index — names only, no clutter — that lists what's actionable right now at the top, and
lets the rest of the dependency structure be crawled like a map instead of held in memory. Built as a
real graph underneath, not just a list with grep tricks, so the eventual visual version — the one
that shows where the actual edge of the project is, for making direction calls — is a second renderer
on the same data, not a second system built from scratch later.

## Related pages

- [RoadmapGraph space index](../index.md)
- [Full proposal](proposal.md)
- [Node format spec](Specs/node-format-spec.md)
- [Graph tooling spec](Specs/graph-tooling-spec.md)
- [Migration plan](migration-plan.md)
