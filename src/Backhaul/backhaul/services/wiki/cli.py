"""CLI entry point for BHW (BackhaulWiki): create pages and roll them up into the index.

Console script: `bhw` (see pyproject.toml [project.scripts]). Every invocation reads
config.local.json fresh, per foundation/config.py's docstring — no reliance on env vars or
persisted cwd. Mirrors backhaul.services.ticket.cli's structure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backhaul.foundation import build_info as _build_info
from backhaul.foundation import config as _config
from backhaul.foundation import frontmatter as _frontmatter
from backhaul.foundation import projects as _projects

from . import create as _create
from . import defaults as _defaults
from . import index as _index

# Backhaul/src/Backhaul/backhaul/services/wiki/cli.py -> parents[5] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[5]
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "config" / "config.local.json"
_PROJECTS_PATH = _REPO_ROOT / "config" / "projects.json"


def _resolve_config_path(args: argparse.Namespace) -> Path:
    """Resolve --project / --config / an upward cwd search / this checkout's own default.
    Shared implementation: foundation.config.resolve_config_path (see BH_019)."""
    return _config.resolve_config_path(
        args, default_config_path=_DEFAULT_CONFIG_PATH, projects_path=_PROJECTS_PATH
    )


def _wiki_root(cfg: dict) -> Path:
    return Path(cfg["content_roots"]["wiki"])


def _index_path(wiki_root: Path) -> Path:
    # One directory up from the pages themselves, same reasoning as BHT's BOARD.md: keeps
    # the index visible and out of its own **/*.md glob once there are a lot of pages.
    return wiki_root.parent / "WIKI_INDEX.md"


def _dashboard_path(wiki_root: Path) -> Path:
    # wiki_root.parent is the "backhaul/" data folder; the dashboard sits one level above
    # that, at the project's true root — mirrors services/ticket/cli.py's _dashboard_path.
    return wiki_root.parent.parent / "BACKHAUL.md"


def _cmd_new(args: argparse.Namespace) -> int:
    cfg = _config.load_config(_resolve_config_path(args))
    wiki_root = _wiki_root(cfg)
    path = _create.create_page(
        wiki_root=wiki_root,
        category=args.category,
        title=args.title,
        slug=args.slug,
        summary=args.summary,
        keywords=args.keywords,
        status=args.status,
    )

    index_path = _index_path(wiki_root)
    dashboard_path = _dashboard_path(wiki_root)
    project_name = _config.get_project_name(cfg)
    _index.refresh_header(path, index_path, dashboard_path=dashboard_path, project_name=project_name)
    _index.build_index(
        wiki_root, index_path,
        dashboard_path=dashboard_path, project_name=project_name, host_root=_config.get_host_root(cfg),
    )
    print(f"OK: created {path.relative_to(wiki_root)}")
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    cfg = _config.load_config(_resolve_config_path(args))
    wiki_root = _wiki_root(cfg)
    out = Path(args.output) if args.output else _index_path(wiki_root)
    kwargs: dict = {
        "dashboard_path": _dashboard_path(wiki_root),
        "project_name": _config.get_project_name(cfg),
        "host_root": _config.get_host_root(cfg),
    }
    if args.category:
        kwargs["category_prefix"] = args.category
    if args.title:
        kwargs["title"] = args.title
    _index.build_index(wiki_root, out, **kwargs)
    print(f"OK: wrote index to {out}")
    return 0


def _cmd_refresh(args: argparse.Namespace) -> int:
    """Recompute every page's header and rebuild the index.

    Same purpose as `bht refresh`: fixes links generated somewhere other than this machine
    (a different checkout path, or a dev sandbox) by recomputing them against this machine's
    real, resolved paths.
    """
    cfg = _config.load_config(_resolve_config_path(args))
    wiki_root = _wiki_root(cfg)
    index_path = _index_path(wiki_root)
    dashboard_path = _dashboard_path(wiki_root)
    project_name = _config.get_project_name(cfg)

    count = 0
    for page_path in sorted(wiki_root.glob("**/*.md")):
        try:
            doc = _frontmatter.parse(page_path)
        except _frontmatter.FrontmatterError:
            continue
        if "category" not in doc.frontmatter:
            continue
        _index.refresh_header(
            page_path, index_path,
            dashboard_path=dashboard_path, project_name=project_name,
        )
        count += 1

    _index.build_index(
        wiki_root, index_path,
        dashboard_path=dashboard_path, project_name=project_name, host_root=_config.get_host_root(cfg),
    )
    print(f"OK: refreshed {count} page(s), rebuilt the index at {index_path}")
    return 0


def _cmd_seed_meta(args: argparse.Namespace) -> int:
    """Install the canonical module-usage pages (maintained as real wiki content in the
    "backhaul" project itself — see that project's own meta/ pages) into this project's wiki.
    Additive only: never overwrites a page that already exists here."""
    cfg = _config.load_config(_resolve_config_path(args))
    wiki_root = _wiki_root(cfg)

    source_cfg_path = _projects.resolve_project_config(_PROJECTS_PATH, args.source_project)
    source_cfg = _config.load_config(source_cfg_path)
    source_wiki_root = _wiki_root(source_cfg)

    try:
        result = _defaults.seed_meta_wiki(wiki_root, source_wiki_root, category=args.category)
    except _defaults.DefaultsError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    index_path = _index_path(wiki_root)
    dashboard_path = _dashboard_path(wiki_root)
    project_name = _config.get_project_name(cfg)
    for slug in result["created"]:
        page_path = (wiki_root / args.category / f"{slug}.md") if args.category else (wiki_root / f"{slug}.md")
        _index.refresh_header(
            page_path, index_path,
            dashboard_path=dashboard_path, project_name=project_name,
        )
    if result["created"]:
        _index.build_index(
            wiki_root, index_path,
            dashboard_path=dashboard_path, project_name=project_name, host_root=_config.get_host_root(cfg),
        )

    if result["created"]:
        print(f"OK: installed {', '.join(result['created'])}")
    if result["skipped"]:
        print(f"Skipped (already present): {', '.join(result['skipped'])}")
    if not result["created"] and not result["skipped"]:
        print("Nothing to install.")
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
    p = argparse.ArgumentParser(prog="bhw", description="BackhaulWiki — wiki page CLI.")
    p.add_argument(
        "--version", action="version", version=_build_info.format_version_string("bhw"),
        help="Print package version (plus branch/commit when running from a git checkout) and exit.",
    )
    location = p.add_mutually_exclusive_group()
    location.add_argument("--project", default=None, help="Named project from config/projects.json (see `bhw projects`).")
    location.add_argument("--config", default=None, help="Explicit path to a config.local.json. Defaults to this checkout's own config if neither --project nor --config is given.")
    sub = p.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Create a new wiki page.")
    p_new.add_argument("--category", required=True, help='e.g. "reference" or "reference/conventions".')
    p_new.add_argument("--title", required=True)
    p_new.add_argument("--slug", default=None, help="Defaults to a slugified --title.")
    p_new.add_argument("--summary", default=None)
    p_new.add_argument("--keywords", default=None, help="Comma-separated.")
    p_new.add_argument("--status", default="draft", choices=["draft", "verified", "published"])
    p_new.set_defaults(func=_cmd_new)

    p_index = sub.add_parser("index", help="Rebuild the wiki index.")
    p_index.add_argument("--output", default=None, help="Defaults to <wiki_root's parent>/WIKI_INDEX.md.")
    p_index.add_argument("--category", default=None, help='Scope to one category and its subcategories, e.g. "frontiermode" (for a subproject landing page). Defaults to all pages.')
    p_index.add_argument("--title", default=None, help='Override the top heading, e.g. "# FrontierMode Wiki". Defaults to "# Wiki Index".')
    p_index.set_defaults(func=_cmd_index)

    p_refresh = sub.add_parser(
        "refresh",
        help="Recompute every page's header and rebuild the index against this machine's real paths.",
    )
    p_refresh.set_defaults(func=_cmd_refresh)

    p_seed = sub.add_parser("seed-meta", help="Install the canonical module-usage pages (bht/bhw/bhrm/...) into this project's wiki.")
    p_seed.add_argument("--category", default="meta", help='Defaults to "meta".')
    p_seed.add_argument("--source-project", default="backhaul", help='Named project to copy the canonical pages from. Defaults to "backhaul" (this repo\'s own dogfooded copy).')
    p_seed.set_defaults(func=_cmd_seed_meta)

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
