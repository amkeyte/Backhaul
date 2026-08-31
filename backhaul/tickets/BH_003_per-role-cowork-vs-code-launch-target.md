---
id: BH_003
uid: BH
number: 3
client: BH
status: done
title: Per-role Cowork vs Code launch target
context: build_code_link() exists, unused. launch.py hardcodes Cowork. See ticket
  body for design.
priority: normal
opened: '2026-08-13'
closed: '2026-08-30'
---

<!-- board:start -->
<!-- board:end -->

## Summary

Per-role Cowork vs Code launch target

## Log

- 2026-08-30: Implemented per user's decision (2026-08-30): new launch_target: cowork|code role frontmatter field (schema.py, default cowork), --launch-target flag on bhrole new, launch.build_launch_link() picks build_cowork_link vs the previously-unused build_code_link based on it. Tests added to test_roles.py/test_roles_cli.py. Documented in wiki/meta/bhrole.md. Full suite green (387).
- 2026-08-13: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
