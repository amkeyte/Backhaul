"""CLI entry point for BHT (BackhaulTicket): open, close, and roll up tickets into a board.

Console script: `bht` (see pyproject.toml [project.scripts]). Every invocation reads
config.local.json fresh, per foundation/config.py's docstring — no reliance on env vars or
persisted cwd.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from backhaul.foundation import config as _config
from backhaul.foundation import frontmatter as _frontmatter
from backhaul.foundation import projects as _projects

from . import board as _board
from . import create as _create
from . import registry as _registry
from .schema import TicketValidationError, validate

# Backhaul/src/Backhaul/backhaul/services/ticket/cli.py -> parents[5] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[5]
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "config" / "config.local.json"
_PROJECTS_PATH = _REPO_ROOT / "config" / "projects.json"


def _resolve_config_path(args: argparse.Namespace) -> Path:
    """Resolve --project (a name from config/projects.json) or --config (a raw path) to a
    config.local.json path. Neither given falls back to this checkout's own config — today's
    default behavior, unchanged."""
    if args.project:
        return _projects.resolve_project_config(_PROJECTS_PATH, args.project)
    if args.config:
        return Path(args.config)
    return _DEFAULT_CONFIG_PATH


def _tickets_root(cfg: dict) -> Path:
    return Path(cfg["content_roots"]["tickets"])


def _registry_path(tickets_root: Path) -> Path:
    return tickets_root / "client-uids.md"


def _board_path(tickets_root: Path) -> Path:
    # One directory up from the tickets themselves — keeps BOARD.md visible instead of
    # getting buried once a folder has 50+ ticket files in it.
    return tickets_root.parent / "BOARD.md"


def _cmd_open(args: argparse.Namespace) -> int:
    cfg = _config.load_config(_resolve_config_path(args))
    tickets_root = _tickets_root(cfg)
    path = _create.create_ticket(
        tickets_root=tickets_root,
        registry_path=_registry_path(tickets_root),
        client=args.client,
        title=args.title,
        uid=args.uid,
        context=args.context,
        priority=args.priority,
    )

    uid = _frontmatter.parse(path).frontmatter["uid"]
    folder = _registry.resolve_client_folder(cfg, uid, tickets_root)

    board_path = _board_path(tickets_root)
    _board.refresh_board_link(path, board_path, folder_path=folder)
    _board.build_board(tickets_root, board_path)
    print(f"OK: opened {path.name}")
    return 0


def _cmd_close(args: argparse.Namespace) -> int:
    tickets_root = _tickets_root(_config.load_config(_resolve_config_path(args)))
    matches = [p for p in tickets_root.glob(f"{args.id}*.md") if p.name != "BOARD.md"]
    if not matches:
        print(f"FAIL: no ticket matching '{args.id}' under {tickets_root}")
        return 1
    if len(matches) > 1:
        print(f"FAIL: ambiguous id '{args.id}' matches: {[m.name for m in matches]}")
        return 1

    path = matches[0]
    doc = _frontmatter.parse(path)
    try:
        validate(doc.frontmatter)
    except TicketValidationError as e:
        print(f"FAIL: {path.name}: {e}")
        return 1

    doc.frontmatter["status"] = "done"
    doc.frontmatter["closed"] = date.today().isoformat()
    _frontmatter.write(doc)

    _board.build_board(tickets_root, _board_path(tickets_root))
    print(f"OK: closed {path.name}")
    return 0


def _cmd_board(args: argparse.Namespace) -> int:
    tickets_root = _tickets_root(_config.load_config(_resolve_config_path(args)))
    out = Path(args.output) if args.output else _board_path(tickets_root)
    _board.build_board(tickets_root, out)
    print(f"OK: wrote board to {out}")
    return 0


def _cmd_refresh(args: argparse.Namespace) -> int:
    """Recompute every ticket's Board/Folder link block and rebuild the board.

    Useful whenever links were generated somewhere other than this machine (a different
    checkout path, or — as happened once — a dev sandbox) and need to be recomputed against
    this machine's real, resolved paths.
    """
    cfg = _config.load_config(_resolve_config_path(args))
    tickets_root = _tickets_root(cfg)
    board_path = _board_path(tickets_root)
    registry_name = _registry_path(tickets_root).name

    count = 0
    for ticket_path in sorted(tickets_root.glob("*.md")):
        if ticket_path.name == registry_name:
            continue
        try:
            doc = _frontmatter.parse(ticket_path)
        except _frontmatter.FrontmatterError:
            continue
        uid = doc.frontmatter.get("uid")
        if not uid:
            continue
        folder = _registry.resolve_client_folder(cfg, uid, tickets_root)
        _board.refresh_board_link(ticket_path, board_path, folder_path=folder)
        count += 1

    _board.build_board(tickets_root, board_path)
    print(f"OK: refreshed {count} ticket(s), rebuilt the board at {board_path}")
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
    p = argparse.ArgumentParser(prog="bht", description="BackhaulTicket — passdown ticket CLI.")
    location = p.add_mutually_exclusive_group()
    location.add_argument("--project", default=None, help="Named project from config/projects.json (see `bht projects`).")
    location.add_argument("--config", default=None, help="Explicit path to a config.local.json. Defaults to this checkout's own config if neither --project nor --config is given.")
    sub = p.add_subparsers(dest="command", required=True)

    p_open = sub.add_parser("open", help="Open a new ticket.")
    p_open.add_argument("--client", required=True)
    p_open.add_argument("--title", required=True)
    p_open.add_argument("--uid", default=None, help="Client UID. Auto-resolved/minted from --client if omitted.")
    p_open.add_argument("--context", default=None)
    p_open.add_argument("--priority", default="normal")
    p_open.set_defaults(func=_cmd_open)

    p_close = sub.add_parser("close", help="Close an existing ticket by ID (or ID prefix).")
    p_close.add_argument("id")
    p_close.set_defaults(func=_cmd_close)

    p_board = sub.add_parser("board", help="Rebuild the work board.")
    p_board.add_argument("--output", default=None, help="Defaults to <tickets_root's parent>/BOARD.md.")
    p_board.set_defaults(func=_cmd_board)

    p_refresh = sub.add_parser(
        "refresh",
        help="Recompute every ticket's Board/Folder link and rebuild the board against this machine's real paths.",
    )
    p_refresh.set_defaults(func=_cmd_refresh)

    p_projects = sub.add_parser("projects", help="List registered projects (config/projects.json).")
    p_projects.set_defaults(func=_cmd_projects)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
