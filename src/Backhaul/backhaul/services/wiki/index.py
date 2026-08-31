"""Renders the wiki category index (replacement for build_index.py): uses
foundation.rollup.collect() to gather pages grouped by category, then renders its own
markdown index — not shared with services/ticket/board.py's rendering.
"""

from __future__ import annotations

import os
from pathlib import Path

from backhaul.foundation import (
    filesafety,
    frontmatter as _frontmatter,
    handler_uri,
    header,
    host_paths,
    markers,
    rollup,
)

from .schema import validate

_COLUMNS = ("Title", "Status", "Summary", "Edit")

# Must match the SCHEME constant in modules/handlers/editmd. Kept as a plain string here
# (rather than importing that module) so services/wiki only depends on foundation, not on
# modules — see migration/ARCHITECTURE.md. Mirrors services/ticket/board.py's approach.
_EDIT_SCHEME = "editmd"


def _relpath(target: str | Path, start: str | Path) -> str:
    """Relative path from directory `start` to `target`, POSIX-style separators. Not resolved:
    paths passed in are trusted as already-correct absolute paths, so no filesystem
    re-derivation is needed. (services/ticket/board.py's own `_relpath` does call `.resolve()`
    — unrelated reasoning specific to that function's own Edit-link building, not a discrepancy
    worth reconciling, since content roots aren't expected to be symlinked.)"""
    return os.path.relpath(Path(target), Path(start)).replace(os.sep, "/")


def _row(item: dict, index_dir: Path, *, runtime_root: Path, host_root: str | None) -> str:
    page = validate(item)
    path = item.get("_path")
    if isinstance(path, Path):
        # Title links to the page itself (view it — e.g. via Markdown Viewer), relative to
        # wherever the index lives. Edit opens it in Notepad++ via the editmd: handler —
        # host_root (see foundation/host_paths.py), when configured, re-roots the absolute
        # path onto the real machine instead of wherever this code is currently running.
        title_cell = f"[{page.title}]({_relpath(path, index_dir)})"
        host_path = host_paths.to_host_path(path, runtime_root=runtime_root, host_root=host_root)
        edit = f"[Edit]({handler_uri.build_uri(_EDIT_SCHEME, host_path)})"
    else:
        title_cell = page.title
        edit = ""
    summary = page.summary or ""
    return f"| {title_cell} | {page.status} | {summary} | {edit} |"


def _render_table(
    items: list[dict], index_dir: Path, *, runtime_root: Path, host_root: str | None
) -> str:
    if not items:
        return "_No pages._\n"
    header = "| " + " | ".join(_COLUMNS) + " |"
    sep = "|" + "|".join(["---"] * len(_COLUMNS)) + "|"
    rows = [_row(item, index_dir, runtime_root=runtime_root, host_root=host_root) for item in items]
    return "\n".join([header, sep, *rows]) + "\n"


def _in_category_scope(category: str, category_prefix: str | None) -> bool:
    if category_prefix is None:
        return True
    return category == category_prefix or category.startswith(category_prefix + "/")


def render_index(
    wiki_root: str | Path,
    index_dir: str | Path | None = None,
    *,
    category_prefix: str | None = None,
    title: str = "# Wiki Index",
    dashboard_path: str | Path | None = None,
    project_name: str = "Backhaul",
    host_root: str | None = None,
) -> str:
    """Collect wiki pages under wiki_root and render the index's markdown body.

    Unlike BHT's board, nothing is excluded by status — draft/verified/published all show up
    (status is informational only, per migration/ARCHITECTURE.md). Grouped by category into
    one table per category, sorted alphabetically. `index_dir` is the directory the rendered
    index will actually live in (defaults to wiki_root itself) — links are relative to it.

    `category_prefix`, if given, scopes this down to just that category and its subcategories
    (e.g. "frontiermode" matches "frontiermode" and "frontiermode/anything") — for a landing
    page covering one subproject's wiki content rather than the whole project's. `title` lets
    the top heading be overridden (e.g. down to "## Wiki" when nesting inside a larger page).

    `dashboard_path`, if given, gets the index its own normalized bh-header — a Dashboard link
    back up, same block every page in the index already carries (see refresh_header) — left
    optional (default None, no header) since render_index is also used to build nested/scoped
    landing pages that aren't standalone top-level pages.
    """
    wiki_root = Path(wiki_root)
    index_dir = Path(index_dir) if index_dir is not None else wiki_root
    runtime_root = wiki_root.parent.parent

    spec = rollup.CollectSpec(
        root=wiki_root,
        glob="**/*.md",
        filter_fn=lambda fm: _in_category_scope(str(fm.get("category") or ""), category_prefix),
        group_by="category",
    )
    grouped = rollup.collect(spec)

    sections: list[str] = []
    if dashboard_path is not None:
        dashboard_rel = _relpath(dashboard_path, index_dir)
        block = header.render_header(project_name=project_name, dashboard_rel=dashboard_rel)
        sections += [f"<!-- {header.MARKER_NAME}:start -->", block, f"<!-- {header.MARKER_NAME}:end -->", ""]
    sections += [title, ""]
    if not grouped:
        sections.append("_No pages yet._")
        return "\n".join(sections) + "\n"

    for category in sorted(grouped.keys()):
        items = grouped[category]
        section_heading = category if category else "(uncategorized)"
        sections.append(f"## {section_heading}")
        sections.append("")
        sections.append(_render_table(items, index_dir, runtime_root=runtime_root, host_root=host_root))
    return "\n".join(sections)


def build_index(
    wiki_root: str | Path,
    output_path: str | Path,
    *,
    category_prefix: str | None = None,
    title: str = "# Wiki Index",
    dashboard_path: str | Path | None = None,
    project_name: str = "Backhaul",
    host_root: str | None = None,
) -> None:
    """Collect wiki pages under wiki_root and write the rendered category index.

    Regenerated wholesale on every run, same as BHT's board — always overwrites output_path.
    """
    output_path = Path(output_path)
    content = render_index(
        wiki_root, index_dir=output_path.parent, category_prefix=category_prefix, title=title,
        dashboard_path=dashboard_path, project_name=project_name, host_root=host_root,
    )
    filesafety.safe_write(output_path, content, overwrite=True)


def refresh_header(
    page_path: str | Path,
    index_path: str | Path | None = None,
    *,
    dashboard_path: str | Path | None = None,
    project_name: str = "Backhaul",
) -> None:
    """Insert/refresh the normalized Backhaul header in a single wiki page: project name,
    Dashboard link, Wiki Index link, category breadcrumb trail — see foundation/header.py.

    The category segments (e.g. "frontiermode / anything") are appended as plain text after
    the Index link, same as the old breadcrumb behavior — there's no per-category index page
    in this version, just the one master index. `dashboard_path` defaults to "BACKHAUL.md"
    (relative) if not given, mirroring services/ticket/board.py's refresh_board_link.
    """
    path = Path(page_path)
    doc = _frontmatter.parse(path)
    category = str(doc.frontmatter.get("category") or "")

    index_rel = _relpath(index_path, path.parent) if index_path is not None else "WIKI_INDEX.md"
    dashboard_rel = _relpath(dashboard_path, path.parent) if dashboard_path is not None else "BACKHAUL.md"
    segments = [seg for seg in category.split("/") if seg]

    block = header.render_header(
        project_name=project_name,
        dashboard_rel=dashboard_rel,
        indexer_label="Wiki Index",
        indexer_rel=index_rel,
        extra=" / ".join(segments) if segments else "",
    )
    doc.body = markers.refresh_block(doc.body, header.MARKER_NAME, block)
    _frontmatter.write(doc)
