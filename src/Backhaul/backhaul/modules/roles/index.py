"""Renders ROLES_INDEX.md — the roster: every role in this project, one row each, with a
Launch link straight into a preloaded Cowork session. Replaces the hand-maintained "## Team"
section LunaFlow's supreme-leader.md carries today with a generated one, same fix
BOARD.md/WIKI_INDEX.md/ROADMAP_INDEX.md already made for tickets/wiki/roadmap.
"""

from __future__ import annotations

import os
from pathlib import Path

from backhaul.foundation import filesafety, handler_uri, header, host_paths, rollup

from . import launch as _launch
from .schema import validate

_COLUMNS = ("Role", "Persona", "Status", "Purpose", "Launch", "Edit")

# Must match the SCHEME constant in modules/handlers/editmd. Kept as a plain string here
# (rather than importing that module) so modules/roles only depends on foundation, not on
# other modules — see migration/ARCHITECTURE.md. Mirrors services/wiki/index.py's approach.
_EDIT_SCHEME = "editmd"


def _relpath(target: str | Path, start: str | Path) -> str:
    """Relative path from directory `start` to `target`, POSIX-style separators. Deliberately
    NOT resolved — see services/ticket/board.py's _relpath for why."""
    return os.path.relpath(Path(target), Path(start)).replace(os.sep, "/")


def _row(
    item: dict,
    index_dir: Path,
    project_root: str | Path | None,
    repo_url: str | None,
    *,
    runtime_root: Path,
    host_root: str | None,
) -> str:
    role = validate(item)
    path = item.get("_path")

    if isinstance(path, Path):
        title_cell = f"[{role.title}]({_relpath(path, index_dir)})"
        # host_root (see foundation/host_paths.py), when configured, re-roots the Edit link's
        # absolute path onto the real machine instead of wherever this code is running.
        host_path = host_paths.to_host_path(path, runtime_root=runtime_root, host_root=host_root)
        edit = f"[Edit]({handler_uri.build_uri(_EDIT_SCHEME, host_path)})"
        link = _launch.build_launch_link(path, project_root=project_root, repo_url=repo_url)
        launch_cell = f"[Launch]({link})" if link else ""
    else:
        title_cell = role.title
        edit = ""
        launch_cell = ""

    persona = role.persona or ""
    purpose = role.purpose or ""
    return f"| {title_cell} | {persona} | {role.status} | {purpose} | {launch_cell} | {edit} |"


def _render_table(
    items: list[dict],
    index_dir: Path,
    project_root: str | Path | None,
    repo_url: str | None,
    *,
    runtime_root: Path,
    host_root: str | None,
) -> str:
    if not items:
        return "_No roles defined yet._\n"
    heading = "| " + " | ".join(_COLUMNS) + " |"
    sep = "|" + "|".join(["---"] * len(_COLUMNS)) + "|"
    rows = [
        _row(item, index_dir, project_root, repo_url, runtime_root=runtime_root, host_root=host_root)
        for item in items
    ]
    return "\n".join([heading, sep, *rows]) + "\n"


def render_index(
    roles_root: str | Path,
    index_dir: str | Path | None = None,
    *,
    title: str = "# Roles",
    dashboard_path: str | Path | None = None,
    project_name: str = "Backhaul",
    project_root: str | Path | None = None,
    repo_url: str | None = None,
    host_root: str | None = None,
) -> str:
    """Collect role pages under roles_root and render the roster's markdown body.

    Sorted by title. `index_dir` is the directory the rendered index will actually live in
    (defaults to roles_root itself) — links are relative to it. `project_root` and `repo_url`,
    if given, are threaded into each row's Launch link as plain-text preamble lines (see
    modules/roles/launch.py for why neither is the link's `folder=` param) — `project_root`
    expected to already be a real, absolute path for the machine this will be clicked on;
    `repo_url` this checkout's own git remote. `host_root`, if given, re-roots each row's Edit
    link the same way (see foundation/host_paths.py) — independently of `project_root`, since
    the Edit link needs the file's offset from roles_root, not just the whole project root.
    `dashboard_path`, if given, gets the index its own normalized bh-header, same convention as
    BOARD.md/WIKI_INDEX.md/ROADMAP_INDEX.md.
    """
    roles_root = Path(roles_root)
    index_dir = Path(index_dir) if index_dir is not None else roles_root
    runtime_root = roles_root.parent.parent

    items = rollup.collect(rollup.CollectSpec(root=roles_root, glob="*.md"))
    items = sorted(items, key=lambda item: str(item.get("title", "")))

    sections: list[str] = []
    if dashboard_path is not None:
        dashboard_rel = _relpath(dashboard_path, index_dir)
        block = header.render_header(project_name=project_name, dashboard_rel=dashboard_rel)
        sections += [f"<!-- {header.MARKER_NAME}:start -->", block, f"<!-- {header.MARKER_NAME}:end -->", ""]
    sections += [
        title, "",
        _render_table(items, index_dir, project_root, repo_url, runtime_root=runtime_root, host_root=host_root),
    ]
    return "\n".join(sections)


def build_index(
    roles_root: str | Path,
    output_path: str | Path,
    *,
    title: str = "# Roles",
    dashboard_path: str | Path | None = None,
    project_name: str = "Backhaul",
    project_root: str | Path | None = None,
    repo_url: str | None = None,
    host_root: str | None = None,
) -> None:
    """Collect role pages under roles_root and write the rendered roster. Regenerated
    wholesale on every run, same as BOARD.md/WIKI_INDEX.md/ROADMAP_INDEX.md — always
    overwrites output_path."""
    output_path = Path(output_path)
    content = render_index(
        roles_root, index_dir=output_path.parent, title=title,
        dashboard_path=dashboard_path, project_name=project_name, project_root=project_root,
        repo_url=repo_url, host_root=host_root,
    )
    filesafety.safe_write(output_path, content, overwrite=True)
