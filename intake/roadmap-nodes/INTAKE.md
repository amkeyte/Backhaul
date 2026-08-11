# Intake: LunaFlow RoadMap Nodes

Raw copy, scraped from `C:\_local\source\LunaFlow_A` on 2026-08-11, for closer review before
shaping into a Backhaul module. Nothing here has been modified from the source — this is a
snapshot, not a working copy. Not wired into Backhaul's config/module system yet.

## Where each piece came from

- `design/` — the full WIP proposal space, from `Documents/ClaudeWiki/RoadmapGraph/`. Node
  format spec, graph-tooling spec, proposal, migration plan, and two mockups (a sample
  generated index + a hand-built HTML graph visualization).
- `tooling/` — the actual implementation, from `scripts/roadmap/`. `roadmap_graph.py`
  (stdlib-only Python: parses node files, builds a dependency graph, answers `validate` /
  `frontier` / `dependents` / `downstream` / `blocking` / `render` / `export-json`),
  `test_roadmap_graph.py` (9 tests), and its own `README.md`.
- `pilot-data/` — real (not fictional) node files, from `Documents/Roadmap/Nodes/`. 14 nodes
  covering Phase 2.6.5 through 2.12 plus three convergence nodes, plus `_index.md`, the flat
  ledger. Useful as reference examples of the node-file format in the wild, not something to
  ship as part of the module itself.

## What it is, briefly

A proposed replacement for LunaFlow's flat phase-number roadmap: every unit of work becomes a
node with a stable ID and explicit `DependsOn` edges instead of a position in a sequence.
"What's actionable" becomes a computed query (`frontier`) instead of a memorized position.
Two node kinds — `work` (terminal once resolved) and `convergence` (milestones, reversible
between `WIP`/`reached`, with an append-only `ReachedLog`). Full rationale in `design/overview.md`
and `design/proposal.md`.

## Status in the source repo

WIP, unratified, not adopted — `Documents/Roadmap/roadmap.md`'s phase table is still LunaFlow's
live source of truth. The tooling (`roadmap_graph.py`) is built and passing its acceptance
criteria, and has been run against the real 14-node pilot, but nothing about the proposal being
adopted has changed. This intake copy doesn't change that status either — it's a separate
question from whether the *tool* becomes a portable Backhaul module.

## Not yet decided

Whether this becomes a `modules/roadmap` following the same `manifest.json` + `enabled_modules`
pattern as `docx`/`shortcuts`, what stays LunaFlow-specific vs. what's generic, and whether
`pilot-data/` ships at all (it's real LunaFlow project content, not template/example material a
module should carry with it).
