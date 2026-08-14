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

## Title length

`WIKI_INDEX.md` renders each page's title as a table column — same reasoning as BHT's length
standard (see `meta/bht.md`). Target title length ≤ ~40 characters; let `summary` carry the
detail instead.

## Cross-references: use real relative links, not double brackets

**Always link with standard markdown — `[Title](relative/path.md)` — resolved relative to the
file doing the linking.** That's the only form guaranteed to be clickable, everywhere, no matter
what renders the file.

Earlier in this project, a double-bracket convention (wrapping a wiki page's slug in two
open-brackets and two close-brackets, borrowed from Obsidian-style wikilinks) spread across
wiki pages, tickets, and roadmap nodes as a lightweight way to reference a wiki page by its
`slug`. It was treated as acceptable on the theory that it was a non-clickable "semantic marker"
by design. In practice this was wrong: it doesn't render as a link in any plain markdown viewer
(it isn't standard Markdown at all), so every one of these ended up reported as "not linking
reliably" regardless of whether the slug it named actually existed. All instances found in
`wiki/` have been converted to real relative links; instances in `tickets/`/`roadmap/` may still
need the same conversion — check before trusting one you find there.

A second, sharper failure mode from the same convention: two independent sessions used it to
reference a **role** (the PM role, the Architect role) rather than a wiki page. Roles live in a
different content root (BHRole) with their own slugs, so that didn't just fail to render — it
pointed at nothing. A real relative link (e.g. `[PM](../../roles/pm.md)`) doesn't have this
failure mode, because it's an actual path, checkable by existence, not a name looked up in a
slug table that may or may not be the right one.

If you genuinely want a non-navigational tag (rare — most of the time you want the reader to be
able to click through), just say so in prose rather than using bracket syntax that looks like a
broken link.

## CLI cheatsheet

```
bhw new --category <cat> --title "..." [--slug code] [--summary "..."] [--status draft]
bhw index [--output PATH] [--category <prefix>] [--title "..."]   # --category scopes to one subtree
bhw refresh                 # recompute breadcrumbs + rebuild the index
bhw seed-meta [--category meta]   # install this project's canonical module-usage pages into another project
bhw projects
```

`--project <name>` / `--config <path>` selects the project, same as BHT.

Set `host_root` in `config.local.json` if `bhw` might run somewhere other than the real machine
(see BHT's meta page and `bhrole`'s) so Edit links stay correct regardless. That fixes links
only — to make `bhw` itself able to read/write real content from a sandbox, export
`BACKHAUL_LOCAL_ROOT` (see the README's "BACKHAUL_LOCAL_ROOT" section) before running any
command.

## Related pages

- [BHT — Ticket Conventions](../meta/bht.md)
- [BHRM — Roadmap Conventions](../meta/bhrm.md)
- [BHRole — Agent Role Conventions](../meta/bhrole.md)
