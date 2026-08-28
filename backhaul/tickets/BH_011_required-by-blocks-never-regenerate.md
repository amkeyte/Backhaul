---
id: BH_011
uid: BH
number: 11
client: BH
status: open
title: Required By blocks never regenerate
context: dependents() is computed correctly by bhrm but never written back into a
  node's Required By section, so it goes stale silently (confirmed wrong on ~10 real
  mcRepos nodes). See BKHL_005 (mcRepos).
priority: normal
opened: '2026-08-24'
closed: null
---

<!-- board:start -->
<!-- board:end -->

## Summary

`modules/roadmap/graph.py`'s `dependents()` computes the correct answer for "what depends on this
node" today. Nothing writes that answer back into a node's own `Required By` section, so the prose
in the file is whatever was true (or hand-typed) whenever someone last touched it — and it goes
stale silently, with no signal anything's wrong. Surfaced by mcRepos'
BKHL_005 (mcRepos project, not this repo — no working relative link across checkouts): confirmed wrong on roughly
ten real `RM_FRO` nodes, several flatly claiming "nothing depends on this" when something does.

This is the same shape BH_009 (slug-in-html) and the codebase's own "computed, not stored"
convention already establish for `Visualize` and node slugs — the fix is regeneration on refresh,
not a smarter human process.

## Suggested direction, not a committed design

- Wire `dependents()` into the same marked-block mechanism `bh-header` already uses (a
  `<!-- required-by:start -->` / `<!-- required-by:end -->` pair, rewritten unconditionally on
  `bhrm index`/`refresh`, matching BH_008's "unconditional rewrite is the point" precedent for the
  HTML graphs).
- Scope: `modules/roadmap/graph.py` (write-back helper), `modules/roadmap/cli.py` (`index`/`refresh`
  call it per node), tests, `wiki/meta/bhrm.md`.
- Open question: does this replace the current freehand `Required By` prose entirely, or does the
  marked block sit alongside author-written context the same way other marked sections do elsewhere
  in this codebase? Worth deciding before implementing rather than guessing.

## Log

- 2026-08-24: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
