"""The normalized Backhaul header: every piece of Backhaul-managed content — a ticket, a wiki
page, a roadmap node — carries the same recognizable header block: the project's display name,
a link back to that project's BACKHAUL.md dashboard, and a link to the content type's own
indexer (BOARD.md / WIKI_INDEX.md / ROADMAP_INDEX.md). Each content type can append its own
extra bit after that (a ticket's Folder link, a wiki page's category trail) — the shared core
is what makes this "feel like one system" rather than three unrelated ones, per the design
conversation that introduced this (see the project's own meta/ wiki pages).

Rendering only — inserting/refreshing the block in a file is each content type's own job
(services/ticket/board.py, services/wiki/index.py, modules/roadmap/header.py), same separation
foundation/markers.py's refresh_block already keeps: this module doesn't know about file I/O.
"""

from __future__ import annotations

#: Marker name every content type's header block is wrapped in — one name, everywhere, so a
#: person or a tool can recognize "this is the Backhaul header" without caring which content
#: type they're looking at.
MARKER_NAME = "bh-header"


def render_header(
    *,
    project_name: str,
    dashboard_rel: str | None = None,
    indexer_label: str | None = None,
    indexer_rel: str | None = None,
    extra: str = "",
) -> str:
    """Render the header line. `indexer_label` is the content type's own indexer name
    ("Board", "Wiki Index", "Roadmap Index"); `extra` is appended after it (already
    markdown-formatted, e.g. a Folder link or a category trail) when given.

    `dashboard_rel` and `indexer_rel` (with its `indexer_label`) are each optional and
    independently omittable — a content file passes both (it has somewhere to point back to
    and its own indexer); an indexer page itself (BOARD.md/WIKI_INDEX.md/ROADMAP_INDEX.md)
    passes only `dashboard_rel` (pointing back at the dashboard, but not at itself); the
    dashboard (BACKHAUL.md) passes neither, since it's already the top of the tree — just the
    bolded project name. Segments are joined with " · " in Dashboard, indexer, extra order.
    """
    segments: list[str] = []
    if dashboard_rel is not None:
        segments.append(f"[Dashboard]({dashboard_rel})")
    if indexer_rel is not None:
        segments.append(f"[{indexer_label}]({indexer_rel})")
    if extra:
        segments.append(extra)

    if not segments:
        return f"**{project_name}**"
    return f"**{project_name}** — " + " · ".join(segments)
