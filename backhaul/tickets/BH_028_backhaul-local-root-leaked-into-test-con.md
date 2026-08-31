---
id: BH_028
uid: BH
number: 28
client: BH
status: done
title: BACKHAUL_LOCAL_ROOT leaked into test configs
context: Corrupted tracked fixture data via BH_026 checklist verification.
priority: normal
opened: '2026-08-31'
closed: '2026-08-31'
---

<!-- board:start -->
<!-- board:end -->

## Summary

`foundation/config.py::load_config()` read `BACKHAUL_LOCAL_ROOT` from the process environment
implicitly whenever `local_root` wasn't explicitly passed — including test fixtures' own
tmp_path-based synthetic configs, not just real production configs. Several test fixtures'
content_roots happened to structurally resemble this project's own real `<root>/content/{x}`
convention, so whenever a dev/agent shell had `export BACKHAUL_LOCAL_ROOT=...` set (a normal,
documented workflow) and then ran `pytest` in that same shell, tests that legitimately drive the
CLI through `main()` silently redirected their own tmp_path writes onto this repo's real, tracked
`content/`/`Fronthaul/` fixture directories instead. Surfaced while verifying the BH_026 test
checklist: two full-suite runs under that combination corrupted 125 tracked files (duplicate
roadmap nodes, duplicate tickets) before anyone noticed — nothing failed, files just landed in
the wrong, real place. The project owner cleaned up the resulting mess with a direct commit
("botch repair", `251513a`) once it was caught; this ticket is the actual underlying fix.

## Suggested direction

Two changes, not one — moving the env-var read alone isn't sufficient, since tests that
correctly exercise `main()` (the right way to test CLI behavior) go through the exact same real
entry point a production invocation does:

1. `load_config()` itself stops reading the env var — becomes a pure function driven only by an
   explicit `local_root=` argument.
2. Each CLI's own entry-point layer (`_load_config()`/`_load_enabled_config()` helper) reads the
   env var and passes it through explicitly — so only a genuine CLI invocation is affected by it.
3. Even with (1) and (2), a test that drives `main()` is still a genuine CLI invocation and would
   still be affected by an ambient env var — so a `tests/conftest.py` autouse fixture strips
   `BACKHAUL_LOCAL_ROOT` before every single test, regardless of what any developer's shell has
   exported. This is the layer that actually closes the hole.

## Log

- 2026-08-31: Fixed. foundation/config.py::load_config() no longer reads BACKHAUL_LOCAL_ROOT implicitly (docstring updated to explain why, referencing this ticket). All 5 CLI entry points (backhaul/cli.py, services/ticket/cli.py, services/wiki/cli.py — including its second seed-meta config load — modules/roadmap/cli.py, modules/roles/cli.py) now read the env var explicitly via their own _load_config()/_load_enabled_config() helper and pass it through. Added tests/conftest.py with an autouse fixture stripping the env var before every test, which is what actually closes the gap for main()-driven tests. Updated the two test_foundation.py tests that asserted the old implicit-read behavior to instead confirm it's now ignored without an explicit param (test_load_config_ignores_env_var_without_explicit_param, test_load_config_explicit_param_wins_regardless_of_env_var), and added test_dashboard.py::test_cli_dashboard_applies_backhaul_local_root_env_var confirming the real CLI path still honors the env var end-to-end. Verified by deliberately reproducing the exact hazardous combo (export BACKHAUL_LOCAL_ROOT=... && backhaul refresh && pytest, all in one shell) three times after the fix: 410 passed each time, zero new files under content/Fronthaul, zero content diff vs HEAD. Before the fix, the same combo reliably corrupted tracked fixture data every time. Full suite: 410 passed (was 409; +1 net test after rewriting 2 and adding 1).
- 2026-08-31: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
