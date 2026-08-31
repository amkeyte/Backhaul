---
id: BH_015
uid: BH
number: 15
client: BH
status: done
title: lint needs a historical-link marker convention
context: 'Two permanent classes of correct-but-flagged content mean lint''s broken-link
  count can never reach zero: illustrative link syntax in prose, and deliberately-dangling
  links to intentionally-retired pages (don''t-rewrite-history convention). An explicit
  marker beats a per-path ignore list. See BKHL_007 (mcRepos).'
priority: normal
opened: '2026-08-24'
closed: '2026-08-28'
---

<!-- board:start -->
<!-- board:end -->

## Summary

`backhaul lint`'s broken-link check (BH_004) is doing real work — mcRepos'
BKHL_007 (mcRepos project, not this repo — no working relative link across checkouts) confirms it surfaced every
finding from a manual doc audit in one command, plus several nobody had caught. But that same ticket
identifies two permanent classes of false positive that mean the broken-link count can never reach
zero as things stand:

1. **Illustrative link syntax in prose** — a worked markdown-link example (title in brackets,
   placeholder path in parens) used to *show* the link syntax, not create a real link. `lint`
   correctly can't tell the two apart today.
2. **Deliberately-dangling historical links** — this project's own "don't rewrite history" convention
   means a closed ticket's log can correctly keep pointing at a page that was intentionally deleted
   afterward. There will always be more of these; every future retirement adds one.

mcRepos' own workaround on 2026-08-21 (un-link the three known instances, keep the text, drop the
link syntax) works but is lossy — the reader can no longer tell the phrase ever named a real page,
and it relies on someone remembering to do it by hand at every future retirement. Worth building the
real thing instead of relying on the workaround indefinitely.

## Suggested direction, not a committed design

- An explicit marker convention (not a per-path ignore list — semantically distinct content should
  say so in the content, and an ignore list grows unboundedly with every retirement). Something like
  a recognizable inline annotation on the link itself that `find_broken_links()` treats as "known,
  intentionally unresolved" and skips, while the link stays visible as a link to a human reader.
- Needs a decision on exact marker syntax before implementing — should be visually unobtrusive in
  rendered markdown, greppable, and unambiguous from a real broken link.
- Related, lower priority, don't build speculatively: BKHL_007 also flags that `bhw`'s two wiki
  conventions (no changelog content, no status prose) keep drifting back after being fixed by hand,
  and suggests a cheap heuristic lint check for dated status markers on wiki pages. Worth revisiting
  once the marker convention above exists and `backhaul refresh` (BH_014) makes lint routine, not
  before.
- Scope: `foundation/lint.py` (`_LINK_RE`/`find_broken_links()`), tests, `wiki/meta/bhw.md` (document
  the marker convention itself), `wiki/meta/backhaul.md` (lint docs).

## Log

- 2026-08-24: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
