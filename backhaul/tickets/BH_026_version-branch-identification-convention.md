---
id: BH_026
uid: BH
number: 26
client: BH
status: done
title: Version/branch identification convention
context: 'Project owner flagged: this branch is a real version deviation from master,
  and nothing marks it as such if someone pulls the wrong branch. Need a locked mechanism
  before pushing.'
priority: normal
opened: '2026-08-31'
closed: '2026-08-31'
---

<!-- board:start -->
<!-- board:end -->

## Summary

Before this batch, `pyproject.toml`'s `version` and `backhaul/__init__.py`'s `__version__` both
sat at `"0.1.0"` regardless of branch, and none of the five CLIs (`backhaul`/`bht`/`bhw`/`bhrm`/
`bhrole`) printed a version at all. `dev` was about to be pushed while still ahead of `master`
(`d7f6871` vs `origin/master`'s `4d07fe0`), with no mechanism to make that divergence visible to
someone who checks out the wrong branch — the concern the project owner raised directly.

## Suggested direction

Two decisions, both confirmed by the project owner: (1) PEP 440 `.devN` dev-release suffix —
master carries a clean release version, any unreleased/diverged branch bumps to the next version
with `.devN` appended, so the two are always distinguishable in `pip show`/`__version__`; (2) add
runtime `--version` to all five CLIs so the mismatch is visible at the point someone actually
runs a command, not just in package metadata someone has to think to check.

## Log

- 2026-08-31: Bumped __version__/pyproject.toml to 0.2.0.dev0. Added foundation/build_info.py (get_git_info + format_version_string) and wired --version into all 5 CLIs, e.g. 'bht 0.2.0.dev0 (dev @ d7f6871)'. Along the way found and fixed a real bug: a bare 'from backhaul import __version__' broke when run from a project root, because every project's own content folder is itself named backhaul/ and can shadow the installed package as a namespace package -- fixed by reading __version__ from __init__.py's source text via Path(__file__) instead of importing the bare package name. Locked the convention in wiki/design/version-branch-convention.md; corrected dev-branch-handoff.md's earlier no-bump-needed answer, now superseded. Added tests for build_info and a --version smoke test per CLI; loosened test_smoke.py's version-literal assertion to a pattern match since it'll otherwise break every dev cycle. Full suite: 408 passed.
- 2026-08-31: Ticket opened.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
