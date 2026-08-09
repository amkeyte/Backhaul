# Backhaul

Portable wiki + ticket (passdown) system: foundation + BHT (ticket) / BHW (wiki) services,
plus optional modules (docx editing, Windows shortcuts, URL-protocol handlers).

**Status:** early scaffold. `identity`, `frontmatter`, and the `shortcuts` module are
implemented; most of `foundation/` and the `ticket`/`wiki` services are stubs
(`raise NotImplementedError`) — see `migration/*.md` for the design docs driving that work.

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

## Layout

- `src/Backhaul/backhaul/foundation/` — shared primitives (config, frontmatter, slugify,
  identity, templating, filesafety, markers, rollup, refs, version_check).
- `src/Backhaul/backhaul/services/` — `ticket` (BHT) and `wiki` (BHW), always enabled.
- `src/Backhaul/backhaul/modules/` — optional, module-gated (`docx`, `shortcuts`, handlers).
- `migration/` — design docs for the migration this project was built to support.

See `migration/ARCHITECTURE.md` and `migration/MODULE_SYSTEM.md` for how these pieces fit
together.
