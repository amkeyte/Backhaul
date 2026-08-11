"""CLI entry point for BHW (BackhaulWiki): create pages and roll them up into the index.

Console script: `bhw` (see pyproject.toml [project.scripts]). Every invocation reads
config.local.json fresh, per foundation/config.py's docstring — no reliance on env vars or
persisted cwd. Mirrors backhaul.services.ticket.cli's structure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backhaul.foundation import config as _config
from backhaul.foundation import frontmatter as _frontmatter
from backhaul.foundation import projects as _projects

from . import create as _create
from . import index as _index

# Backhaul/src/Backhaul/backhaul/services/wiki/cli.py -> parents[5] is the repo root.
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


def _wiki_root(cfg: dict) -> Path:
    return Path(cfg["content_roots"]["wiki"])


def _index_path(wiki_root: Path) -> Path:
    # One directory up from the pages themselves, same reasoning as BHT's BOARD.md: keeps
    # the index visible and out of its own **/*.md glob once there are a lot of pages.
    return wiki_root.parent / "WIKI_INDEX.md"


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
    _index.refresh_breadcrumb(path, index_path)
    _index.build_index(wiki_root, index_path)
    print(f"OK: created {path.relative_to(wiki_root)}")
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    cfg = _config.load_config(_resolve_config_path(args))
    wiki_root = _wiki_root(cfg)
    out = Path(args.output) if args.output else _index_path(wiki_root)
    kwargs: dict = {}
    if args.category:
        kwargs["category_prefix"] = args.category
    if args.title:
        kwargs["title"] = args.title
    _index.build_index(wiki_root, out, **kwargs)
    print(f"OK: wrote index to {out}")
    return 0


def _cmd_refresh(args: argparse.Namespace) -> int:
    """Recompute every page's breadcrumb and rebuild the index.

    Same purpose as `bht refresh`: fixes links generated somewhere other than this machine
    (a different checkout path, or a dev sandbox) by recomputing them against this machine's
    real, resolved paths.
    """
    cfg = _config.load_config(_resolve_config_path(args))
    wiki_root = _wiki_root(cfg)
    index_path = _index_path(wiki_root)

    count = 0
    for page_path in sorted(wiki_root.glob("**/*.md")):
        try:
            doc = _frontmatter.parse(page_path)
        except _frontmatter.FrontmatterError:
            continue
        if "category" not in doc.frontmatter:
            continue
        _index.refresh_breadcrumb(page_path, index_path)
        count += 1

    _index.build_index(wiki_root, index_path)
    print(f"OK: refreshed {count} page(s), rebuilt the index at {index_path}")
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
        help="Recompute every page's breadcrumb and rebuild the index against this machine's real paths.",
    )
    p_refresh.set_defaults(func=_cmd_refresh)

    p_projects = sub.add_parser("projects", help="List registered projects (config/projects.json).")
    p_projects.set_defaults(func=_cmd_projects)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
