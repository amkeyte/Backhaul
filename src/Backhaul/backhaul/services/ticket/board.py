"""Renders the ticket board (replacement for build_board.py): uses
foundation.rollup.collect() to gather open/closed tickets per client, then renders its own
markdown table — this rendering step is intentionally not shared with services/wiki/index.py.
"""

from __future__ import annotations

from pathlib import Path


def build_board(tickets_root: str | Path, output_path: str | Path) -> None:
    """Collect all tickets under tickets_root and write the rendered board to output_path."""
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md §6")


def refresh_board_link(ticket_path: str | Path, context: str | None = None) -> None:
    """Insert/refresh the Edit + Folder link block in a single ticket file's header."""
    raise NotImplementedError("stub — mirrors current _passdown/scripts/build_board.py")
