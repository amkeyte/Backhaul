"""Idempotent marked-block injection/refresh, e.g. `<!-- board:start -->...<!-- board:end -->`.

Used for injecting generated nav/link blocks into otherwise hand-edited files (the ticket
board nav, the folder/edit links in ticket headers) without clobbering the rest of the file
on repeat runs.
"""

from __future__ import annotations

import re


def _pattern(marker: str) -> re.Pattern[str]:
    start = re.escape(f"<!-- {marker}:start -->")
    end = re.escape(f"<!-- {marker}:end -->")
    return re.compile(f"{start}.*?{end}", re.DOTALL)


def refresh_block(text: str, marker: str, new_content: str) -> str:
    """Replace the content between `<!-- {marker}:start -->` and `<!-- {marker}:end -->`
    with new_content, inserting the markers if they don't yet exist. Returns the updated text.

    Idempotent: running this twice with the same inputs produces the same output, so it's
    safe to call on every board/breadcrumb refresh without hand-editing risk.
    """
    block = f"<!-- {marker}:start -->\n{new_content}\n<!-- {marker}:end -->"
    pattern = _pattern(marker)

    if pattern.search(text):
        return pattern.sub(lambda _: block, text, count=1)

    if text and not text.endswith("\n"):
        text += "\n"
    return text + block + "\n"
