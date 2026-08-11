"""Installs the canonical "meta" wiki pages — module usage conventions (ID schemes, slug
conventions, CLI cheatsheets) — into a project's wiki.

The canonical copy is real wiki content, not a hardcoded string in this file: it's maintained
as actual pages in the `backhaul` project itself (this repo's own dogfooded BHW instance —
`backhaul/wiki/meta/{bht,bhw,bhrm}.md`, resolved via `config/projects.json`'s `"backhaul"`
entry), edited the same way any other wiki page is, with `bhw`. This module just knows how to
copy pages from one project's wiki into another's — see services/wiki/cli.py's `seed-meta`
subcommand for how the source project gets resolved.

Installing is additive and non-destructive: a page that already exists at the destination
(same category + filename) is left untouched, never overwritten — a project that's customized
its own copy keeps it.
"""

from __future__ import annotations

from pathlib import Path


class DefaultsError(Exception):
    """Raised when the source wiki has no pages under the requested category to copy."""


def seed_meta_wiki(
    dest_wiki_root: str | Path,
    source_wiki_root: str | Path,
    *,
    category: str = "meta",
) -> dict[str, list[str]]:
    """Copy every page under source_wiki_root/<category>/ into dest_wiki_root/<category>/,
    skipping any file that already exists at the destination.

    Returns {"created": [...], "skipped": [...]} — filenames without extension. Header
    refresh and index rebuild are the caller's job (services/wiki/cli.py's `seed-meta` command)
    since a copied page's header needs recomputing against the *destination* project's own
    WIKI_INDEX.md, not the source's.
    """
    source_dir = Path(source_wiki_root) / category if category else Path(source_wiki_root)
    dest_dir = Path(dest_wiki_root) / category if category else Path(dest_wiki_root)

    if not source_dir.is_dir():
        raise DefaultsError(f"{source_dir}: no such category in the source wiki")

    source_pages = sorted(source_dir.glob("*.md"))
    if not source_pages:
        raise DefaultsError(f"{source_dir}: no pages found to install")

    created: list[str] = []
    skipped: list[str] = []
    for src_path in source_pages:
        dest_path = dest_dir / src_path.name
        if dest_path.exists():
            skipped.append(src_path.stem)
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
        created.append(src_path.stem)

    return {"created": created, "skipped": skipped}
