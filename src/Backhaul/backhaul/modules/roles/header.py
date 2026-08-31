"""Normalized Backhaul header for role page files — mirrors services/ticket/board.py's
refresh_board_link, services/wiki/index.py's refresh_header, and modules/roadmap/header.py's
refresh_header.
"""

from __future__ import annotations

import os
from pathlib import Path

from backhaul.foundation import frontmatter as _frontmatter
from backhaul.foundation import header, markers


def _relpath(target: str | Path, start: str | Path) -> str:
    """Relative path from directory `start` to `target`, POSIX-style separators. Not resolved:
    paths passed in are trusted as already-correct absolute paths, so no filesystem
    re-derivation is needed. (services/ticket/board.py's own `_relpath` does call `.resolve()`
    — unrelated reasoning specific to that function's own Edit-link building, not a discrepancy
    worth reconciling, since content roots aren't expected to be symlinked.)"""
    return os.path.relpath(Path(target), Path(start)).replace(os.sep, "/")


def refresh_header(
    role_path: str | Path,
    index_path: str | Path | None = None,
    *,
    dashboard_path: str | Path | None = None,
    project_name: str = "Backhaul",
) -> None:
    """Insert/refresh the normalized Backhaul header in a single role page: project name,
    Dashboard link, Roles Index link — see foundation/header.py. `index_path` defaults to
    "ROLES_INDEX.md" (relative) and `dashboard_path` to "BACKHAUL.md" (relative) when not
    given, same convention as BHT/BHW/BHRM.
    """
    path = Path(role_path)
    doc = _frontmatter.parse(path)

    index_rel = _relpath(index_path, path.parent) if index_path is not None else "ROLES_INDEX.md"
    dashboard_rel = _relpath(dashboard_path, path.parent) if dashboard_path is not None else "BACKHAUL.md"

    block = header.render_header(
        project_name=project_name,
        dashboard_rel=dashboard_rel,
        indexer_label="Roles Index",
        indexer_rel=index_rel,
    )
    doc.body = markers.refresh_block(doc.body, header.MARKER_NAME, block)
    _frontmatter.write(doc)
