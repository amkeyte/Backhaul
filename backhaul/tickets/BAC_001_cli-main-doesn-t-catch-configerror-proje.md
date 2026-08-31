---
id: BAC_001
uid: BAC
number: 1
client: Backhaul
status: done
title: CLI main() doesn't catch ConfigError/ProjectsError
context: All 5 CLIs (bht, bhw, bhrm, bhrole, backhaul) dump a raw traceback on a missing/malformed
  config or unknown --project, instead of a clean FAIL. Found via full-codebase review.
priority: normal
opened: '2026-08-30'
closed: '2026-08-30'
---

<!-- board:start -->
<!-- board:end -->

## Summary

CLI main() doesn't catch ConfigError/ProjectsError

## Log

- 2026-08-30: Mis-minted: --client Backhaul auto-suggested a fresh UID (BAC) instead of reusing this project's own established BH UID. Superseded by a correctly-numbered ticket opened under --client BH. Closing without further action.
- 2026-08-30: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul/backhaul)
<!-- bh-header:end -->
