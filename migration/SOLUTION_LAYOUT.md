# Solution Layout — what lives in Backhaul.sln

**Status:** Draft.
**Depends on:** `PYTHON_PROJECT_SETUP.md` (Python project internals — this doc covers the
whole solution, that one covers just the code project in detail).

`Backhaul.sln` currently has one thing: a **Solution Folder** called "Solution Items" holding
`.gitattributes`, `.gitignore`, `README.md` (this is the standard VS mechanism for grouping
loose files that aren't part of a buildable project — no compiler, just organization in
Solution Explorer). Everything below builds on that same mechanism plus one real code project.

## The four groupings

```
Backhaul.sln
├─ Solution Items/          (existing)         .gitattributes, .gitignore, README.md
├─ Docs/                    (NEW)              migration/*.md, and wiki/ once phase 5 moves it in
├─ Skills/                  (NEW)              skills/*/SKILL.md, instructions/, build/
└─ Backhaul (Python project) (NEW)             src/backhaul/, tests/, pyproject.toml, ...
```

### Docs

A Solution Folder pointed at `migration/` (kept at that name — it's already referenced
throughout every doc's cross-links, no reason to rename it to `docs/` and break them). Once
migration phase 5 happens, `wiki/` joins it too. Purpose is purely organizational: right now
these five `.md` files are just loose in the repo root's `migration/` folder; grouping them in
Solution Explorer makes them visible/navigable the same way code is, without needing any build
tooling — markdown doesn't compile.

**Mechanic:** classic Solution Folders (the kind already used for "Solution Items") list
member files individually in the `.sln`'s `ProjectSection(SolutionItems)` block — adding a new
doc means adding one line there, not something that auto-discovers new files. Newer VS2022
builds also support folder-backed solution folders that mirror a real directory's contents
automatically (no manual per-file entries) — worth checking whether that option's available
in Aaron's specific VS2022 install before committing to the manual-itemized approach, since
it'd save the "remember to add it to the .sln" step every time a new migration doc shows up.
I can't click through the actual VS UI to confirm which is available — that's a two-minute
check on Aaron's end (right-click the solution → Add → New Solution Folder, then right-click
that folder and see whether "Add → Existing Folder" or similar shows up as an option).

### Skills

Same mechanism, pointed at `skills/`. Kept separate from Docs even though it's mostly markdown
too (`SKILL.md` + `instructions/*.md`), because it's a genuinely different kind of artifact —
each `skills/<name>/` folder is a real installable deliverable (gets zipped into a `.skill`
file, per `MIGRATION_PLAN.md` §7), not reference documentation. Worth being able to look at
Solution Explorer and immediately tell "this is something I ship" apart from "this is a design
doc," rather than one big undifferentiated Docs bucket.

### Backhaul (the Python project)

One project, not split — **resolving `PYTHON_PROJECT_SETUP.md`'s open question**: a single
`Backhaul.pyproj` covering both `src/backhaul/` and `tests/`, using the VS Python Test Adapter
for `tests/` discovery rather than a separate test project. At this size (foundation +
two services + a handful of modules), a second project file buys organizational purity at the
cost of two things to keep in sync (two environments, two sets of project settings) for no
real benefit yet. Revisit only if the test suite grows enough that independent build/run
actually matters — not a prediction that'll happen, just the condition under which it'd be
worth reopening this.

Full internals (venv setup, `pyproject.toml`, CLI entry points, `.gitignore` additions) are in
`PYTHON_PROJECT_SETUP.md` — this doc just fixes where it sits relative to Docs/Skills.

## Net picture in Solution Explorer

```
Backhaul
├─ Solution Items
│    .gitattributes
│    .gitignore
│    README.md
├─ Docs
│    migration/MIGRATION_PLAN.md
│    migration/ARCHITECTURE.md
│    migration/FOUNDATION_DESIGN.md
│    migration/MODULE_SYSTEM.md
│    migration/PYTHON_PROJECT_SETUP.md
│    migration/SOLUTION_LAYOUT.md
│    (wiki/... once phase 5 lands)
├─ Skills
│    skills/ticket/...
│    skills/wiki/...
│    skills/docx/...
└─ Backhaul (Python Application)
     src/backhaul/foundation/...
     src/backhaul/services/...
     src/backhaul/modules/...
     tests/...
     pyproject.toml
     requirements.txt
```
