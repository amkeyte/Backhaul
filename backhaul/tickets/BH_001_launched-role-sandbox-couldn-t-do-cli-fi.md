---
id: BH_001
uid: BH
number: 1
client: BH
status: done
title: Launched-role sandbox couldn't do CLI file I/O against Windows content_roots
context: 'A role launched into a Cowork sandbox (mcRepos) reinstalled the CLI via
  repo_url fine, but content_roots (Windows paths) don''t resolve on Linux, so writes
  silently no-op or land at cwd. Fixed in two stages: (1) load_config() fail-loud
  validation rejects non-absolute content_roots instead of writing to the wrong place
  (task #76). (2) BACKHAUL_LOCAL_ROOT env var re-roots content_roots onto wherever
  the project is actually mounted this session, applied before the fail-loud check
  runs (task #77). Live-verified against the real mcRepos config: with the guardrail,
  the session hit a clean ConfigError (confirming #76 works); after export BACKHAUL_LOCAL_ROOT=<mount
  path> + pip install --upgrade --force-reinstall to pick up the fix, bht board wrote
  correctly to backhaul/BOARD.md with correct host_root-translated links, no stray
  files. Documented in README.md ''BACKHAUL_LOCAL_ROOT'' section and bht.md/bhw.md/bhrole.md
  meta pages. ID-minting concurrency (multiple sessions creating tickets/nodes at
  once) remains an accepted, unaddressed gap.'
priority: normal
opened: '2026-08-11'
closed: '2026-08-11'
---

<!-- board:start -->
<!-- board:end -->

## Summary

Launched-role sandbox couldn't do CLI file I/O against Windows content_roots

## Log

- 2026-08-11: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_LocalFiles/source/repos/Backhaul)
<!-- bh-header:end -->
