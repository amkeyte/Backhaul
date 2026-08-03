"""Renders the wiki category index (replacement for build_index.py): uses
foundation.rollup.collect() to gather pages grouped by category, then renders its own
markdown index — not shared with services/ticket/board.py's rendering.
"""

from __future__ import annotations

from pathlib import Path


def build_index(wiki_root: str | Path, output_path: str | Path) -> None:
    """Collect all wiki pages under wiki_root and write the rendered category index."""
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md §6")
