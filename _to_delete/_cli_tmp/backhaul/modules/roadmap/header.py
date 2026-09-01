"""Normalized Backhaul header for roadmap node files — mirrors services/ticket/board.py's
refresh_board_link and services/wiki/index.py's refresh_header.

Kept out of graph.py deliberately: graph.py's docstring is explicit that it's read-only against
node files and never writes — header refresh needs to write, so it lives here instead, alongside
create.py (which also writes node files).
"""

from __future__ import annotations

import os
from pathlib import Path

from backhaul.foundation import frontmatter as _frontmatter
from backhaul.foundation import header, markers


def _relpath(target: str | Path, start: str | Path) -> str:
    """Relative path from directory `start` to `target`, POSIX-style separators. Deliberately
    NOT resolved — same reasoning as services/ticket/board.py's _relpath."""
    return os.path.relpath(Path(target), Path(start)).replace(os.sep, "/")


def refresh_header(
    node_path: str | Path,
    index_path: str | Path | None = None,
    *,
    dashboard_path: str | Path | None = None,
    project_name: str = "Backhaul",
) -> None:
    """Insert/refresh the normalized Backhaul header in a single roadmap node file: project
    name, Dashboard link, Roadmap Index link, the node's own UID graph as plain-text trail —
    see foundation/header.py. `index_path` defaults to "ROADMAP_INDEX.md" (relative) and
    `dashboard_path` to "BACKHAUL.md" (relative) when not given, same convention as BHT/BHW.
    """
    path = Path(node_path)
    doc = _frontmatter.parse(path)
    uid = str(doc.frontmatter.get("uid") or "")

    index_rel = _relpath(index_path, path.parent) if index_path is not None else "ROADMAP_INDEX.md"
    dashboard_rel = _relpath(dashboard_path, path.parent) if dashboard_path is not None else "BACKHAUL.md"

    block = header.render_header(
        project_name=project_name,
        dashboard_rel=dashboard_rel,
        indexer_label="Roadmap Index",
        indexer_rel=index_rel,
        extra=uid,
    )
    doc.body = markers.refresh_block(doc.body, header.MARKER_NAME, block)
    _frontmatter.write(doc)
