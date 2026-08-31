---
id: BH_022
uid: BH
number: 22
client: BH
status: done
title: CLI main() didn't catch ConfigError
context: All 5 CLIs dumped a raw traceback on a bad config/unknown --project. Found
  via full review.
priority: normal
opened: '2026-08-30'
closed: '2026-08-30'
---

<!-- board:start -->
<!-- board:end -->

## Summary

Found during a full-codebase review (2026-08-30). None of `bht`, `bhw`, `bhrm`, `bhrole`, or
`backhaul`'s `main()` caught `foundation.config.ConfigError` or `foundation.projects.ProjectsError`
— a missing/malformed `config.local.json`, a config with the wrong schema version, or an unknown
`--project` name all dumped a full Python traceback instead of a clean `FAIL: ...` message.
`bhrm`/`bhrole` already wrapped `args.func(args)` to catch their own domain-specific
`RoadmapCliError`/`RolesCliError`, but not these two upstream exception types; `bht`/`bhw`/
`backhaul` didn't wrap anything at all. Verified empirically (`bht open` against a nonexistent
config path produced a full traceback; exit code was still 1, so scripted callers checking the
exit code weren't broken — only the error message was bad).

## Suggested direction

Add `ConfigError`/`ProjectsError` to each CLI's existing (or new) `except` clause around
`args.func(args)` in `main()`, printing `FAIL: {e}` to stderr and returning 1 — same treatment
every CLI already gives its own domain errors.

## Log

- 2026-08-30: Fixed: wrapped args.func(args) in all 5 main() functions to catch ConfigError/ProjectsError (bhrm/bhrole's existing except clauses extended, bht/bhw/backhaul got a new one), printing FAIL: and returning 1. Added regression tests to test_cli.py, test_wiki_cli.py, test_roadmap_cli.py, test_roles_cli.py, test_dashboard.py (missing-config + unknown---project cases); updated 4 existing tests that had asserted ProjectsError propagates uncaught, since that was the exact bug. Full suite green (377 passed).
- 2026-08-30: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
