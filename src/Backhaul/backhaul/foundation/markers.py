"""Idempotent marked-block injection/refresh, e.g. `<!-- board:start -->...<!-- board:end -->`.

Used for injecting generated nav/link blocks into otherwise hand-edited files (the ticket
board nav, the folder/edit links in ticket headers) without clobbering the rest of the file
on repeat runs.
"""

from __future__ import annotations


def refresh_block(text: str, marker: str, new_content: str) -> str:
    """Replace the content between `<!-- {marker}:start -->` and `<!-- {marker}:end -->`
    with new_content, inserting the markers if they don't yet exist. Returns the updated text.
    """
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md")
