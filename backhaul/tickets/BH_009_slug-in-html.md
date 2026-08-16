---
id: BH_009
uid: BH
number: 9
client: BH
status: done
title: Show node slug bold in render-html labels
context: Slug already lives in the filename (--slug at bhrm new); surface it, don't
  store it twice. See body.
priority: normal
opened: '2026-08-16'
closed: '2026-08-16'
---

<!-- board:start -->
<!-- board:end -->

## Summary

Show node slug bold in render-html labels

## Full report

Feature request (project owner, 2026-08-16): a way to see each node's slug in the generated
roadmap HTML, bold, after the ID label — needed for referencing a node meaningfully as a human
("the Betty node"), not just by its `RM_FRO_011`-style ID. The project's PM had apparently been
hand-editing this directly into the generated HTML — which BH_008 (unconditional HTML rewrite
on every `index`/`refresh`) would now silently wipe out every time, making this the right moment
to build it properly instead.

**No new storage — the slug already exists.** Every node's filename is `<ID>_<slug>.md`
(`--slug` at `bhrm new`, or `slugify(title)` by default), and mcRepos' real nodes already all
carry meaningful ones (the 1945-baby-names sweep). Adding a second, independently-editable
`slug:` frontmatter field would be a second place for the same fact to drift from the filename
— exactly the dual-write risk this codebase's own conventions call out repeatedly (Required By,
Visualize: both "computed, not stored"). So this ships as a derived property, not a new field.

## Design (locked, same session)

- `Node.slug` (new property in `modules/roadmap/graph.py`): strips the `<ID>_` prefix and
  `.md` suffix from `self.path.name`. Empty string for the rare ID-only filename (a title that
  slugifies to nothing).
- `render_html()`: the node label's `<text>` element gets a `<tspan class="node-slug">` appended
  after the ID, only when `node.slug` is non-empty — same graceful-omit pattern as everything
  else in this renderer. New CSS class `.node-slug { font-weight: 700; fill: #ffe066; }` — bold
  and a distinct accent color so it reads as a name, not part of the ID. Also added to the
  per-node hover `<title>` tooltip (`RM_FRO_011 · betty — ...`), not just the visible label.
- No change to `schema.py`, `export_json()`, or the markdown `render()` output — scoped to the
  HTML view only, per the actual request.

Scope: `modules/roadmap/graph.py` (`Node.slug` property, `render_html()`'s label generation),
tests (`tests/test_roadmap.py` — slug extraction, empty-filename case, bold tspan present/absent
in output), docs (`wiki/meta/bhrm.md`).

## Log

- 2026-08-16: Ticket opened.
- 2026-08-16: Implemented same session — see Design above. Full suite green (320 passed).
  Regenerated both mcRepos graphs via `bhrm index` to confirm live. Closed.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
