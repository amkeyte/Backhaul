---
id: meta/backhaul
category: meta
slug: backhaul
title: Backhaul — Cross-Service Command Conventions
summary: 'The top-level backhaul CLI: dashboard, lint, projects — commands that span
  every service instead of belonging to one.'
keywords: null
status: draft
updated: '2026-08-14'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · meta
<!-- bh-header:end -->

# Backhaul — Cross-Service Command Conventions

The top-level backhaul CLI: dashboard, lint, projects — commands that span every service instead of belonging to one.

`backhaul` (as opposed to `bht`/`bhw`/`bhrm`/`bhrole`) is where a command lives when it doesn't
belong to one service — `dashboard` rebuilds `BACKHAUL.md` from every service's own generated
aggregate; `lint` (below) walks every content root together, since a link or an orphan problem
doesn't respect service boundaries.

## lint

`backhaul lint [--check orphaned,links] [--format text|json]` audits content for two generic
markdown-graph problems, walked across every content root this project has configured (tickets,
wiki, and roadmap/roles when both a content root and the module are enabled) — not one service
at a time, since a ticket can link to a wiki page and vice versa.

- **orphaned** — a `.md` file nothing else links to. The generated aggregate files
  (`BOARD.md`, `WIKI_INDEX.md`, `ROADMAP_INDEX.md`, `ROLES_INDEX.md`, `BACKHAUL.md`) aren't part
  of this check at all — each lives one directory *above* its content root, not inside it, so
  lint's per-root walk never reaches them. `client-uids.md` (inside `content_roots.tickets`, the
  registry BHT/BHRM share) is explicitly exempted — infrastructure a reader finds by convention,
  not by following a link, same reasoning LunaFlow's own doc-lint exempts `index.md`/`README*`
  for.
- **links** — a relative markdown link whose target doesn't resolve from the linking file.
  Skips `http(s)://`, `mailto:`, `editmd:`, `openfolder:`, `claude:` — none of those are local
  paths to check.

Ported from LunaFlow_A's `doc-lint.py`, generalized: only the two checks that are genuinely
project-agnostic markdown-graph problems shipped in v1. LunaFlow-specific checks (free-text
status-drift outside three hardcoded folder names, a ticket-specific `## Decision` heading
requirement, ALL-CAPS `DEPRECATED` marker completeness) don't have a direct Backhaul equivalent
— Backhaul already structures status in frontmatter rather than free text, and doesn't share
LunaFlow's ticket-template conventions — so they're out of scope here, not forgotten.

No auto-fix, same discipline as the source tool: deciding where to link an orphan from, or what
a broken link should point at instead, is an editorial call this command can't make for you.
Exit codes: `0` clean, `1` findings (informational, not a hard failure on its own), `2` a bad
`--check` name.

## CLI cheatsheet

```
backhaul dashboard [--output PATH]
backhaul lint [--check orphaned,links] [--format text|json]
backhaul projects
```

`--project <name>` / `--config <path>` selects the project, same as every other CLI here.

## Related pages

- [BHT — Ticket Conventions](bht.md)
- [BHW — Wiki Conventions](bhw.md)
- [BHRM — Roadmap Conventions](bhrm.md)
- [BHRole — Agent Role Conventions](bhrole.md)
