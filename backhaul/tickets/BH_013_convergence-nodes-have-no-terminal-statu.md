---
id: BH_013
uid: BH
number: 13
client: BH
status: open
title: Convergence nodes have no terminal status
context: 'Convergence kind only has WIP/reached -- a deprecated-but-kept convergence
  has nowhere terminal to go, and superseded_by is stored but never checked for staleness.
  Project owner''s call: reuse superseded for both work and convergence kinds. See
  BKHL_004 (mcRepos).'
priority: normal
opened: '2026-08-24'
closed: null
---

<!-- board:start -->
<!-- board:end -->

## Summary

`CONVERGENCE_STATES` currently only has `WIP`/`reached` — a reversible pair (see `ReachedLog`), with
no terminal state at all. Two real gaps fall out of that, both surfaced by mcRepos'
BKHL_004 (mcRepos project, not this repo — no working relative link across checkouts):

1. A convergence node that gets deprecated but kept (for history, per this codebase's own
   "don't rewrite history" convention) has nowhere terminal to land — it's stuck oscillating between
   `WIP` and `reached` forever, which reads as "still actionable" to anything that queries the graph.
2. `superseded_by` is stored on a node's frontmatter but nothing reads it back — a reference to a
   node that's since been superseded gets no warning anywhere.

**Project owner's decision (2026-08-24): reuse `superseded` for both `work` and `convergence` kinds**
rather than adding a convergence-specific terminal status name.

## Suggested direction, not a committed design

- Add `superseded` to `CONVERGENCE_STATES` in `modules/roadmap/schema.py`, terminal (like `work`'s
  own `superseded`/`resolved` — check `WORK_STATES` for the exact validation shape already in use).
- New advisory check, sibling to `find_convergence_bypasses()`: walk all nodes' `superseded_by`
  references and flag any that point at a node whose own status shows it was in fact superseded (or
  any dangling reference to a node that no longer exists) — same "advisory, not blocking" framing as
  `convergence-bypass`.
- Scope: `modules/roadmap/schema.py` (vocabulary), `modules/roadmap/graph.py` (stale-reference
  check), `modules/roadmap/cli.py` (new subcommand, or fold into `lint`/`refresh` once BH_014/BH_015
  land), tests, `wiki/meta/bhrm.md`.

## Log

- 2026-08-24: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
