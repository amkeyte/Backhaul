"""Backhaul's cross-service front page: a small dashboard linking to the ticket board and
wiki index for one project, with a quick open-ticket/page-count summary.

Lives at the top of the package (not under services/ or modules/) deliberately — it's the
composition root that knows about both BHT and BHW, which is different from one *service*
depending on another (something migration/ARCHITECTURE.md explicitly avoids; BHT and BHW
only reference each other via typed Refs, never each other's internals). An orchestrator
sitting above both and rendering a combined view is expected to import both.
"""

from __future__ import annotations

import os
from pathlib import Path

from backhaul.foundation import filesafety, rollup
from backhaul.services.ticket.schema import OPEN_STATES


def _relpath(target: str | Path, start: str | Path) -> str:
    """Relative path from directory `start` to `target`, POSIX-style separators. Deliberately
    NOT resolved — same reasoning as services/ticket/board.py's _relpath."""
    return os.path.relpath(Path(target), Path(start)).replace(os.sep, "/")


def _count_open_tickets(tickets_root: Path) -> int:
    if not tickets_root.is_dir():
        return 0
    spec = rollup.CollectSpec(
        root=tickets_root, glob="*.md", filter_fn=lambda fm: fm.get("status") in OPEN_STATES
    )
    items = rollup.collect(spec)
    return len(items) if isinstance(items, list) else 0


def _count_wiki_pages(wiki_root: Path) -> int:
    if not wiki_root.is_dir():
        return 0
    items = rollup.collect(rollup.CollectSpec(root=wiki_root, glob="**/*.md"))
    return len(items) if isinstance(items, list) else 0


def render_dashboard(
    *,
    tickets_root: str | Path,
    wiki_root: str | Path,
    board_path: str | Path,
    index_path: str | Path,
    dashboard_dir: str | Path,
) -> str:
    """Render BACKHAUL.md's body: links to the board and wiki index, each with a live count."""
    tickets_root = Path(tickets_root)
    wiki_root = Path(wiki_root)
    dashboard_dir = Path(dashboard_dir)

    open_count = _count_open_tickets(tickets_root)
    page_count = _count_wiki_pages(wiki_root)

    board_rel = _relpath(board_path, dashboard_dir)
    index_rel = _relpath(index_path, dashboard_dir)

    ticket_word = "ticket" if open_count == 1 else "tickets"
    page_word = "page" if page_count == 1 else "pages"

    return (
        "# Backhaul\n\n"
        f"- [Work Board]({board_rel}) — {open_count} open {ticket_word}\n"
        f"- [Wiki Index]({index_rel}) — {page_count} {page_word}\n"
    )


def build_dashboard(
    *,
    tickets_root: str | Path,
    wiki_root: str | Path,
    board_path: str | Path,
    index_path: str | Path,
    output_path: str | Path,
) -> None:
    """Render and write BACKHAUL.md to output_path, overwriting wholesale like BOARD.md/
    WIKI_INDEX.md — it's a generated front page, not something to hand-edit."""
    output_path = Path(output_path)
    content = render_dashboard(
        tickets_root=tickets_root,
        wiki_root=wiki_root,
        board_path=board_path,
        index_path=index_path,
        dashboard_dir=output_path.parent,
    )
    filesafety.safe_write(output_path, content, overwrite=True)
