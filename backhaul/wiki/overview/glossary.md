---
id: overview/glossary
category: overview
slug: glossary
title: Backhaul — Glossary
summary: 'Terminology used across Backhaul: services, modules, config, identity, and
  roadmap concepts.'
keywords: null
status: published
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · overview
<!-- bh-header:end -->

# Backhaul — Glossary

Terms used across Backhaul's code, config, and wiki content, in one alphabetical list. See
[Backhaul — System Overview](../overview/readme.md) for how the pieces fit together, and
[Architecture](../design/architecture.md) for the foundation/services/modules layering this
glossary keeps referring back to.

- **backhaul** (the CLI) — the top-level cross-service command (`backhaul dashboard`,
  `backhaul projects`) for things that span BHT and BHW rather than belonging to either alone.

- **BACKHAUL.md** — a project's generated dashboard: front-page links to its Board, Wiki
  Index, and (if enabled) Roadmap Index, each with a live count. Rebuilt wholesale by
  `backhaul dashboard`; never hand-edited.

- **bh-header** — the marker name every normalized header block is wrapped in
  (`<!-- bh-header:start -->...<!-- bh-header:end -->`), whether it's on a ticket, a wiki
  page, a roadmap node, or an indexer page. One recognizable header shape across all content
  types — see `foundation/header.py`.

- **BHRM** (BackhaulRoadmap) — the optional dependency-graph roadmap module. CLI: `bhrm`.

- **BHT** (BackhaulTicket) — the ticket (passdown) service. Always enabled. CLI: `bht`.

- **BHW** (BackhaulWiki) — the category-based wiki service. Always enabled. CLI: `bhw`.

- **BOARD.md** — a project's ticket indexer: open tickets grouped by status, regenerated
  wholesale by `bht board` / `bht refresh` / `bht open` / `bht close`.

- **client-uids.md** — the UID registry file, shared between BHT and BHRM so a client's short
  code (e.g. `ARR`) means the same client whether it's a ticket or a roadmap node.

- **config.local.json** — a per-machine, gitignored config file: `content_roots`,
  `enabled_modules`, `client_folders`, an optional `project_name`, and a schema `version`.
  Every CLI invocation reads it fresh — never cached, never assumed.

- **content_roots** — the config field mapping a content type (`tickets`, `wiki`, `roadmap`)
  to the folder it lives in on this machine.

- **convergence** (node kind) — a reversible roadmap milestone: cycles between `WIP` and
  `reached` rather than closing permanently. Contrast with **work**.

- **dashboard** — see **BACKHAUL.md**.

- **DependsOn** / **depends_on** — a roadmap node's prerequisite edges. A node is only
  actionable once every node it depends on is `resolved`/`reached`. Crossing UIDs in a
  `depends_on` entry is a hard error — see **UID**.

- **dogfooding** — Backhaul tracking its own development with itself: the repo root's
  `backhaul/` folder is a real, self-referential project (registered as `"backhaul"` in
  `config/projects.json`) with its own tickets, wiki, and roadmap.

- **editmd:** — the protocol-handler scheme that opens a file in Notepad++ from a rendered
  Edit link. Needs `modules/handlers/editmd` installed on the machine to actually resolve.

- **enabled_modules** — the config field listing which optional modules are turned on for
  this machine. Checked (not just documented) by every module CLI except `projects`.

- **foundation** — the one shared, domain-agnostic primitives layer everything else builds
  on: frontmatter parsing, identity, slugify, templating, file safety, markers, rollup,
  the client registry, the normalized header, protocol-handler URIs, project resolution.

- **frontier** — the set of a roadmap graph's currently-actionable nodes: open/WIP and every
  dependency already satisfied. `bhrm frontier --uid <UID>` prints it.

- **frontmatter** — the YAML metadata block at the top of every ticket, wiki page, and
  roadmap node file, between `---` delimiters.

- **manifest.json** — the metadata file every service and module carries: `id`, its own
  `version` (independent of the package version), `kind`, `description`, `requires`.

- **marker block** — a generic idempotent, HTML-comment-delimited generated section
  (`<!-- name:start -->...<!-- name:end -->`) that can be refreshed in place without
  clobbering hand-written content around it. **bh-header** is the one marker every content
  type shares.

- **module** — optional functionality under `modules/`, gated by **enabled_modules** —
  `roadmap`, `handlers/editmd`, `handlers/openfolder`, `shortcuts`, `docx` (still a stub).

- **NumberedIdentity** — the `UID_NNN` identity scheme (e.g. `ARR_001`, `RM_ARR_001`) used by
  BHT tickets and BHRM nodes. Needs a registry (**client-uids.md**) to mint/look up UIDs.

- **node** — one unit of roadmap-tracked work: **work** or **convergence**, identified by
  `RM_<UID>_NNN`, with a title, an owner, and `depends_on` edges.

- **openfolder:** — the protocol-handler scheme that opens a folder in Explorer from a
  rendered Folder link. Needs `modules/handlers/openfolder` installed on the machine.

- **PathIdentity** — the `category/slug` identity scheme (e.g. `reference/car-maintenance`)
  used by BHW wiki pages. No registry — the path itself is the identity.

- **project** — a named, registered set of content roots + its own `config.local.json`,
  resolved via `--project <name>` against `config/projects.json`. `bht`/`bhw`/`bhrm`/`backhaul`
  all default to this checkout's own config when neither `--project` nor `--config` is given.

- **projects.json** — the gitignored, per-machine registry mapping project names to their
  `config.local.json` paths.

- **Ref** — a typed, lightweight cross-reference between a ticket and a wiki page
  (`kind:id`, e.g. `wiki:reference/das-project-lifecycle`). Designed in
  [Architecture](../design/architecture.md) §3 and [Foundation Design](../design/foundation-design.md)
  §4; `foundation/refs.py` exists but `resolve()` is still a stub, not wired into BHT/BHW yet.

- **refresh** — the CLI subcommand (`bht refresh` / `bhw refresh` / `bhrm refresh`) that
  recomputes every file's header/links and rebuilds the indexer, against this machine's real,
  resolved paths — for when content was generated somewhere else (a different checkout path,
  a dev sandbox).

- **ROADMAP_INDEX.md** — a project's roadmap indexer: every UID's graph, sectioned
  separately (graphs are never merged), regenerated wholesale by `bhrm index` / `bhrm refresh`.

- **rollup** — the foundation primitive (`CollectSpec` + `collect()`) that walks, parses,
  filters, and groups content files. Deliberately does not render — turning a rollup into a
  board table vs. a category index is each service's own job.

- **seed-meta** — the `bhw` subcommand that installs the canonical module-usage pages
  (`meta/bht.md`, `meta/bhw.md`, `meta/bhrm.md`) from one project's wiki into another's.
  Additive only — never overwrites a page that's already there.

- **service** — baseline functionality, always enabled on every machine, never gated by
  `enabled_modules` — BHT and BHW. Contrast with **module**.

- **slug** — a short, sanitized filename code. Auto-derived from a title by default;
  `--slug <code>` overrides it, recommended wherever a short reference matters (roadmap
  `depends_on` edges especially).

- **UID** — a client's short code (e.g. `ARR` for Arryn), looked up or auto-minted from
  `--client`/`--uid` the first time a client is seen, recorded in **client-uids.md**. Every
  BHRM node's own `uid` is `RM_<UID>` — a fully independent graph; a `depends_on` edge can
  never cross into a different UID.

- **VERSION** — the framework version marker file at the repo root, meant to be checked
  against a machine's `config.local.json` to catch stale-checkout drift
  (`foundation/version_check.py`) — designed in
  [Migration Plan](../design/migration-plan.md) §6, still a stub (`NotImplementedError`).

- **WIKI_INDEX.md** — a project's wiki indexer: every page grouped by category, regenerated
  wholesale by `bhw index` / `bhw refresh` / `bhw new` / `bhw seed-meta`.

- **work** (node kind) — a terminal roadmap milestone: `open` → `resolved`/`superseded`,
  doesn't reopen. Contrast with **convergence**.
