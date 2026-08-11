"""Top-level `backhaul` CLI: cross-service commands that span BHT + BHW.

Per-service commands stay on their own CLIs — `bht` for tickets, `bhw` for wiki. This one is
for things that don't belong to either alone: currently just `dashboard` (rebuild BACKHAUL.md)
and `projects` (list what's registered in config/projects.json).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backhaul.foundation import config as _config
from backhaul.foundation import projects as _projects

from . import dashboard as _dashboard

# Backhaul/src/Backhaul/backhaul/cli.py -> parents[3] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "config" / "config.local.json"
_PROJECTS_PATH = _REPO_ROOT / "config" / "projects.json"


def _resolve_config_path(args: argparse.Namespace) -> Path:
    """Same resolution rule as bht/bhw: --project (name from config/projects.json), or
    --config (raw path), or fall back to this checkout's own config."""
    if args.project:
        return _projects.resolve_project_config(_PROJECTS_PATH, args.project)
    if args.config:
        return Path(args.config)
    return _DEFAULT_CONFIG_PATH


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
    )
    print(f"OK: wrote dashboard to {output_path}")
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
    p = argparse.ArgumentParser(prog="backhaul", description="Backhaul — cross-service commands.")
    location = p.add_mutually_exclusive_group()
    location.add_argument("--project", default=None, help="Named project from config/projects.json.")
    location.add_argument("--config", default=None, help="Explicit path to a config.local.json.")
    sub = p.add_subparsers(dest="command", required=True)

    p_dash = sub.add_parser("dashboard", help="Rebuild BACKHAUL.md (links to the board + wiki index).")
    p_dash.add_argument("--output", default=None, help="Defaults to the backhaul data folder's parent / BACKHAUL.md.")
    p_dash.set_defaults(func=_cmd_dashboard)

    p_proj = sub.add_parser("projects", help="List registered projects (config/projects.json).")
    p_proj.set_defaults(func=_cmd_projects)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
