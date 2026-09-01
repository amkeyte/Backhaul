"""File-safety helpers: guard against overwriting content the caller didn't mean to touch.

Covers things like: refusing to create a file that already exists unless forced, atomic
write-then-rename, and confirming a target path is inside the expected content root before
writing (protects against a bad config pointing scripts at the wrong folder).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


class UnsafeWriteError(Exception):
    """Raised when a write would clobber an existing file or escape the expected root."""


def safe_write(path: str | Path, content: str, *, overwrite: bool = False) -> None:
    """Write content to path, refusing to overwrite an existing file unless overwrite=True.

    Writes atomically (write to a sibling temp file, then rename) so a crash mid-write never
    leaves a half-written file behind.
    """
    p = Path(path)
    if p.exists() and not overwrite:
        raise UnsafeWriteError(f"{p}: already exists (pass overwrite=True to replace it)")

    p.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(dir=p.parent, prefix=f".{p.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_name, p)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def assert_within_root(path: str | Path, root: str | Path) -> None:
    """Raise UnsafeWriteError if path is not inside root.

    Resolves both paths first (symlinks, `..`, relative segments) so this can't be fooled by
    a path that only looks contained before normalization. Doesn't require either path to
    exist on disk.
    """
    resolved_path = Path(path).resolve()
    resolved_root = Path(root).resolve()
    if resolved_root != resolved_path and resolved_root not in resolved_path.parents:
        raise UnsafeWriteError(f"{resolved_path} is not inside expected root {resolved_root}")
