---
id: meta/bht
category: meta
slug: bht
title: BHT — Ticket Conventions
summary: Ticket ID scheme, slug convention, and CLI cheatsheet.
keywords: null
status: draft
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · meta
<!-- bh-header:end -->

# BHT — Ticket Conventions

Ticket ID scheme, slug convention, and CLI cheatsheet.

BHT (`bht`) is the passdown ticket system — one open item per file, rolled up into a live
`BOARD.md`.

## ID scheme

Every ticket ID is `<UID>_<NNN>` (e.g. `ARR_001`) — a client's short code plus a sequential
number, scoped per UID. The UID is looked up or auto-minted from `--client` the first time a
client is seen (via this project's `client-uids.md`), or set explicitly with `--uid`.

## Filenames and --slug

A ticket's filename is `<ID>_<slug>.md`. By default the slug is the title, slugified
(`Clean the car` -> `clean-the-car`). Pass `--slug <code>` to use a short code instead when the
title is long or you want an easy-to-reference filename:

```
bht open --client Arryn --title "Replace the roof antenna and check the mounting bracket" --slug antenna
```

Either way the value is sanitized (lowercased, spaces/punctuation stripped) before it lands in
the filename.

## Lifecycle

`open` -> `in-progress` | `blocked` -> `done`. Only `done` tickets drop off `BOARD.md` — they
stay on disk, just excluded from the live board.

## CLI cheatsheet

```
bht open --client <name> --title "..." [--uid X] [--slug code] [--context "..."] [--priority high]
bht close <id-or-prefix>
bht board [--output PATH]
bht refresh                 # recompute Board/Folder links against this machine's real paths
bht projects                # list config/projects.json entries
```

`--project <name>` (or `--config <path>`) selects which project's tickets/board this touches;
omit both for this checkout's own default config.

If `bht` might ever run somewhere other than the real machine (e.g. inside a role's Cowork
sandbox — see `bhrole`'s meta page), set `host_root` in `config.local.json` so Edit/Folder links
still point at the real path instead of wherever the CLI happens to be executing.

## Related pages

- [BHW — Wiki Conventions](../meta/bhw.md)
- [BHRM — Roadmap Conventions](../meta/bhrm.md)
- [BHRole — Roles Conventions](../meta/bhrole.md)
