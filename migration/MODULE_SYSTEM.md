# Module System — the poor man's plugin design

**Status:** Draft — proposes a design, has an open fork that needs a decision (§4).
**Depends on:** `MIGRATION_PLAN.md` (config design, §6), `PYTHON_PROJECT_SETUP.md` (package
layout), `ARCHITECTURE.md` (foundation/services/modules layer model — **read that first**,
this doc's `core/` references below mean "foundation," and BHT/BHW live in `services/`, not
inside this folder).

## 1. The problem

Not everything sorts cleanly into "system (repo)" vs. "content (Aaron K)." Some things are
system — not client data, safe to version-control — but only relevant on machines actually
doing that kind of work. The example: the docx/DAS tooling isn't needed on a personal PC,
and if this repo ever gets handed to a coworker, they may want the docx tooling *without*
wanting the ticket/wiki system at all. Domain-specific, but a different axis than
content-vs-system.

## 2. Design: `foundation/` + `services/` + `modules/<name>/`

```
Backhaul/
  foundation/
    manifest.json          <- {"id": "foundation", "requires": []}
    src/backhaul/foundation/
      config.py             <- config loader
      frontmatter.py         <- frontmatter parser
      collection.py          <- generic engine BHT/BHW specialize (see ARCHITECTURE.md)
      version_check.py
  services/
    ticket/                 <- BHT
      manifest.json          <- {"id": "ticket", "requires": ["foundation"]}
      skills/ticket/
    wiki/                   <- BHW
      manifest.json          <- {"id": "wiki", "requires": ["foundation"]}
      skills/wiki/
  modules/
    docx/
      manifest.json         <- {"id": "docx", "requires": ["foundation"], "deps": ["python-docx", ...]}
      src/
      skills/
        docx/               <- travels with the module when it's packaged
      requirements.txt      <- module-specific deps, on top of foundation's
  scripts/
    package_module.py        <- zip a module (+ its dependency chain) for hand-carrying
    install_module.py        <- unpack a module zip on a receiving machine, register it
```

Each module (and each service) is a self-contained folder: its own code, its own skill
package(s), its own extra dependencies. `manifest.json` declares what it needs from the rest
of the repo (currently just `requires: [other ids]`, could grow fields later — kept minimal
on purpose). Services and modules use the same manifest shape — a service is just a module
that happens to specialize `foundation.collection` rather than doing something foundation
doesn't already provide.

## 3. Config gets an `enabled_modules` list

**Decided (2026-07-31): BHT and BHW are always present, on every machine, unconditionally.**
Per Aaron — they're "the point" of this whole system, not optional pieces. So `foundation`,
`services/ticket`, and `services/wiki` are baseline: every checkout has them, no toggle, no
entry in the config needed to "turn them on." `enabled_modules` exists only for genuinely
optional things under `modules/` — docx today, whatever comes later.

Extends the schema from `MIGRATION_PLAN.md` §6:

```json
{
  "content_root": "C:\\_R Clone\\Project_Managers\\Aaron K",
  "setup_version": "0.1.0",
  "enabled_modules": []
}
```

Personal PC's config simply has an empty (or absent) `enabled_modules` list — no docx, but
still has ticket/wiki, since those aren't part of this toggle at all. Any skill or script
that's module-specific (docx, etc.) checks this list before assuming it's available, and
fails with a clear "this module isn't installed here" message rather than a confusing import
error. This is the actual "roll it into the config problem" part — a machine's config is now
also the answer to "what optional stuff is installed here," on top of "where's the content."

## 4. Packaging: `git archive`, not custom zip logic

Since this is already a git repo, the zip mechanism doesn't need to be invented — `git archive`
does exactly this natively:

```bash
git archive --format=zip -o docx.zip HEAD -- modules/docx foundation   # (foundation included if required)
```

`scripts/package_module.py <name>` is a thin wrapper: read `modules/<name>/manifest.json`,
resolve the `requires` chain, run `git archive` over the resulting set of paths, done. No
custom zip-building code — this is what "minimal infrastructure" looks like in practice.

On the receiving machine: unzip into a `Backhaul/` folder (fresh or existing), run
`scripts/install_module.py <name>` — which either bootstraps a new `config.local.json` (first
module ever installed there) or appends to an existing one's `enabled_modules`.

## 5. Open fork — needs a decision

**Does a domain module depend on `foundation`, or should modules be designed to also stand
completely alone?**

- **If modules always require `foundation`:** `package_module.py docx` bundles `foundation`
  automatically (per its manifest), so a coworker gets config-loading and frontmatter parsing
  along with docx tools — but *not* the ticket/wiki system, since (per `ARCHITECTURE.md`)
  BHT/BHW are services, not part of foundation. Simpler to build — one dependency model, no
  special-casing.
- **If modules can be foundation-free too:** docx tooling would need to not import anything
  from `backhaul.foundation` at all — fully standalone scripts. More work up front, matches
  "hand a coworker exactly what they need" most literally, but foundation is small enough
  (config + frontmatter + version check) that this is probably not worth the duplication.

Leaning toward the first option — a module depending on `foundation` but never automatically
pulling in `services/ticket` or `services/wiki` unless it specifically needs them — but this
is genuinely your call.
