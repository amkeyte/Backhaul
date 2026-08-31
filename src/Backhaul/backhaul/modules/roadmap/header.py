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

#: `## Required By`'s own marker name, sibling to `bh-header`'s -- see refresh_required_by.
_REQUIRED_BY_MARKER = "required-by"
_REQUIRED_BY_HEADING = "## Required By"


def _relpath(target: str | Path, start: str | Path) -> str:
    """Relative path from directory `start` to `target`, POSIX-style separators. Not resolved:
    paths passed in are trusted as already-correct absolute paths, so no filesystem
    re-derivation is needed. (services/ticket/board.py's own `_relpath` does call `.resolve()`
    — unrelated reasoning specific to that function's own Edit-link building, not a discrepancy
    worth reconciling, since content roots aren't expected to be symlinked.)"""
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


def _render_required_by_content(node_dir: Path, dependents: list[tuple[str, str, Path]]) -> str:
    if not dependents:
        return "*(computed — nothing depends on this yet)*"
    return "\n".join(
        f"- [**{did}**]({_relpath(dpath, node_dir)}) — {dtitle}"
        for did, dtitle, dpath in sorted(dependents)
    )


def refresh_required_by(node_path: str | Path, dependents: list[tuple[str, str, Path]]) -> None:
    """Rewrite one node file's `## Required By` marked block from an already-computed reverse-
    dependency list — see BH_011. `dependents` is `[(id, title, path), ...]` for every node whose
    own `depends_on` names this one; the caller (graph.py's `build_index()`, which already has
    the loaded graph and its own `dependents()` query in scope) computes this rather than this
    module importing graph.py itself, so there's no import cycle between the two (graph.py's
    `build_index()` is what calls this, delegating the node-body write — graph.py's own docstring
    is explicit that graph.py itself never writes to a node file directly).

    Handles three states of the target file, since every real node predates this feature:
    1. The marked block already exists (a node this has already run against once) — replaced via
       the same idempotent `markers.refresh_block()` `bh-header` already uses.
    2. A freehand `## Required By` heading exists with no markers yet (every node created before
       this shipped) — migrated in place: markers inserted around fresh content, replacing the
       stale placeholder prose rather than leaving it duplicated alongside a new block.
    3. No `## Required By` section at all — a fresh one is appended.
    """
    path = Path(node_path)
    doc = _frontmatter.parse(path)
    content = _render_required_by_content(path.parent, dependents)
    marked_block = f"<!-- {_REQUIRED_BY_MARKER}:start -->\n{content}\n<!-- {_REQUIRED_BY_MARKER}:end -->"

    if f"<!-- {_REQUIRED_BY_MARKER}:start -->" in doc.body:
        doc.body = markers.refresh_block(doc.body, _REQUIRED_BY_MARKER, content)
    else:
        heading_idx = doc.body.find(_REQUIRED_BY_HEADING)
        if heading_idx == -1:
            body = doc.body if doc.body.endswith("\n") else doc.body + "\n"
            doc.body = f"{body}\n{_REQUIRED_BY_HEADING}\n\n{marked_block}\n"
        else:
            content_start = doc.body.find("\n\n", heading_idx)
            content_start = content_start + 2 if content_start != -1 else heading_idx + len(_REQUIRED_BY_HEADING)
            next_heading = doc.body.find("\n## ", content_start)
            content_end = next_heading + 1 if next_heading != -1 else len(doc.body)
            doc.body = doc.body[:content_start] + marked_block + "\n" + doc.body[content_end:]

    _frontmatter.write(doc)
