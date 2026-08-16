---
id: meta/bhrm
category: meta
slug: bhrm
title: BHRM — Roadmap Conventions
summary: Roadmap node ID scheme, why short slugs matter here, and CLI cheatsheet.
keywords: null
status: draft
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · meta
<!-- bh-header:end -->

# BHRM — Roadmap Conventions

Roadmap node ID scheme, why short slugs matter here, and CLI cheatsheet.

BHRM (`bhrm`) is the dependency-graph roadmap module — optional, gated by `enabled_modules`.
Every unit of roadmap-load-bearing work is a node (`work` or `convergence`) with explicit
`depends_on` edges; `frontier` computes what's actionable instead of that being a memorized
position in a list.

## ID scheme

A node's ID is `RM_<uid>_<NNN>` (e.g. `RM_ARR_001`). The UID is `RM_` + a client's short code —
the *same* code BHT uses for that client (they share one `client-uids.md`), so `ARR` means the
same client whether it's a ticket or a node. **Each UID is its own fully independent graph** —
`validate`/`frontier`/`downstream`/etc. are always scoped to one UID, and a `depends_on` entry
naming a node under a different UID is a hard error, not a cross-project link. This is how one
shared `content_roots.roadmap` folder hosts multiple, unrelated roadmaps side by side (e.g. one
project hosting both FrontierMode's and Satchel's graphs).

## Filenames and --slug — use a short code here, not the description

A node's filename is `<ID>_<slug>.md`. **For roadmap nodes specifically, always pass
`--slug <code>` with a short, one-word mnemonic** (e.g. `alma`, `scaffold`) rather than letting
it default to the slugified title:

```
bhrm new --client FrontierMode --title "Set up the initial mod scaffolding and build pipeline" --owner Arryn --slug scaffold
```

This matters more here than for BHT/BHW: `depends_on` edges reference IDs directly
(`RM_FRO_003`), and a node's own body/render output is meant to be skimmed as a dependency
graph, not a flat list — a long descriptive slug makes both harder to eyeball and
tab-complete than a short code does. The ID itself never contains the slug (only the filename
does), so this is purely about keeping files easy to work with, not about identity.

## Title length

`ROADMAP_INDEX.md` renders each node's title as part of a one-line list entry — same reasoning
as BHT's length standard (see `meta/bht.md`). Target title length ≤ ~40 characters; put the
detail (specific classes/files/packages involved) in the node's body instead of stuffing it into
the title. Several nodes from the initial roadmap backfill run well over this — worth trimming
next time they're touched, not urgent enough to warrant a dedicated pass on its own.

## Status vocabulary (kind-dependent)

- **work**: `open` -> `resolved` | `superseded` (terminal once left `open`).
- **convergence**: `WIP` <-> `reached` (reversible — a milestone can un-converge on real
  evidence of a gap, with a `ReachedLog` recording every time it was reached, never erased).

## HTML graph view (bhrm render-html)

`bhrm render-html --uid RM_XXX [--output PATH] [--title "..."]` generates a standalone,
self-contained HTML/SVG view of one UID's graph — no external assets, no network calls, safe to
open as a local file. A real, data-driven successor to the original hand-laid-out mockup this
was ported from (`intake/roadmap-nodes/design/Mockups/sample-visualization.html`).

Layout: nodes are laid out left to right by `_depth()` (the same longest-path-from-root value
`render`'s markdown indentation already uses), top to bottom within a layer ordered by node ID —
deterministic, same graph always produces byte-identical output. Color: five buckets lifted from
the mockup's own legend — work/resolved-or-superseded green, work/open-and-actionable blue,
work/open-and-blocked gray, convergence/reached gold solid border, convergence/WIP orange dashed
border. Supports `?focus=RM_XXX_NNN` in the URL — highlights and scrolls to that node on load,
same behavior the mockup proved against real pilot data.

**Slug shown bold, after the ID, in each node's label (BH_009).** Not a new stored field — a
node's slug already lives in its own filename (`<ID>_<slug>.md`, set via `--slug` at `bhrm new`
or defaulted from the title), and `Node.slug` just reads it back from `self.path.name`. Lets a
human reference a node meaningfully ("the Betty node") instead of only by its `RM_FRO_011`-style
ID. Omitted entirely for the rare node whose filename has no slug part.

**`bhrm index`/`bhrm refresh` unconditionally rewrite every UID's HTML view, every run.** Not
gated on whether `ROADMAP_GRAPH_<uid>.html` already existed — every `index`/`refresh` call is a
full rebuild of both the markdown index and every discovered UID's HTML graph view, using the
conventional filename (`html_graph_filename(uid)`, e.g. `ROADMAP_GRAPH_RM_FRO.html`), same
directory as `ROADMAP_INDEX.md`. `render-html --output` is still available and fully
user-controlled for a one-off render elsewhere, but the index routine no longer needs it —
running `bhrm index`/`refresh` is enough to keep both current (BH_008). `render_index()` then
links to that freshly-written file — `**Graph view:** [Open in browser ↗]` under that UID's
section — since the HTML is written before the markdown index is rendered in the same call.

**A UID whose graph fails to load or validate aborts the whole `index`/`refresh` call — on
purpose.** No partial-failure or skip-and-continue mode: per the project owner, a broken graph
should surface loudly as part of the normal index/refresh routine, the same way it already
surfaces inside `render_index()` itself — this is the mechanism for finding invalid roadmap
state, not something to route around.

The full `Visualize` line from the original node-format-spec.md (wired into every node's own
header, not just the index) is still deliberately not built — a narrower version of that idea,
scoped to the index only, is what shipped here.

## Convergence-bypass check (advisory)

`bhrm convergence-bypass --uid RM_XXX` lists `DependsOn` edges that reach back into a
convergence node's own prerequisite territory without ever routing through the convergence
node itself — "skipping the checkpoint." First formal definition of "bypass" in this codebase
(see BH_006) — the idea traces back to a hand-colored `.gate-edge` on the original pilot
mockup, never written down as a rule until this.

Precisely: for convergence node C, a node N is a bypass candidate when N isn't one of C's own
ancestors, isn't already gated by C (C itself or anything downstream of it), and N's own
ancestor closure shares at least one node with C's ancestor closure. Output is one line per
`(N, C, shared ancestors)` — same worklist style as `dependents`/`downstream`/`blocking`, never
a pass/fail verdict and never raises, even when it finds real candidates. A shared ancestor
doesn't automatically mean N *should* depend on C; it means it's worth a human looking at why
it doesn't. Deliberately does **not** factor in a node's `created` date to filter out nodes
that predate the convergence node — one clear rule for v1, not a second date-based heuristic.

This is separate from `bhrm validate` on purpose — `validate`'s contract is "raises on a cycle,
silent otherwise," a hard error; this is advisory and never blocks anything, so it stays its
own command rather than changing what `validate` means.

## CLI cheatsheet

```
bhrm new --client <name> --title "..." --owner <name> [--kind work|convergence] [--slug code] [--depends-on ID,ID]
bhrm validate --uid RM_XXX
bhrm frontier --uid RM_XXX
bhrm dependents <ID>   |   bhrm downstream <ID>   |   bhrm blocking <ID>
bhrm convergence-bypass --uid RM_XXX
bhrm render --uid RM_XXX [--output PATH] [--title "..."]
bhrm render-html --uid RM_XXX [--output PATH] [--title "..."]
bhrm export-json --uid RM_XXX [--out PATH]
bhrm index [--output PATH] [--title "..."]    # every UID's graph, its own section
bhrm projects
```

`--project <name>` / `--config <path>` selects the project. Every subcommand except `projects`
refuses to run if `"roadmap"` isn't in that project's `enabled_modules`.

## Related pages

- [BHT — Ticket Conventions](../meta/bht.md)
- [BHW — Wiki Conventions](../meta/bhw.md)
- [BHRole — Agent Role Conventions](../meta/bhrole.md)
- [Backhaul — Cross-Service Command Conventions](../meta/backhaul.md)
