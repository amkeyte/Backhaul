---
id: meta/bhw
category: meta
slug: bhw
title: BHW — Wiki Conventions
summary: Wiki page ID scheme, slug convention, and CLI cheatsheet.
keywords: null
status: draft
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · meta
<!-- bh-header:end -->

# BHW — Wiki Conventions

Wiki page ID scheme, slug convention, and CLI cheatsheet.

BHW (`bhw`) is the category-based wiki — no numbering, the path itself is the identity.

## ID scheme

A page's ID is `<category>/<slug>` (e.g. `reference/conventions/wiki-style`). Categories can be
nested (`reference/conventions`) — each segment becomes a real subfolder. There's no registry
and no counter, unlike BHT: two pages never collide unless they'd share the exact same
category + slug.

## Filenames and --slug

By default the slug is the title, slugified. Pass `--slug <code>` for a short, hand-picked
filename instead:

```
bhw new --category reference --title "How the Cartridge Mechanism Actually Works" --slug cartridge
```

## Status

`draft` -> `verified` / `published` — informational only. Unlike BHT's ticket status, nothing
here gates whether a page shows up in `WIKI_INDEX.md`; all statuses are listed.

## CLI cheatsheet

```
bhw new --category <cat> --title "..." [--slug code] [--summary "..."] [--status draft]
bhw index [--output PATH] [--category <prefix>] [--title "..."]   # --category scopes to one subtree
bhw refresh                 # recompute breadcrumbs + rebuild the index
bhw seed-meta [--category meta]   # install this project's canonical module-usage pages into another project
bhw projects
```

`--project <name>` / `--config <path>` selects the project, same as BHT.

## Related pages

- [BHT — Ticket Conventions](../meta/bht.md)
- [BHRM — Roadmap Conventions](../meta/bhrm.md)
