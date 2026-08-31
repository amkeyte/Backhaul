---
id: BH_027
uid: BH
number: 27
client: BH
status: done
title: shortcuts module crashed test collection without pylnk3
context: Found by the test-checklist agent on a fresh machine.
priority: normal
opened: '2026-08-31'
closed: '2026-08-31'
---

<!-- board:start -->
<!-- board:end -->

## Summary

Found by an agent actually running `dev-branch-test-checklist.md` on a fresh test machine
(BH_026's own checklist, first real use). `pip install -e "src/Backhaul[dev]"` — the checklist's
own prescribed install command — does not pull in `pylnk3` (a separate `shortcuts` extra in
`pyproject.toml`, not part of `dev`). But `backhaul/modules/shortcuts/__init__.py` did `from
.lnk import LnkBuildError, LnkSpec, build, build_and_verify, verify`, and `lnk.py` did `import
pylnk3` at module top level — so `test_smoke.py`'s bare `import backhaul.modules.shortcuts`
(a "does the package structure import cleanly" check) aborted pytest collection entirely.
Result was `1 skipped, 1 error` with nothing actually running, not one failing test.

`backhaul.modules.docx` already deferred its own heavy optional import (its `__init__.py` is
empty; `python-docx` is only imported inside whichever submodule actually needs it) — `shortcuts`
just hadn't followed that established pattern. This repo's own sandbox happened to already have
`pylnk3` installed from earlier work, so 408 passing tests here never surfaced the gap; the
checklist run on a genuinely fresh install is what caught it.

## Suggested direction

Match `shortcuts` to `docx`'s existing pattern: defer the optional import to only the functions
that actually need it, rather than folding `pylnk3` into the `dev` extra (which would make every
dev/CI environment install a Windows-shortcut-building library it never uses).

## Log

- 2026-08-31: Fixed: moved `import pylnk3` out of lnk.py's module scope and into build()/verify() (the only two functions that touch it) — LnkSpec/LnkBuildError/TargetType and the public re-exports in shortcuts/__init__.py are unchanged, so no consumer's import shape changed. Verified via a sys.meta_path block simulating pylnk3's absence: `import backhaul.modules.shortcuts` now succeeds, LnkSpec constructs fine, and build() raises a normal ModuleNotFoundError only when actually called. Added a permanent regression test (test_smoke.py::test_shortcuts_imports_without_pylnk3_installed) using the same block technique, so this can't regress silently even in environments where pylnk3 happens to already be installed. Updated dev-branch-test-checklist.md's step 5 with the expected count and a note for anyone hitting this on an older commit. Full suite: 409 passed (was 408; +1 new regression test).
- 2026-08-31: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
