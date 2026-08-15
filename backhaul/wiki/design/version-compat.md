---
id: design/version-compat
category: design
slug: version-compat
title: Version & Schema Compatibility Plan
summary: 'How framework/module/instance versions interact: schema_version stamped
  per file, explicit migrate command, hard-fail on unmigratable drift. Supersedes
  the git-diff drift-check sketch in migration-plan.md §6.'
keywords: null
status: draft
updated: '2026-08-14'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · design
<!-- bh-header:end -->

# Version & Schema Compatibility Plan

**Status:** Draft — supersedes the version-tracking sketch in [Backhaul Migration
Plan](migration-plan.md) §6. That sketch (one `VERSION` file, one `setup_version` in
`config.local.json`, a git-diff prose summary read by a human/agent on mismatch) is dropped
outright, not kept as a fallback — see §6 below for why.

**Purpose:** when a consumer project (mcRepos, LunaFlow_A, ...) pulls in new Backhaul
functionality that changes a module's schema, existing content in that project must either
keep working, be cleanly migratable, or fail loudly and specifically. Silent misreads
(dropped fields, wrong defaults, a corrupted rewrite) are the failure mode this exists to rule
out — never a "probably fine" outcome.

## 1. The version axes already in the repo

Four version concepts exist or are implied today; only one is new.

| Axis | Where it lives | What it currently does |
|---|---|---|
| Framework version | `VERSION`, `pyproject.toml["version"]` | Identifies the checkout. Gates nothing at runtime. |
| Config schema version | `config.schema.json["version"]` / `CONFIG_SCHEMA_VERSION` | Already enforced — `load_config()` refuses a `config.local.json` whose `version` doesn't match. Covers only the shape of the config file itself. |
| Module schema version | Each `manifest.json["version"]` (foundation, ticket, wiki, roadmap, roles, ...) | Informational only. Bumped by convention on a breaking change to that module's own schema/behavior, but nothing reads it to compare against anything. |
| **Instance version** (new) | Not tracked anywhere today | Which schema a given *content file* (one ticket, one wiki page, one roadmap node, one role page) was actually written against. Without this there is no way to distinguish an old-shape file from a new one once a module's schema changes. |

This plan's only structural addition is the fourth row. The other three keep their current
jobs unchanged — in particular, config schema versioning is already solved and out of scope
here.

## 2. `schema_version`: a new frontmatter field

Every content template (`ticket.md.tmpl`, `page.md.tmpl`, the roadmap node template, the role
template) gains a `schema_version` frontmatter field, written once by `foundation`'s shared
templating helper at create time — every service picks it up automatically rather than
reimplementing it. Value is the owning module's `manifest.json["version"]` at the moment the
file was created (or last migrated).

Existing files with no `schema_version` field are treated as stamped at the oldest version the
running code still knows about for that module (documented per-module, not inferred) — this
covers today's real content without a one-time bulk-stamping pass.

## 3. The compatibility contract, at load time

Whenever a service loads a content file (a `bht`/`bhw`/`bhrm`/`bhrole` read, not just a
write), it compares that file's `schema_version` against its owning module's current
`manifest.json["version"]`:

| File's `schema_version` vs. module's current version | Outcome |
|---|---|
| Equal | Proceed normally. The common case, no ceremony. |
| Older, and the module declares this specific gap backward-compatible (a registered no-op — the new field has a safe default, nothing structurally changed) | Proceed normally. |
| Older, and a migration is registered for this gap | **Refuse the read** with a message naming the file, its stamped version, the current version, and the exact `migrate` command to run. Never migrate as a side effect of a plain read. |
| Older, and nothing is registered (no compat, no migration) | Hard fail. Same message shape — name the file and both versions — but there's no remediation to point at beyond "this needs a manual look." |
| **Newer** than the running code's module version (stale checkout reading already-migrated content — e.g. a rollback, or a sandbox that never re-pulled) | Hard fail, symmetric to the row above. Old code must never guess at a newer shape either. |

Every branch either proceeds on a known-safe basis or stops with a specific, actionable
message. There is no branch that reads a mismatched file and produces output anyway on a
best-effort basis.

## 4. Migration: explicit command, never automatic

A `migrate` subcommand per service (`bht migrate`, `bhw migrate`, `bhrm migrate`, `bhrole
migrate`), each a thin wrapper over one shared `foundation` runner so the mechanics (find
files under this project's content root for this module, apply the registered transform chain,
rewrite via the existing `safe_write()`, update `schema_version` on success) exist once, not
four times.

A migration is registered as `(module_id, from_version, to_version) -> transform(frontmatter_dict) -> frontmatter_dict`.
The runner chains adjacent registered steps to cover a multi-version gap (e.g. 0.1.0 → 0.3.0
via 0.1.0→0.2.0 then 0.2.0→0.3.0) rather than requiring every pairwise combination to be
hand-written.

**Decided: no autorun.** A migration only ever runs when `migrate` is invoked explicitly. A
plain `bht board` or `bhw index` never rewrites a file as a side effect, even when it knows
exactly how — reading and mutating are kept strictly separate operations, on purpose, so
running a normal command is never a way to accidentally lose the pre-migration copy of
something.

## 5. No project-level version cache

**Decided: no cache.** An earlier sketch considered a `config.local.json` field recording
"module versions this project was last validated against," as a fast summary check before
touching individual files. Dropped — a cache is a second thing that can itself drift from the
truth (a file migrated by hand, a partial migration run that didn't update the cache), which
reintroduces exactly the silent-mismatch risk this whole plan exists to remove. Compatibility
is always derived directly from each file's own `schema_version` stamp, which is the single
source of truth and cannot go stale independently of the file it describes.

## 6. What this drops from the original sketch, and why

The original `migration-plan.md` §6 design — one repo-wide `VERSION`, one `setup_version` in
config, and a git-diff-based prose summary read by a human/agent on mismatch — is dropped
entirely, not kept as a coarse first pass alongside the per-file check:

- A single repo-wide version number can't say *which* module or *which* files are actually
  affected — every mismatch would need the same manual git-log reading regardless of whether
  the real answer is "nothing you have is affected" or "everything needs migrating."
- A prose summary is read and judged by a human or agent, not enforced by code — exactly the
  kind of soft gate that can be misread or skipped under time pressure, which is the silent-
  muck-up failure mode this plan is meant to close off.
- Per-file `schema_version` plus the compatibility table in §3 gives a stronger, cheaper
  answer than the git-diff approach ever could: mechanical, per-file, no judgment call
  required.

`VERSION`/`pyproject.toml["version"]` still exist and still identify the checkout — they're
just no longer load-bearing for compatibility decisions. `foundation/version_check.py`'s two
stub functions (`read_version`, `check_version_drift`) are superseded by this plan and should
be removed or replaced with the §3 per-file check when this is implemented, not left as dead
stubs pointing at a design this page now supersedes.

## 7. Consumer flow: mcRepos pulling new functionality

1. mcRepos' `config.local.json` has `repo_url` set, so a role's Launch link (or a manual `pip
   install "git+<repo_url>#subdirectory=src/Backhaul" --break-system-packages`) re-installs the
   CLI from `origin/master`, picking up whatever module schema changes have landed there.
2. The next `bht`/`bhw`/`bhrm`/`bhrole` command run against mcRepos' existing content hits §3's
   check per file it touches.
3. If nothing that command touches changed schema: no visible difference, exactly today's
   behavior.
4. If something did and a migration exists: the command refuses with the specific `migrate`
   command to run; running it fixes the affected files; re-running the original command
   succeeds.
5. If something did and no migration exists yet: hard fail naming the file and versions —
   surfaces the gap immediately at the point of use, rather than at some later, harder-to-trace
   point where a script silently misread a field.

## 8. Testing implications

Fixture content stamped at an intentionally old `schema_version`, plus a fake registered
migration and a fake version bump, are needed to exercise all four non-trivial branches of §3
(compatible-old, migratable-old, unmigratable-old, newer-than-code) without waiting for a real
future schema change to test against. This belongs in `foundation`'s own test suite, run once,
not duplicated per service.

## 9. Non-goals for this pass

- Not designing what the *first* real schema change under this system will be — this plan is
  the mechanism, not a specific migration.

