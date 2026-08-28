---
id: BH_012
uid: BH
number: 12
client: BH
status: open
title: bhrm render --output ignores file extension
context: render writes markdown regardless of --output's extension; pointing it at
  a .html path silently clobbers a generated HTML graph with no warning, exit 0. Hit
  live in mcRepos, both graphs clobbered once. See BKHL_008 (mcRepos).
priority: normal
opened: '2026-08-24'
closed: null
---

<!-- board:start -->
<!-- board:end -->

## Summary

`bhrm render --uid X --output PATH` always writes markdown; `bhrm index` writes the HTML graph
(`ROADMAP_GRAPH_<UID>.html`) as a side effect. `render` never looks at `--output`'s extension, so
pointing it at a `.html` path succeeds — `OK: wrote render to ...`, exit 0 — while silently replacing
a generated SVG graph with a flat markdown file that happens to share the extension. Hit live in
mcRepos (BKHL_008 (mcRepos project, not this repo — no working relative link across checkouts)): both
`ROADMAP_GRAPH_*.html` files got clobbered this way, caught only by diffing against a copy taken
beforehand. The failure is silent and the damage lands on a file that carries a "generated, do not
hand-edit" notice, so it wouldn't get a second look in review either.

## Suggested direction, not a committed design

- Refuse the mismatch: if `--output` ends in `.html`, error with a pointer to `bhrm index` rather
  than silently writing markdown into it. Erroring beats guessing at intent.
- Document the split explicitly in `wiki/meta/bhrm.md`'s CLI cheatsheet — it currently lists
  `render` and `index` without saying which produces what.
- Worth a quick check whether `bhw`/`bht`/`bhrole` have any output-path command with the same shape
  before closing this out — BKHL_008 only looked at `bhrm`.

## Log

- 2026-08-24: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
