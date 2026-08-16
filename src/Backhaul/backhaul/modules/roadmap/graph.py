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

    @property
    def slug(self) -> str:
        """The human-chosen mnemonic from this node's own filename (`<ID>_<slug>.md`) — not a
        stored frontmatter field, on purpose: the filename already asserts it durably (every
        node gets one, `--slug` or the slugified title, see create.py), and a second,
        independently-editable slug field would just be a second place for the value to drift
        from what the filename says — the exact dual-write risk this codebase avoids everywhere
        else (Required By, Visualize: computed, never stored). Empty string only for the rare
        filename that ends up ID-only (a title that slugifies to nothing)."""
        stem = self.path.stem
        prefix = f"{self.id}_"
        return stem[len(prefix):] if stem.startswith(prefix) else ""


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


def ancestors(nodes: dict[str, Node], nid: str) -> list[str]:
    """Full transitive closure of DependsOn, regardless of status — every node nid depends on,
    directly or indirectly. Mirror of downstream() (which walks dependents() forward); this
    walks depends_on forward instead. Unlike blocking(), which only returns the *unsatisfied*
    subset of ancestors, this returns the complete prerequisite set whether resolved/reached or
    not — see BH_006 for why find_convergence_bypasses() needs the full set, not just the
    unsatisfied one."""
    seen: list[str] = []
    seen_set: set[str] = set()
    queue = list(nodes[nid].depends_on)
    while queue:
        current = queue.pop(0)
        if current in seen_set:
            continue
        seen_set.add(current)
        seen.append(current)
        for nxt in nodes[current].depends_on:
            if nxt not in seen_set:
                queue.append(nxt)
    return seen


def find_convergence_bypasses(nodes: dict[str, Node]) -> list[tuple[str, str, list[str]]]:
    """Candidate list (never a verdict — see below) of DependsOn edges that reach back into a
    convergence node's own prerequisite territory without ever routing through the convergence
    node itself. First formal definition of "bypass" in this codebase — see BH_006, which this
    implements verbatim.

    For each convergence node C, a node N is a bypass candidate when:
    1. N is not one of C's own ancestors (C's prerequisites obviously don't depend on C).
    2. N is not "gated by" C — not C itself, and not already downstream of C (properly routed
       through the checkpoint).
    3. N's own ancestor closure shares at least one node with C's ancestor closure — N reaches
       back into the same prerequisite territory C was built to gate, without depending on C.

    Advisory only, same discipline every other query here holds itself to (graph-tooling-spec's
    "computes lists for a human to judge"): never raises, never blocks anything. A shared
    ancestor doesn't automatically mean N *should* route through C — it may just coincidentally
    share an early, unrelated prerequisite. This is "worth a human look," not "this graph is
    invalid," unlike validate_graph()'s cycle check.

    Deliberately does NOT factor in a node's `created` date to filter out nodes that predate the
    convergence node (an option BH_006 explicitly left open, "left to the dev to decide at build
    time") — keeping this to one clear rule for v1 rather than a second, date-based heuristic;
    revisit if real usage shows this producing too much noise.

    Returns (bypass_node_id, convergence_node_id, sorted shared-ancestor ids) tuples, sorted for
    deterministic output.
    """
    findings: list[tuple[str, str, list[str]]] = []
    for c in sorted(nodes.values(), key=lambda node: node.id):
        if c.kind != "convergence":
            continue
        c_ancestors = set(ancestors(nodes, c.id))
        gated_by_c = {c.id} | set(downstream(nodes, c.id))
        for n in sorted(nodes.values(), key=lambda node: node.id):
            if n.id == c.id or n.id in c_ancestors or n.id in gated_by_c:
                continue
            n_ancestors = set(ancestors(nodes, n.id))
            overlap = n_ancestors & c_ancestors
            if overlap:
                findings.append((n.id, c.id, sorted(overlap)))
    return sorted(findings, key=lambda finding: (finding[0], finding[1]))


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
        html_path = output_dir / html_graph_filename(uid)
        if html_path.exists():
            lines.append(f"**Graph view:** [Open in browser ↗]({html_graph_filename(uid)})")
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
    wholesale on every run, same as BOARD.md/WIKI_INDEX.md — always overwrites output_path.

    Also unconditionally rewrites every discovered UID's HTML graph view
    (`ROADMAP_GRAPH_<uid>.html`, same directory as output_path) first, before rendering the
    markdown index itself — deliberate per the project owner (BH_008): every `bhrm index`/
    `refresh` call is a full rebuild of both, not just the markdown, and never gated on whether
    an HTML file already existed. Doing HTML first (not after) means render_index()'s own
    "Graph view" link — which checks html_graph_filename(uid) for existence — reflects *this*
    run's freshly-written file, not a stale one from before this call. A UID whose graph fails
    to load or validate raises here and aborts the whole call, same as it already would inside
    render_index() itself — per the project owner, that failure is the intended way a broken
    graph gets surfaced, not something to route around or skip past.
    """
    output_path = Path(output_path)
    nodes_root = Path(nodes_root)
    output_dir = output_path.parent

    for uid in discover_uids(nodes_root):
        nodes = load_graph(nodes_root, uid)
        validate_graph(nodes)
        html = render_html(nodes, title=f"{project_name} — {uid} Roadmap")
        filesafety.safe_write(output_dir / html_graph_filename(uid), html, overwrite=True)

    content = render_index(
        nodes_root, title=title, output_dir=output_dir,
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


# ---------------------------------------------------------------------------
# HTML/SVG rendering (bhrm render-html) — see BH_005's Design section for the
# decisions this implements: depth-layered layout, five-bucket status color,
# the export_json()-as-second-renderer split, and the edge-direction gotcha.
# ---------------------------------------------------------------------------

def html_graph_filename(uid: str) -> str:
    """Conventional filename `render_index()` looks for, sitting next to the index itself
    (same directory as ROADMAP_INDEX.md), to link a UID's HTML graph view automatically. Purely
    a filesystem-existence check at render time — `bhrm render-html --output` is never forced
    to this name (still fully user-controlled), so a project that's never generated one just
    gets no link, same graceful-omit pattern the rest of this module uses (no Roadmap/Roles
    module enabled -> no dashboard line, no ticket -> no Ticket line, etc.). Using this name is
    what makes the link appear without any new per-project config or CLI flag."""
    return f"ROADMAP_GRAPH_{uid}.html"


_HTML_BOX_WIDTH = 190
_HTML_WORK_HEIGHT = 44
_HTML_CONV_HEIGHT = 70
_HTML_MARGIN_X = 40
_HTML_MARGIN_Y = 40
_HTML_GAP_X = 60
_HTML_GAP_Y = 20

Position = tuple[float, float, float, float]  # x, y, width, height


def _html_layout(nodes: dict[str, Node]) -> tuple[dict[str, Position], float, float]:
    """Compute (x, y, w, h) for every node: layer = _depth() (already computed for render()'s
    markdown indentation), left to right; within a layer, nodes ordered by ID — the same
    tie-break render() itself uses. Deterministic: the same graph always produces the same
    layout, never dependent on dict iteration order. Returns (positions, canvas_width,
    canvas_height)."""
    cache: dict[str, int] = {}
    depths = {nid: _depth(nodes, nid, cache) for nid in nodes}

    layers: dict[int, list[str]] = {}
    for nid in sorted(nodes, key=lambda n: (depths[n], n)):
        layers.setdefault(depths[nid], []).append(nid)

    positions: dict[str, Position] = {}
    x = float(_HTML_MARGIN_X)
    canvas_height = float(_HTML_MARGIN_Y)
    for depth in sorted(layers):
        y = float(_HTML_MARGIN_Y)
        for nid in layers[depth]:
            h = _HTML_CONV_HEIGHT if nodes[nid].kind == "convergence" else _HTML_WORK_HEIGHT
            positions[nid] = (x, y, float(_HTML_BOX_WIDTH), float(h))
            y += h + _HTML_GAP_Y
        canvas_height = max(canvas_height, y - _HTML_GAP_Y + _HTML_MARGIN_Y)
        x += _HTML_BOX_WIDTH + _HTML_GAP_X
    canvas_width = x - _HTML_GAP_X + _HTML_MARGIN_X
    return positions, canvas_width, canvas_height


def _html_color(node: Node, actionable: bool) -> tuple[str, str, str]:
    """(fill, stroke, dash-array) for one node — five buckets lifted from the original
    mockup's own legend (already validated against real pilot data, not aesthetic guessing):
    work/resolved-or-superseded -> green, work/open+actionable -> blue,
    work/open+blocked -> gray, convergence/reached -> gold solid,
    convergence/WIP -> orange dashed."""
    if node.kind == "convergence":
        if node.status == "reached":
            return "#b8860b", "#f0c25a", ""
        return "#a3450f", "#ffb27a", "5,3"
    if node.status in ("resolved", "superseded"):
        return "#2e7d4a", "#2e7d4a", ""
    if actionable:
        return "#1565c0", "#1565c0", ""
    return "#4a4f58", "#4a4f58", ""


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; background: #14161a; color: #e8e8e8; margin: 0; padding: 24px; }}
  h1 {{ margin: 0 0 4px 0; font-size: 20px; }}
  .subtitle {{ color: #9aa0a6; font-size: 13px; margin-bottom: 12px; }}
  .legend {{ display: flex; gap: 18px; flex-wrap: wrap; margin-bottom: 16px; font-size: 12px; color: #cfd3d8; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .swatch {{ width: 14px; height: 14px; border-radius: 3px; display: inline-block; flex-shrink: 0; }}
  .frontier-banner {{ background: #123b2a; border: 1px solid #2e7d4a; color: #a6f2c9; padding: 8px 14px; border-radius: 6px; font-size: 13px; margin-bottom: 16px; }}
  svg {{ background: #1b1e24; border-radius: 8px; border: 1px solid #2a2e36; }}
  .node-label {{ font-size: 11px; fill: #f2f2f2; font-weight: 600; }}
  .node-slug {{ font-weight: 700; fill: #ffe066; }}
  .node-sub {{ font-size: 9px; fill: #cfd3d8; }}
  .edge {{ stroke: #5a6270; stroke-width: 1.4; fill: none; marker-end: url(#arrow); }}
  .focus-banner {{ display: none; padding: 8px 14px; border-radius: 6px; font-size: 13px; margin-bottom: 16px; }}
  .node-group rect {{ transition: stroke 0.15s ease, filter 0.15s ease; }}
  .node-group.focused rect {{ stroke: #ffe066 !important; stroke-width: 4px !important; filter: drop-shadow(0 0 10px rgba(255, 224, 102, 0.85)); }}
  .node-group.focused .node-label {{ fill: #ffe066; }}
</style>
</head>
<body>

<h1>{title}</h1>
<div class="subtitle">Generated by `bhrm render-html` — do not hand-edit.</div>

<div class="frontier-banner"><strong>Actionable now:</strong> {frontier_text}</div>

<div id="focus-banner" class="focus-banner"></div>

<div class="legend">
  <div class="legend-item"><span class="swatch" style="background:#2e7d4a;"></span> resolved / superseded</div>
  <div class="legend-item"><span class="swatch" style="background:#1565c0;"></span> open &amp; actionable</div>
  <div class="legend-item"><span class="swatch" style="background:#4a4f58;"></span> open &amp; blocked</div>
  <div class="legend-item"><span class="swatch" style="background:#b8860b;"></span> convergence · reached</div>
  <div class="legend-item"><span class="swatch" style="background:#a3450f; border:1px dashed #ffb27a;"></span> convergence · WIP</div>
</div>

{svg}

<script>
(function () {{
  var params = new URLSearchParams(window.location.search);
  var focus = params.get('focus');
  var banner = document.getElementById('focus-banner');
  if (!focus) return;

  focus = focus.trim().toUpperCase();
  var target = document.querySelector('.node-group[data-id="' + focus + '"]');

  banner.style.display = 'block';
  if (target) {{
    target.classList.add('focused');
    target.scrollIntoView({{ behavior: 'smooth', block: 'center', inline: 'center' }});
    banner.style.background = '#123b2a';
    banner.style.border = '1px solid #2e7d4a';
    banner.style.color = '#a6f2c9';
    banner.textContent = 'Focused on ' + focus + ' — highlighted below.';
  }} else {{
    banner.style.background = '#4a2f0a';
    banner.style.border = '1px solid #a3661a';
    banner.style.color = '#ffd9a0';
    banner.textContent = 'No node "' + focus + '" in this graph.';
  }}
}})();
</script>

</body>
</html>
"""


def render_html(nodes: dict[str, Node], *, title: str = "Roadmap Graph") -> str:
    """Render one graph as a standalone, self-contained HTML/SVG document — a real, data-driven
    successor to the hand-laid-out mockup
    (intake/roadmap-nodes/design/Mockups/sample-visualization.html). No external assets, no
    network calls; safe to open as a local file or serve as-is.

    Consumes export_json(nodes) for node/edge data (a second renderer over the same export, not
    a second parser) plus this module's own _depth() for layout, mirroring how render() already
    reuses both. Layout and color are both pure functions of the graph's own data — same graph,
    byte-identical output, no wall-clock timestamps or unsorted-dict-order dependence.
    """
    payload = export_json(nodes)
    positions, canvas_width, canvas_height = _html_layout(nodes)

    node_svg: list[str] = []
    for entry in payload["nodes"]:
        nid = entry["id"]
        node = nodes[nid]
        x, y, w, h = positions[nid]
        fill, stroke, dash = _html_color(node, entry["actionable"])
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        label = _xml_escape(node.id)
        slug = _xml_escape(node.slug)
        slug_tspan = f' <tspan class="node-slug">{slug}</tspan>' if slug else ""
        name = _xml_escape(node.title)
        status_tag = _xml_escape(f"{node.kind} · {node.status}")
        tooltip_slug = f" · {slug}" if slug else ""
        node_svg.append(
            f'<g class="node-group" data-id="{node.id}">'
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="6" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"{dash_attr}/>'
            f'<text x="{x + 10:g}" y="{y + 18:g}" class="node-label">{label}{slug_tspan}</text>'
            f'<text x="{x + 10:g}" y="{y + 32:g}" class="node-sub">{name}</text>'
            f"<title>{label}{tooltip_slug} — {status_tag}. {name}</title>"
            f"</g>"
        )

    edge_svg: list[str] = []
    for edge in payload["edges"]:
        # edge = {"from": dependent, "to": prerequisite}. Visual flow is left-to-right,
        # prerequisite into what it unlocks, so the drawn source is "to" and the drawn target
        # is "from" — reversed from the field names. See this function's own docstring / BH_005's
        # Design section for why this isn't a literal from->to draw.
        dependent, prerequisite = edge["from"], edge["to"]
        sx, sy, sw, sh = positions[prerequisite]
        tx, ty, tw, th = positions[dependent]
        x1, y1 = sx + sw, sy + sh / 2
        x2, y2 = tx, ty + th / 2
        cx = (x1 + x2) / 2
        edge_svg.append(f'<path class="edge" d="M{x1:g},{y1:g} C{cx:g},{y1:g} {cx:g},{y2:g} {x2:g},{y2:g}"/>')

    svg = "\n".join(
        [
            f'<svg viewBox="0 0 {canvas_width:g} {canvas_height:g}" width="{canvas_width:g}" '
            f'height="{canvas_height:g}" xmlns="http://www.w3.org/2000/svg">',
            '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" '
            'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L7,3 z" fill="#5a6270"/></marker></defs>',
            *edge_svg,
            *node_svg,
            "</svg>",
        ]
    )

    front = frontier(nodes)
    frontier_text = (
        ", ".join(f"{nid} ({nodes[nid].title})" for nid in front) if front else "nothing right now"
    )

    return _HTML_TEMPLATE.format(
        title=_xml_escape(title), svg=svg, frontier_text=_xml_escape(frontier_text)
    )
