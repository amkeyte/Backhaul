---
id: design/python-project-setup
category: design
slug: python-project-setup
title: Python Project Setup — Backhaul.sln
summary: The Python package layout, VS2022 project setup, and .gitignore additions.
keywords: null
status: published
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · design
<!-- bh-header:end -->

# Python Project Setup — Backhaul.sln

**Status:** Draft — plan for the Python project Aaron will add to the solution.
**Depends on:** `MIGRATION_PLAN.md` (target structure, §5), `ARCHITECTURE.md`
(foundation/services/modules layer model — this doc's layout follows that, superseding the
flat `src/backhaul/ticket|wiki|...` sketch this file originally had), `SOLUTION_LAYOUT.md`
(where this project sits relative to the Docs/Skills groupings, and the single-vs-split
`.pyproj` decision — resolved there as **single project**).

This doc covers the Python project's internals specifically. For the whole solution picture
(Docs, Skills, and how this project fits alongside them), see `SOLUTION_LAYOUT.md`.

## Recommended layout

```
Backhaul/
  src/
    backhaul/
      __init__.py
      foundation/      <- config loader, frontmatter parser, the generic collection engine
                            BHT/BHW specialize, version_check
      services/
        ticket/         <- BHT: schema + lifecycle + access rules, rest inherited from foundation
        wiki/           <- BHW: same, for wiki pages
      modules/
        docx/           <- pack/unpack/verify/populate_form; depends on foundation only
        shortcuts/      <- .lnk builder (the pylnk3 segment-typing fix lives here)
        handlers/
          editmd/
          openfolder/
  tests/
    test_foundation.py
    test_ticket.py
    test_wiki.py
    test_docx.py
    fixtures/         <- SYNTHETIC ticket/wiki content only — never real client data,
                          per the migration plan's risk register (content-in-git-history)
  Backhaul.pyproj      <- VS project file
  pyproject.toml       <- packaging metadata + CLI entry points
  requirements.txt
  .venv/                <- gitignored, project-local virtual environment
```

## Decision point: package vs. loose scripts

`MIGRATION_PLAN.md` §5 originally sketched `scripts/ticket/`, `scripts/wiki/`, etc. as folders
of standalone CLI scripts — matching how things exist today in Aaron K (each script does its
own `sys.path.insert` and re-derives its root by walking up from `__file__`).

Setting this up as a real VS Python project is a natural point to upgrade that into an actual
installable package (`src/backhaul/`) instead of loose scripts. That gets proper imports
instead of path-hacking, real IntelliSense/type-checking in VS, a place for the shared `lib/`
modules to actually be shared (rather than each script separately inserting the same
`sys.path` entry), and clean CLI entry points — `bht open --title "..."` instead of
`python3 scripts/ticket/new_ticket.py --title "..."` — which the router skills can call
directly.

**Recommending this change**, but flagging it explicitly since it revises what §5 already
described rather than just matching it. Needs a yes/no before the ticket/wiki scripts actually
get ported (migration phase 3).

## VS2022 setup steps

1. Solution Explorer → right-click the solution → **Add → New Project** → a Python project
   template (Application or Package), rooted at `src/`, named `Backhaul` (per
   `SOLUTION_LAYOUT.md` — one project, not split).
2. Under that project's **Python Environments** node → **Add Environment → Virtualenv**,
   pointed at `.venv/`, built from `requirements.txt`. Keeps the interpreter project-local
   instead of depending on whatever Python is globally installed on a given machine — matters
   more once this is running on a second PC with an unknown Python setup.
3. Add `tests/` to the same project and install `pytest` + the VS Python Test Adapter, so Test
   Explorer can discover and run the suite directly. This is what makes "tests as part of the
   migration" (per `MIGRATION_PLAN.md` §8) something that actually gets run day to day, not
   just talked about.
4. `pyproject.toml` with `[project.scripts]` entries for the CLI surface —
   `bht = "backhaul.ticket.cli:main"`, `bhw = "backhaul.wiki.cli:main"` — installed via
   `pip install -e .` inside the venv.

## `.gitignore` additions needed

The current `.gitignore` already covers `__pycache__/` and `*.pyc` (PTVS section), but nothing
for a virtual environment or the local config file yet:

```
.venv/
config/config.local.json
*.egg-info/
```

## Resolved

Single project vs. split test project — **decided single**, see `SOLUTION_LAYOUT.md`. Revisit
only if the test suite grows enough to want independent build/run, not before.
