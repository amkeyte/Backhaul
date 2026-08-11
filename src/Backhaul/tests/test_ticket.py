"""Tests for services/ticket (BHT) — schema, registry, ticket creation, and board rendering.

Only synthetic fixtures under tmp_path are used here, never real client data, per
migration/PYTHON_PROJECT_SETUP.md's fixtures note.
"""

from datetime import date
from pathlib import Path

import pytest

from backhaul.foundation import frontmatter
from backhaul.services.ticket import board, create, registry
from backhaul.services.ticket.schema import TicketValidationError, validate

# --- schema ----------------------------------------------------------------------------


def test_validate_accepts_full_frontmatter():
    ticket = validate(
        {
            "uid": "GEN",
            "number": 3,
            "client": "General",
            "status": "open",
            "title": "Fix the thing",
            "priority": "high",
        }
    )
    assert ticket.id == "GEN_003"
    assert ticket.priority == "high"


def test_validate_rejects_missing_fields():
    with pytest.raises(TicketValidationError):
        validate({"uid": "GEN", "number": 1, "status": "open", "title": "X"})


def test_validate_rejects_bad_status():
    with pytest.raises(TicketValidationError):
        validate({"uid": "GEN", "number": 1, "client": "General", "status": "sleeping", "title": "X"})


# --- registry ----------------------------------------------------------------------------


def test_registry_round_trip(tmp_path: Path):
    reg_path = tmp_path / "client-uids.md"
    assert registry.load_registry(reg_path) == {}

    registry.register_uid(reg_path, "UW", "University of Washington")
    assert registry.load_registry(reg_path) == {"UW": "University of Washington"}
    assert registry.find_uid(reg_path, "university of washington") == "UW"
    assert registry.find_uid(reg_path, "Nobody") is None


def test_registry_rejects_conflicting_uid(tmp_path: Path):
    reg_path = tmp_path / "client-uids.md"
    registry.register_uid(reg_path, "UW", "University of Washington")
    with pytest.raises(registry.RegistryError):
        registry.register_uid(reg_path, "UW", "Some Other Client")


def test_suggest_uid():
    assert registry.suggest_uid("University of Washington") == "UW"
    assert registry.suggest_uid("General") == "GEN"
    assert registry.suggest_uid("Precision Electric") == "PE"


def test_resolve_client_folder_falls_back_to_tickets_root_parent(tmp_path: Path):
    tickets_root = tmp_path / "Fronthaul" / "tickets"
    tickets_root.mkdir(parents=True)
    cfg = {"client_folders": {}}
    assert registry.resolve_client_folder(cfg, "ARR", tickets_root) == tmp_path / "Fronthaul"


def test_resolve_client_folder_uses_configured_entry(tmp_path: Path):
    tickets_root = tmp_path / "Fronthaul" / "tickets"
    tickets_root.mkdir(parents=True)
    cfg = {"client_folders": {"UW": str(tmp_path / "Projects" / "UW")}}
    assert registry.resolve_client_folder(cfg, "UW", tickets_root) == tmp_path / "Projects" / "UW"


# --- create_ticket -------------------------------------------------------------------------


def test_create_ticket_mints_uid_and_writes_file(tmp_path: Path):
    tickets_root = tmp_path / "tickets"
    reg_path = tmp_path / "client-uids.md"

    path = create.create_ticket(
        tickets_root=tickets_root,
        registry_path=reg_path,
        client="University of Washington",
        title="Replace the roof antenna",
        today=date(2026, 8, 9),
    )

    assert path.exists()
    assert path.name.startswith("UW_001_")
    assert registry.find_uid(reg_path, "University of Washington") == "UW"

    doc = frontmatter.parse(path)
    assert doc.frontmatter["status"] == "open"
    assert doc.frontmatter["title"] == "Replace the roof antenna"
    assert doc.frontmatter["opened"] == "2026-08-09"
    assert "Replace the roof antenna" in doc.body


def test_create_ticket_numbers_sequentially(tmp_path: Path):
    tickets_root = tmp_path / "tickets"
    reg_path = tmp_path / "client-uids.md"

    first = create.create_ticket(
        tickets_root=tickets_root, registry_path=reg_path, client="General", title="First"
    )
    second = create.create_ticket(
        tickets_root=tickets_root, registry_path=reg_path, client="General", title="Second"
    )
    assert first.name.startswith("GEN_001_")
    assert second.name.startswith("GEN_002_")


def test_create_ticket_respects_explicit_uid(tmp_path: Path):
    tickets_root = tmp_path / "tickets"
    reg_path = tmp_path / "client-uids.md"

    path = create.create_ticket(
        tickets_root=tickets_root,
        registry_path=reg_path,
        client="Precision Electric",
        title="Site walk",
        uid="PREC",
    )
    assert path.name.startswith("PREC_001_")
    assert registry.find_uid(reg_path, "Precision Electric") == "PREC"


# --- board -----------------------------------------------------------------------------


def test_build_board_groups_by_status_and_excludes_done(tmp_path: Path):
    tickets_root = tmp_path / "tickets"
    reg_path = tmp_path / "client-uids.md"

    open_path = create.create_ticket(
        tickets_root=tickets_root, registry_path=reg_path, client="General", title="Open one"
    )
    done_path = create.create_ticket(
        tickets_root=tickets_root, registry_path=reg_path, client="General", title="Closed one"
    )
    doc = frontmatter.parse(done_path)
    doc.frontmatter["status"] = "done"
    frontmatter.write(doc)

    # Board lives one directory up from tickets_root — matches the CLI's default layout, and
    # keeps a large tickets/ folder (50+ files) from burying the board file among them.
    board_path = tmp_path / "BOARD.md"
    board.build_board(tickets_root, board_path)
    content = board_path.read_text(encoding="utf-8")

    assert "Open one" in content
    assert "Closed one" not in content
    assert "## open" in content
    assert f"tickets/{open_path.name}" in content  # ID link is relative to the board's dir
    assert f"editmd:///{open_path.as_posix()}" in content  # Edit link opens in Notepad++


def test_build_board_overwrites_existing(tmp_path: Path):
    tickets_root = tmp_path / "tickets"
    reg_path = tmp_path / "client-uids.md"
    create.create_ticket(tickets_root=tickets_root, registry_path=reg_path, client="General", title="One")

    board_path = tmp_path / "BOARD.md"
    board.build_board(tickets_root, board_path)
    first_render = board_path.read_text(encoding="utf-8")

    board.build_board(tickets_root, board_path)  # should not raise UnsafeWriteError
    assert board_path.read_text(encoding="utf-8") == first_render


def test_refresh_board_link_is_idempotent(tmp_path: Path):
    tickets_root = tmp_path / "tickets"
    reg_path = tmp_path / "client-uids.md"
    path = create.create_ticket(tickets_root=tickets_root, registry_path=reg_path, client="General", title="One")
    board_path = tmp_path / "BOARD.md"  # one directory up from tickets_root

    board.refresh_board_link(path, board_path)
    once = path.read_text(encoding="utf-8")
    board.refresh_board_link(path, board_path)
    twice = path.read_text(encoding="utf-8")

    assert once == twice
    assert "../BOARD.md" in once


def test_refresh_board_link_folder_defaults_to_ticket_dir(tmp_path: Path):
    tickets_root = tmp_path / "tickets"
    reg_path = tmp_path / "client-uids.md"
    path = create.create_ticket(tickets_root=tickets_root, registry_path=reg_path, client="General", title="One")

    board.refresh_board_link(path)
    content = path.read_text(encoding="utf-8")
    assert f"openfolder:///{tickets_root.as_posix()}" in content


def test_refresh_board_link_folder_uses_client_folder(tmp_path: Path):
    tickets_root = tmp_path / "tickets"
    reg_path = tmp_path / "client-uids.md"
    client_folder = tmp_path / "Projects" / "General"
    path = create.create_ticket(tickets_root=tickets_root, registry_path=reg_path, client="General", title="One")

    board.refresh_board_link(path, folder_path=client_folder)
    content = path.read_text(encoding="utf-8")
    assert f"openfolder:///{client_folder.as_posix()}" in content
