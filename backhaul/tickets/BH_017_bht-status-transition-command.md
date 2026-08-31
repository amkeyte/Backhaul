---
id: BH_017
uid: BH
number: 17
client: BH
status: done
title: bht status-transition command
context: open always starts at open, close always ends at done -- in-progress/blocked
  have no command, only hand-edited frontmatter. Same root cause as BH_010. See BKHL_012
  (mcRepos).
priority: normal
opened: '2026-08-28'
closed: '2026-08-28'
---

<!-- board:start -->
<!-- board:end -->

## Summary

`bht.md` documents the lifecycle as `open -> in-progress | blocked -> done`, but `bht`'s only
write verbs are `open` (always starts at `open`) and `close` (always ends at `done`). The two
middle states have no command at all — the only way to set them is hand-editing `status:` in a
ticket's frontmatter directly. Surfaced by mcRepos'
BKHL_012 (mcRepos project, not this repo — no working relative link across checkouts): same root
cause as BH_010 (bht status vocabulary not validated on write), seen from the write-verb side
rather than the validation side — if `bht` had a real command for every documented lifecycle
value, hand-editing frontmatter would stop being the *normal* path for two out of four states, not
just the accidental path for one.

## Suggested direction, not a committed design

- `bht status <id> <in-progress|blocked|open>` — validated against BHT's documented vocabulary,
  rejecting anything else (this becomes the natural place BH_010's validation logic lives once
  both land, rather than two separate implementations).
- Worth deciding at implementation time whether `blocked` should accept a `--reason`, mirroring how
  `close` records a closed date — not asserted here.
- Scope: `services/ticket/cli.py` (new subcommand), `services/ticket/` write helper, tests,
  `wiki/meta/bht.md`. Natural to build alongside BH_010 given the shared vocabulary-validation
  logic.

## Log

- 2026-08-28: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
