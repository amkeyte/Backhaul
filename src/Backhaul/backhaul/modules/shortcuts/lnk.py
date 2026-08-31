"""Core .lnk-building logic, ported from Aaron K's CLAUDE Stuff/Scripts/make_lnk.py.

Root cause this works around:
pylnk3's PathSegmentEntry.create_for_path() decides FOLDER vs FILE by calling
os.path.isdir() on the literal Windows path string (e.g. "C:\\_R Clone\\..."). Run from a
Linux sandbox, that path never exists on the local filesystem, so os.path.isdir() is always
False and every segment gets tagged FILE. Windows then walks the shortcut's ID list, hits a
"file" where a folder should be, can't resolve it, and silently does nothing on double-click.

Fix: after pylnk3 builds the link, walk shell_item_id_list.items and retype each
directory-level segment to FOLDER. For a folder target, every segment is FOLDER. For a file
target, every segment is FOLDER except the last, which stays FILE.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# pylnk3 is deliberately NOT imported at module level: it's an optional dependency
# (pyproject.toml's `shortcuts` extra, not part of `dev`), and this module is reachable via
# `backhaul.modules.shortcuts`'s eager `from .lnk import ...` re-export (see that package's
# __init__.py) — so a bare `import backhaul.modules.shortcuts`, e.g. test_smoke.py's "does the
# package structure import cleanly" check, must succeed without pylnk3 installed. Only `build()`
# and `verify()` actually touch pylnk3, so each imports it locally, raising the normal
# ImportError with pylnk3's own install hint only if someone actually tries to build/verify a
# .lnk without the extra installed. Matches `modules/docx`'s existing pattern (its own heavy
# import is deferred to whichever submodule actually needs it) — `shortcuts` just hadn't
# followed it. See BH_027.

TargetType = Literal["folder", "file"]


class LnkBuildError(Exception):
    """Raised when a .lnk fails to build or fails post-build verification."""


@dataclass
class LnkSpec:
    target: str  # literal Windows path embedded in the shortcut
    out: str | Path  # filesystem path to write the .lnk to
    type: TargetType = "folder"
    name: str | None = None
    workdir: str | None = None
    args: str | None = None
    icon: str | None = None
    icon_index: int = 0
    force: bool = False


def build(spec: LnkSpec) -> pylnk3.Lnk:
    """Build and save a .lnk file per spec, with corrected FOLDER/FILE segment typing."""
    import pylnk3

    out_path = str(spec.out)
    if not out_path.lower().endswith(".lnk"):
        out_path += ".lnk"

    if os.path.exists(out_path) and not spec.force:
        raise LnkBuildError(f"'{out_path}' already exists. Pass force=True to overwrite.")

    workdir = spec.workdir
    if spec.type == "folder" and not workdir:
        workdir = spec.target

    lnk = pylnk3.for_file(
        spec.target,
        lnk_name=None,
        arguments=spec.args,
        description=spec.name,
        icon_file=spec.icon,
        icon_index=spec.icon_index or 0,
        work_dir=workdir,
    )

    # --- the fix: retype path segments ---
    items = getattr(lnk.shell_item_id_list, "items", None) if lnk.shell_item_id_list else None
    if items:
        # items[0] is RootEntry, items[1] is DriveEntry - leave those alone.
        # items[2:] are PathSegmentEntry objects, one per path component after the drive.
        path_segments = items[2:]
        last_index = len(path_segments) - 1
        for i, seg in enumerate(path_segments):
            if spec.type == "folder":
                seg.type = pylnk3.TYPE_FOLDER
            else:
                seg.type = pylnk3.TYPE_FOLDER if i < last_index else pylnk3.TYPE_FILE
            # folder-type segments must have file_size 0 or _validate() raises
            if seg.type == pylnk3.TYPE_FOLDER:
                seg.file_size = 0

    lnk.save(out_path)
    return lnk


def verify(out_path: str | Path, expected_target: str, expect_all_folder: bool) -> tuple[bool, list[str]]:
    """Re-parse a built .lnk and confirm the embedded target and segment typing are correct."""
    import pylnk3

    lnk = pylnk3.parse(str(out_path))
    ok = True
    problems: list[str] = []

    target = lnk.path
    if target.rstrip("\\").lower() != expected_target.rstrip("\\").lower():
        ok = False
        problems.append(f"target mismatch: embedded='{target}' expected='{expected_target}'")

    items = getattr(lnk.shell_item_id_list, "items", None) if lnk.shell_item_id_list else None
    if items:
        path_segments = items[2:]
        last_index = len(path_segments) - 1
        for i, seg in enumerate(path_segments):
            seg_name = getattr(seg, "full_name", None) or getattr(seg, "short_name", None)
            if expect_all_folder or i < last_index:
                if seg.type != pylnk3.TYPE_FOLDER:
                    ok = False
                    problems.append(f"segment '{seg_name}' is {seg.type}, expected FOLDER")
            else:
                if seg.type != pylnk3.TYPE_FILE:
                    ok = False
                    problems.append(f"segment '{seg_name}' is {seg.type}, expected FILE")
    else:
        problems.append("no shell_item_id_list present to verify")

    return ok, problems


def build_and_verify(spec: LnkSpec) -> str:
    """Build spec, verify the result, and return the written .lnk path.

    Raises LnkBuildError with all problems listed if verification fails.
    """
    out_path = str(spec.out)
    if not out_path.lower().endswith(".lnk"):
        out_path += ".lnk"

    build(spec)
    ok, problems = verify(out_path, spec.target, expect_all_folder=(spec.type == "folder"))
    if not ok:
        raise LnkBuildError(f"'{out_path}' built but verification failed: " + "; ".join(problems))
    return out_path
