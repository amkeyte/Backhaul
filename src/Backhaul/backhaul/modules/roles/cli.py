"""CLI entry point for BHRole: mint role pages and rebuild the roster.

Console script: `bhrole` (see pyproject.toml [project.scripts]). Every invocation reads
config.local.json fresh, per foundation/config.py's docstring. Mirrors modules/roadmap/cli.py's
structure — an optional module: every subcommand except `projects` checks
config.enabled_modules and refuses to run with a clear message if "roles" isn't listed.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from backhaul.foundation import build_info as _build_info
from backhaul.foundation import config as _config
from backhaul.foundation import frontmatter as _frontmatter
from backhaul.foundation import projects as _projects

from . import create as _create
from . import header as _header
from . import index as _index

# Backhaul/src/Backhaul/backhaul/modules/roles/cli.py -> parents[5] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[5]
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "config" / "config.local.json"
_PROJECTS_PATH = _REPO_ROOT / "config" / "projects.json"

_MODULE_ID = "roles"


class RolesCliError(Exception):
    """Raised for a clean, expected CLI failure (module not enabled, etc.) — caught in
    main() and printed without a traceback."""


def _resolve_config_path(args: argparse.Namespace) -> Path:
    """Resolve --project / --config / an upward cwd search / this checkout's own default.
    Shared implementation: foundation.config.resolve_config_path (see BH_019)."""
    return _config.resolve_config_path(
        args, default_config_path=_DEFAULT_CONFIG_PATH, projects_path=_PROJECTS_PATH
    )


def _load_enabled_config(args: argparse.Namespace) -> dict:
    """Load config and refuse to proceed if the roles module isn't enabled here — same
    enforcement pattern modules/roadmap/cli.py established.

    Applies BACKHAUL_LOCAL_ROOT from this process's own environment if set — the one place in
    this CLI that reads that env var (see BH_028). `foundation.config.load_config()` itself
    deliberately doesn't anymore, so a bare call to it (e.g. every test's own synthetic config)
    is unaffected by whatever happens to be exported in the ambient shell; only this real CLI
    entry point is."""
    cfg = _config.load_config(
        _resolve_config_path(args), local_root=os.environ.get(_config.LOCAL_ROOT_ENV_VAR)
    )
    if _MODULE_ID not in _config.get_enabled_modules(cfg):
        raise RolesCliError(
            f"module {_MODULE_ID!r} is not enabled in this config's enabled_modules — "
            f"add \"roles\" to enabled_modules in the resolved config.local.json to use bhrole here."
        )
    return cfg


def _roles_root(cfg: dict) -> Path:
    if "roles" not in cfg.get("content_roots", {}):
        raise RolesCliError(
            "this config has no content_roots.roles — add one (a folder for this "
            "project's role pages) before using bhrole."
        )
    return Path(cfg["content_roots"]["roles"])


def _index_path(roles_root: Path) -> Path:
    # One directory up from the role files themselves — same convention BOARD.md/
    # WIKI_INDEX.md/ROADMAP_INDEX.md already use.
    return roles_root.parent / "ROLES_INDEX.md"


def _dashboard_path(roles_root: Path) -> Path:
    # roles_root.parent is the "backhaul/" data folder; the dashboard sits one level above
    # that, at the project's true root — mirrors modules/roadmap/cli.py's _dashboard_path.
    return roles_root.parent.parent / "BACKHAUL.md"


def _project_root(roles_root: Path, host_root: str | None) -> str | Path:
    # Same folder _dashboard_path resolves BACKHAUL.md's parent to — the project's true root,
    # which is what a role's Launch link names as the folder it needs (see modules/roles/
    # launch.py). When host_root is configured, that IS the real path to tell a human about —
    # use it directly rather than the runtime-resolved path (which may be a sandbox mount).
    return host_root if host_root is not None else roles_root.parent.parent


def _cmd_new(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    roles_root = _roles_root(cfg)

    path = _create.create_role(
        roles_root=roles_root,
        title=args.title,
        slug=args.slug,
        persona=args.persona,
        purpose=args.purpose,
        authority=args.authority,
        reports_to=args.reports_to,
        status=args.status,
        launch_target=args.launch_target,
    )
    _header.refresh_header(
        path, _index_path(roles_root),
        dashboard_path=_dashboard_path(roles_root), project_name=_config.get_project_name(cfg),
    )
    host_root = _config.get_host_root(cfg)
    _index.build_index(
        roles_root, _index_path(roles_root),
        dashboard_path=_dashboard_path(roles_root), project_name=_config.get_project_name(cfg),
        project_root=_project_root(roles_root, host_root), repo_url=_config.get_repo_url(cfg),
        host_root=host_root,
    )
    print(f"OK: created {path.name}")
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    cfg = _load_enabled_config(args)
    roles_root = _roles_root(cfg)
    out = Path(args.output) if args.output else _index_path(roles_root)
    host_root = _config.get_host_root(cfg)
    kwargs = {
        "dashboard_path": _dashboard_path(roles_root),
        "project_name": _config.get_project_name(cfg),
        "project_root": _project_root(roles_root, host_root),
        "repo_url": _config.get_repo_url(cfg),
        "host_root": host_root,
    }
    if args.title:
        kwargs["title"] = args.title
    _index.build_index(roles_root, out, **kwargs)
    print(f"OK: wrote index to {out}")
    return 0


def _cmd_refresh(args: argparse.Namespace) -> int:
    """Recompute every role's header and rebuild the roster.

    Same purpose as `bht refresh` / `bhw refresh` / `bhrm refresh`: fixes links generated
    somewhere other than this machine (a different checkout path, or a dev sandbox) by
    recomputing them against this machine's real, resolved paths.
    """
    cfg = _load_enabled_config(args)
    roles_root = _roles_root(cfg)
    index_path = _index_path(roles_root)
    dashboard_path = _dashboard_path(roles_root)
    project_name = _config.get_project_name(cfg)

    count = 0
    for role_path in sorted(roles_root.glob("*.md")):
        try:
            doc = _frontmatter.parse(role_path)
        except _frontmatter.FrontmatterError:
            continue
        if "slug" not in doc.frontmatter:
            continue
        _header.refresh_header(
            role_path, index_path,
            dashboard_path=dashboard_path, project_name=project_name,
        )
        count += 1

    host_root = _config.get_host_root(cfg)
    _index.build_index(
        roles_root, index_path,
        dashboard_path=dashboard_path, project_name=project_name,
        project_root=_project_root(roles_root, host_root), repo_url=_config.get_repo_url(cfg),
        host_root=host_root,
    )
    print(f"OK: refreshed {count} role(s), rebuilt the roster at {index_path}")
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
    p = argparse.ArgumentParser(prog="bhrole", description="BackhaulRole — agent-role page CLI.")
    p.add_argument(
        "--version", action="version", version=_build_info.format_version_string("bhrole"),
        help="Print package version (plus branch/commit when running from a git checkout) and exit.",
    )
    location = p.add_mutually_exclusive_group()
    location.add_argument("--project", default=None, help="Named project from config/projects.json (see `bhrole projects`).")
    location.add_argument("--config", default=None, help="Explicit path to a config.local.json. Defaults to this checkout's own config if neither --project nor --config is given.")
    sub = p.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Create a new role page.")
    p_new.add_argument("--title", required=True, help='e.g. "QA / Verification".')
    p_new.add_argument("--slug", default=None, help="Defaults to a slugified --title.")
    p_new.add_argument("--persona", default=None, help='Optional named voice, e.g. "Lothar".')
    p_new.add_argument("--purpose", default=None, help="One-liner shown in the roster.")
    p_new.add_argument("--authority", default=None, help="Free text — what this role can decide/block vs. propose.")
    p_new.add_argument("--reports-to", default=None, help="Another role's slug, if this one reports to it.")
    p_new.add_argument("--status", default="active", choices=["active", "retired"])
    p_new.add_argument(
        "--launch-target", default="cowork", choices=["cowork", "code"],
        help="Which claude:// deep link the Launch column opens. Defaults to \"cowork\".",
    )
    p_new.set_defaults(func=_cmd_new)

    p_index = sub.add_parser("index", help="Rebuild the roster (ROLES_INDEX.md).")
    p_index.add_argument("--output", default=None, help="Defaults to <roles_root's parent>/ROLES_INDEX.md.")
    p_index.add_argument("--title", default=None, help='Override the top heading. Defaults to "# Roles".')
    p_index.set_defaults(func=_cmd_index)

    p_refresh = sub.add_parser(
        "refresh",
        help="Recompute every role's header and rebuild the roster against this machine's real paths.",
    )
    p_refresh.set_defaults(func=_cmd_refresh)

    p_projects = sub.add_parser("projects", help="List registered projects (config/projects.json).")
    p_projects.set_defaults(func=_cmd_projects)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except (RolesCliError, _config.ConfigError, _projects.ProjectsError) as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
