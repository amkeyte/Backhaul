---
id: BH_019
uid: BH
number: 19
client: BH
status: open
title: Default config resolution ignores checkout, contradicts bht.md
context: bht.md says omit --config for the checkout's own default; for any pip-installed
  consumer project that default resolves relative to the package's own install location,
  not cwd, and always fails. See BKHL_014 (mcRepos).
priority: normal
opened: '2026-08-28'
closed: null
---

<!-- board:start -->
<!-- board:end -->

## Summary

`bht.md`'s CLI cheatsheet says: "`--project <name>` (or `--config <path>`) selects which project's
tickets/board this touches; omit both for **this checkout's own default config**." Every bare
`bht`/`bhw`/`bhrm`/`bhrole` command run tonight from inside a real mcRepos checkout — cwd inside
the repo, `BACKHAUL_LOCAL_ROOT` correctly exported — failed until `--config` was added explicitly.
Surfaced by mcRepos'
BKHL_014 (mcRepos project, not this repo — no working relative link across checkouts).

**Root cause, traced in `cli.py`/`services/*/cli.py`'s shared `_resolve_config_path`:** the
no-flag fallback is `Path(__file__).resolve().parents[N] / "config" / "config.local.json"` —
relative to wherever the `backhaul` *package* is physically installed, not to cwd and not to
anything under the actual checkout being worked on. This only ever resolves correctly in one
specific scenario: running the CLI directly against Backhaul's own source checkout without
installing it (`python3 -m backhaul...` from inside this repo, `__file__` pointing at this repo's
own tree) — exactly this session's own dogfooding pattern. For any pip-installed consumer project
(every real project — mcRepos, LunaFlow_A), `parents[N]` resolves somewhere under Python's install
prefix, which never has that project's `config.local.json`, so the bare default is not an edge
case that sometimes fails for consumers — it cannot ever succeed for them as currently built.

## Suggested direction, not a committed design

Two independent ways to close this, either sufficient alone — BKHL_014 deliberately doesn't assert
which is correct, and this ticket doesn't either:

1. **Make the no-flag default search upward from cwd** for a `config.local.json` under a
   `backhaul/` (or similarly named) directory, the way `git` finds `.git` — so "this checkout's own
   default config" becomes literally true for a consumer project too, not just for running against
   this repo's own source. Genuinely useful beyond just fixing the doc: `cd` into a project and run
   bare `bht`/`bhrm` without needing `--config` every time.
2. **If today's behavior (config lives next to wherever the package is installed, full stop) is
   intentional** — e.g. deliberately supporting a machine with several unrelated checkouts and no
   single "current" one — fix `bht.md`'s wording instead, since the doc is what's wrong in that
   case, and say plainly that consumer usage always needs `--project`/`--config`.

Worth checking whether this is genuinely a per-service `_resolve_config_path` (duplicated near-
identically across `cli.py`, `services/ticket/cli.py`, `services/wiki/cli.py`,
`modules/roadmap/cli.py`, `modules/roles/cli.py`) or worth consolidating into `foundation` while
fixing it, since the same fix would otherwise need applying five times.

## Log

- 2026-08-28: Ticket opened.
<!-- bh-header:start -->
**Fronthaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:////sessions/vigilant-magical-hamilton/mnt/Backhaul/backhaul)
<!-- bh-header:end -->
