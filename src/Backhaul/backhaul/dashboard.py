"""Backhaul's cross-service front page: a small dashboard linking to the ticket board and
wiki index for one project, with a quick open-ticket/page-count summary.

Lives at the top of the package (not under services/ or modules/) deliberately — it's the
composition root that knows about both BHT and BHW, which is different from one *service*
depending on another (something migration/ARCHITECTURE.md explicitly avoids; BHT and BHW
only reference each other via typed Refs, never each other's internals). An orchestrator
sitting above both and rendering a combined view is expected to import both.
"""

from __future__ import annotations

import os
from pathlib import Path

from backhaul.foundation import filesafety, frontmatter as _frontmatter, header, rollup
from backhaul.modules.roadmap import graph as _roadmap_graph
from backhaul.modules.roles import schema as _roles_schema
from backhaul.services.ticket.schema import OPEN_STATES


def _relpath(target: str | Path, start: str | Path) -> str:
    """Relative path from directory `start` to `target`, POSIX-style separators. Not resolved:
    paths passed in are trusted as already-correct absolute paths, so no filesystem
    re-derivation is needed. (services/ticket/board.py's own `_relpath` does call `.resolve()`
    — unrelated reasoning specific to that function's own Edit-link building, not a discrepancy
    worth reconciling, since content roots aren't expected to be symlinked.)"""
    return os.path.relpath(Path(target), Path(start)).replace(os.sep, "/")


def _count_open_tickets(tickets_root: Path) -> int:
    if not tickets_root.is_dir():
        return 0
    spec = rollup.CollectSpec(
        root=tickets_root, glob="*.md", filter_fn=lambda fm: fm.get("status") in OPEN_STATES
    )
    items = rollup.collect(spec)
    return len(items) if isinstance(items, list) else 0


def _count_wiki_pages(wiki_root: Path) -> int:
    if not wiki_root.is_dir():
        return 0
    items = rollup.collect(rollup.CollectSpec(root=wiki_root, glob="**/*.md"))
    return len(items) if isinstance(items, list) else 0


def _count_roadmap(roadmap_root: Path) -> tuple[int, int]:
    """Return (graph_count, actionable_count) across every UID under roadmap_root.

    Tolerant of a single UID's graph failing to load/validate — skips just that graph rather
    than failing dashboard generation over one bad node file somewhere in a shared folder.
    """
    if not roadmap_root.is_dir():
        return 0, 0
    graph_count = 0
    actionable_count = 0
    for uid in _roadmap_graph.discover_uids(roadmap_root):
        try:
            nodes = _roadmap_graph.load_graph(roadmap_root, uid)
            _roadmap_graph.validate_graph(nodes)
        except _roadmap_graph.GraphError:
            continue
        graph_count += 1
        actionable_count += len(_roadmap_graph.frontier(nodes))
    return graph_count, actionable_count


def _count_roles(roles_root: Path) -> int:
    """Return the count of active roles under roles_root. Tolerant of a single role file
    failing to parse/validate — skips just that file, same reasoning _count_roadmap uses."""
    if not roles_root.is_dir():
        return 0
    count = 0
    for path in sorted(roles_root.glob("*.md")):
        try:
            fm = _frontmatter.parse(path).frontmatter
            role = _roles_schema.validate(fm)
        except (_frontmatter.FrontmatterError, _roles_schema.RoleValidationError):
            continue
        if role.status == "active":
            count += 1
    return count


def render_dashboard(
    *,
    tickets_root: str | Path,
    wiki_root: str | Path,
    board_path: str | Path,
    index_path: str | Path,
    dashboard_dir: str | Path,
    roadmap_root: str | Path | None = None,
    roadmap_index_path: str | Path | None = None,
    roles_root: str | Path | None = None,
    roles_index_path: str | Path | None = None,
    project_name: str = "Backhaul",
    build_ready: str | None = None,
) -> str:
    """Render BACKHAUL.md's body: links to the board and wiki index, each with a live count.

    The Roadmap/Team lines are only included when roadmap_root/roles_root are given — the CLI
    only passes them through when that module is both configured (content_roots.roadmap /
    content_roots.roles) and enabled (enabled_modules), so a project that doesn't use a module
    never sees a dead link.

    `build_ready` (BH_007), when given ("ready" or "notReady" — see foundation/config.py's
    get_build_ready), renders a bolded one-line marker right under the title, ahead of every
    other line — the whole point is a human can answer "is this buildable right now" without
    reading the board/roadmap/tickets separately, so it has to be the first thing seen, not
    buried alongside the counts. Omitted (None, the default) shows no marker line at all — a
    project that hasn't opted into this convention sees exactly today's dashboard, unchanged.
    Deliberately kept out of foundation/header.py's shared bh-header block: that block is
    rendered on every piece of Backhaul content (tickets, pages, nodes, roles), and this marker
    is specific to the dashboard's own front page, not something every ticket should carry.

    Gets its own bh-header too (see foundation/header.py) — just the bolded project name, no
    Dashboard link (this file *is* the dashboard) and no indexer link (there are several, one
    per line below) — so a project's front page is instantly identifiable the same way every
    ticket/page/node under it already is.
    """
    tickets_root = Path(tickets_root)
    wiki_root = Path(wiki_root)
    dashboard_dir = Path(dashboard_dir)

    open_count = _count_open_tickets(tickets_root)
    page_count = _count_wiki_pages(wiki_root)

    board_rel = _relpath(board_path, dashboard_dir)
    index_rel = _relpath(index_path, dashboard_dir)

    ticket_word = "ticket" if open_count == 1 else "tickets"
    page_word = "page" if page_count == 1 else "pages"

    header_block = header.render_header(project_name=project_name)
    lines = [
        f"<!-- {header.MARKER_NAME}:start -->",
        header_block,
        f"<!-- {header.MARKER_NAME}:end -->",
        "",
        "# Backhaul",
        "",
    ]
    if build_ready == "ready":
        lines += ["**Build status: Ready**", ""]
    elif build_ready == "notReady":
        lines += ["**Build status: Not ready**", ""]
    lines += [
        f"- [Work Board]({board_rel}) — {open_count} open {ticket_word}",
        f"- [Wiki Index]({index_rel}) — {page_count} {page_word}",
    ]

    if roadmap_root is not None and roadmap_index_path is not None:
        graph_count, actionable_count = _count_roadmap(Path(roadmap_root))
        roadmap_rel = _relpath(roadmap_index_path, dashboard_dir)
        graph_word = "graph" if graph_count == 1 else "graphs"
        node_word = "node" if actionable_count == 1 else "nodes"
        lines.append(
            f"- [Roadmap]({roadmap_rel}) — {graph_count} {graph_word}, "
            f"{actionable_count} actionable {node_word}"
        )

    if roles_root is not None and roles_index_path is not None:
        role_count = _count_roles(Path(roles_root))
        roles_rel = _relpath(roles_index_path, dashboard_dir)
        role_word = "role" if role_count == 1 else "roles"
        lines.append(f"- [Team]({roles_rel}) — {role_count} {role_word}")

    return "\n".join(lines) + "\n"


def build_dashboard(
    *,
    tickets_root: str | Path,
    wiki_root: str | Path,
    board_path: str | Path,
    index_path: str | Path,
    output_path: str | Path,
    roadmap_root: str | Path | None = None,
    roadmap_index_path: str | Path | None = None,
    roles_root: str | Path | None = None,
    roles_index_path: str | Path | None = None,
    project_name: str = "Backhaul",
    build_ready: str | None = None,
) -> None:
    """Render and write BACKHAUL.md to output_path, overwriting wholesale like BOARD.md/
    WIKI_INDEX.md — it's a generated front page, not something to hand-edit."""
    output_path = Path(output_path)
    content = render_dashboard(
        tickets_root=tickets_root,
        wiki_root=wiki_root,
        board_path=board_path,
        index_path=index_path,
        dashboard_dir=output_path.parent,
        roadmap_root=roadmap_root,
        roadmap_index_path=roadmap_index_path,
        roles_root=roles_root,
        roles_index_path=roles_index_path,
        project_name=project_name,
        build_ready=build_ready,
    )
    filesafety.safe_write(output_path, content, overwrite=True)
