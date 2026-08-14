---
id: BH_005
uid: BH
number: 5
client: BH
status: open
title: Real HTML roadmap graph view (bhrm render-html)
context: Mockup existed, never automated. export_json()+_depth() are the reusable
  foundation. See body.
priority: low
opened: '2026-08-14'
closed: null
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

## Log

- 2026-08-13: Ticket opened.
