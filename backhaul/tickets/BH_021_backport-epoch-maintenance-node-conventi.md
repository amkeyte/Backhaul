---
id: BH_021
uid: BH
number: 21
client: BH
status: open
title: Backport epoch-maintenance-node convention to defaults
context: mcRepos worked out a real convention for unplanned rework containers on the
  roadmap graph, live, over several rounds -- worth landing in Backhaul's own default
  docs/templates so future projects don't re-derive it. See BKHL_017 (mcRepos).
priority: normal
opened: '2026-08-28'
closed: null
---

<!-- board:start -->
<!-- board:end -->

## Summary

mcRepos worked out, live over several rounds of real usage, a roadmap convention this project's
own tickets had been silently needing: a formal place on the graph for unplanned rework/health/
review-fix work that doesn't belong on a persona-named feature node but was previously only
discoverable by searching tickets. Full writeup landed in mcRepos'
`wiki/meta/bhrm.md#epoch-maintenance-nodes-containers`, per
BKHL_017 (mcRepos project, not this repo — no working relative link across checkouts). Worth
landing in Backhaul's own default docs/templates so a future project gets this pattern without
re-deriving it live the way mcRepos just did — same "found in the field, backport to defaults"
shape as BKHL_008 → BH_012.

## The convention, as landed in mcRepos

- An **epoch** is the span between two convergence nodes, named for the one that opens it.
- A **maintenance container** is an ordinary `kind: work` node, no schema change needed — slugged
  `<epoch>-01`/`<epoch>-02`/etc. instead of a persona name, `ticket: null`, with what actually
  landed on it tracked in its own log.
- Every epoch gets two standing containers by default (start, end/"review-fix" — the epoch's next
  planned node depends on the end container clearing), plus as many middle containers as an
  epoch's actual rework warrants.
- `depends_on` wiring onto a container is real and blocking wherever it lands, including reopening
  an already-`resolved` node when a container's work casts real doubt on its done bar.
- A container's own `status` tracks whether it's currently blocking anything, not whether every
  ticket ever logged on it is closed — `resolved` means "nothing currently gating downstream
  remains open," non-blocking follow-up content can stay open and logged underneath. mcRepos
  adopted an interim `Deferred, non-blocking:` callout convention for this — worth keeping as
  documentation practice regardless of what the status vocabulary below decides.

## Suggested direction, not a committed design

Three things left open by mcRepos deliberately, worth an opinion here rather than there:

1. Whether this stays a pure documentation/naming convention on plain `work` nodes, or earns a
   first-class `kind: maintenance` with its own reversible status pair (proposed:
   `collecting <-> clear`, mirroring convergence's `WIP <-> reached`) — structural instead of a
   documentation habit, plus its own graph color/shape in `render_html()`'s output. mcRepos
   deliberately deferred building this; worth an opinion once more than one project has used the
   plain-`work` version, not before.
2. Whether `bhrm new` should grow a shortcut for creating the standing start+end container pair
   together, once there's evidence the pattern holds up outside mcRepos.
3. If `kind: maintenance` does land, whether it needs its own advisory checks (a
   `convergence-bypass`-style one, or reuse the existing convergence one) — not scoped here.

Not urgent — mcRepos' plain-`work` version already works today; this is about giving the next
project the pattern without a live re-derivation, not fixing something broken now.

## Log

- 2026-08-28: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
