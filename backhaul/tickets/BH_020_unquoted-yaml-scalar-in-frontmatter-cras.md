---
id: BH_020
uid: BH
number: 20
client: BH
status: done
title: Unquoted YAML scalar in frontmatter crashes CLI project-wide
context: A title containing an unquoted colon-space breaks yaml.safe_load with no
  file context in the error; since board/open scan every ticket, one bad file takes
  down the CLI for the whole project. High priority -- confirmed live crash. See BKHL_016
  (mcRepos).
priority: high
opened: '2026-08-28'
closed: '2026-08-28'
---

<!-- board:start -->
<!-- board:end -->

## Summary

`bht board` (and `bht open`, which rebuilds the board as a side effect) crashed with
`yaml.scanner.ScannerError: mapping values are not allowed here` on an unrelated ticket open, in
mcRepos. Root cause: a ticket's frontmatter had an unquoted title containing `: ` (colon-space) —
`title: Border load count: client vs server` — which YAML reads as the start of a second mapping
key inside the value position. `foundation/frontmatter.py`'s `parse()` hands the raw YAML straight
to `yaml.safe_load` with no defense against this, so one malformed file anywhere in the tickets
folder takes down `board`/`open` — two of the most frequently run commands — for the entire
project, not just reading that one file, and the raw traceback gives no file-path context to find
the offending file from. Surfaced and fixed live by hand (quoted the string directly) in mcRepos'
BKHL_016 (mcRepos project, not this repo — no working relative link across checkouts), marked high
priority there since it's an active crash, not a hygiene gap.

## Suggested direction, not a committed design

Two independent hardening items, both worth doing:

1. **Writers should always emit quoted string scalars for free-text fields** (`title`, `context`,
   any other user-supplied string) rather than relying on the value happening to be YAML-safe
   unquoted. This specific crash couldn't have happened if the tool itself had quoted the title at
   creation time — applies to `bht open`, `bhw new`, `bhrm new`, `bhrole` equivalents, wherever
   `foundation`'s shared templating/frontmatter-write helper is used.
2. **`frontmatter.parse()` should catch `yaml.YAMLError` and raise a `FrontmatterParseError` naming
   the offending file path**, rather than letting a raw YAML traceback with no file context surface
   to the CLI user. A rollup over dozens of files with one bad apple currently gives no clue which
   file is the problem short of manual binary-search reasoning.

## Log

- 2026-08-28: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
