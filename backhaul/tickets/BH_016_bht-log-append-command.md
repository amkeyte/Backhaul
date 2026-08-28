---
id: BH_016
uid: BH
number: 16
client: BH
status: open
title: bht log-append command
context: open/close are the only write verbs; every dated Log entry today is a hand-edit
  against fragile exact-string anchors. See BKHL_011 (mcRepos).
priority: normal
opened: '2026-08-28'
closed: null
---

<!-- board:start -->
<!-- board:end -->

## Summary

`bht`'s write surface is `open` and `close` only. Every dated `## Log` entry in between — which is
most of what a real ticket's history actually is, given BHT's own convention that a ticket's
history lives in its log, not the wiki — has no CLI path at all, and has to happen as a raw
markdown edit against the live file. Surfaced by mcRepos'
BKHL_011 (mcRepos project, not this repo — no working relative link across checkouts): a single
Lead Dev session wrote five dated log entries by hand in one sitting, two of the five failing on
the first try (one from an indentation mismatch, one from a live re-read showing the anchor text
wasn't quite what static reasoning about the file predicted) — recoverable, but real risk for zero
benefit when the fix is mechanical.

## Suggested direction, not a committed design

- `bht log <id> --entry "..."` — appends a new `- YYYY-MM-DD: <entry>` line to that ticket's
  `## Log` section, dated from the CLI's own clock (not caller-supplied), so no exact-string
  anchor is ever needed for the common case.
- Multi-paragraph entries are the common case in practice, not the exception — worth accepting
  `--entry-file <path>` or reading multi-line input from stdin, rather than forcing every entry
  into one CLI string argument.
- Scope: `services/ticket/cli.py` (new subcommand), `services/ticket/` write helper (find the
  `## Log` heading, append after it — same shape as `_cmd_close`'s existing frontmatter-write
  pattern, just targeting the body instead), tests, `wiki/meta/bht.md`.

## Log

- 2026-08-28: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
