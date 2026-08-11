"""Renders the ticket board (replacement for build_board.py): uses
foundation.rollup.collect() to gather open/closed tickets per client, then renders its own
markdown table — this rendering step is intentionally not shared with services/wiki/index.py.
"""

from __future__ import annotations

import os
from pathlib import Path

from backhaul.foundation import filesafety, frontmatter as _frontmatter, handler_uri, markers, rollup

from .schema import OPEN_STATES, validate

_COLUMNS = ("Ticket", "Client", "Pri", "Title", "Context", "Edit")

# Must match the SCHEME constants in modules/handlers/editmd and modules/handlers/openfolder.
# Kept as plain strings here (rather than importing those modules) so services/ticket only
# depends on foundation, not on modules — see migration/ARCHITECTURE.md.
_EDIT_SCHEME = "editmd"
_FOLDER_SCHEME = "openfolder"


def _relpath(target: str | Path, start: str | Path) -> str:
    """Relative path from directory `start` to `target`, POSIX-style separators so the
    markdown link renders the same whether generated on Windows or in a Linux sandbox."""
    return os.path.relpath(Path(target).resolve(), Path(start).resolve()).replace(os.sep, "/")


def _row(item: dict, board_dir: Path) -> str:
    ticket = validate(item)
    path = item.get("_path")
    if isinstance(path, Path):
        # Ticket ID links to the .md file itself, to view it (e.g. via the Markdown Viewer
        # Chrome extension) — relative to wherever the board lives.
        id_cell = f"[{ticket.id}]({_relpath(path, board_dir)})"
        # Edit opens it in Notepad++ via the editmd: protocol handler — needs an absolute
        # path. Deliberately NOT .resolve()'d: path is already absolute (built from
        # tickets_root, which config.local.json guarantees is absolute on the real machine),
        # and .resolve() re-derives the path against whatever filesystem this code is
        # actually running on — wrong when that's a dev sandbox with content mounted at a
        # different location than the target machine's real path.
        edit = f"[Edit]({handler_uri.build_uri(_EDIT_SCHEME, path)})"
    else:
        id_cell = ticket.id
        edit = ""
    context = ticket.context or ""
    return f"| {id_cell} | {ticket.client} | {ticket.priority} | {ticket.title} | {context} | {edit} |"


def _render_table(items: list[dict], board_dir: Path) -> str:
    if not items:
        return "_No tickets in this state._\n"
    header = "| " + " | ".join(_COLUMNS) + " |"
    sep = "|" + "|".join(["---"] * len(_COLUMNS)) + "|"
    rows = [_row(item, board_dir) for item in items]
    return "\n".join([header, sep, *rows]) + "\n"


def render_board(tickets_root: str | Path, board_dir: str | Path | None = None) -> str:
    """Collect open tickets under tickets_root and render the board's markdown body.

    Only OPEN_STATES tickets are collected at all (`done` tickets are excluded from the
    rollup but stay on disk, unchanged from the legacy behavior) — grouped by status into one
    table per state. `board_dir` is the directory the rendered board will actually live in
    (defaults to tickets_root itself) — Edit links are computed relative to it, so the board
    can live alongside tickets_root or a directory up from it without broken links.
    """
    tickets_root = Path(tickets_root)
    board_dir = Path(board_dir) if board_dir is not None else tickets_root

    spec = rollup.CollectSpec(
        root=tickets_root,
        glob="*.md",
        filter_fn=lambda fm: fm.get("status") in OPEN_STATES,
        group_by="status",
    )
    grouped = rollup.collect(spec)

    sections = ["# Work Board", ""]
    for status in OPEN_STATES:
        items = grouped.get(status, []) if isinstance(grouped, dict) else []
        sections.append(f"## {status}")
        sections.append("")
        sections.append(_render_table(items, board_dir))
    return "\n".join(sections)


def build_board(tickets_root: str | Path, output_path: str | Path) -> None:
    """Collect all tickets under tickets_root and write the rendered board to output_path.

    The board is regenerated wholesale on every run — never hand-edited, per
    migration/MIGRATION_PLAN.md §4 — so this always overwrites output_path. output_path may
    live in tickets_root itself or a parent directory of it (e.g. to keep a large ticket
    folder from burying the board); Edit links are relative to wherever it actually lands.
    """
    output_path = Path(output_path)
    content = render_board(tickets_root, board_dir=output_path.parent)
    filesafety.safe_write(output_path, content, overwrite=True)


def refresh_board_link(
    ticket_path: str | Path,
    board_path: str | Path | None = None,
    folder_path: str | Path | None = None,
) -> None:
    """Insert/refresh the Board + Folder link block in a single ticket file's header.

    `folder_path` is the folder the Folder link opens (via the openfolder: protocol handler)
    — normally the client's configured project folder (see registry.resolve_client_folder),
    not necessarily the ticket's own containing directory. Defaults to the ticket's own
    directory if not given.
    """
    path = Path(ticket_path)
    doc = _frontmatter.parse(path)

    board_rel = _relpath(board_path, path.parent) if board_path is not None else "BOARD.md"
    # Not .resolve()'d, same reasoning as the Edit link above — folder_path is expected to
    # already be an absolute, correct path (from registry.resolve_client_folder, which reads
    # it straight out of config.local.json's client_folders when set).
    folder = Path(folder_path) if folder_path is not None else path.parent
    folder_uri = handler_uri.build_uri(_FOLDER_SCHEME, folder)

    block = f"[Board]({board_rel}) | [Folder]({folder_uri})"
    doc.body = markers.refresh_block(doc.body, "board", block)
    _frontmatter.write(doc)
