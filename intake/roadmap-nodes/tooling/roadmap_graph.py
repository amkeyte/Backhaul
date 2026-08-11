#!/usr/bin/env python3
"""
roadmap_graph.py — Stage 0 real tooling for the RM node dependency graph.

Implements the buildable spec at
Documents/ClaudeWiki/RoadmapGraph/Specs/graph-tooling-spec.md against the node file format at
Documents/ClaudeWiki/RoadmapGraph/Specs/node-format-spec.md.

One script, one in-memory graph, several read-only queries against it. Never writes to a node file.
Never makes a judgment call — it computes lists for a human to judge (see graph-tooling-spec.md's
"Purpose" section for the QA-tooling precedent this mirrors).

Standard library only, on purpose — this is meant to run the same way scripts/qa/'s tooling does,
with nothing extra to install.

Usage:
    python roadmap_graph.py validate
    python roadmap_graph.py frontier
    python roadmap_graph.py dependents RM-0010
    python roadmap_graph.py downstream RM-0010
    python roadmap_graph.py blocking RM-0011
    python roadmap_graph.py render
    python roadmap_graph.py export-json [--out FILE]

All commands accept --nodes-dir to point at a different Nodes folder (defaults to
Documents/Roadmap/Nodes relative to the real repo, resolved from this script's own location so it
works regardless of the caller's current directory).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

RM_ID_RE = re.compile(r"RM-\d{4}")
H1_RE = re.compile(r"^#\s+(RM-\d{4})\s*(?:—|-{1,2})\s*(.+?)\s*$")
FIELD_RE = re.compile(r"^\*\*([A-Za-z ]+):\*\*\s*(.*)$")

WORK_STATUSES = {"open", "resolved", "superseded"}
CONVERGENCE_STATUSES = {"WIP", "reached"}
SATISFIED_STATUSES = {"resolved", "reached"}


class NodeParseError(Exception):
    """A single node file failed to parse — fail loud, name the file, refuse to run."""


@dataclass
class Node:
    id: str
    kind: str
    status: str
    created: str
    owner: str
    depends_on: List[str]
    name: str
    ticket: Optional[str]
    file_path: Path


def _read_header_block(lines: List[str]) -> Dict[str, str]:
    """Consume the contiguous **Field:** block immediately after the H1 + blank line.

    Stops at the first blank line following the header fields — deliberately does not scan the
    rest of the file, so a body paragraph that happens to mention "**Something:**" (dated notes do
    this a lot in the real pilot data) can never be mistaken for a header field.
    """
    fields: Dict[str, str] = {}
    i = 0
    # skip to first blank line after H1
    while i < len(lines) and lines[i].strip() != "":
        i += 1
    i += 1  # step past the blank line
    while i < len(lines):
        line = lines[i].rstrip("\n")
        if line.strip() == "":
            break
        m = FIELD_RE.match(line)
        if not m:
            break
        fields[m.group(1).strip()] = m.group(2).strip()
        i += 1
    return fields


def parse_node(path: Path) -> Node:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise NodeParseError(f"{path}: could not read file ({exc})") from exc

    lines = text.splitlines()
    if not lines:
        raise NodeParseError(f"{path}: empty file")

    h1 = H1_RE.match(lines[0].strip())
    if not h1:
        raise NodeParseError(
            f"{path}: first line is not a valid '# RM-NNNN — Title' header (got: {lines[0]!r})"
        )
    id_from_title, name = h1.group(1), h1.group(2)
    id_from_filename = path.stem.split("-")[0] + "-" + path.stem.split("-")[1]
    if id_from_title != id_from_filename:
        raise NodeParseError(
            f"{path}: filename implies {id_from_filename} but the H1 header says {id_from_title}"
        )

    fields = _read_header_block(lines)

    for required in ("Kind", "Status", "Created", "Owner", "DependsOn"):
        if required not in fields:
            raise NodeParseError(f"{path}: missing required header field '{required}:'")

    kind = fields["Kind"].strip()
    if kind not in ("work", "convergence"):
        raise NodeParseError(
            f"{path}: unknown Kind '{kind}' — must be 'work' or 'convergence'"
        )

    status = fields["Status"].strip()
    valid_statuses = WORK_STATUSES if kind == "work" else CONVERGENCE_STATUSES
    if status not in valid_statuses:
        raise NodeParseError(
            f"{path}: Kind is '{kind}' but Status is '{status}' — expected one of "
            f"{sorted(valid_statuses)}"
        )

    depends_on = list(dict.fromkeys(RM_ID_RE.findall(fields["DependsOn"])))

    ticket = fields.get("Ticket") or None

    return Node(
        id=id_from_title,
        kind=kind,
        status=status,
        created=fields["Created"].strip(),
        owner=fields["Owner"].strip(),
        depends_on=depends_on,
        name=name,
        ticket=ticket,
        file_path=path,
    )


def load_graph(nodes_dir: Path) -> Dict[str, Node]:
    node_files = sorted(nodes_dir.glob("RM-*.md"))
    if not node_files:
        raise NodeParseError(f"{nodes_dir}: no RM-*.md files found")

    nodes: Dict[str, Node] = {}
    for path in node_files:
        node = parse_node(path)
        if node.id in nodes:
            raise NodeParseError(
                f"{path}: duplicate node ID {node.id}, already defined in "
                f"{nodes[node.id].file_path}"
            )
        nodes[node.id] = node

    # Second pass: every DependsOn entry must resolve to a real node.
    for node in nodes.values():
        for dep_id in node.depends_on:
            if dep_id not in nodes:
                raise NodeParseError(
                    f"{node.file_path}: DependsOn references {dep_id}, which does not exist "
                    f"as a node file in {nodes_dir}"
                )

    return nodes


# ---------------------------------------------------------------------------
# Graph queries
# ---------------------------------------------------------------------------


def validate(nodes: Dict[str, Node]) -> None:
    """Raise NodeParseError naming every node in a cycle, if one exists."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in nodes}
    stack: List[str] = []

    def visit(nid: str) -> None:
        color[nid] = GRAY
        stack.append(nid)
        for dep in nodes[nid].depends_on:
            if color[dep] == GRAY:
                cycle_start = stack.index(dep)
                cycle = stack[cycle_start:] + [dep]
                raise NodeParseError(
                    "Cycle detected in DependsOn: " + " -> ".join(cycle)
                )
            if color[dep] == WHITE:
                visit(dep)
        stack.pop()
        color[nid] = BLACK

    for nid in nodes:
        if color[nid] == WHITE:
            visit(nid)


def is_actionable(nodes: Dict[str, Node], nid: str) -> bool:
    node = nodes[nid]
    status_ok = (node.kind == "work" and node.status == "open") or (
        node.kind == "convergence" and node.status == "WIP"
    )
    if not status_ok:
        return False
    return all(nodes[dep].status in SATISFIED_STATUSES for dep in node.depends_on)


def frontier(nodes: Dict[str, Node]) -> List[str]:
    return sorted(nid for nid in nodes if is_actionable(nodes, nid))


def dependents(nodes: Dict[str, Node], nid: str) -> List[str]:
    """Direct, one-hop reverse of DependsOn — every node naming nid in its own DependsOn."""
    return sorted(other for other, node in nodes.items() if nid in node.depends_on)


def downstream(nodes: Dict[str, Node], nid: str) -> List[str]:
    """Full transitive closure of dependents, in dependency order (closest to farthest)."""
    seen: List[str] = []
    seen_set = set()
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


def blocking(nodes: Dict[str, Node], nid: str) -> List[str]:
    """Every ancestor (via DependsOn, walked transitively) not yet resolved/reached."""
    seen_set = set()
    result: List[str] = []
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


def _depth(nodes: Dict[str, Node], nid: str, cache: Dict[str, int]) -> int:
    """Longest path from a root (a node with no DependsOn) to nid, for render()'s indentation."""
    if nid in cache:
        return cache[nid]
    deps = nodes[nid].depends_on
    d = 0 if not deps else 1 + max(_depth(nodes, dep, cache) for dep in deps)
    cache[nid] = d
    return d


def render(nodes: Dict[str, Node]) -> str:
    lines: List[str] = []
    lines.append("# Roadmap Graph — generated index")
    lines.append("")
    lines.append("*Generated by scripts/roadmap/roadmap_graph.py — do not hand-edit.*")
    lines.append("")
    lines.append("## Actionable now")
    lines.append("")
    front = frontier(nodes)
    if front:
        lines.append(
            "Everything below has no unsatisfied dependency. This is the menu — pick from here, "
            "not from a line."
        )
        lines.append("")
        for nid in front:
            lines.append(f"- **{nid}** — {nodes[nid].name}")
    else:
        lines.append("Nothing is currently actionable.")
    lines.append("")
    lines.append("## Dependency structure")
    lines.append("")
    lines.append(
        "Depth-ordered (longest path from a root), not a literal tree — a node with multiple "
        "prerequisites is listed once, with all of them named inline, rather than repeated under "
        "each parent."
    )
    lines.append("")

    cache: Dict[str, int] = {}
    depths = {nid: _depth(nodes, nid, cache) for nid in nodes}
    ordered = sorted(nodes, key=lambda nid: (depths[nid], nid))

    for nid in ordered:
        node = nodes[nid]
        indent = "  " * depths[nid]
        actionable_tag = " · ACTIONABLE" if is_actionable(nodes, nid) else ""
        status_tag = f"{node.kind} · {node.status}{actionable_tag}"
        deps_tag = (
            f" — depends on: {', '.join(node.depends_on)}" if node.depends_on else ""
        )
        lines.append(f"{indent}- **{nid}** [{status_tag}] {node.name}{deps_tag}")

    return "\n".join(lines) + "\n"


def export_json(nodes: Dict[str, Node]) -> dict:
    return {
        "nodes": [
            {
                "id": nid,
                "kind": node.kind,
                "status": node.status,
                "name": node.name,
                "actionable": is_actionable(nodes, nid),
                "owner": node.owner,
                "ticket": node.ticket,
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
# CLI
# ---------------------------------------------------------------------------


def default_nodes_dir() -> Path:
    # scripts/roadmap/roadmap_graph.py -> repo root -> Documents/Roadmap/Nodes
    return Path(__file__).resolve().parents[2] / "Documents" / "Roadmap" / "Nodes"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--nodes-dir",
        type=Path,
        default=None,
        help="Path to Documents/Roadmap/Nodes (default: resolved relative to this script)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="Check the graph for cycles.")
    sub.add_parser("frontier", help="List every currently-actionable node.")

    p = sub.add_parser("dependents", help="Direct (one-hop) reverse dependents of an RM-ID.")
    p.add_argument("rm_id")

    p = sub.add_parser("downstream", help="Full transitive closure of dependents of an RM-ID.")
    p.add_argument("rm_id")

    p = sub.add_parser("blocking", help="Unresolved ancestors of an RM-ID, transitively.")
    p.add_argument("rm_id")

    sub.add_parser("render", help="Generate the crawlable markdown index.")

    p = sub.add_parser("export-json", help="Export the graph as structured JSON.")
    p.add_argument("--out", type=Path, default=None, help="Write JSON to this file instead of stdout.")

    args = parser.parse_args(argv)
    nodes_dir = args.nodes_dir or default_nodes_dir()

    try:
        nodes = load_graph(nodes_dir)
        validate(nodes)
    except NodeParseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    def require_known_id(rm_id: str) -> bool:
        if rm_id not in nodes:
            print(f"ERROR: unknown node {rm_id}", file=sys.stderr)
            return False
        return True

    if args.command == "validate":
        print(f"OK — {len(nodes)} nodes, no cycles.")
        return 0

    if args.command == "frontier":
        for nid in frontier(nodes):
            print(f"{nid}\t{nodes[nid].name}")
        return 0

    if args.command == "dependents":
        if not require_known_id(args.rm_id):
            return 1
        for nid in dependents(nodes, args.rm_id):
            print(nid)
        return 0

    if args.command == "downstream":
        if not require_known_id(args.rm_id):
            return 1
        for nid in downstream(nodes, args.rm_id):
            print(nid)
        return 0

    if args.command == "blocking":
        if not require_known_id(args.rm_id):
            return 1
        for nid in blocking(nodes, args.rm_id):
            print(nid)
        return 0

    if args.command == "render":
        print(render(nodes), end="")
        return 0

    if args.command == "export-json":
        payload = json.dumps(export_json(nodes), indent=2)
        if args.out:
            args.out.write_text(payload + "\n", encoding="utf-8")
            print(f"Wrote {args.out}")
        else:
            print(payload)
        return 0

    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
