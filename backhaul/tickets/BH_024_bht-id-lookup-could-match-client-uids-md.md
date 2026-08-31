---
id: BH_024
uid: BH
number: 24
client: BH
status: done
title: bht id lookup could match client-uids.md
context: _find_one_ticket excluded BOARD.md by name but not the registry file; a generic
  prefix like 'c' could match it and crash parsing it as a ticket.
priority: normal
opened: '2026-08-30'
closed: '2026-08-30'
---

<!-- board:start -->
<!-- board:end -->

## Summary

bht id lookup could match client-uids.md

## Log

- 2026-08-30: Fixed: _find_one_ticket now excludes both BOARD.md and client-uids.md by name, matching _cmd_refresh's own exclusion set. Turned out worse than a spurious ambiguous-match: since the registry match was the ONLY match for a prefix like 'c', it was returned as THE ticket and would have crashed on _frontmatter.parse() (client-uids.md isn't a frontmatter doc). Added test_status_id_prefix_does_not_match_client_uids_registry. Full suite green (379).
- 2026-08-30: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
