---
id: overview/readme
category: overview
slug: readme
title: Backhaul — System Overview
summary: Setup, project registry, module usage, and repo layout overview.
keywords: null
status: published
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · overview
<!-- bh-header:end -->

# Backhaul

Portable wiki + ticket (passdown) system: foundation + BHT (ticket) / BHW (wiki) services,
plus optional modules (docx editing, Windows shortcuts, URL-protocol handlers, a dependency-
graph roadmap, agent roles).

**Status:** `foundation/`, the `ticket` (BHT) service, and the `wiki` (BHW) service are all
implemented, with working `bht`/`bhw` CLIs. `modules/handlers/{editmd,openfolder}` (Notepad++
and Explorer integration for rendered links), `modules/roadmap` (`bhrm` — see below), and
`modules/roles` (`bhrole` — see below) are implemented too; `modules/docx` and
`modules/shortcuts` are the remaining stubs — see `migration/*.md` for the design docs driving
that work.

## Setup on a new machine

1. Clone the repo and open `Backhaul.sln` (Visual Studio 2022+ with Python Tools), or just
   work from `src/Backhaul/` directly with any editor.

2. Create a project-local virtualenv and install the package in editable mode:

   ```
   cd src/Backhaul
   python -m venv .venv
   .venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
   pip install -e .[dev]
   ```

   Optional extras, install as needed:
   - `pip install -e .[docx]` — for the docx module
   - `pip install -e .[shortcuts]` — for Windows `.lnk` shortcut creation

3. Copy the config template and point it at this machine's actual content:

   ```
   cp config/config.local.example.json config/config.local.json
   ```

   Edit `config/config.local.json` to set `content_roots.tickets` / `content_roots.wiki` to
   real paths on this machine, and list any `enabled_modules`. This file is gitignored —
   never committed, since it's per-machine. Shape is defined in `config/config.schema.json`.

4. Run the test suite to confirm the install is good:

   ```
   pytest
   ```

## Multiple projects

`bht`/`bhw` aren't limited to one ticket/wiki root. Each project gets its own
`config.local.json` (own `content_roots`, own board/index, own client registry) — for
example, a separate `config.local.json` living inside another repo entirely, with its own
tickets folder and `BOARD.md`.

To avoid needing to pass a raw `--config <path>` around, register a project once in
`config/projects.json` (gitignored, per-machine — copy `config/projects.example.json` to
start):

```json
{
  "personal": "C:\\_local\\source\\Backhaul\\config\\config.local.json",
  "mcrepos": "C:\\_local\\mcRepos\\backhaul\\config.local.json",
  "backhaul": "C:\\_local\\source\\Backhaul\\backhaul\\config.local.json"
}
```

Then `bht --project mcrepos open --client FrontierMode --title "..."` resolves the config by
name from anywhere — no path needed. Omitting both `--project` and `--config` falls back to
this checkout's own `config/config.local.json` (today's default, unchanged). `bht projects` /
`bhw projects` lists what's registered.

### Project folder layout

Inside a project (e.g. `mcRepos/`), Backhaul's own files live under a single `backhaul/`
subfolder — `tickets/`, `wiki/`, `BOARD.md`, `WIKI_INDEX.md`, and (for a project registered in
`projects.json`) its own `config.local.json` — so they don't clutter the project's real
content sitting next to them:

```
mcRepos/
  BACKHAUL.md          <- generated front page, the one thing at the root
  backhaul/
    config.local.json
    tickets/
    wiki/
    BOARD.md
    WIKI_INDEX.md
  FrontierMode/         <- actual project content, untouched
  Satchel/
```

`backhaul dashboard` (re)generates `BACKHAUL.md` — a front page one level above the
`backhaul/` folder linking to the board and wiki index, with live open-ticket/page counts.
`backhaul projects` lists registered projects, same as `bht projects`/`bhw projects`.

## Roadmap module (BHRM)

`modules/roadmap` — a dependency-graph roadmap, ported from a LunaFlow_A prototype
(`intake/roadmap-nodes/`). Every unit of roadmap-load-bearing work is a node (`work` or
`convergence`) with explicit `depends_on` edges instead of a position in a flat sequence;
`frontier` computes what's actionable right now instead of that being memorized. Optional —
add `"roadmap"` to a project's `enabled_modules` and `content_roots.roadmap` to a folder before
`bhrm` will run there. Every subcommand except `projects` checks `enabled_modules` and refuses
to run with a clear message if it isn't listed, rather than silently working regardless.

Node IDs are `RM_<uid>_NNN` (e.g. `RM_ARR_001`), reusing the same `NumberedIdentity` scheme and
the same client-uids.md registry BHT already uses — `--client Arryn` resolves/mints a UID the
same way `bht open --client` does. Each UID is a fully independent graph: `validate`, `frontier`,
`downstream`, etc. are all scoped to one UID, and a `depends_on` entry naming a node under a
different UID is a hard error, not a cross-project link. This is how one shared
`content_roots.roadmap` folder hosts multiple, fully separate roadmaps (e.g. `mcRepos` hosting
both FrontierMode's and Satchel's graphs side by side).

```
bhrm --project lunaflow new --client LunaFlow_A --title "..." --owner Kofi --slug alma
bhrm --project lunaflow frontier --uid RM_LUNA
bhrm --project lunaflow downstream RM_LUNA_010
bhrm --project lunaflow render --uid RM_LUNA --output <path>/ROADMAP.md
```

Pass `--slug <code>` with a short one-word code (not the full title, slugified) when creating a
node — `depends_on` edges and a rendered graph are meant to be skimmed, and a short code reads
better there than a long descriptive slug. `render`/`index` link every node ID straight to its
own file. See the `bhrm` meta wiki page (below) for the full convention writeup.

## Roles module (BHRole)

`modules/roles` — a small, hand-curated set of agent-role pages per project (PM, Architect,
Dev, QA, ...): who's on the team, what each role owns, and a paste-in session bootstrap prompt
for standing up a fresh agent session in that role. Optional — add `"roles"` to a project's
`enabled_modules` and `content_roots.roles` to a folder before `bhrole` will run there.

Unlike BHT/BHW/BHRM, role pages use a **flat slug identity** — a role's `id` is just its
`slug`, no numbering or shared registry — since a project's role set is a short list, not a
growing tree. A role page carrying a `## Session bootstrap prompt` heading + fenced code block
gets a **Launch link** on `ROLES_INDEX.md`: a `claude://cowork/new?q=<prompt>` deep link that
opens a new Cowork session with the bootstrap prompt already in the composer, ready to send. A
role page without that section just has no Launch link.

The link deliberately doesn't auto-attach the project folder via `folder=` — on Windows, `q`
combined with `folder` was observed to flash the prefilled text and then silently clear it
before it could be sent. `bhrole` instead folds the project root into the prompt text itself
("This role's project folder is `<path>` — ask me to attach it before reading anything."), so
the role still knows what to request without fighting that reset.

A launched session is also a bare sandbox — no Backhaul source, nothing pip-installed. Set
`repo_url` in that project's `config.local.json` to this checkout's own git remote (e.g.
`"https://github.com/amkeyte/Backhaul"`) and every Launch link gets a `pip install
"git+<repo_url>.git#subdirectory=src/Backhaul" --break-system-packages` line prepended too, so
the role installs its own CLI before asking for folder access. That reinstalls from
`origin/master` every session, so it only ever sees what's actually been pushed — commit and
push before expecting a freshly launched session to have the latest `bhrole`.

```
bhrole --project lunaflow new --title "QA" --slug qa --persona "Lothar" --purpose "..." --authority "..."
bhrole --project lunaflow index
bhrole --project lunaflow refresh
```

The dashboard shows a `Team` line with the count of `active` roles once both the content root
and the module are configured. See the `bhrole` meta wiki page (below) for the full convention
writeup.

## Running from somewhere other than the real machine (host_root)

Every `editmd:`/`openfolder:` Edit and Folder link, and a role's Launch-link project-folder
line, is built from `content_roots` as configured — correct by construction when the CLI runs
directly on the real machine (the original use case: a human in VS2022), since "where the CLI
is reading files" and "where a human will click the link" are the same machine.

A role launched into a Cowork session breaks that: it's a Linux sandbox, so it can't do file
I/O against `content_roots` written as real Windows paths, and a translated scratch config that
*can* do the I/O then bakes sandbox-mounted paths into every generated link instead of ones a
human can actually open.

Set `host_root` in `config.local.json` to this project's real root path (e.g.
`"C:\\_local\\mcRepos"`) to fix this structurally: every Edit/Folder/Launch-preamble path gets
re-rooted onto `host_root` — computed as its offset from the project root, rejoined onto
`host_root` — instead of wherever `content_roots` currently resolves at runtime. An explicit
`client_folders` entry is never touched (it's already expected to be a real path); only paths
derived from `content_roots` are. Omit `host_root` to keep today's default: links are built
straight from `content_roots` as printed, same as always.

`host_root` only fixes what gets *printed*. The other direction — the CLI's own file I/O —
still trusts `content_roots` literally, and a Windows path like `content_roots.tickets =
"C:\\_local\\mcRepos\\backhaul\\tickets"` isn't absolute on Linux (`os.path.isabs` is false),
so `pathlib` treats it as one opaque relative segment. Left unchecked, every write this config
drives lands relative to wherever the CLI happened to be invoked from — a stray `BOARD.md`
dropped at cwd, not an error, and easy to miss. `load_config()` refuses to load a config
containing any `content_roots` path that isn't absolute on the machine actually running the
command, specifically to turn that into a loud failure instead of a silent wrong-place write.

### BACKHAUL_LOCAL_ROOT — actually doing I/O from a sandbox

`host_root` fixes links; the fail-loud check above only stops the CLI from writing to the
wrong place — neither one lets a launched role's sandbox actually *read or write* real
content. `BACKHAUL_LOCAL_ROOT` is the runtime mount override that does: export it to tell this
one process where the project's true root actually lives on *its own* filesystem right now
(e.g. wherever Cowork mounted the project folder this session), and `load_config()` re-roots
every `content_roots` value onto it before the absolute-path check runs — so a config written
in Windows paths, which would otherwise be refused, loads and works correctly instead:

```
export BACKHAUL_LOCAL_ROOT=/sessions/<session>/mnt/mcRepos
bht --config backhaul/config.local.json board
```

It's an environment variable, not a config field or CLI flag, on purpose: the correct value is
different every fresh Cowork session (a per-machine `config.local.json` can't hold a value
that changes every time), and a session issues many commands, so exporting it once beats
repeating a flag on every call. Only `content_roots` values that fall under the project's
computed Windows-style true root get remapped (via `PureWindowsPath`, so the split works even
though the process itself may be on Linux) — a `client_folders` entry or any other path is
untouched, same as `host_root`'s translation.

This does not address concurrent writes from multiple sessions sharing one filesystem (e.g.
several launched roles working the same project at once). Aggregate-file rebuilds
(`BOARD.md`, `WIKI_INDEX.md`, `ROLES_INDEX.md`) are safe from corruption — `safe_write()`
writes atomically — but not from lost updates, which is low-stakes since those files are
always regenerated wholesale, never hand-edited. ID minting (`bht open`, `bhrm new`) has no
locking and can collide under true concurrent creates; this is a known, accepted gap, not
solved here.

## Dogfooding: Backhaul tracks itself

Since this system exists, Backhaul's own development uses it: `backhaul/` at the repo root
(distinct from `config/config.local.json`, the `personal` project) is a real, self-referential
project registered as `"backhaul"` — its own `tickets/`, `wiki/`, and `roadmap/`, all enabled.

Its wiki's `meta/` category is the **canonical** copy of the module-usage pages
(`bht.md`/`bhw.md`/`bhrm.md`/`bhrole.md` — ID schemes, slug conventions, CLI cheatsheets),
maintained as real content with `bhw` itself rather than hardcoded anywhere. Install (or
update) a copy of these pages into any other project with:

```
bhw --project mcrepos seed-meta
```

Additive only — a page you've since customized in the destination project is never overwritten.
`--source-project` overrides which project's `meta/` category gets copied from (defaults to
`"backhaul"`); `--category` overrides the destination category (defaults to `"meta"`).

## Viewing tickets and the board

Ticket files and `BOARD.md` are plain Markdown. On this machine they're viewed in Chrome
with the **Markdown Viewer** extension (enable "Allow access to file URLs" in the extension's
details page so it can render local `.md` files directly).

## Layout

- `src/Backhaul/backhaul/foundation/` — shared primitives (config, projects, frontmatter,
  slugify, identity, client_registry, templating, filesafety, markers, rollup, refs,
  handler_uri, version_check).
- `src/Backhaul/backhaul/services/` — `ticket` (BHT) and `wiki` (BHW), always enabled.
- `src/Backhaul/backhaul/modules/` — optional, module-gated (`docx`, `shortcuts`, `roadmap`,
  `roles`, handlers). Every module's `manifest.json` carries its own `version` — bumped on a
  breaking change to that module's own behavior/schema, independent of the package's overall
  version.
- `migration/` — design docs for the migration this project was built to support.
- `intake/roadmap-nodes/` — the original LunaFlow_A RoadmapGraph proposal + prototype tooling
  `modules/roadmap` was ported from, kept as reference (design docs, pilot data used as test
  fixtures) — not shipped as part of the module itself.

See `migration/ARCHITECTURE.md` and `migration/MODULE_SYSTEM.md` for how these pieces fit
together.
