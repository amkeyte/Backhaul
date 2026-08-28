---
id: BH_014
uid: BH
number: 14
client: BH
status: open
title: backhaul refresh orchestrator command
context: No single entry point runs bht board + bhw index + bhrm index + bhrole index
  + backhaul dashboard + lint together -- the current five-commands-plus-remember-the-sixth
  shape is what keeps going stale. See BKHL_007 (mcRepos).
priority: normal
opened: '2026-08-24'
closed: null
---

<!-- board:start -->
<!-- board:end -->

## Summary

Refreshing a project today means remembering to run `bht board`, `bhw index`, `bhrm index`,
`bhrole index`, and `backhaul dashboard` separately — `wiki/meta/bhrole.md` already documents the
exact failure mode this produces ("refreshing the sub-indexes without refreshing the root dashboard
is how `BACKHAUL.md` silently goes stale while everything underneath it looks fine"), and per
mcRepos' BKHL_007 (mcRepos project, not this repo — no working relative link across checkouts), it has now happened
twice against a documented warning. The rule is correct and not being followed, which means the
problem isn't that people don't know it — it's that the five/six-command shape itself is the failure
mode.

## Suggested direction, not a committed design

- A single `backhaul refresh` command that runs `bht board`, `bhw index`, `bhrm index`,
  `bhrole index`, `backhaul dashboard`, and `backhaul lint` (advisory, non-blocking — same framing as
  `convergence-bypass`) in order.
- Should work whether or not every module is enabled for a given project — skip cleanly rather than
  error on a project with `enabled_modules: []` for roadmap/roles.
- Once BH_015 (lint historical-link marker) lands, `refresh` running lint by default becomes safe to
  treat as routine rather than optional — worth sequencing BH_015 first or alongside this.
- Scope: likely a new top-level `cli.py` entry point that shells out to (or directly calls) each
  service's own CLI function, tests, `wiki/meta/backhaul.md` (top-level CLI docs).

## Log

- 2026-08-24: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
