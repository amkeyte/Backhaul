"""File-safety helpers: guard against overwriting content the caller didn't mean to touch.

Covers things like: refusing to create a file that already exists unless forced, atomic
write-then-rename, and confirming a target path is inside the expected content root before
writing (protects against a bad config pointing scripts at the wrong folder).
"""

from __future__ import annotations

from pathlib import Path


class UnsafeWriteError(Exception):
    """Raised when a write would clobber an existing file or escape the expected root."""


def safe_write(path: str | Path, content: str, *, overwrite: bool = False) -> None:
    """Write content to path, refusing to overwrite an existing file unless overwrite=True."""
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md")


def assert_within_root(path: str | Path, root: str | Path) -> None:
    """Raise UnsafeWriteError if path is not inside root."""
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md")
