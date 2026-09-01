---
id: BH_007
uid: BH
number: 7
client: BH
status: open
title: Build-ready marker on the dashboard
context: Per-project ready/notReady/none flag rendered on BACKHAUL.md. See ticket
  body for open design questions.
priority: normal
opened: '2026-08-16'
closed: null
---

<!-- board:start -->
<!-- board:end -->

## Summary

Build-ready marker on the dashboard

## Full report

Feature request (project owner, 2026-08-16): a build-ready marker shown on `BACKHAUL.md`, with
a three-value option — **ready** / **notReady** / unset (no marker shown at all, the default).
Motivation: after a work session touching multiple roadmap graphs and real source code (as in
mcRepos), there's currently no single place that says "is this project in a state someone could
actually build/playtest right now" — a human has to read the board, the roadmap index, and the
handoff tickets separately to piece that together.

Open questions, deliberately not resolved here — flagging so they're not rediscovered as
surprises at build time, not committing to answers:

- **Scope: one marker per project, or one per roadmap UID?** A project can host multiple
  independent graphs (mcRepos hosts both `RM_FRO` and `RM_SAT` side by side) — a single
  project-wide marker conflates two potentially-different states. Per-UID is more precise but
  needs its own place to render (the Roadmap line currently shows one aggregate count, not a
  per-UID breakdown) and doesn't cover projects with no roadmap module at all, which still have
  a board/wiki that could plausibly want a ready marker.
- **Manually set, or computed?** The three-value framing ("ready/notReady/none") reads like a
  human-toggled field, not a derived one — closer to `config.local.json`'s existing
  human-maintained fields (`project_name`, `repo_url`) than to `dashboard.py`'s computed counts.
  Could instead be computed from roadmap state (e.g. "ready" if every convergence node for a
  UID is `reached` and nothing's `WIP`) — worth deciding which, since a manual field can drift
  from reality the same way any hand-maintained status can, but a computed one needs a precise
  rule that doesn't exist yet (unlike `frontier`'s already-precise "actionable" definition).
- **Where on the dashboard, exactly?** A new line near the top (own row, like Work
  Board/Wiki Index/Roadmap/Team), or a badge/prefix on an existing line? `header.py`'s
  `render_header()` and `dashboard.py`'s `render_dashboard()` are the two places that would
  need to know about this.

Suggested shape (not committed) — if manual: a new optional `build_ready` field in
`config.local.json` (`"ready" | "notReady"`, omitted = no marker), validated but not required by
`config.schema.json` (additive optional key, same as `content_roots.roadmap` — no
`CONFIG_SCHEMA_VERSION` bump needed per that field's own doc-comment). `backhaul dashboard`
renders a line only when set, same graceful-omit pattern the Team/Roadmap lines already use when
their own module isn't configured.

Scope (indicative, not final): `config/config.schema.json`, `foundation/config.py` (a
`get_build_ready()` accessor, mirroring `get_project_name()`/`get_repo_url()`), `dashboard.py`
(render + build), `cli.py` (if a CLI flag ends up needed for a computed variant), tests, README
if the field is documented there alongside the other `config.local.json` fields.

Priority: normal — explicitly requested, not a self-generated backlog idea like BH_004/005/006.

## Log

- 2026-08-16: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_LocalFiles/source/repos/Backhaul)
<!-- bh-header:end -->
