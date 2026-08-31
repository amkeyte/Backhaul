"""Top-level `backhaul` CLI: cross-service commands that span BHT + BHW.

Per-service commands stay on their own CLIs — `bht` for tickets, `bhw` for wiki. This one is
for things that don't belong to either alone: currently just `dashboard` (rebuild BACKHAUL.md)
and `projects` (list what's registered in config/projects.json).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backhaul.foundation import build_info as _build_info
from backhaul.foundation import config as _config
from backhaul.foundation import lint as _lint
from backhaul.foundation import projects as _projects
from backhaul.modules.roadmap import graph as _roadmap_graph
from backhaul.modules.roles import index as _roles_index
from backhaul.services.ticket import board as _ticket_board
from backhaul.services.wiki import index as _wiki_index

from . import dashboard as _dashboard

# Backhaul/src/Backhaul/backhaul/cli.py -> parents[3] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "config" / "config.local.json"
_PROJECTS_PATH = _REPO_ROOT / "config" / "projects.json"


def _resolve_config_path(args: argparse.Namespace) -> Path:
    """Resolve --project / --config / an upward cwd search / this checkout's own default.
    Shared implementation: foundation.config.resolve_config_path (see BH_019)."""
    return _config.resolve_config_path(
        args, default_config_path=_DEFAULT_CONFIG_PATH, projects_path=_PROJECTS_PATH
    )


def _cmd_dashboard(args: argparse.Namespace) -> int:
    cfg = _config.load_config(_resolve_config_path(args))
    tickets_root = Path(cfg["content_roots"]["tickets"])
    wiki_root = Path(cfg["content_roots"]["wiki"])

    # Same convention bht/bhw use for BOARD.md/WIKI_INDEX.md: one directory up from the
    # tickets/pages themselves.
    board_path = tickets_root.parent / "BOARD.md"
    index_path = wiki_root.parent / "WIKI_INDEX.md"

    if args.output:
        output_path = Path(args.output)
    else:
        # tickets_root.parent and wiki_root.parent are expected to be the same "backhaul/"
        # data folder (both content roots configured as siblings under it); the dashboard
        # sits one level further up, at that folder's parent — the project's true root.
        output_path = tickets_root.parent.parent / "BACKHAUL.md"

    # Roadmap and Roles are both optional — only wire either into the dashboard when this
    # project has both configured a content root for it *and* enabled the module. A project
    # that's never touched bhrm/bhrole shouldn't get a dead "0 graphs"/"0 roles" link on its
    # front page.
    enabled_modules = _config.get_enabled_modules(cfg)
    content_roots = cfg.get("content_roots", {})

    roadmap_root = None
    roadmap_index_path = None
    if "roadmap" in content_roots and "roadmap" in enabled_modules:
        roadmap_root = Path(content_roots["roadmap"])
        roadmap_index_path = roadmap_root.parent / "ROADMAP_INDEX.md"

    roles_root = None
    roles_index_path = None
    if "roles" in content_roots and "roles" in enabled_modules:
        roles_root = Path(content_roots["roles"])
        roles_index_path = roles_root.parent / "ROLES_INDEX.md"

    _dashboard.build_dashboard(
        tickets_root=tickets_root,
        wiki_root=wiki_root,
        board_path=board_path,
        index_path=index_path,
        output_path=output_path,
        roadmap_root=roadmap_root,
        roadmap_index_path=roadmap_index_path,
        roles_root=roles_root,
        roles_index_path=roles_index_path,
        project_name=_config.get_project_name(cfg),
        build_ready=_config.get_build_ready(cfg),
    )
    print(f"OK: wrote dashboard to {output_path}")
    return 0


def _cmd_refresh(args: argparse.Namespace) -> int:
    """One-command project refresh (BH_014): rebuild every enabled service's index, run lint
    advisory-only, then rebuild the dashboard — same end state as running each service's own
    `refresh`/`index` command by hand, in the right order, without having to know which
    commands exist or which modules are enabled.

    Mirrors `_cmd_dashboard`'s own content-root/enabled-module resolution so a project with
    `enabled_modules: []` for roadmap/roles just skips those steps cleanly rather than erroring.
    Lint findings are printed but never fail this command — lint is diagnostic, not a gate.
    """
    cfg = _config.load_config(_resolve_config_path(args))
    tickets_root = Path(cfg["content_roots"]["tickets"])
    wiki_root = Path(cfg["content_roots"]["wiki"])
    host_root = _config.get_host_root(cfg)
    project_name = _config.get_project_name(cfg)

    board_path = tickets_root.parent / "BOARD.md"
    index_path = wiki_root.parent / "WIKI_INDEX.md"
    output_path = tickets_root.parent.parent / "BACKHAUL.md"

    _ticket_board.build_board(
        tickets_root, board_path,
        dashboard_path=output_path, project_name=project_name, host_root=host_root,
    )
    _wiki_index.build_index(
        wiki_root, index_path,
        dashboard_path=output_path, project_name=project_name, host_root=host_root,
    )

    enabled_modules = _config.get_enabled_modules(cfg)
    content_roots = cfg.get("content_roots", {})

    roadmap_root = None
    roadmap_index_path = None
    if "roadmap" in content_roots and "roadmap" in enabled_modules:
        roadmap_root = Path(content_roots["roadmap"])
        roadmap_index_path = roadmap_root.parent / "ROADMAP_INDEX.md"
        try:
            _roadmap_graph.build_index(
                roadmap_root, roadmap_index_path,
                dashboard_path=output_path, project_name=project_name,
            )
        except _roadmap_graph.GraphError as e:
            print(f"FAIL: roadmap index: {e}", file=sys.stderr)
            return 2

    roles_root = None
    roles_index_path = None
    if "roles" in content_roots and "roles" in enabled_modules:
        roles_root = Path(content_roots["roles"])
        roles_index_path = roles_root.parent / "ROLES_INDEX.md"
        roles_project_root = host_root if host_root is not None else roles_root.parent.parent
        _roles_index.build_index(
            roles_root, roles_index_path,
            dashboard_path=output_path, project_name=project_name,
            project_root=roles_project_root, repo_url=_config.get_repo_url(cfg),
            host_root=host_root,
        )

    try:
        findings = _lint.run_lint(cfg)
    except _lint.LintError as e:
        print(f"warning: lint could not run: {e}", file=sys.stderr)
        findings = []
    if findings:
        print(f"lint: {len(findings)} finding(s) (advisory, not blocking refresh):")
        for f in findings:
            print(f"  {f}")
    else:
        print("lint: OK, no findings.")

    _dashboard.build_dashboard(
        tickets_root=tickets_root,
        wiki_root=wiki_root,
        board_path=board_path,
        index_path=index_path,
        output_path=output_path,
        roadmap_root=roadmap_root,
        roadmap_index_path=roadmap_index_path,
        roles_root=roles_root,
        roles_index_path=roles_index_path,
        project_name=project_name,
        build_ready=_config.get_build_ready(cfg),
    )
    print(f"OK: refreshed board, wiki index, roadmap/roles (if enabled), lint, and dashboard at {output_path}")
    return 0


def _cmd_lint(args: argparse.Namespace) -> int:
    cfg = _config.load_config(_resolve_config_path(args))
    checks = [c.strip() for c in args.check.split(",") if c.strip()] if args.check else None

    try:
        findings = _lint.run_lint(cfg, checks=checks)
    except _lint.LintError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps([f.to_dict() for f in findings], indent=2))
    else:
        if not findings:
            print("OK: no findings.")
        else:
            for f in findings:
                print(str(f))

    return 1 if findings else 0


def _cmd_projects(args: argparse.Namespace) -> int:
    known = _projects.load_projects(_PROJECTS_PATH)
    if not known:
        print(f"No projects registered in {_PROJECTS_PATH}.")
        return 0
    for name, path in sorted(known.items()):
        print(f"{name}: {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="backhaul", description="Backhaul — cross-service commands.")
    p.add_argument(
        "--version", action="version", version=_build_info.format_version_string("backhaul"),
        help="Print package version (plus branch/commit when running from a git checkout) and exit.",
    )
    location = p.add_mutually_exclusive_group()
    location.add_argument("--project", default=None, help="Named project from config/projects.json.")
    location.add_argument("--config", default=None, help="Explicit path to a config.local.json.")
    sub = p.add_subparsers(dest="command", required=True)

    p_dash = sub.add_parser("dashboard", help="Rebuild BACKHAUL.md (links to the board + wiki index).")
    p_dash.add_argument("--output", default=None, help="Defaults to the backhaul data folder's parent / BACKHAUL.md.")
    p_dash.set_defaults(func=_cmd_dashboard)

    p_refresh = sub.add_parser(
        "refresh",
        help="Rebuild board, wiki index, roadmap/roles indexes (if enabled), run lint (advisory), rebuild the dashboard.",
    )
    p_refresh.set_defaults(func=_cmd_refresh)

    p_lint = sub.add_parser("lint", help="Audit content for orphaned pages and broken links.")
    p_lint.add_argument(
        "--check", default=None,
        help=f"Comma-separated check names to run (default: all). Known: {', '.join(_lint.CHECKS)}.",
    )
    p_lint.add_argument("--format", default="text", choices=["text", "json"], help="Output format.")
    p_lint.set_defaults(func=_cmd_lint)

    p_proj = sub.add_parser("projects", help="List registered projects (config/projects.json).")
    p_proj.set_defaults(func=_cmd_projects)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except (_config.ConfigError, _projects.ProjectsError) as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
