---
id: design/migration-plan
category: design
slug: migration-plan
title: Backhaul Migration Plan
summary: 'The Aaron K -> Backhaul migration: goals, phases, config/versioning design,
  decisions log.'
keywords: null
status: published
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · design
<!-- bh-header:end -->

# Backhaul Migration Plan

**Status:** Draft — for review, not yet approved for execution.
**Purpose:** Extract the reusable "system" (scripts, templates, skills, how-to wiki) currently
living inside `C:\_R Clone\Project_Managers\Aaron K\CLAUDE Stuff\` into this repo (Backhaul),
so it's version-controlled, portable across machines, and improvable without touching the
live client data it currently sits next to. Client content stays exactly where it is and
keeps working unmodified throughout.

---

## 1. Naming

**Backhaul** — "Claude Backed Information Hauler System" (per the repo README). The metaphor:
this repo is the backhaul link that carries a working setup to wherever it needs to reach,
without degrading it.

**Decided naming scheme for sub-components:**
- Long/service names: **BackhaulTicket**, **BackhaulWiki** (and future services follow the
  same `Backhaul<Thing>` pattern).
- Short/code names: **BHT** (BackhaulTicket), **BHW** (BackhaulWiki) — for use in code,
  filenames, config keys, CLI prefixes, etc.

## 2. Goals

- Move all reusable logic (scripts, templates, skill instructions, process/how-to wiki
  pages) into this git repo, so it can be improved on one machine and pulled onto another.
- Make the system **config-driven**: no hardcoded paths to a specific machine's content
  folder. One gitignored local config file per machine tells the repo where that machine's
  content lives.
- Keep the existing Aaron K system **fully working and untouched** until the migrated
  version is proven equivalent. This is a copy-then-cut-over migration, not an in-place
  rewrite.
- Reduce the "update N skills every time I fix something" problem via thin router skills
  whose installed body is just a pointer into this repo, read fresh at invocation time.

## 3. Non-goals (for this pass)

- **`Templates/` is content-side, decided.** DAS Annual Form, Blank Document Template, style
  guides — these stay in Aaron K, not Backhaul. Even though they're not client-*specific*,
  they're operational content (get filled in/edited per job) rather than system tooling.
- Not changing the ticket/wiki file *formats* in this pass — the goal is relocation +
  config-driven paths, not a redesign of what a ticket or wiki page looks like. Format
  changes are a later, separate effort once the schema-versioning mechanism (§6) exists to
  support them safely.
- Not deleting anything from Aaron K. Decommissioning the old in-place scripts is the last
  phase, done deliberately, not as a side effect of this migration.

## 4. Current-state inventory: system vs. content

The existing structure already separates these reasonably well by folder — the migration
mostly follows lines that already exist rather than inventing new ones.

### System (moves to Backhaul)

| Area | Path (under `CLAUDE Stuff/`) | Contents |
|---|---|---|
| Ticket engine | `_passdown/scripts/`, `_passdown/templates/` | `new_ticket.py`, `build_board.py`, `ticket.md.tmpl` — becomes **BHT** (`services/ticket/`), rewritten as a specialization of `foundation.collection`, not relocated as-is (see `ARCHITECTURE.md`) |
| Wiki engine | `Wiki/scripts/`, `Wiki/templates/` | `new_page.py`, `build_index.py`, `page.md.tmpl` — becomes **BHW** (`services/wiki/`), same treatment |
| General scripts | `Scripts/*.py`, `Scripts/editmd/`, `Scripts/openfolder/` | docx pack/unpack/verify, form populators → `modules/docx/`; `make_lnk.py` → `modules/shortcuts/`; `namecheck.py` + config/frontmatter helpers → `foundation/`; the two URL-protocol handlers → `modules/handlers/` |
| How-to wiki | `Wiki/conventions/`, `Wiki/reference/`, `Wiki/meta/`, `Wiki/windows/`, `Wiki/pctel/`, `Wiki/skills/` | process documentation — how to edit docx, the DAS project lifecycle, PCTEL data model, wiki conventions, etc. |
| Skill definitions | (wherever the `.plugin`/skill source lives — see §7) | `ticket`, `new-wiki-page`, `doc-lint`, `doc-scaffold`, `qa-verify`, `create-shortcut` |

### Content (stays in Aaron K, never moves)

| Area | Path | Why it's content |
|---|---|---|
| Client knowledge | `Wiki/knowledge-base/clients/**` | Real client names, contacts, site facts |
| AHJ knowledge | `Wiki/knowledge-base/ahj/**` | Real fire marshal names/phone numbers — identifying info, not process |
| Client registry | `_passdown/client-uids.md` | Literally a list of real client names |
| Ticket instances | `_passdown/GEN_*.md`, `__Projects/<Client>/_passdown/*.md` | Live work state — currently 9 global + 3 Precision Electric + 5 Shoreline SD + 1 Swedish + 2 University of Washington |
| Generated board | `passdown-board.md` | Derived from ticket instances; regenerated, never hand-edited, never migrated |
| Project files | `__Projects/**` (everything else) | The actual client deliverables, drawings, coverage data |

### Borderline / needs a call

- `Wiki/knowledge-base/index.md` and `Wiki/knowledge-base/clients/index.md` — hand-maintained
  pages that mix a content list (real client names) with structural content (the category
  description). These get **rewritten**, not moved: Backhaul's wiki gets its own empty/generic
  index; the content-side index stays in Aaron K and keeps listing real clients.

## 5. Target repo structure (Backhaul)

**Superseded by `ARCHITECTURE.md` and `PYTHON_PROJECT_SETUP.md` — this is the reconciled
version.** Code lives under `src/backhaul/` as an installable package (`foundation` /
`services/` / `modules/`, per `ARCHITECTURE.md`), not as loose top-level `scripts/` folders as
originally sketched here.

```
Backhaul/
  migration/                 <- this plan and its follow-ups
  config/
    config.schema.json        <- documents the expected shape of a local config
    config.local.json         <- GITIGNORED. Created once per machine.
  src/backhaul/
    foundation/                <- config loader, frontmatter parser, the generic collection
                                   engine BHT/BHW specialize, version_check. Always present.
    services/
      ticket/                   <- BHT. Always present (not gated by enabled_modules).
      wiki/                     <- BHW. Always present.
    modules/
      docx/                     <- pack/unpack/verify/populate_form. Optional (enabled_modules).
      shortcuts/                <- make_lnk.py + the pylnk3 segment-typing fix. Optional.
      handlers/
        editmd/                 <- editmd.vbs, editmd.reg, editmd_link.py
        openfolder/              <- openfolder.vbs, openfolder.reg, openfolder_link.py
  wiki/                       <- the how-to wiki (conventions/reference/meta/windows/pctel/skills)
  skills/
    ticket/                  <- BackhaulTicket (BHT): real installable skill folder
      SKILL.md               <- trigger metadata + router body pointing at instructions/
      instructions/
        INSTRUCTIONS.md
    wiki/                    <- BackhaulWiki (BHW): same shape
      SKILL.md
      instructions/
        INSTRUCTIONS.md
    docx/
      ...
    build/                   <- zips each skill/<name>/ folder into <name>.skill for
                                 drag-and-drop install into the Claude app
  tests/                      <- pytest, against synthetic fixtures only (see §8, §10)
  VERSION                     <- current framework version (see §6)
  requirements.txt            <- pyyaml, pylnk3, pinned
  pyproject.toml              <- packaging metadata + CLI entry points (bht, bhw, ...)
  Backhaul.pyproj              <- VS2022 project file
  README.md
```

## 6. Config + versioning design

**Config file:** `Backhaul/config/config.local.json`, gitignored, created once per machine by
a small interactive `configure.py` (asks for the content-root path, writes the file). Every
script in the repo reads this file relative to its own location (`Path(__file__).parents[N] /
"config" / "config.local.json"`) — never assumes it's colocated with content, never relies on
an environment variable (bash calls in this environment don't persist env or cwd between
calls, so a file is the only reliable mechanism).

Minimum schema:
```json
{
  "content_root": "C:\\_R Clone\\Project_Managers\\Aaron K",
  "setup_version": "0.1.0"
}
```

**Versioning:** two markers, per Aaron's plan.
- `Backhaul/VERSION` — the framework version this checkout is at.
- `config.local.json["setup_version"]` — the version this machine was last set up/acknowledged
  against.

Every skill's router body checks these on invocation; a mismatch surfaces a note rather than
silently running against a stale checkout. Running an agent against a stale repo without
pulling is treated as user error, per Aaron — the system's job is only to make that visible.

**Decided: one version number for now**, not split framework/schema. Good enough as a tripwire
— it doesn't need to be precise about *what* changed, just that something did, so a check runs
before continuing work. When `VERSION` and `config.local.json["setup_version"]` disagree, the
safety check is: **read a `git diff`/`git log` between the two versions** (tags, or just
commit range) and summarize what changed — that's enough to tell whether the drift is
cosmetic (a docs fix) or something that actually needs remediation in existing content (a
format change). This becomes a small script (`scripts/lib/version_check.py` or similar):
given an old and new version marker, produce a plain-language summary of what's different,
surfaced to the agent/Aaron before other work proceeds. Cheaper than maintaining a second
version number, and works because the repo's own history is the source of truth for "what
changed."

## 7. Skill architecture: router pattern

Each installed skill (`ticket`, `wiki`, etc.) keeps only:
- Its trigger metadata (name + description) — the only part that requires a `save_skill` call
  to update, and should change rarely.
- A short body that (a) points at `Backhaul/skills/<name>/INSTRUCTIONS.md` for the full
  procedure, read fresh via `Read` every invocation, and (b) contains a small internal index
  so the agent doesn't have to load the entire instructions file for every request shape
  (e.g. "opening a ticket → §2; closing → §4; board question → §1").

Net effect: fixing a bug or adding a step to how tickets get created is a normal git commit —
zero Cowork-side sync. Only new skills or changed trigger conditions need `save_skill`.

**Decided: `Backhaul/skills/` holds the real, properly-formatted skill packages** — each a
folder with a correctly-named `SKILL.md` (frontmatter matching what Cowork expects) plus its
`instructions/` subfolder, structured so it can be zipped into a `<name>.skill` file and
installed by dragging it into the Claude app (the app renders `.skill` files with a "Save
skill" install button). A `skills/build/` step handles the zipping so the repo always has an
installable artifact ready, not just source.

This is orthogonal to the native-vs-mechanical question (§8) — the router only changes *where*
instructions are loaded from, not *what* runs as a script vs. what the agent reasons through.

## 8. Native (agent reasoning) vs. mechanical (script) split

Kept from the existing pattern, made explicit as a rule going forward:

- **Script territory:** anything that must be exactly right every time and is cheap to make
  deterministic — ticket templating, ID numbering, frontmatter YAML, board generation, wiki
  index/breadcrumbs, docx pack/unpack, the pylnk3 segment-retyping fix. These get tests
  (a small pytest suite that runs the real scripts against fixture content) as part of this
  migration, not as an afterthought.
- **Agent territory:** judgment calls that a script shouldn't be trying to replicate —
  interviewing for ticket content, deciding what's content vs. system for a new item, writing
  prose for a Summary/Log entry, deciding which wiki category something belongs in.

## 9. Migration phases

**Revised 2026-07-31** to reflect the foundation/services/modules architecture — the original
version of this section assumed a light relocation ("copy the scripts as-is"), which no longer
matches: `foundation.collection` is a genuine rewrite that BHT and BHW both specialize, not a
file move. Aaron K's live scripts keep running untouched throughout regardless — that
guarantee doesn't change, just how "porting" is defined.

1. **Snapshot for reference, don't touch the original.** Copy the system-side files (§4 table)
   into a `migration/legacy-snapshot/` folder in this repo — not the target `src/` location —
   purely so the old implementation is a fixed, version-controlled reference to build the new
   one against and diff parity later. Aaron K's live scripts are untouched and stay
   authoritative. This is a snapshot, not the start of the real port.
2. **Build the foundation.** Implement `foundation/` (config loader, frontmatter parser,
   `collection.py`, `version_check.py`) per the interface design in `ARCHITECTURE.md`. This is
   new code, not adapted from the legacy snapshot — the legacy scripts don't have a
   generic/parameterized engine to lift, that's the whole point of building one. Gets its own
   test coverage before anything is built on top of it.
3. **Build BHT and BHW as specializations.** Each defines its schema, lifecycle states, and
   access rules, and calls into `foundation.collection` for the shared mechanics. Tested as a
   dry run against Aaron K's real content — output compared against what the legacy
   `new_ticket.py`/`build_board.py`/`new_page.py`/`build_index.py` produce — before either is
   considered done. Legacy scripts stay live and authoritative until parity is confirmed.
4. **Port the optional modules.** `docx`, `shortcuts`, `handlers/editmd`, `handlers/openfolder`
   move into `modules/`, each with a `manifest.json`, depending on `foundation` only (per the
   open fork in `MODULE_SYSTEM.md` §5 — resolve that before this phase, not during it).
5. **Split the wiki.** Move `conventions/reference/meta/windows/pctel/skills` into
   `Backhaul/wiki/`, now that BHW exists to serve it. Content-side wiki gets a plain-text "see
   the repo wiki for details" pointer where useful; no cross-linking (per Aaron).
6. **Stand up router skills.** Rewrite each skill's installed body down to trigger metadata +
   pointer, move the actual procedures into `Backhaul/skills/*/instructions/INSTRUCTIONS.md`.
   `save_skill` each one once. Build the `.skill` packaging step (`skills/build/`).
7. **Cut over.** Repoint the live system at the Backhaul-hosted services/modules/skills. Old
   in-place copies in Aaron K marked deprecated (not silently left ambiguous).
8. **Decommission.** After a burn-in period with no issues, remove the deprecated in-place
   copies from Aaron K, leaving only content there.

Each phase should be its own PR/commit set, independently revertible.

## 10. Risk register

| Risk | Mitigation |
|---|---|
| Sandbox may not persist `pip install`s across separate Cowork sessions (only within one) | Every script-invoking instruction does a cheap idempotent dependency check/install, not a "assume it's there" call |
| Two copies (old + new) coexist during migration; an agent defaults to the old path out of habit | Explicit, unambiguous deprecation markers in phase 6, not a quiet parallel existence |
| Ticket/wiki format drift breaks the regex/YAML-based parsers | Small pytest suite over real fixture content, run before any script is considered "ported" |
| Content accidentally committed to git history (e.g. a real client name in a README example) | Pre-commit check extending the existing `namecheck.py` pattern to scan for known client names before a commit lands |
| Two independent wikis drift or duplicate the same how-to content | Convention: content wiki never restates how-to, only points at "the repo wiki"; periodic manual check, not automated for now |
| Config file missing/stale on a given machine | `configure.py` is idempotent and safe to re-run; version mismatch is surfaced at skill invocation, not silently ignored |
| Agent session has only one of {repo, content} folder connected | Skills should fail loud with a clear "connect the other folder" message rather than guessing paths |

## 11. Decisions log

Original open-decisions list, all resolved 2026-07-31:

1. Does `Templates/` count as system? → **Content-side.** Stays in Aaron K.
2. One version number or two? → **One**, with a git-diff-based safety check run on
   mismatch (see §6) rather than a second precise schema marker.
3. Where do Cowork skill sources live? → **`Backhaul/skills/`** — real, properly-formatted,
   drag-and-drop-installable skill packages, source of truth in the repo, `save_skill` (or a
   manual drag-and-drop) as the publish step.
4. Naming scheme? → **Decided** — see §1 (BackhaulTicket/BHT, BackhaulWiki/BHW).

Decisions made since, each in its own doc:

- **Package vs. loose scripts** → package (`src/backhaul/`, installable, CLI entry points).
  See `PYTHON_PROJECT_SETUP.md`.
- **Domain-optional tooling** (docx/DAS not needed on every machine) → `foundation/` +
  `services/` + `modules/<name>/`, `git archive`-based packaging, `enabled_modules` in config.
  See `MODULE_SYSTEM.md`. **Still open within that doc:** whether a module may depend on
  `foundation` only or must also be able to stand fully alone (§5 there).
- **Does every module get its own core?** → No — one shared `foundation/`; BHT/BHW are
  services built on it, not modules beside it. See `ARCHITECTURE.md`.
- **Are BHT/BHW themselves optional?** → No — baseline, always present, not gated by
  `enabled_modules`. Per Aaron: they're the point of the system. See `ARCHITECTURE.md` and
  `MODULE_SYSTEM.md` §3.
- **Migration phase list** → revised to match this architecture; see §9 above. Phase 1 is now
  a reference snapshot, not a relocation — the real port (phases 2–3) is new code against a
  designed interface, not adapted from the legacy scripts.
- **Solution Explorer layout** → four groupings in `Backhaul.sln`: the existing Solution
  Items, a new **Docs** folder (`migration/`, later `wiki/`), a new **Skills** folder
  (`skills/`), and one Python project (`Backhaul.pyproj`, not split from tests). See
  `SOLUTION_LAYOUT.md`.
- **`foundation.collection` design** → it's not one class. It's a toolkit of independent
  primitives (frontmatter, identity, templating, file safety, marked-block refresh, rollup
  building, cross-references, version check) that BHT and BHW each wire together according to
  their own schema/lifecycle/identity scheme, which turn out to differ more than the earlier
  docs assumed (numbered vs. path-based identity; single vs. multi-document rollups). Full
  interface design, plus how each service wires it, in `FOUNDATION_DESIGN.md`. Rollup
  rendering is deliberately *not* shared — `foundation.rollup` only collects/filters/groups;
  each service renders its own output shape (board table vs. category index).

## 12. Appendix: exact current inventory (as of 2026-07-31)

**Scripts (`CLAUDE Stuff/Scripts/`):** `pack.py`, `unpack.py`, `verify.py`, `make_lnk.py`,
`namecheck.py`, `populate_form.py`, `populate_das_form.py`, `populate_canyon_pointe_das.py`,
`prune_empty_critical_points.py`, `editmd/` (4 files), `openfolder/` (4 files).

**Ticket engine (`CLAUDE Stuff/_passdown/`):** `scripts/new_ticket.py`, `scripts/build_board.py`,
`templates/ticket.md.tmpl`. Content alongside it (not moving): `client-uids.md`, 9 global
tickets, plus per-client `_passdown/` folders (Precision Electric: 3, Shoreline School
District: 5, Swedish: 1, University of Washington: 2).

**Wiki engine (`CLAUDE Stuff/Wiki/`):** `scripts/new_page.py`, `scripts/build_index.py`,
`templates/page.md.tmpl`. How-to categories (moving): `conventions/` (7 pages),
`reference/` (4), `meta/` (1), `windows/` (1), `pctel/` (13), `skills/` (index only).
Content categories (not moving): `knowledge-base/` (clients + ahj, 7 pages currently).

**Skills currently wrapping this system:** `ticket`, `new-wiki-page`, `doc-lint`,
`doc-scaffold`, `qa-verify`, `create-shortcut`.
