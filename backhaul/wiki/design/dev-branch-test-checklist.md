---
id: design/dev-branch-test-checklist
category: design
slug: dev-branch-test-checklist
title: Dev Branch Test Checklist -- 2026-08-31
summary: Copy-pasteable checklist for an agent on a fresh test machine to exercise
  before this branch goes further -- especially the new --version/branch-identification
  mechanism, which has only been tested from this repo's own editable dogfooding install
  so far.
keywords: null
status: draft
updated: '2026-08-31'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · design
<!-- bh-header:end -->

# Dev Branch Test Checklist -- 2026-08-31

Copy-pasteable checklist for an agent on a fresh test machine to exercise before this branch goes further -- especially the new --version/branch-identification mechanism, which has only been tested from this repo's own editable dogfooding install so far.

Companion to [Dev Branch Handoff — 2026-08-30](dev-branch-handoff.md), which explains what's on
the branch and why. This page is narrower: concrete steps to run, with the expected result for
each, so a pass/fail verdict doesn't depend on the agent's own judgment about what "working"
means. Work through it in order; stop and report back on the first failure rather than working
around it.

## 1. Environment setup

1. Fresh clone (or copy) of this repo on the test machine, `dev` branch checked out.
2. Fresh virtualenv: `python3 -m venv .venv && source .venv/bin/activate` (or the Windows
   equivalent).
3. Editable install: `pip install -e "src/Backhaul[dev]"` from the repo root (add
   `--break-system-packages` only if the environment demands it — most real machines won't).
4. `pip show backhaul` — confirm **Version: 0.2.0.dev0**, not `0.1.0`. If it still says `0.1.0`,
   the install picked up stale cached metadata; `pip uninstall backhaul` and reinstall before
   continuing, since everything below assumes this is current.
5. `cd src/Backhaul && python3 -m pytest -q` — expect **408 passed, 0 failed**. Do not proceed
   past a failure here; nothing below is meaningful on top of a red suite.

## 2. Version & branch identification (BH_026) — the actual point of this checklist

This is the newest, least-exercised part of the branch — steps 5-7 below deliberately test paths
this session's own work never got to run for real (see [Version & Branch Identification
Convention](version-branch-convention.md) for why each matters).

5. **Shadow-bug regression.** From the repo root (the cwd that contains this project's own
   `backhaul/` content folder — the exact condition that broke a bare `from backhaul import
   __version__` during development), run all five:
   ```
   backhaul --version
   bht --version
   bhw --version
   bhrm --version
   bhrole --version
   ```
   Expect each to print cleanly, e.g. `bht 0.2.0.dev0 (dev @ d7f6871)` — no `ImportError`, no
   traceback. A traceback here means the namespace-shadow fix in `foundation/build_info.py`
   didn't actually hold on this machine.
6. **Branch/commit accuracy.** Compare the `(branch @ commit)` shown above against `git branch
   --show-current` and `git rev-parse --short HEAD` run directly in the checkout. They must
   match exactly.
7. **Wheel-install fallback (untested until now).** In a *separate* fresh venv, install
   **non-editable**: `pip install src/Backhaul` (no `-e`). This puts the installed files in
   site-packages with no `.git` directory anywhere near them — the actual shape of a role's own
   Launch-link install. Run `bht --version` again: expect it to fall back to just `bht
   0.2.0.dev0` with **no** `(branch @ commit)` suffix, and — same as step 5 — no error. If this
   throws instead of falling back cleanly, that's a real bug in `get_git_info()`'s exception
   handling, not a cosmetic issue.
8. **Master actually differs.** Check out `master` in a second clone or worktree and run
   `backhaul --version` there (or just read `pyproject.toml`'s `version`). Expect **0.1.0** —
   confirming `dev` and `master` are distinguishable in practice, not just by design.

## 3. Regression checks for this batch's other fixes

9. **BH_022 — config error handling.** Run any command against a config path that doesn't exist,
   e.g. `bht open --config /nonexistent/config.local.json --client X --title test`. Expect a
   clean `FAIL: ...` line on stderr and exit code 1 — not a Python traceback.
10. **BH_023 — roadmap HTML color.** In a test roadmap graph, create a convergence node and set
    its `status: superseded`, then `bhrm render`. Open the HTML output and confirm that node
    renders in the same green "done" styling a superseded *work* node gets — not the orange
    dashed WIP style.
11. **BH_024 — ticket ID lookup.** Against a project with a populated `client-uids.md` registry,
    run `bht status <a single short letter or prefix> blocked` (something that could
    glob-match the registry file itself). Expect a clean "no ticket matching ..." message, not a
    crash while parsing `client-uids.md` as if it were a ticket.
12. **BH_003 — role launch target.** `bhrole new --title "Test Role" --launch-target code` (plus
    a bootstrap-prompt code block in the body), then check the generated Launch link uses
    `claude://code/new?...`, not `claude://cowork/...`.
13. **BH_007 — build-ready marker.** Set `"build_ready": "ready"` in a test `config.local.json`,
    run `backhaul dashboard`, confirm `**Build status: Ready**` renders directly under the
    `# Backhaul` title, above the Work Board line. Remove the field, re-run, confirm the line is
    gone entirely (not blank — absent).

## 4. Real-usage smoke test

14. Point `--config` at a real (non-synthetic-fixture) project and run `backhaul refresh`
    end-to-end. Confirm it completes without error and that `BACKHAUL.md`, `BOARD.md`, and
    `WIKI_INDEX.md` look sane — right counts, working links, no stale content.

## 5. Before merging back

15. BH_025 (dead stub modules — `version_check.py`/`refs.py`) is still open on the board. That's
    expected, not a regression to chase down here — it's a deliberate open product question, not
    a bug this checklist is meant to catch.
16. If everything above passes: this branch is ready to merge. Drop the `.devN` suffix from
    `backhaul/__init__.py`'s `__version__` and `pyproject.toml`'s `version` as part of that merge
    (see [Version & Branch Identification Convention](version-branch-convention.md)) — not
    before, since dropping it early would defeat the whole point of this batch.

## Related pages

- [Dev Branch Handoff — 2026-08-30](dev-branch-handoff.md)
- [Version & Branch Identification Convention](version-branch-convention.md)
