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

## Status vocabulary (kind-dependent)

- **work**: `open` -> `resolved` | `superseded` (terminal once left `open`).
- **convergence**: `WIP` <-> `reached` (reversible — a milestone can un-converge on real
  evidence of a gap, with a `ReachedLog` recording every time it was reached, never erased).

## CLI cheatsheet

```
bhrm new --client <name> --title "..." --owner <name> [--kind work|convergence] [--slug code] [--depends-on ID,ID]
bhrm validate --uid RM_XXX
bhrm frontier --uid RM_XXX
bhrm dependents <ID>   |   bhrm downstream <ID>   |   bhrm blocking <ID>
bhrm render --uid RM_XXX [--output PATH] [--title "..."]
bhrm export-json --uid RM_XXX [--out PATH]
bhrm index [--output PATH] [--title "..."]    # every UID's graph, its own section
bhrm projects
```

`--project <name>` / `--config <path>` selects the project. Every subcommand except `projects`
refuses to run if `"roadmap"` isn't in that project's `enabled_modules`.

## Related pages

- [BHT — Ticket Conventions](../meta/bht.md)
- [BHW — Wiki Conventions](../meta/bhw.md)
