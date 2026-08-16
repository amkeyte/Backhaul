---
id: BH_008
uid: BH
number: 8
client: BH
status: done
title: Wire HTML rebuild into roadmap index routine
context: bhrm index/refresh should keep an already-generated ROADMAP_GRAPH_<uid>.html
  current automatically. See body.
priority: normal
opened: '2026-08-16'
closed: '2026-08-16'
---

<!-- board:start -->
<!-- board:end -->

## Summary

Wire HTML rebuild into roadmap index routine

## Full report

Feature request (project owner, 2026-08-16): `bhrm index`/`bhrm refresh` should keep an
already-generated `ROADMAP_GRAPH_<uid>.html` current automatically, instead of requiring a
separate manual `bhrm render-html --uid X --output ...` call per UID that's easy to forget.

Background — this gap is not hypothetical, it was hit directly in real usage. `render_index()`
(BH_005's follow-up) already links to `ROADMAP_GRAPH_<uid>.html` from `ROADMAP_INDEX.md` when
that file exists next to the index — but only *links* to it, never regenerates it. Across one
real work session against mcRepos, the generated HTML silently drifted stale twice (new roadmap
nodes added, the HTML still reflecting the old graph) and both times had to be caught by hand —
comparing node-file mtimes against the HTML's own mtime — before re-running `render-html`
manually. That manual-catch step is exactly the kind of thing that should be automatic.

Open questions, deliberately not resolved here:

- **Always regenerate, or opt-in only for a UID that already has one?** The "maintain what's
  already there" pattern is the safer default — mirrors how `render_index()`'s own link-check
  only looks for the conventional filename rather than assuming every UID wants an HTML view.
  Concretely: on `bhrm index`/`refresh`, for each UID, if `ROADMAP_GRAPH_<uid>.html` already
  exists next to the index, regenerate it in place; if it doesn't exist, leave it absent — never
  force-create a new HTML file for a UID that's never opted in. This seems like the right
  default but is this ticket's suggestion, not a locked decision.
- **`index` only, or `new`/per-node commands too?** `bhrm new` (minting one node) doesn't
  currently touch the index at all — regenerating a whole UID's HTML on every single `new` call
  is a bigger behavior change than doing it as part of `index`/`refresh`, which already
  regenerate the whole aggregate view. Leaning toward `index`/`refresh` only for v1.
  performance is fine either way, worth stating explicitly rather than as an unstated assumption
  someone has to verify — determinism (same graph -> same output) was already load-bearing for
  BH_005's own design.
- **Failure mode:** should a `render_html()` failure (e.g. a graph that fails `validate_graph()`
  for an unrelated UID) block the whole `index`/`refresh` run, or just skip that UID's HTML
  regen with a warning and continue? `bhrm refresh` today already treats a `GraphError` as fatal
  for the whole run (see `_cmd_refresh`'s `except _graph.GraphError` re-raising as
  `RoadmapCliError`) — probably stays consistent with that rather than inventing a partial-
  failure mode just for this.

Suggested shape (not committed): extend `build_index()`/`_cmd_index`/`_cmd_refresh` in
`modules/roadmap/graph.py` / `modules/roadmap/cli.py` — after computing `uids` via
`discover_uids()`, for each uid check `html_graph_filename(uid)` existence next to the index
(the same helper `render_index()`'s link-check already uses) and call `render_html()` again if
present.

Scope: `modules/roadmap/graph.py` (`build_index()`, or a small new orchestration function),
`modules/roadmap/cli.py` (`_cmd_index`/`_cmd_refresh`), tests (a UID with an existing HTML file
gets it regenerated with new content reflected; a UID with none stays without one), docs
(`wiki/meta/bhrm.md`).

Priority: normal — explicitly requested, not a self-generated backlog idea like BH_004/005/006.

## Log

- 2026-08-16: Ticket opened.
- 2026-08-16: Both open questions answered directly by the project owner: **always
  unconditionally regenerate both files** (not gated on whether the HTML already existed —
  "we can just arbitrarily rewrite both html files whenever the index is requested"), and on
  failure mode, **no skip-and-continue** — a broken graph should fail the whole call loudly,
  since that's the mechanism for finding invalid state in the first place ("this is how I find
  it to tell agents how to fix it"). `index`-only (not `new`) confirmed as the right scope,
  unchallenged.

  Implemented: `build_index()` in `modules/roadmap/graph.py` now writes every discovered UID's
  `ROADMAP_GRAPH_<uid>.html` first, unconditionally, before rendering the markdown index — doing
  HTML first (not after) means `render_index()`'s own Graph-view link reflects this run's fresh
  write, not a stale existence-check from before it. A `GraphError` during any UID's
  load/validate aborts the whole call, same as it already did for the markdown path alone.
  `_cmd_index`/`_cmd_refresh` needed no code changes — both already call `build_index()`, only
  their help text was updated. Tests: unconditional-write-when-none-existed,
  overwrite-reflects-new-graph-content, link-reflects-same-run's-write, and
  raises-instead-of-skipping-on-invalid-graph, in `tests/test_roadmap.py`; CLI-level
  confirmation for both `index` and `refresh` in `tests/test_roadmap_cli.py`. Docs:
  `wiki/meta/bhrm.md`. Full suite green (316 passed). Closed.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
