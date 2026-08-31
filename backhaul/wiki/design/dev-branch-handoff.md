---
id: design/dev-branch-handoff
category: design
slug: dev-branch-handoff
title: Dev Branch Handoff -- 2026-08-30
summary: 'Orients a fresh agent picking up the dev branch cold: what''s on it, why,
  verification status, what''s still open, and whether a version bump is needed.'
keywords: null
status: draft
updated: '2026-08-31'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · design
<!-- bh-header:end -->

# Dev Branch Handoff -- 2026-08-30

Orients a fresh agent picking up the `dev` branch cold: what's on it, why, verification status, what's still open, and whether a version bump is needed.

## What's on this branch

Two batches, back to back, both starting from real usage rather than speculative design:

1. **BH_010-BH_021** (twelve tickets). Filed after processing mcRepos' `BKHL_*` reports from a
   live testbed session — see each ticket's own body for the specific bug/gap it tracks. Design
   and build order: [BH_010-021 Implementation Architecture](bh010-021-architecture.md), written
   *before* implementation started. All twelve closed; two decisions (BH_019's config-resolution
   direction, BH_015's lint marker syntax) were explicitly delegated by the project owner and are
   documented as locked in that doc.
2. **BH_022-BH_025, plus BH_003 and BH_007**. Filed/closed after a full-codebase review of batch
   1's result. BH_022 (no CLI caught a bad-config error, all five dumped a raw traceback),
   BH_023 (a superseded convergence node rendered identically to an active WIP one in the HTML
   graph — a bug in batch 1's own BH_013), and BH_024 (a ticket-id lookup could match
   `client-uids.md` itself and crash) are real bugs, found and fixed directly, no separate design
   doc — each was small enough to fix off the review finding alone. BH_025 (two fully-stubbed,
   uncalled foundation modules) is filed but **left open** — implement-vs-remove is a product
   call, not an engineering one. BH_003 and BH_007 were unrelated feature requests that had been
   sitting open on the board for weeks; they got implemented in the same pass per the project
   owner's on-the-spot decisions (recorded in each ticket's own Log: BH_003 — role frontmatter
   field over any other mechanism; BH_007 — manual, one-per-project, not computed or per-UID).

3. **BH_026 — version/branch identification.** Filed after the project owner flagged that this
   branch, once pushed, would be a real version deviation from master with nothing marking it as
   such. Bumped `__version__`/`pyproject.toml` to a PEP 440 dev-release suffix, added `--version`
   to all five CLIs, and locked the convention in
   [Version & Branch Identification Convention](version-branch-convention.md). See that page for
   the mechanism; see BH_026's own ticket for the before/after.
4. **BH_027 — shortcuts module crashed test collection without `pylnk3`.** Found by an agent
   actually running [Dev Branch Test Checklist](dev-branch-test-checklist.md) on a fresh machine
   — `pip install -e "src/Backhaul[dev]"` (this checklist's own step 3) doesn't pull in `pylnk3`
   (a separate `shortcuts` extra), but `backhaul.modules.shortcuts`'s `__init__.py` imported it
   eagerly, so `test_smoke.py`'s bare `import backhaul.modules.shortcuts` aborted pytest
   collection entirely — not a single failing test, nothing ran. `docx` already deferred its own
   optional heavy import the same way; `shortcuts` just hadn't followed that pattern. Fixed by
   moving `import pylnk3` into the two functions that actually touch it (`build()`/`verify()` in
   `lnk.py`), same shape `docx` already had. First real proof the checklist catches things a
   same-machine dogfooding session can't — this repo's own sandbox happened to already have
   `pylnk3` installed, so 408 tests passing here never surfaced it.

Every ticket's own `## Log` section has the specific before/after and what was tested — this
page is an index into those, not a replacement for reading one when the detail matters.

## Status

- Full suite: 409 passing, 0 failing. Run it yourself before trusting this:
  `cd src/Backhaul && python3 -m pytest -q`.
- `backhaul refresh` has been run against this repo's own real content (not just synthetic test
  fixtures) — `BOARD.md`/`BACKHAUL.md` are current. Only BH_025 is open.
- **Nothing on this branch has been committed.** The working tree has code, tests, and wiki/
  ticket content changes sitting uncommitted — the agent that did this work never runs
  state-changing git commands (`add`/`commit`/`push`) per standing instruction; the project
  owner commits and pushes themselves. `git status`/`git diff` on `dev` show the real, current
  diff — trust that over this page if they ever disagree.

## What to do next

1. Review the diff.
2. Re-run the full suite in your own environment — don't trust a stale "408 passing" claim once
   any further change lands.
3. On a fresh test machine, work through [Dev Branch Test Checklist —
   2026-08-31](dev-branch-test-checklist.md) before pushing further — it covers a fresh install
   (not just this repo's own editable dogfooding checkout) and every fix in this batch, with an
   expected result for each step so a pass/fail verdict doesn't depend on judgment calls.
4. Commit and push. Version is already bumped (`0.2.0.dev0` — see Versioning below); drop the
   `.devN` suffix as part of the merge to master, not before.
5. BH_025 is the one open item, and it needs a decision from the project owner, not more
   engineering: implement `version_check.py`/`refs.py` per their original (unbuilt) design, or
   delete them now that nothing calls either.

## Versioning

**Superseded 2026-08-31 — a bump was needed after all, just not the kind this section originally
said no to.** The reasoning below about `CONFIG_SCHEMA_VERSION` was and still is correct — config-
shape additivity was never in question. What was missing: nothing distinguished this branch's own
package version from master's, so someone who pulled `dev` by accident had no way to notice. See
[Version & Branch Identification Convention](version-branch-convention.md) for the actual, now-
locked mechanism; summary:

- `backhaul/__init__.py`'s `__version__` and `pyproject.toml`'s `version` are both now
  `"0.2.0.dev0"` (was `"0.1.0"` on both, same as master) — a PEP 440 dev-release suffix that
  master will never carry, so the two are always distinguishable. Drop the suffix on merge.
- All five CLIs (`backhaul`/`bht`/`bhw`/`bhrm`/`bhrole`) now accept `--version`, printing the
  package version plus branch/commit when run from a git checkout — the point is runtime
  visibility, not just something `pip show` can answer if someone thinks to check.
- `config/config.schema.json`'s `"version"` / `foundation/config.py`'s `CONFIG_SCHEMA_VERSION`
  remain unrelated to this — those still only bump on a *breaking* config-shape change (a
  required key added, renamed, or removed), and every field this batch added (`build_ready`,
  `launch_target`) is still optional and additive. That part of the original answer stands;
  it's just not the whole answer to "does anything need to change" anymore.
- [Version & Schema Compatibility Plan](version-compat.md) (still `status: draft`) remains a
  separate, unbuilt concern — per-content-file `schema_version` drift detection, not package/
  branch identity. Still no bearing on this batch.

## Related pages

- [BH_010-021 Implementation Architecture](bh010-021-architecture.md)
- [Dev Branch Test Checklist — 2026-08-31](dev-branch-test-checklist.md)
- [Version & Branch Identification Convention](version-branch-convention.md)
- [Version & Schema Compatibility Plan](version-compat.md)
- [Backhaul — Cross-Service Command Conventions](../meta/backhaul.md)
