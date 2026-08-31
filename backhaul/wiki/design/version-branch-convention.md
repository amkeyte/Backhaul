---
id: design/version-branch-convention
category: design
slug: version-branch-convention
title: Version & Branch Identification Convention
summary: 'Locked convention: how a package version signals which branch you''re running,
  so a wrong-branch checkout is never silent.'
keywords: null
status: verified
updated: '2026-08-31'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · design
<!-- bh-header:end -->

# Version & Branch Identification Convention

Locked convention: how a package version signals which branch you're running, so a wrong-branch checkout is never silent.

## The problem this closes

Before this convention, `pyproject.toml`'s `version` sat at `"0.1.0"` on both `master` and every
feature branch — nothing distinguished them. None of the five CLIs printed a version at all.
Someone who had `dev` checked out locally, forgot it wasn't `master`, and ran `bht`/`bhw`/
`bhrm`/`bhrole`/`backhaul` had no way to find out short of `git status`. That's the accident this
locks down: **a version mismatch must be visible at the point someone actually runs a command,
not just discoverable by someone who thinks to check.**

## The rule

**`master` always carries a clean release version** (`MAJOR.MINOR.PATCH`, e.g. `"0.1.0"`) —
whatever was last actually released. **Any branch that has diverged from the last release and
hasn't merged back bumps `__version__` to the next version with a PEP 440 `.devN` suffix** (e.g.
`"0.2.0.dev0"`). The two numbers can never collide: master's version and a diverged branch's
version are always different strings, by construction, so `pip show backhaul`, `python -c
"import backhaul; print(backhaul.__version__)"`, and every CLI's `--version` output all differ
from what master reports.

Two places carry the same number and must be kept in sync by hand:

- `backhaul/__init__.py`'s `__version__`
- `pyproject.toml`'s `[project] version`

There's no build step that derives one from the other — bump both, in the same commit, whenever
a branch first diverges from a just-released master. (`CONFIG_SCHEMA_VERSION` in
`foundation/config.py` and `config/config.schema.json`'s own `"version"` field are unrelated —
those gate breaking *config-shape* changes, not branch identity. See that constant's own
doc-comment; don't conflate the two.)

**On merge to master**, drop the `.devN` suffix. If the diverged work only needed a patch-level
bump, land it as the next real patch version; if it needs more (a minor or major bump), decide
that at merge time based on what actually shipped — this convention only fixes the *branch*
number, not the eventual *release* number, which is still a human call.

## Runtime visibility: `--version` on all five CLIs

`backhaul`, `bht`, `bhw`, `bhrm`, and `bhrole` all accept `--version` (standard argparse
`action="version"`, so it short-circuits even though every one of these CLIs otherwise requires
a subcommand — same reason `pip --version` works despite `pip` having required subcommands).
Output:

```
bht 0.2.0.dev0 (dev @ d7f6871)
```

Package version always prints. Branch + short commit print too, when available — best-effort,
via `foundation/build_info.py`'s `get_git_info()`, which shells out to `git rev-parse` from
wherever the installed package actually lives. A pip-installed wheel (the normal path for a
role's own Launch-link install — see `bhrole.md`'s "Getting the CLI into a fresh session",
which always installs from `origin/master`) has no `.git` directory at all, so branch/commit are
silently omitted there; only a local git checkout (this repo's own dogfooding, or a developer's
clone) has anything to report.

## A gotcha this surfaced: don't `import backhaul` bare

Building `build_info.py`, a plain `from backhaul import __version__` raised `ImportError:
cannot import name '__version__' from 'backhaul' (unknown location)` when run from this repo's
own root — even though every *submodule* import (`from backhaul.foundation import config`, and
so on) worked fine. Cause: every Backhaul-managed project has its own content folder literally
named `backhaul/` (tickets/wiki/roadmap/roles/config.local.json — see any project's own
`content_roots`). When a CLI runs with that project's root as cwd — the common case, since
`BACKHAUL_LOCAL_ROOT` workflows and this repo's own dogfooding both do exactly that — Python's
import resolution can find that plain directory (no `__init__.py`) as a same-named PEP 420
namespace package before it finds the real installed package, because the editable-install
finder that maps `backhaul` to its real source location is registered *after* the standard
path-based finder in `sys.meta_path`. Submodule imports (`backhaul.foundation.build_info`) are
unaffected — they resolve through a different code path in that same finder — only a bare
top-level `import backhaul` / `from backhaul import X` is at risk.

Fix applied in `build_info.py`: read `__version__` directly from `backhaul/__init__.py`'s own
source text (via this file's own already-unambiguous `Path(__file__)`), never importing the bare
`backhaul` name. Anywhere else in this codebase that might someday want `from backhaul import
__version__` (or anything else off the bare top-level package) should do the same, or at minimum
be aware this shadow exists — it's specific to `backhaul` because of the project-content-folder
naming convention, not a general Python footgun.

## Related pages

- [Dev Branch Handoff — 2026-08-30](dev-branch-handoff.md)
- [Version & Schema Compatibility Plan](version-compat.md) — a different, unrelated versioning
  concern (per-content-file `schema_version` drift detection, not yet built); don't conflate the
  two just because both pages have "version" in the title.
- [Backhaul — Cross-Service Command Conventions](../meta/backhaul.md)
