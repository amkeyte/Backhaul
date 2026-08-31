---
id: BH_023
uid: BH
number: 23
client: BH
status: done
title: Superseded convergence renders as WIP in HTML graph
context: graph.py _html_color() never got BH_013's superseded status; rendered identical
  to WIP orange-dashed.
priority: normal
opened: '2026-08-30'
closed: '2026-08-30'
---

<!-- board:start -->
<!-- board:end -->

## Summary

Superseded convergence renders as WIP in HTML graph

## Log

- 2026-08-30: Fixed: _html_color() now checks status=='superseded' before the kind split, so a superseded convergence node lands in the same green 'resolved/superseded' bucket a superseded work node already uses, instead of falling through to the orange-dashed WIP bucket. Legend text ('resolved / superseded') already covered this generically, no HTML template change needed. Added test_html_color_convergence_superseded_is_green_not_wip_orange. Full suite green.
- 2026-08-30: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
