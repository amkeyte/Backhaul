---
id: BH_025
uid: BH
number: 25
client: BH
status: open
title: 'Dead stub modules: version_check.py, refs.py'
context: Both fully NotImplementedError, 0% coverage, nothing calls them. Implement
  or remove -- open question.
priority: normal
opened: '2026-08-30'
closed: null
---

<!-- board:start -->
<!-- board:end -->

## Summary

Found during a full-codebase review (2026-08-30). Two foundation modules are pure scaffolding
left over from the original migration design docs, never finished and never wired up:

- `foundation/version_check.py`: both `read_version()` and `check_version_drift()` raise
  `NotImplementedError` unconditionally. Docstring points at `migration/MIGRATION_PLAN.md §6`
  for the intended design (a VERSION marker file + a git-diff drift check against what a
  machine's `config.local.json` last recorded).
- `foundation/refs.py`: `Ref.resolve()` raises `NotImplementedError` unconditionally, per its
  own docstring pointing at `migration/ARCHITECTURE.md` — meant to resolve a typed
  ticket/wiki cross-reference to a display string or path without either service needing to
  expose its internals to the other, but the dispatch was never built.

Confirmed via grep and a coverage run: nothing in the codebase imports or calls either module's
functions — 0% test coverage on both, not because they're untested but because there's nothing
exercising them at all. Not a live bug (nothing breaks today), but dead weight: a reader hitting
either file reasonably assumes it's live infrastructure.

## Open question

Implement per the original design, or remove now that the features they were meant to support
(config-version drift warnings, cross-service Ref resolution) haven't been needed in practice —
deliberately not decided here, since it's a product call (is this still wanted?) not an
engineering one.

## Log

- 2026-08-30: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
