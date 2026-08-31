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
doesn't respect service boundaries; `refresh` (below) is the one-command entry point that runs
every service's own refresh/index step in the right order.

## Build-ready marker (BH_007)

Set `build_ready: "ready"` or `"notReady"` in `config.local.json` and `backhaul dashboard`/
`backhaul refresh` render a bolded `**Build status: Ready**` / `**Build status: Not ready**`
line right under `BACKHAUL.md`'s title, ahead of every other line — the point is a human can
answer "is this project in a state someone could actually build/playtest right now" without
reading the board, the roadmap index, and the handoff tickets separately to piece that
together. Omit the field entirely (the default) and no marker line renders at all — every
project not using this convention sees exactly today's dashboard, unchanged.

Manually set, not computed — closer to `project_name`/`repo_url` (a human-maintained fact) than
to `dashboard.py`'s own live counts, since no precise, project-agnostic rule for "ready" exists
yet (unlike `frontier`'s already-precise "actionable" definition). One marker per project, not
per roadmap UID — a project hosting multiple independent graphs (e.g. `RM_FRO` and `RM_SAT` side
by side) gets one shared marker for now; scoping it per-UID would need its own place to render
(today's `Roadmap` line shows one aggregate count across every UID, not a per-UID breakdown) and
wouldn't cover a project with no roadmap module at all, which can still plausibly want one.

## refresh (BH_014)

`backhaul refresh` is the recommended one-command way to bring a project's generated files
current: rebuilds the ticket board, the wiki index, the roadmap index and roles roster (each
only if its content root is configured *and* its module is enabled — skips cleanly otherwise,
same gating `dashboard` already uses), runs `lint` and prints any findings, then rebuilds
`BACKHAUL.md` last so it reflects everything the earlier steps just wrote.

Lint findings here are always advisory — printed, never a reason to stop or to make `refresh`
return non-zero. `refresh`'s job is "make the generated files current," not "gate on content
being perfect"; use `backhaul lint` directly when you want lint's own exit code to mean
something. A UID whose roadmap graph fails to load still aborts the whole `refresh` call,
though — same "surface loudly" rule `bhrm index` already follows (see `bhrm.md`).

Doesn't sweep every individual ticket/page/node's own header the way `bht refresh`/`bhw
refresh`/`bhrm refresh`/`bhrole refresh` do (recomputing relative links against this machine's
resolved paths) — `backhaul refresh` only rebuilds the aggregate index/board files. Run a
service's own `refresh` first if you suspect stale per-file headers, then `backhaul refresh` to
bring every aggregate current in one pass.

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
  paths to check. Also skips a link marked `<!-- historical-link -->` on the same line (see
  below) — a deliberate reference to something that's gone, not a mistake.

### Historical links (BH_015)

A link that's *meant* to point at something that may no longer exist — e.g. a wiki page's "see
also" naming a ticket that's since closed and been archived, kept as a paper trail — shouldn't
show up as a `links` finding every time lint runs. Mark it by appending an HTML comment right
after the link, same line:

```
See [BH_003](../../tickets/BH_003_old-thing.md) <!-- historical-link --> for the original design.
```

Matches this project's existing marker idiom (`<!-- board:start -->`, `<!-- bh-header:start -->`)
rather than a markdown title attribute (`[text](target "historical")`) — a title attribute
renders as hover text in some viewers, which would look like a broken/confusing tooltip instead
of a clear marker. Scoped to `find_broken_links()` only: a historical link still counts as a real
inbound link for the `orphaned` check, so marking a link this way doesn't also make its target
look unlinked.

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
backhaul refresh
backhaul lint [--check orphaned,links] [--format text|json]
backhaul projects
```

`--project <name>` / `--config <path>` selects the project, same as every other CLI here.

## Related pages

- [BHT — Ticket Conventions](bht.md)
- [BHW — Wiki Conventions](bhw.md)
- [BHRM — Roadmap Conventions](bhrm.md)
- [BHRole — Agent Role Conventions](bhrole.md)
