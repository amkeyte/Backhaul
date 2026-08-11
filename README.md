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

```
bhrole --project lunaflow new --title "QA" --slug qa --persona "Lothar" --purpose "..." --authority "..."
bhrole --project lunaflow index
bhrole --project lunaflow refresh
```

The dashboard shows a `Team` line with the count of `active` roles once both the content root
and the module are configured. See the `bhrole` meta wiki page (below) for the full convention
writeup.

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
