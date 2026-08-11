"""Roadmap dependency-graph queries — ported from LunaFlow_A's scripts/roadmap/roadmap_graph.py
(see ../../../../../intake/roadmap-nodes/tooling/roadmap_graph.py for the original), adapted to:

- Backhaul's real YAML frontmatter (foundation.frontmatter + schema.validate()) instead of a
  hand-parsed "# RM-NNNN — Title" / "**Field:**" markdown header block.
- UID-scoped graphs: node IDs are RM_<uid>_NNN (foundation.identity.NumberedIdentity), and every
  query operates over exactly one UID's nodes. A DependsOn entry naming a node outside that UID
  is a hard error, not a cross-project link — "one node system each" per client/mod, enforced
  here rather than left as a convention.

Read-only against node files. Never writes. Never makes a judgment call — computes lists for a
human to judge, same boundary the original spec held itself to (graph-tooling-spec.md's Purpose
section, echoing qa.md's "script output becomes the evidence for verdicts, not raw code reads").

Deliberately does NOT use foundation.rollup.collect() here, unlike board.py/index.py — collect()
silently skips a file that fails frontmatter parsing (right for a board/index tolerating a stray
non-frontmatter file in the folder; wrong here, since graph-tooling-spec.md's Input section
requires a malformed node file to be a *hard* error naming the offending file, never a silent
drop that could produce a frontier missing an entry).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backhaul.foundation import filesafety, header
from backhaul.foundation import frontmatter as _frontmatter

from .schema import OPEN_STATUS, RoadmapNodeFrontmatter, RoadmapValidationError, validate

SATISFIED_STATUSES = frozenset({"resolved", "reached"})


def _relpath(target: str | Path, start: str | Path) -> str:
    """Relative path from directory `start` to `target`, POSIX-style separators. Deliberately
    NOT resolved — same reasoning as services/ticket/board.py's _relpath (paths are trusted as
    given, not re-derived against whatever filesystem this code happens to run on)."""
    return os.path.relpath(Path(target), Path(start)).replace(os.sep, "/")


class GraphError(Exception):
    """Raised on a malformed node file, a duplicate ID, a dangling DependsOn, a DependsOn
    crossing UIDs, or a dependency cycle — fail loud rather than silently producing a wrong
    frontier."""


@dataclass
class Node:
    frontmatter: RoadmapNodeFrontmatter
    path: Path

    @property
    def id(self) -> str:
        return self.frontmatter.id

    @property
    def kind(self) -> str:
        return self.frontmatter.kind

    @property
    def status(self) -> str:
        return self.frontmatter.status

    @property
    def title(self) -> str:
        return self.frontmatter.title

    @property
    def depends_on(self) -> list[str]:
        return self.frontmatter.depends_on


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_graph(nodes_root: str | Path, uid: str) -> dict[str, Node]:
    """Load every node belonging to `uid` under nodes_root into an in-memory graph.

    Other UIDs' node files may live in the same folder (one shared content_roots.roadmap per
    project) — only files matching this UID's `{uid}_*.md` prefix are considered. Raises
    GraphError on a parse failure, a schema violation, a duplicate ID, a DependsOn pointing at
    a nonexistent node, or a DependsOn crossing into a different UID.
    """
    nodes_root = Path(nodes_root)
    prefix = f"{uid}_"

    paths = sorted(nodes_root.glob(f"{prefix}*.md"))
    if not paths:
        raise GraphError(f"{nodes_root}: no {prefix}*.md node files found for uid {uid!r}")

    nodes: dict[str, Node] = {}
    for path in paths:
        try:
            doc = _frontmatter.parse(path)
            node_fm = validate(doc.frontmatter)
        except (_frontmatter.FrontmatterError, RoadmapValidationError) as e:
            raise GraphError(f"{path}: {e}") from e

        if node_fm.uid != uid:
            raise GraphError(
                f"{path}: file matched the {prefix!r} glob but its own uid field is {node_fm.uid!r}"
            )
        if node_fm.id in nodes:
            raise GraphError(
                f"{path}: duplicate node ID {node_fm.id}, already defined in {nodes[node_fm.id].path}"
            )
        nodes[node_fm.id] = Node(frontmatter=node_fm, path=path)

    for node in nodes.values():
        for dep_id in node.depends_on:
            if not dep_id.startswith(prefix):
                raise GraphError(
                    f"{node.path}: DependsOn entry {dep_id!r} belongs to a different UID than "
                    f"{uid!r} — each UID is its own independent graph, cross-UID edges aren't allowed"
                )
            if dep_id not in nodes:
                raise GraphError(
                    f"{node.path}: DependsOn references {dep_id}, which does not exist as a "
                    f"node file for uid {uid!r} in {nodes_root}"
                )

    return nodes


# ---------------------------------------------------------------------------
# Graph queries
# ---------------------------------------------------------------------------


def validate_graph(nodes: dict[str, Node]) -> None:
    """Raise GraphError naming every node in a cycle, if one exists."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in nodes}
    stack: list[str] = []

    def visit(nid: str) -> None:
        color[nid] = GRAY
        stack.append(nid)
        for dep in nodes[nid].depends_on:
            if color[dep] == GRAY:
                cycle_start = stack.index(dep)
                cycle = stack[cycle_start:] + [dep]
                raise GraphError("Cycle detected in DependsOn: " + " -> ".join(cycle))
            if color[dep] == WHITE:
                visit(dep)
        stack.pop()
        color[nid] = BLACK

    for nid in nodes:
        if color[nid] == WHITE:
            visit(nid)


def is_actionable(nodes: dict[str, Node], nid: str) -> bool:
    node = nodes[nid]
    if node.status != OPEN_STATUS[node.kind]:
        return False
    return all(nodes[dep].status in SATISFIED_STATUSES for dep in node.depends_on)


def frontier(nodes: dict[str, Node]) -> list[str]:
    return sorted(nid for nid in nodes if is_actionable(nodes, nid))


def dependents(nodes: dict[str, Node], nid: str) -> list[str]:
    """Direct, one-hop reverse of DependsOn — every node naming nid in its own DependsOn."""
    return sorted(other for other, node in nodes.items() if nid in node.depends_on)


def downstream(nodes: dict[str, Node], nid: str) -> list[str]:
    """Full transitive closure of dependents, in dependency order (closest to farthest)."""
    seen: list[str] = []
    seen_set: set[str] = set()
    queue = list(dependents(nodes, nid))
    while queue:
        current = queue.pop(0)
        if current in seen_set:
            continue
        seen_set.add(current)
        seen.append(current)
        for nxt in dependents(nodes, current):
            if nxt not in seen_set:
                queue.append(nxt)
    return seen


def blocking(nodes: dict[str, Node], nid: str) -> list[str]:
    """Every ancestor (via DependsOn, walked transitively) not yet resolved/reached."""
    seen_set: set[str] = set()
    result: list[str] = []
    queue = list(nodes[nid].depends_on)
    while queue:
        current = queue.pop(0)
        if current in seen_set:
            continue
        seen_set.add(current)
        if nodes[current].status not in SATISFIED_STATUSES:
            result.append(current)
        for nxt in nodes[current].depends_on:
            if nxt not in seen_set:
                queue.append(nxt)
    return result


def _depth(nodes: dict[str, Node], nid: str, cache: dict[str, int]) -> int:
    """Longest path from a root (a node with no DependsOn) to nid, for render()'s indentation."""
    if nid in cache:
        return cache[nid]
    deps = nodes[nid].depends_on
    d = 0 if not deps else 1 + max(_depth(nodes, dep, cache) for dep in deps)
    cache[nid] = d
    return d


def _node_link(node: Node, output_dir: Path) -> str:
    """`[**RM_FRO_001**](relative/path/to/file.md)` — every node ID rendered anywhere in
    render()/render_index() links straight to its own file, same convention board.py's ticket
    IDs and index.py's page titles already use."""
    return f"[**{node.id}**]({_relpath(node.path, output_dir)})"


def _render_body(nodes: dict[str, Node], *, level: int, output_dir: Path) -> list[str]:
    """Shared "Actionable now" + "Dependency structure" body, at heading depth level+1 —
    level=1 for render() (one graph, its own document), level=2 for render_index()'s per-UID
    sections (nested under that UID's own "## <uid>" heading). Kept as one implementation so
    the two renderers can't silently drift apart on what "actionable" or "depth" means.
    output_dir is the directory the rendered doc will actually live in — every node link is
    relative to it."""
    h = "#" * (level + 1)
    lines: list[str] = [f"{h} Actionable now", ""]
    front = frontier(nodes)
    if front:
        lines.append(
            "Everything below has no unsatisfied dependency. This is the menu — pick from "
            "here, not from a line."
        )
        lines.append("")
        for nid in front:
            lines.append(f"- {_node_link(nodes[nid], output_dir)} — {nodes[nid].title}")
    else:
        lines.append("Nothing is currently actionable.")
    lines.append("")
    lines.append(f"{h} Dependency structure")
    lines.append("")
    lines.append(
        "Depth-ordered (longest path from a root), not a literal tree — a node with multiple "
        "prerequisites is listed once, with all of them named inline, rather than repeated "
        "under each parent."
    )
    lines.append("")

    cache: dict[str, int] = {}
    depths = {nid: _depth(nodes, nid, cache) for nid in nodes}
    ordered = sorted(nodes, key=lambda nid: (depths[nid], nid))

    for nid in ordered:
        node = nodes[nid]
        indent = "  " * depths[nid]
        actionable_tag = " · ACTIONABLE" if is_actionable(nodes, nid) else ""
        status_tag = f"{node.kind} · {node.status}{actionable_tag}"
        deps_tag = f" — depends on: {', '.join(node.depends_on)}" if node.depends_on else ""
        lines.append(f"{indent}- {_node_link(node, output_dir)} [{status_tag}] {node.title}{deps_tag}")

    return lines


def render(
    nodes: dict[str, Node],
    *,
    title: str = "# Roadmap Graph — generated index",
    output_dir: str | Path | None = None,
) -> str:
    """Render one graph's markdown doc. output_dir is where this rendered text will actually be
    saved — every node link is relative to it. Defaults to the first node's own directory (the
    common case: the doc is saved right alongside the node files) when not given."""
    if output_dir is None:
        output_dir = next(iter(nodes.values())).path.parent if nodes else Path(".")
    output_dir = Path(output_dir)

    lines: list[str] = [title, "", "*Generated by `bhrm render` — do not hand-edit.*", ""]
    lines.extend(_render_body(nodes, level=1, output_dir=output_dir))
    return "\n".join(lines) + "\n"


def discover_uids(nodes_root: str | Path) -> list[str]:
    """Return every distinct client UID with at least one node file under nodes_root, sorted.

    Reads each file's own `uid` frontmatter field rather than inferring one from the filename,
    so a file that's been renamed away from the ID-prefix convention still counts toward the
    graph it actually declares itself to belong to. Tolerates a file that fails to parse at all
    (unlike graph loading itself, this is just a listing, not a query needing a hard guarantee
    over one specific graph) — a truly malformed node still surfaces loudly the moment its own
    UID's graph is actually loaded/validated.
    """
    nodes_root = Path(nodes_root)
    if not nodes_root.is_dir():
        return []
    uids: set[str] = set()
    for path in sorted(nodes_root.glob("*.md")):
        try:
            doc = _frontmatter.parse(path)
        except _frontmatter.FrontmatterError:
            continue
        uid = doc.frontmatter.get("uid")
        if uid:
            uids.add(str(uid))
    return sorted(uids)


def render_index(
    nodes_root: str | Path,
    *,
    title: str = "# Roadmap Graphs",
    output_dir: str | Path | None = None,
    dashboard_path: str | Path | None = None,
    project_name: str = "Backhaul",
) -> str:
    """Render every UID's graph under nodes_root as its own section in one combined, crawlable
    index — the roadmap module's equivalent of BHW's WIKI_INDEX.md / BHT's BOARD.md. Each
    section is a full graph in its own right (own frontier, own dependency structure) — graphs
    are never merged, only listed side by side, per "one node system each" (foundation
    __init__.py's docstring). output_dir is the directory the rendered index will actually live
    in — defaults to nodes_root's parent, matching the real convention the CLI writes to
    (ROADMAP_INDEX.md sits one level above the node files, same as BOARD.md/WIKI_INDEX.md).

    `dashboard_path`, if given, gets the index its own normalized bh-header — a Dashboard link
    back up, same block every node in the index already carries (see modules/roadmap/header.py).
    Rendering text only, same as the rest of this module — writing is build_index's job.
    """
    nodes_root = Path(nodes_root)
    output_dir = Path(output_dir) if output_dir is not None else nodes_root.parent
    uids = discover_uids(nodes_root)

    lines: list[str] = []
    if dashboard_path is not None:
        dashboard_rel = _relpath(dashboard_path, output_dir)
        block = header.render_header(project_name=project_name, dashboard_rel=dashboard_rel)
        lines += [f"<!-- {header.MARKER_NAME}:start -->", block, f"<!-- {header.MARKER_NAME}:end -->", ""]
    lines += [title, "", "*Generated by `bhrm index` — do not hand-edit.*", ""]
    if not uids:
        lines.append("_No roadmap graphs yet._")
        return "\n".join(lines) + "\n"

    for uid in uids:
        nodes = load_graph(nodes_root, uid)
        validate_graph(nodes)
        lines.append(f"## {uid}")
        lines.append("")
        lines.extend(_render_body(nodes, level=2, output_dir=output_dir))
        lines.append("")

    return "\n".join(lines) + "\n"


def build_index(
    nodes_root: str | Path,
    output_path: str | Path,
    *,
    title: str = "# Roadmap Graphs",
    dashboard_path: str | Path | None = None,
    project_name: str = "Backhaul",
) -> None:
    """Render every UID's graph under nodes_root and write the combined index. Regenerated
    wholesale on every run, same as BOARD.md/WIKI_INDEX.md — always overwrites output_path."""
    output_path = Path(output_path)
    content = render_index(
        nodes_root, title=title, output_dir=output_path.parent,
        dashboard_path=dashboard_path, project_name=project_name,
    )
    filesafety.safe_write(output_path, content, overwrite=True)


def export_json(nodes: dict[str, Node]) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "id": nid,
                "kind": node.kind,
                "status": node.status,
                "name": node.title,
                "actionable": is_actionable(nodes, nid),
                "owner": node.frontmatter.owner,
                "ticket": node.frontmatter.ticket,
            }
            for nid, node in sorted(nodes.items())
        ],
        "edges": [
            {"from": nid, "to": dep}
            for nid, node in sorted(nodes.items())
            for dep in node.depends_on
        ],
    }
