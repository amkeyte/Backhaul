"""Package version + git branch/commit, combined into a single --version line shared by all
five CLIs (backhaul/bht/bhw/bhrm/bhrole).

Exists because pyproject.toml's version alone doesn't answer "which branch is this" at the
point someone actually runs a command — the exact accident this guards against: someone has
`dev` checked out locally, forgets it isn't `master`, and doesn't find out until something
behaves differently than expected. See wiki/design/version-branch-convention.md for the full
convention this implements (the PEP 440 `.devN` scheme, and why master vs. any unreleased
branch always differ in `__version__`).

Git info is best-effort, not required. A pip-installed wheel — the normal path for a role's own
Launch-link install, which always pulls `origin/master` regardless (see bhrole.md's "Getting
the CLI into a fresh session") — has no `.git` directory at all, so `get_git_info()` returns
`(None, None)` rather than raising. Only a local git checkout (this repo's own dogfooding, or a
developer's clone) has anything to report; `format_version_string()` falls back to just the
package version when it doesn't.

PACKAGE_VERSION is deliberately read straight from `backhaul/__init__.py`'s own source text
rather than via `import backhaul` / `from backhaul import __version__` — a bare top-level import
of "backhaul" is unsafe here: every Backhaul-managed project has its own content folder
literally named `backhaul/` (tickets/wiki/roadmap/roles/config.local.json — see any project's
own `content_roots`), and when a CLI runs with that project's root as cwd (the common case —
BACKHAUL_LOCAL_ROOT workflows do exactly this), that plain directory can shadow the real
installed package as a same-named namespace package if it resolves before the real one on
sys.path. Discovered while building this module: `from backhaul import __version__` raised
`ImportError: cannot import name '__version__' from 'backhaul' (unknown location)` when run
from this repo's own root, even though `backhaul.foundation.build_info` itself (a *submodule*
import) resolved to the correct file — only the bare top-level name is ambiguous. Reading the
version from this file's own known location (`Path(__file__)`, already unambiguous) sidesteps
the whole problem rather than needing cwd to cooperate.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def _read_package_version() -> str:
    init_path = Path(__file__).resolve().parent.parent / "__init__.py"
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init_path.read_text(encoding="utf-8"))
    return match.group(1) if match else "unknown"


PACKAGE_VERSION = _read_package_version()


def get_git_info(start_path: str | Path | None = None) -> tuple[str | None, str | None]:
    """Return (branch, short_commit) for the git checkout containing `start_path` (defaults to
    this file's own location — i.e. wherever the installed `backhaul` package actually lives),
    or (None, None) if it isn't inside a git working tree at all. Deliberately doesn't check for
    a `.git` directory by hand first — `git rev-parse` itself already reports "not a git repo"
    via a non-zero exit, and `git` may not even be on PATH in a bare pip-install environment, so
    every failure mode collapses to the same "no git info available" result rather than needing
    separate handling.
    """
    cwd = Path(start_path) if start_path is not None else Path(__file__).resolve().parent
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        # OSError covers "git" not being on PATH at all; SubprocessError covers a timeout.
        return None, None
    if branch.returncode != 0 or commit.returncode != 0:
        return None, None
    return branch.stdout.strip() or None, commit.stdout.strip() or None


def format_version_string(prog: str) -> str:
    """One line for a CLI's --version: "<prog> <version>" plus " (<branch> @ <commit>)" when
    git info is available, omitted entirely when it isn't (a wheel install, or git not on PATH).
    """
    branch, commit = get_git_info()
    if branch and commit:
        return f"{prog} {PACKAGE_VERSION} ({branch} @ {commit})"
    return f"{prog} {PACKAGE_VERSION}"
