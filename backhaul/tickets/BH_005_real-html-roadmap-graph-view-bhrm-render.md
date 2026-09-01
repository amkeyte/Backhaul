---
id: BH_005
uid: BH
number: 5
client: BH
status: done
title: Real HTML roadmap graph view (bhrm render-html)
context: Mockup existed, never automated. export_json()+_depth() are the reusable
  foundation. See body.
priority: low
opened: '2026-08-14'
closed: '2026-08-14'
---

## Summary

Real HTML roadmap graph view (bhrm render-html)

## Full report

Feature request: a real, auto-generated HTML/SVG visualization of a roadmap graph, driven
by bhrm export-json's own data -- not a second hand-maintained artifact.

What actually existed in the model project (intake/roadmap-nodes/), researched 2026-08-13
Not a working generator -- a hand-built proof of concept. design/Mockups/sample-visualization.html
is one static HTML file with SVG node positions hand-typed as coordinates for that one 14-node
pilot graph (dark theme, legend, frontier banner, a small vanilla-JS `?focus=RM-NNNN` handler that
highlights + smooth-scrolls to the matching node). Its own banner says so outright: "MOCKUP --
hand-laid-out, not real tooling output." design/Specs/graph-tooling-spec.md explicitly scoped
"generating the HTML visualization itself" as OUT of scope for the real tool, deferred to "a future
consumer of export-json's output" -- that consumer was never built, even in the original project.
design/Specs/node-format-spec.md documents a `Visualize` line meant to live in every node's header
(a link to the graph view, `?focus=`-deep-linked to itself, computed not stored) -- also never
wired into real tooling, only hand-added to the mockup's source nodes.

What Backhaul already has as reusable foundation
- `bhrm export-json --uid X [--out PATH]` -- already ported (modules/roadmap/graph.py's
  export_json()), already produces nodes (id/kind/status/name) + edges (from/to), plus extras the
  original spec didn't have (actionable, owner, ticket).
- `_depth()` in modules/roadmap/graph.py -- longest-path-from-root, already computed for render()'s
  markdown indentation. Directly reusable as a real layout basis (layer nodes by depth) instead of
  the mockup's hand-placed coordinates.
- No `Visualize` line exists anywhere in Backhaul's render() output or roadmap schema today --
  this concept from the original spec was never picked up during the port.

Suggested shape (not a full design -- flagging the direction)
- New renderer, e.g. `bhrm render-html --uid X [--output PATH]`, consuming export_json()'s dict
  directly (no need to round-trip through an actual JSON file on disk).
- Real layout: layer nodes by `_depth()` (already computed), position within a layer by simple
  even spacing -- doesn't need to be pretty, needs to be correct and not require hand-maintenance
  per node the way the mockup did.
- Lift the `?focus=RM-NNNN` JS behavior near-verbatim from the mockup -- it's small, self-contained,
  and already proven against real data.
- Wire a `Visualize` line into render()'s per-node output (or ROADMAP_INDEX.md's per-node entries),
  pointing at wherever the generated HTML lives with `?focus=<own-id>` appended -- the piece the
  original node-format-spec.md wanted but never got built.
- Legend/color scheme from the mockup (resolved/reached green, actionable blue, blocked gray,
  convergence gold/orange) is a reasonable visual starting point -- it was already validated
  against real pilot data, not just aesthetic guessing.

Scope
- backhaul/modules/roadmap/graph.py -- no change needed to export_json()/_depth(), both reused.
- backhaul/modules/roadmap/ -- new render_html.py (or similar) for the SVG/HTML generation.
- backhaul/modules/roadmap/cli.py -- new `render-html` subcommand.
- backhaul/modules/roadmap/schema.py -- no new stored field (Visualize is computed, not stored,
  same discipline the original spec held: "a fact an author invents or maintains by hand" is
  exactly what this avoids).
- Tests: layout determinism (same graph -> same output), `?focus=` behavior (can be a JS-behavior
  smoke test or just documented as manually verified, consistent with how little of this project's
  test suite touches actual browser rendering), Visualize-line presence/correctness in render().
- Docs: wiki/meta/bhrm.md (new command + Visualize convention), README if relevant.

Priority: low -- future feature, not blocking anything currently in flight.

## Design (locked 2026-08-14)

New `render_html(nodes, *, output_dir=None, title=...)` in `modules/roadmap/graph.py`, sitting
next to `render()`. Layout: layer = `_depth()` (already computed, unchanged), left to right;
within a layer, nodes sorted by ID — the same tie-break `render()` already uses for its own
ordering, kept for determinism (same graph -> byte-identical output). Internally calls
`export_json(nodes)` for the node/edge data rather than re-deriving fields from `Node` objects
directly — a second renderer over the same export, per the original spec's own framing, not a
second parser.

**Edge-direction gotcha, worth calling out before someone implements this and gets it
backwards:** `export_json`'s edges are `{"from": nid, "to": dep}` — *nid depends on dep*. The
mockup's arrows flow left-to-right, prerequisite into what it unlocks, so the drawn arrow must
go from `to` (the prerequisite, lower depth) to `from` (the dependent, higher depth) —
reversed from the field names, not a literal from-to draw.

Color scheme (five buckets, lifted from the mockup's own legend, already validated against
real pilot data):
- kind=work, status=resolved/superseded -> green
- kind=work, status=open, actionable -> blue
- kind=work, status=open, not actionable -> gray
- kind=convergence, status=reached -> gold, solid border
- kind=convergence, status=WIP -> orange fill, dashed border

`?focus=RM-NNNN` behavior lifted near-verbatim from the mockup's `<script>` block — small,
self-contained, already proven against real data.

**Visualize-line wiring into `render()`/`index()`: deferred, not part of this ticket.** Wiring
it in would require those commands to know where the HTML output actually lives (a new
`--html-path` or a location convention), which is extra cross-command coupling this ticket
doesn't need to take on. `render-html` ships standalone; the Visualize line is a follow-up once
a real project has an HTML view checked in somewhere and the "where does it live" question has
a real answer instead of a guessed one.

`schema.py`: confirmed no change — Visualize stays computed, never stored, same as the original
spec's own discipline.

CLI: `bhrm render-html --uid X [--output PATH] [--title "..."]`, mirroring `render`'s existing
flags — stdout by default, `--output` to write a file, same convention `render`/`export-json`
already use.

Scope: `modules/roadmap/graph.py` (`render_html()` + a small layout/color helper), `modules/roadmap/cli.py`
(new subcommand), tests (layout determinism on a fixed synthetic graph, color-mapping per
kind/status/actionable combination), `wiki/meta/bhrm.md` (new command, note Visualize wiring is
deferred).

## Log

- 2026-08-13: Ticket opened.
- 2026-08-14: Design locked — see Design section above. Not yet implemented.
- 2026-08-14: Implemented per the Design section — `render_html()` + `_html_layout()`/
  `_html_color()` in `modules/roadmap/graph.py`, `bhrm render-html` subcommand, tests
  (layout determinism, edge-direction, color-mapping in `tests/test_roadmap.py`, CLI tests in
  `tests/test_roadmap_cli.py`), docs (`wiki/meta/bhrm.md`). Dropped the unused `output_dir`
  parameter from the locked signature — nothing in the actual implementation needed it (the
  HTML is self-contained, no relative links to other files the way `render()`'s markdown output
  has). Full suite green (296 passed). Closed.
- 2026-08-14: Follow-up, requested against real mcRepos usage — `render_index()` now links a
  UID's HTML graph view from `ROADMAP_INDEX.md` when one exists at the conventional path
  (`html_graph_filename(uid)` = `ROADMAP_GRAPH_<uid>.html`, sitting next to the index itself).
  Pure filesystem-existence check at render time, no new config/CLI flag — a project that's
  never run `render-html` just gets no link, same graceful-omit pattern as the rest of this
  module. `render-html --output` itself is still fully user-controlled (unchanged default:
  stdout) — using the conventional name is what makes the link appear, not a requirement.
  This is a narrower version of the Visualize-line wiring the original Design section deferred
  (that was about wiring into every node's own header; this is just the index). Tests added
  (`test_render_index_links_html_graph_view_when_present` and siblings in `tests/test_roadmap.py`,
  CLI test in `tests/test_roadmap_cli.py`). Full suite green (300 passed).
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_LocalFiles/source/repos/Backhaul)
<!-- bh-header:end -->
