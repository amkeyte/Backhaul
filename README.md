# Backhaul

Portable wiki + ticket (passdown) system: foundation + BHT (ticket) / BHW (wiki) services,
plus optional modules (docx editing, Windows shortcuts, URL-protocol handlers).

**Status:** `foundation/`, the `ticket` (BHT) service, and the `wiki` (BHW) service are all
implemented, with working `bht`/`bhw` CLIs. `modules/handlers/{editmd,openfolder}` (Notepad++
and Explorer integration for rendered links) are implemented too; `modules/docx` and
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
  "mcrepos": "C:\\_local\\mcRepos\\backhaul\\config.local.json"
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

## Viewing tickets and the board

Ticket files and `BOARD.md` are plain Markdown. On this machine they're viewed in Chrome
with the **Markdown Viewer** extension (enable "Allow access to file URLs" in the extension's
details page so it can render local `.md` files directly).

## Layout

- `src/Backhaul/backhaul/foundation/` — shared primitives (config, projects, frontmatter,
  slugify, identity, templating, filesafety, markers, rollup, refs, handler_uri, version_check).
- `src/Backhaul/backhaul/services/` — `ticket` (BHT) and `wiki` (BHW), always enabled.
- `src/Backhaul/backhaul/modules/` — optional, module-gated (`docx`, `shortcuts`, handlers).
- `migration/` — design docs for the migration this project was built to support.

See `migration/ARCHITECTURE.md` and `migration/MODULE_SYSTEM.md` for how these pieces fit
together.
