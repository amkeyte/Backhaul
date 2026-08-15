"""CLI entry point for BHRM (BackhaulRoadmap): mint nodes and query the dependency graph.

Console script: `bhrm` (see pyproject.toml [project.scripts]). Every invocation reads
config.local.json fresh, per foundation/config.py's docstring. Mirrors services/ticket/cli.py
and services/wiki/cli.py's structure — but unlike those two (always-on baseline services),
this is an optional module: every subcommand except `projects` checks config.enabled_modules
and refuses to run with a clear message if "roadmap" isn't listed, rather than silently working
regardless of what the machine's config says is installed here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from backhaul.foundation import config as _config
from backhaul.foundation import frontmatter as _frontmatter
from backhaul.foundation import projects as _projects

from . import create as _create
from . import graph as _graph
from . import header as _header

# Backhaul/src/Backhaul/backhaul/modules/roadmap/cli.py -> parents[5] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[5]
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "config" / "config.local.json"
_PROJECTS_PATH = _REPO_ROOT / "config" / "projects.json"

_MODULE_ID = "roadmap"
_UID_FROM_ID_RE = re.compile(r"^(.+)_\d+$")


class RoadmapCliError(Exception):
    """Raised for a clean, expected CLI failure (module not enabled, unknown node, etc.) —
    caught in main() and printed without a traceback."""


def _resolve_config_path(args: argparse.Namespace) -> Path:
    """Resolve --project (a name from config/projects.json) or --config (a raw path) to a
    config.local.json path. Neither given falls back to this checkout's own config."""
    if args.project:
        return _projects.resolve_project_config(_PROJECTS_PATH, args.project)
    if args.config:
        return Path(args.config)
    return _DEFAULT_CONFIG_PATH


def _load_enabled_config(args: argparse.Namespace) -> dict:
    """Load config and refuse to proceed if the roadmap module isn't enabled here — the actual
    enforcement of enabled_modules this module was built to demonstrate (previously purely
    decorative — see foundation/config.py's get_enabled_modules docstring)."""
    cfg = _config.load_config(_resolve_config_path(args))
    if _MODULE_ID not in _config.get_enabled_modules(cfg):
        raise RoadmapCliError(
            f"module {_MODULE_ID!r} is not enabled in this config's enabled_modules — "
            f"add \"roadmap\" to enabled_modules in the resolved config.local.json to use bhrm here."
        )
    return cfg


def _nodes_root(cfg: dict) -> Path:
    if "roadmap" not in cfg.get("content_roots", {}):
        raise RoadmapCliError(
            "this config has no content_roots.roadmap — add one (a folder for this "
            "project's roadmap node files) before using bhrm."
        )
    return Path(cfg["content_roots"]["roadmap"])


def _registry_path(cfg: dict) -> Path:
    # Shared with BHT: the same client-uids.md means "ARR" is the same client whether it's a
    # ticket or a roadmap node. BHT is always enabled, so content_roots.tickets always exists.
    return Path(cfg["content_roots"]["tickets"]) / "client-uids.md"


def _uid_from_id(node_id: str) -> str:
    match = _UID_FROM_ID_RE.match(node_id)
    if not match:
        raise RoadmapCliError(f"{node_id!r} doesn't look like a node ID (expected UID_NNN)")
    return match.group(1)


def _load_graph_for_uid(cfg: dict, uid: str) -> dict[str, _graph.Node]:
    nodes_root = _nodes_root(cfg)
    try:
        nodes = _graph.load_graph(nodes_root, uid)
        _graph.validate_graph(nodes)
    except _graph.GraphError as e:
        raise RoadmapCliError(str(e)) from e
    return nodes


def _index_path(nodes_root: Path) -> Path:
    # One directory up from the node files themselves — same convention BOARD.md/
    # WIKI_INDEX.md already use, keeps it visible instead of getting buried in the glob.
    return nodes_root.parent / "ROADMAP_INDEX.md"


def _dashboard_path(nodes_root: Path) -> Path:
    # nodes_root.parent is the "backhaul/" data folder; the dashboard sits one level above
    # that, at the project's true root — mirrors services/ticket/cli.py's _dashboard_path.
    return nodes_root.parent.parent / "BACKHAUL.md"


def _cmd_new(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    nodes_root = _nodes_root(cfg)
    depends_on = [d.strip() for d in args.depends_on.split(",") if d.strip()] if args.depends_on else []

    path = _create.create_node(
        nodes_root=nodes_root,
        registry_path=_registry_path(cfg),
        client=args.client,
        title=args.title,
        owner=args.owner,
        kind=args.kind,
        depends_on=depends_on,
        base_uid=args.base_uid,
        slug=args.slug,
        status=args.status,
    )
    _header.refresh_header(
        path, _index_path(nodes_root),
        dashboard_path=_dashboard_path(nodes_root), project_name=_config.get_project_name(cfg),
    )
    print(f"OK: created {path.name}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    nodes = _load_graph_for_uid(cfg, args.uid)
    print(f"OK — {len(nodes)} node(s) for {args.uid}, no cycles.")
    return 0


def _cmd_frontier(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    nodes = _load_graph_for_uid(cfg, args.uid)
    for nid in _graph.frontier(nodes):
        print(f"{nid}\t{nodes[nid].title}")
    return 0


def _cmd_dependents(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    uid = _uid_from_id(args.id)
    nodes = _load_graph_for_uid(cfg, uid)
    if args.id not in nodes:
        raise RoadmapCliError(f"unknown node {args.id}")
    for nid in _graph.dependents(nodes, args.id):
        print(nid)
    return 0


def _cmd_downstream(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    uid = _uid_from_id(args.id)
    nodes = _load_graph_for_uid(cfg, uid)
    if args.id not in nodes:
        raise RoadmapCliError(f"unknown node {args.id}")
    for nid in _graph.downstream(nodes, args.id):
        print(nid)
    return 0


def _cmd_blocking(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    uid = _uid_from_id(args.id)
    nodes = _load_graph_for_uid(cfg, uid)
    if args.id not in nodes:
        raise RoadmapCliError(f"unknown node {args.id}")
    for nid in _graph.blocking(nodes, args.id):
        print(nid)
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    nodes = _load_graph_for_uid(cfg, args.uid)
    # Links need to know where the doc will actually live — default to the same convention
    # ROADMAP_INDEX.md uses (one level above the node files) even for a stdout dump, since
    # that's where a render's output conventionally ends up saved.
    output_dir = Path(args.output).parent if args.output else _nodes_root(cfg).parent
    kwargs = {"title": args.title} if args.title else {}
    text = _graph.render(nodes, output_dir=output_dir, **kwargs)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"OK: wrote render to {args.output}")
    else:
        print(text, end="")
    return 0


def _cmd_render_html(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    nodes = _load_graph_for_uid(cfg, args.uid)
    kwargs = {"title": args.title} if args.title else {}
    text = _graph.render_html(nodes, **kwargs)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"OK: wrote render-html to {args.output}")
    else:
        print(text, end="")
    return 0


def _cmd_export_json(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    nodes = _load_graph_for_uid(cfg, args.uid)
    payload = json.dumps(_graph.export_json(nodes), indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(f"OK: wrote {args.out}")
    else:
        print(payload)
    return 0


def _cmd_refresh(args: argparse.Namespace) -> int:
    """Recompute every node's header and rebuild the combined index.

    Same purpose as `bht refresh` / `bhw refresh`: fixes links generated somewhere other than
    this machine (a different checkout path, or a dev sandbox) by recomputing them against this
    machine's real, resolved paths. Sweeps every UID's node files under content_roots.roadmap,
    not just one graph.
    """
    cfg = _load_enabled_config(args)
    nodes_root = _nodes_root(cfg)
    index_path = _index_path(nodes_root)
    dashboard_path = _dashboard_path(nodes_root)
    project_name = _config.get_project_name(cfg)

    count = 0
    for node_path in sorted(nodes_root.glob("*.md")):
        try:
            doc = _frontmatter.parse(node_path)
        except _frontmatter.FrontmatterError:
            continue
        if "uid" not in doc.frontmatter:
            continue
        _header.refresh_header(
            node_path, index_path,
            dashboard_path=dashboard_path, project_name=project_name,
        )
        count += 1

    try:
        _graph.build_index(nodes_root, index_path, dashboard_path=dashboard_path, project_name=project_name)
    except _graph.GraphError as e:
        raise RoadmapCliError(str(e)) from e
    print(f"OK: refreshed {count} node(s), rebuilt the index at {index_path}")
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    nodes_root = _nodes_root(cfg)
    out = Path(args.output) if args.output else _index_path(nodes_root)
    kwargs = {
        "dashboard_path": _dashboard_path(nodes_root),
        "project_name": _config.get_project_name(cfg),
    }
    if args.title:
        kwargs["title"] = args.title
    try:
        _graph.build_index(nodes_root, out, **kwargs)
    except _graph.GraphError as e:
        raise RoadmapCliError(str(e)) from e
    print(f"OK: wrote index to {out}")
    return 0


def _cmd_projects(args: argparse.Namespace) -> int:
    known = _projects.load_projects(_PROJECTS_PATH)
    if not known:
        print(f"No projects registered in {_PROJECTS_PATH}.")
        return 0
    for name, path in sorted(known.items()):
        print(f"{name}: {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bhrm", description="BackhaulRoadmap — dependency-graph roadmap CLI.")
    location = p.add_mutually_exclusive_group()
    location.add_argument("--project", default=None, help="Named project from config/projects.json (see `bhrm projects`).")
    location.add_argument("--config", default=None, help="Explicit path to a config.local.json. Defaults to this checkout's own config if neither --project nor --config is given.")
    sub = p.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Create a new roadmap node.")
    p_new.add_argument("--client", required=True, help="Client display name — shares BHT's client-uids.md registry.")
    p_new.add_argument("--title", required=True)
    p_new.add_argument("--owner", required=True)
    p_new.add_argument("--kind", default="work", choices=["work", "convergence"])
    p_new.add_argument("--depends-on", default=None, help="Comma-separated node IDs, e.g. RM_ARR_001,RM_ARR_002.")
    p_new.add_argument("--base-uid", default=None, help="Override the auto-resolved/minted client UID.")
    p_new.add_argument("--slug", default=None, help="Short filename code (e.g. \"alma\") instead of a slugified --title — recommended for roadmap nodes so DependsOn edges stay easy to type/read.")
    p_new.add_argument("--status", default=None, help="Defaults to 'open' (work) / 'WIP' (convergence).")
    p_new.set_defaults(func=_cmd_new)

    p_validate = sub.add_parser("validate", help="Check one UID's graph for cycles.")
    p_validate.add_argument("--uid", required=True, help='e.g. "RM_ARR".')
    p_validate.set_defaults(func=_cmd_validate)

    p_frontier = sub.add_parser("frontier", help="List every currently-actionable node for one UID.")
    p_frontier.add_argument("--uid", required=True)
    p_frontier.set_defaults(func=_cmd_frontier)

    p_dependents = sub.add_parser("dependents", help="Direct (one-hop) reverse dependents of a node ID.")
    p_dependents.add_argument("id")
    p_dependents.set_defaults(func=_cmd_dependents)

    p_downstream = sub.add_parser("downstream", help="Full transitive closure of dependents of a node ID.")
    p_downstream.add_argument("id")
    p_downstream.set_defaults(func=_cmd_downstream)

    p_blocking = sub.add_parser("blocking", help="Unresolved ancestors of a node ID, transitively.")
    p_blocking.add_argument("id")
    p_blocking.set_defaults(func=_cmd_blocking)

    p_render = sub.add_parser("render", help="Generate the crawlable markdown index for one UID.")
    p_render.add_argument("--uid", required=True)
    p_render.add_argument("--output", default=None, help="Write to this path instead of stdout.")
    p_render.add_argument("--title", default=None, help='Override the top heading. Defaults to "# Roadmap Graph — generated index".')
    p_render.set_defaults(func=_cmd_render)

    p_render_html = sub.add_parser("render-html", help="Generate a standalone HTML/SVG graph view for one UID.")
    p_render_html.add_argument("--uid", required=True)
    p_render_html.add_argument("--output", default=None, help="Write to this path instead of stdout.")
    p_render_html.add_argument("--title", default=None, help='Override the page title. Defaults to "Roadmap Graph".')
    p_render_html.set_defaults(func=_cmd_render_html)

    p_export = sub.add_parser("export-json", help="Export one UID's graph as structured JSON.")
    p_export.add_argument("--uid", required=True)
    p_export.add_argument("--out", default=None, help="Write JSON to this file instead of stdout.")
    p_export.set_defaults(func=_cmd_export_json)

    p_index = sub.add_parser("index", help="Rebuild the combined roadmap index — every UID's graph, its own section.")
    p_index.add_argument("--output", default=None, help="Defaults to <nodes_root's parent>/ROADMAP_INDEX.md.")
    p_index.add_argument("--title", default=None, help='Override the top heading. Defaults to "# Roadmap Graphs".')
    p_index.set_defaults(func=_cmd_index)

    p_refresh = sub.add_parser(
        "refresh",
        help="Recompute every node's header and rebuild the index against this machine's real paths.",
    )
    p_refresh.set_defaults(func=_cmd_refresh)

    p_projects = sub.add_parser("projects", help="List registered projects (config/projects.json).")
    p_projects.set_defaults(func=_cmd_projects)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except RoadmapCliError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
