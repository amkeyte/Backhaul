"""Integration tests for the bht CLI, run against synthetic tmp_path fixtures — never real
client data. Exercises argument parsing + wiring end-to-end, not just the underlying library
functions (those get their own coverage in test_ticket.py).
"""

import json
from pathlib import Path

import pytest

from backhaul.foundation import frontmatter
from backhaul.foundation.projects import ProjectsError
from backhaul.services.ticket.cli import main


def _write_config(tmp_path: Path, client_folders: dict | None = None) -> Path:
    cfg_path = tmp_path / "config.local.json"
    cfg_path.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": str(tmp_path / "Fronthaul" / "tickets"),
                    "wiki": str(tmp_path / "Fronthaul" / "wiki"),
                },
                "enabled_modules": [],
                "client_folders": client_folders or {},
            }
        ),
        encoding="utf-8",
    )
    return cfg_path


def test_open_close_and_board(tmp_path: Path):
    cfg_path = _write_config(tmp_path)

    assert main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"]) == 0

    ticket_path = tmp_path / "Fronthaul" / "tickets" / "ARR_001_clean-the-car.md"
    assert ticket_path.exists()

    board_path = tmp_path / "Fronthaul" / "BOARD.md"
    assert board_path.exists()
    assert "Clean the car" in board_path.read_text(encoding="utf-8")

    assert main(["--config", str(cfg_path), "close", "ARR_001"]) == 0
    assert frontmatter.parse(ticket_path).frontmatter["status"] == "done"
    assert "Clean the car" not in board_path.read_text(encoding="utf-8")


def test_board_includes_header_linking_back_to_dashboard(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"])

    board_path = tmp_path / "Fronthaul" / "BOARD.md"
    content = board_path.read_text(encoding="utf-8")
    assert content.startswith("<!-- bh-header:start -->")
    assert "[Dashboard](../BACKHAUL.md)" in content


def test_open_with_slug_override(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    assert main([
        "--config", str(cfg_path), "open", "--client", "Arryn",
        "--title", "A much longer descriptive title", "--slug", "alma",
    ]) == 0
    assert (tmp_path / "Fronthaul" / "tickets" / "ARR_001_alma.md").exists()


def test_refresh_recomputes_links_against_current_config(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"])

    ticket_path = tmp_path / "Fronthaul" / "tickets" / "ARR_001_clean-the-car.md"
    stale_block = "<!-- bh-header:start -->\n[Board](../BOARD.md) | [Folder](openfolder:///C:/stale/path)\n<!-- bh-header:end -->"
    doc = frontmatter.parse(ticket_path)
    import re

    doc.body = re.sub(r"<!-- bh-header:start -->.*?<!-- bh-header:end -->", stale_block, doc.body, flags=re.DOTALL)
    frontmatter.write(doc)
    assert "stale/path" in ticket_path.read_text(encoding="utf-8")

    assert main(["--config", str(cfg_path), "refresh"]) == 0

    content = ticket_path.read_text(encoding="utf-8")
    assert "stale/path" not in content
    expected_folder = (tmp_path / "Fronthaul").as_posix()
    assert f"openfolder:///{expected_folder}" in content


def test_refresh_uses_configured_client_folder(tmp_path: Path):
    client_folder = tmp_path / "Projects" / "Arryn"
    cfg_path = _write_config(tmp_path, client_folders={"ARR": str(client_folder)})
    main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"])

    assert main(["--config", str(cfg_path), "refresh"]) == 0

    ticket_path = tmp_path / "Fronthaul" / "tickets" / "ARR_001_clean-the-car.md"
    content = ticket_path.read_text(encoding="utf-8")
    assert f"openfolder:///{client_folder.as_posix()}" in content


# --- --project flag (config/projects.json) ------------------------------------------------


def test_project_flag_resolves_via_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_path = _write_config(tmp_path)
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"myproj": str(cfg_path)}), encoding="utf-8")

    import backhaul.services.ticket.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["--project", "myproj", "open", "--client", "Arryn", "--title", "Test"]) == 0
    assert (tmp_path / "Fronthaul" / "tickets" / "ARR_001_test.md").exists()


def test_project_flag_unknown_name_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"known": "x"}), encoding="utf-8")

    import backhaul.services.ticket.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    with pytest.raises(ProjectsError):
        main(["--project", "typo", "board"])


def test_projects_command_lists_registered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"alpha": "a.json", "beta": "b.json"}), encoding="utf-8")

    import backhaul.services.ticket.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["projects"]) == 0
    out = capsys.readouterr().out
    assert "alpha: a.json" in out
    assert "beta: b.json" in out


def test_project_and_config_are_mutually_exclusive(tmp_path: Path):
    with pytest.raises(SystemExit):
        main(["--project", "x", "--config", "y", "board"])
