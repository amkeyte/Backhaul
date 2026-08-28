---
id: BH_018
uid: BH
number: 18
client: BH
status: open
title: bht open should warn on oversized title/context
context: bht.md's own 40/100-char guideline isn't checked on write; nothing signals
  a caller went over until someone eyeballs the rendered board. See BKHL_013 (mcRepos).
priority: low
opened: '2026-08-28'
closed: null
---

<!-- board:start -->
<!-- board:end -->

## Summary

`bht.md`'s own length standard (title ≤ ~40 chars, context ≤ 100) exists because `BOARD.md` renders
both as table columns that wrap awkwardly when they're blown past. It's explicitly documented as a
target, not a hard rule — real detail sometimes needs the room, and the doc already says to push it
into the ticket body instead. But nothing checks it at all: `bht open` gives no feedback either
way, so a value that quietly blew past the guideline only ever surfaces later, by eyeballing the
rendered board. Surfaced by mcRepos'
BKHL_013 (mcRepos project, not this repo — no working relative link across checkouts): manually
counting characters against a CLI argument before running it is exactly the kind of check a tool
should do for you.

## Suggested direction, not a committed design

- A soft warning only, printed to stderr, that doesn't block the write: something like
  `warning: title is 52 chars (guideline: ~40) -- consider shortening or moving detail to the
  ticket body`. Keeps the "target, not a hard rule" intent intact while closing the actual gap —
  right now nothing says anything, ever, even when a value is dramatically over.
- Scope: `services/ticket/cli.py`'s `_cmd_open` (length check after building the ticket, before or
  after write — doesn't need to block either way), tests.

## Log

- 2026-08-28: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
