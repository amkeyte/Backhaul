"""Re-root an absolute path from wherever the CLI is currently executing (`runtime_root` —
e.g. a Linux Cowork sandbox's mount point) onto the path a human should actually see and click
(`host_root` — e.g. this project's real Windows path), for building links (editmd:,
openfolder:, and role Launch links) meant to work on the *target* machine, not necessarily the
machine that generated them.

Exists because config.local.json's content_roots always reflects wherever the CLI can actually
read/write files right now — true and sufficient for the original use case (a human running
bht/bhw directly on their own Windows machine, where "here" and "the machine that opens the
link" are the same machine) but not for a role launched into an ephemeral Cowork sandbox, whose
filesystem is never the target machine's. A sandbox can't do file I/O against content_roots
written as real Windows paths, so it has to work from a translated (sandbox-mounted) view of
the same project — and every absolute-path link it then generates would otherwise bake in that
sandbox path instead of the one a human can actually open. See modules/roles/launch.py and the
`bhrole` meta wiki page for the fuller story of how this surfaced (2026-08-11).

Pure string manipulation — no filesystem access, no OS-specific path resolution — same
philosophy as handler_uri.py, and deliberately not `Path.resolve()`-based for the same reason
that module gives: resolving would re-derive the path against whatever filesystem this code
happens to be running on right now, which is exactly the thing being worked around here.
"""

from __future__ import annotations

import os
from pathlib import Path


def to_host_path(path: str | Path, *, runtime_root: str | Path, host_root: str | None) -> str:
    """Re-express `path` (expected to live under `runtime_root`) rooted at `host_root` instead.

    Returns `str(path)` unchanged when `host_root` is None — the CLI's long-standing default
    (trust content_roots as printed), for configs that haven't opted into this. When
    `host_root` is given, computes `path`'s location relative to `runtime_root` (a filesystem-
    neutral relative path — the same "how deep is this file under the project root" that never
    needed translation) and rejoins it onto `host_root`, matching whichever path-separator
    style `host_root` itself uses (backslash if it looks like a Windows path, forward slash
    otherwise).
    """
    if host_root is None:
        return str(path)
    rel = os.path.relpath(str(path), str(runtime_root)).replace(os.sep, "/")
    host_root_str = str(host_root).rstrip("\\/")
    sep = "\\" if "\\" in host_root_str else "/"
    return host_root_str + sep + rel.replace("/", sep)
