---
id: BH_010
uid: BH
number: 10
client: BH
status: done
title: bht status vocabulary not validated on write
context: 'Six mcRepos tickets carry status: closed, outside BHT''s open/in-progress/blocked/done
  vocabulary, and nothing rejected it. See BKHL_006 (mcRepos).'
priority: low
opened: '2026-08-24'
closed: '2026-08-28'
---

<!-- board:start -->
<!-- board:end -->

## Summary

[BHT — Ticket Conventions](../wiki/meta/bht.md) defines the lifecycle as
`open -> in-progress | blocked -> done`. Nothing in `bht open`/`bht close` (or anywhere else on the
write path) rejects a status outside that set. Surfaced by mcRepos'
BKHL_006 (mcRepos project, not this repo — no working relative link across checkouts): six tickets there carried
`status: closed` — harmless today only by accident (`bht board` happens to filter *for* the open-ish
states, so `closed` falls off the board the same way `done` does) — but any future consumer that
asks "was this verified" by matching on `done` gets a silently wrong answer for a `closed` ticket.
Project owner's call on that instance: no distinct meaning intended, normalize and move on — but the
underlying gap (nothing validates on write) is real and should be closed structurally, not just
patched by hand each time it recurs.

## Suggested direction, not a committed design

- `bht open`/`bht close` should validate `status` against the documented vocabulary the same way
  `bhrm` already validates its own kind-dependent vocabulary (`WORK_STATES` / `CONVERGENCE_STATES`
  in `modules/roadmap/schema.py`) — reject on write rather than silently accepting anything.
- Worth deciding whether this also becomes a `backhaul lint` check (flag any existing ticket with an
  out-of-vocabulary status) so a hand-edited or agent-written file that bypassed the CLI still gets
  caught later, not just at `bht open`/`close` time.

## Log

- 2026-08-28: Superseded by BH_017 -- status validation on write already covers open/close; the real gap was the missing in-progress/blocked transition command, which bht status now provides. Closing as a duplicate rather than shipping redundant validation.
- 2026-08-24: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
