"""CLI entry point for BHT (BackhaulTicket): open, close, and roll up tickets into a board.

Console script: `bht` (see pyproject.toml [project.scripts]). Every invocation reads
config.local.json fresh, per foundation/config.py's docstring — no reliance on env vars or
persisted cwd.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from backhaul.foundation import body_log as _body_log
from backhaul.foundation import build_info as _build_info
from backhaul.foundation import config as _config
from backhaul.foundation import frontmatter as _frontmatter
from backhaul.foundation import projects as _projects

from . import board as _board
from . import create as _create
from . import registry as _registry
from .schema import STATES, TicketValidationError, validate

#: bht.md's own length standard (2026-08-11) -- not CLI-enforced until BH_018, a soft warning.
_TITLE_GUIDELINE = 40
_CONTEXT_GUIDELINE = 100

#: bht status's own write verb only sets the three non-terminal states -- "done" stays `close`'s
#: job specifically, so the two commands don't overlap in what they're each responsible for.
_STATUS_COMMAND_VALUES = tuple(s for s in STATES if s != "done")

# Backhaul/src/Backhaul/backhaul/services/ticket/cli.py -> parents[5] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[5]
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "config" / "config.local.json"
_PROJECTS_PATH = _REPO_ROOT / "config" / "projects.json"


def _resolve_config_path(args: argparse.Namespace) -> Path:
    """Resolve --project / --config / an upward cwd search / this checkout's own default.
    Shared implementation: foundation.config.resolve_config_path (see BH_019)."""
    return _config.resolve_config_path(
        args, default_config_path=_DEFAULT_CONFIG_PATH, projects_path=_PROJECTS_PATH
    )


def _load_config(config_path: str | Path) -> dict:
    """Load a config, applying BACKHAUL_LOCAL_ROOT from this process's own environment if set.

    The one place in this CLI that reads that env var (see BH_028) — `foundation.config
    .load_config()` itself deliberately doesn't anymore, so every other call to it (including
    every test's own synthetic config) is unaffected by whatever happens to be exported in the
    ambient shell. Real CLI invocations go through here instead."""
    return _config.load_config(config_path, local_root=os.environ.get(_config.LOCAL_ROOT_ENV_VAR))


def _tickets_root(cfg: dict) -> Path:
    return Path(cfg["content_roots"]["tickets"])


def _registry_path(tickets_root: Path) -> Path:
    return tickets_root / "client-uids.md"


def _board_path(tickets_root: Path) -> Path:
    # One directory up from the tickets themselves — keeps BOARD.md visible instead of
    # getting buried once a folder has 50+ ticket files in it.
    return tickets_root.parent / "BOARD.md"


def _dashboard_path(tickets_root: Path) -> Path:
    # tickets_root.parent is the "backhaul/" data folder; the dashboard sits one level above
    # that, at the project's true root — same convention backhaul/cli.py's own dashboard
    # command uses.
    return tickets_root.parent.parent / "BACKHAUL.md"


def _cmd_open(args: argparse.Namespace) -> int:
    cfg = _load_config(_resolve_config_path(args))
    tickets_root = _tickets_root(cfg)
    host_root = _config.get_host_root(cfg)
    path = _create.create_ticket(
        tickets_root=tickets_root,
        registry_path=_registry_path(tickets_root),
        client=args.client,
        title=args.title,
        uid=args.uid,
        slug=args.slug,
        context=args.context,
        priority=args.priority,
    )

    uid = _frontmatter.parse(path).frontmatter["uid"]
    folder = _registry.resolve_client_folder(cfg, uid, tickets_root, host_root=host_root)
    dashboard_path = _dashboard_path(tickets_root)
    project_name = _config.get_project_name(cfg)

    board_path = _board_path(tickets_root)
    _board.refresh_board_link(
        path, board_path, folder_path=folder,
        dashboard_path=dashboard_path, project_name=project_name,
    )
    _board.build_board(
        tickets_root, board_path,
        dashboard_path=dashboard_path, project_name=project_name, host_root=host_root,
    )

    if len(args.title) > _TITLE_GUIDELINE:
        print(
            f"warning: title is {len(args.title)} chars (guideline: ~{_TITLE_GUIDELINE}) -- "
            f"consider shortening or moving detail to the ticket body",
            file=sys.stderr,
        )
    if args.context and len(args.context) > _CONTEXT_GUIDELINE:
        print(
            f"warning: context is {len(args.context)} chars (guideline: ~{_CONTEXT_GUIDELINE}) "
            f"-- consider shortening or moving detail to the ticket body",
            file=sys.stderr,
        )

    print(f"OK: opened {path.name}")
    return 0


def _find_one_ticket(tickets_root: Path, ticket_id: str) -> Path | None:
    """Resolve an id-or-prefix to exactly one ticket path, printing a FAIL message and
    returning None on no-match/ambiguous-match -- the lookup `_cmd_close` already had inline,
    now shared with `_cmd_status`/`_cmd_log` too.

    Excludes BOARD.md and the client-uids.md registry by name (BH_024) -- both live inside
    tickets_root itself, so a generic enough id-or-prefix (e.g. a bare "c") could otherwise
    spuriously match the registry file, the same exclusion `_cmd_refresh`'s own sweep already
    applies via its `registry_name` check.
    """
    exempt = {"BOARD.md", _registry_path(tickets_root).name}
    matches = [p for p in tickets_root.glob(f"{ticket_id}*.md") if p.name not in exempt]
    if not matches:
        print(f"FAIL: no ticket matching '{ticket_id}' under {tickets_root}")
        return None
    if len(matches) > 1:
        print(f"FAIL: ambiguous id '{ticket_id}' matches: {[m.name for m in matches]}")
        return None
    return matches[0]


def _cmd_close(args: argparse.Namespace) -> int:
    cfg = _load_config(_resolve_config_path(args))
    tickets_root = _tickets_root(cfg)
    path = _find_one_ticket(tickets_root, args.id)
    if path is None:
        return 1

    doc = _frontmatter.parse(path)
    try:
        validate(doc.frontmatter)
    except TicketValidationError as e:
        print(f"FAIL: {path.name}: {e}")
        return 1

    doc.frontmatter["status"] = "done"
    doc.frontmatter["closed"] = date.today().isoformat()
    _frontmatter.write(doc)

    _board.build_board(
        tickets_root, _board_path(tickets_root),
        dashboard_path=_dashboard_path(tickets_root), project_name=_config.get_project_name(cfg),
        host_root=_config.get_host_root(cfg),
    )
    print(f"OK: closed {path.name}")
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    """Set a ticket's status to one of the three non-terminal lifecycle states. "done" stays
    `close`'s job — this exists so `in-progress`/`blocked` (which previously had no CLI path at
    all) stop requiring a hand-edit, the same way `close` already covers `done`. See BH_017
    (supersedes BH_010 — see that ticket's closing log for why validating `open`/`close` more
    strictly wouldn't have caught BKHL_006's six mistyped tickets, since none of them were ever
    touched by the CLI in the first place)."""
    cfg = _load_config(_resolve_config_path(args))
    tickets_root = _tickets_root(cfg)
    path = _find_one_ticket(tickets_root, args.id)
    if path is None:
        return 1

    doc = _frontmatter.parse(path)
    try:
        validate(doc.frontmatter)
    except TicketValidationError as e:
        print(f"FAIL: {path.name}: {e}")
        return 1

    doc.frontmatter["status"] = args.value
    if args.value != "done" and doc.frontmatter.get("closed"):
        # Reopening a previously-done ticket -- closed no longer describes anything real.
        doc.frontmatter["closed"] = None
    _frontmatter.write(doc)

    _board.build_board(
        tickets_root, _board_path(tickets_root),
        dashboard_path=_dashboard_path(tickets_root), project_name=_config.get_project_name(cfg),
        host_root=_config.get_host_root(cfg),
    )
    print(f"OK: set {path.name} to status {args.value!r}")
    return 0


def _cmd_log(args: argparse.Namespace) -> int:
    """Append a dated entry to a ticket's `## Log` section — see BH_016. Entry text comes from
    --entry, --entry-file (for multi-paragraph text, the common case per BKHL_011's own finding),
    or stdin, checked in that order."""
    cfg = _load_config(_resolve_config_path(args))
    tickets_root = _tickets_root(cfg)
    path = _find_one_ticket(tickets_root, args.id)
    if path is None:
        return 1

    if args.entry:
        entry_text = args.entry
    elif args.entry_file:
        entry_text = Path(args.entry_file).read_text(encoding="utf-8")
    else:
        entry_text = sys.stdin.read()
    entry_text = entry_text.strip()
    if not entry_text:
        print("FAIL: no entry text given (use --entry, --entry-file, or pipe text via stdin)")
        return 1

    doc = _frontmatter.parse(path)
    try:
        doc.body = _body_log.append_log_entry(doc.body, entry_text)
    except _body_log.BodyLogError as e:
        print(f"FAIL: {path.name}: {e}")
        return 1
    _frontmatter.write(doc)
    print(f"OK: appended log entry to {path.name}")
    return 0


def _cmd_board(args: argparse.Namespace) -> int:
    cfg = _load_config(_resolve_config_path(args))
    tickets_root = _tickets_root(cfg)
    out = Path(args.output) if args.output else _board_path(tickets_root)
    _board.build_board(
        tickets_root, out,
        dashboard_path=_dashboard_path(tickets_root), project_name=_config.get_project_name(cfg),
        host_root=_config.get_host_root(cfg),
    )
    print(f"OK: wrote board to {out}")
    return 0


def _cmd_refresh(args: argparse.Namespace) -> int:
    """Recompute every ticket's Board/Folder link block and rebuild the board.

    Useful whenever links were generated somewhere other than this machine (a different
    checkout path, or — as happened once — a dev sandbox) and need to be recomputed against
    this machine's real, resolved paths.
    """
    cfg = _load_config(_resolve_config_path(args))
    tickets_root = _tickets_root(cfg)
    host_root = _config.get_host_root(cfg)
    board_path = _board_path(tickets_root)
    dashboard_path = _dashboard_path(tickets_root)
    project_name = _config.get_project_name(cfg)
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
        folder = _registry.resolve_client_folder(cfg, uid, tickets_root, host_root=host_root)
        _board.refresh_board_link(
            ticket_path, board_path, folder_path=folder,
            dashboard_path=dashboard_path, project_name=project_name,
        )
        count += 1

    _board.build_board(
        tickets_root, board_path,
        dashboard_path=dashboard_path, project_name=project_name, host_root=host_root,
    )
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
    p.add_argument(
        "--version", action="version", version=_build_info.format_version_string("bht"),
        help="Print package version (plus branch/commit when running from a git checkout) and exit.",
    )
    location = p.add_mutually_exclusive_group()
    location.add_argument("--project", default=None, help="Named project from config/projects.json (see `bht projects`).")
    location.add_argument("--config", default=None, help="Explicit path to a config.local.json. Defaults to this checkout's own config if neither --project nor --config is given.")
    sub = p.add_subparsers(dest="command", required=True)

    p_open = sub.add_parser("open", help="Open a new ticket.")
    p_open.add_argument("--client", required=True)
    p_open.add_argument("--title", required=True)
    p_open.add_argument("--uid", default=None, help="Client UID. Auto-resolved/minted from --client if omitted.")
    p_open.add_argument("--slug", default=None, help="Short filename code (e.g. \"alma\"). Defaults to a slugified --title.")
    p_open.add_argument("--context", default=None)
    p_open.add_argument("--priority", default="normal")
    p_open.set_defaults(func=_cmd_open)

    p_status = sub.add_parser(
        "status",
        help="Set a ticket's status to open/in-progress/blocked. Use `close` for done.",
    )
    p_status.add_argument("id")
    p_status.add_argument("value", choices=list(_STATUS_COMMAND_VALUES))
    p_status.set_defaults(func=_cmd_status)

    p_log = sub.add_parser("log", help="Append a dated entry to a ticket's Log section.")
    p_log.add_argument("id")
    p_log.add_argument("--entry", default=None, help="Entry text. Reads --entry-file or stdin if omitted.")
    p_log.add_argument("--entry-file", default=None, help="Read entry text from this file instead of --entry.")
    p_log.set_defaults(func=_cmd_log)

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
    try:
        return args.func(args)
    except (_config.ConfigError, _projects.ProjectsError) as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
