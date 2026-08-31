"""Integration tests for the bht CLI, run against synthetic tmp_path fixtures — never real
client data. Exercises argument parsing + wiring end-to-end, not just the underlying library
functions (those get their own coverage in test_ticket.py).
"""

import json
from pathlib import Path

import pytest

from backhaul.foundation import frontmatter
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


def test_project_flag_unknown_name_fails_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """main() catches ProjectsError itself (BH_022) and reports it as a clean FAIL, rather than
    letting it propagate as a raw exception -- same treatment as a missing/malformed config."""
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"known": "x"}), encoding="utf-8")

    import backhaul.services.ticket.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["--project", "typo", "board"]) == 1
    assert "FAIL:" in capsys.readouterr().err


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


# --- ConfigError/ProjectsError surfaced as a clean FAIL, not a traceback (BH_022) ------------


def test_missing_config_fails_cleanly_not_a_traceback(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    missing = tmp_path / "nope" / "config.local.json"
    assert main(["--config", str(missing), "board"]) == 1
    assert "FAIL:" in capsys.readouterr().err


def test_version_flag_prints_prog_and_package_version(capsys: pytest.CaptureFixture[str]):
    from backhaul import __version__ as package_version

    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "bht" in out
    assert package_version in out


# --- status (BH_017, supersedes BH_010) ----------------------------------------------------


def test_status_sets_in_progress(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"])

    assert main(["--config", str(cfg_path), "status", "ARR_001", "in-progress"]) == 0
    ticket_path = tmp_path / "Fronthaul" / "tickets" / "ARR_001_clean-the-car.md"
    assert frontmatter.parse(ticket_path).frontmatter["status"] == "in-progress"


def test_status_sets_blocked_and_stays_on_board(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"])

    assert main(["--config", str(cfg_path), "status", "ARR_001", "blocked"]) == 0
    board_path = tmp_path / "Fronthaul" / "BOARD.md"
    assert "Clean the car" in board_path.read_text(encoding="utf-8")


def test_status_reopening_a_done_ticket_clears_closed_date(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"])
    main(["--config", str(cfg_path), "close", "ARR_001"])

    assert main(["--config", str(cfg_path), "status", "ARR_001", "open"]) == 0
    ticket_path = tmp_path / "Fronthaul" / "tickets" / "ARR_001_clean-the-car.md"
    fm = frontmatter.parse(ticket_path).frontmatter
    assert fm["status"] == "open"
    assert fm["closed"] is None


def test_status_rejects_done_as_a_value(tmp_path: Path):
    # "done" stays `close`'s job -- status's own choices don't include it.
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"])

    with pytest.raises(SystemExit):
        main(["--config", str(cfg_path), "status", "ARR_001", "done"])


def test_status_unknown_id_fails_cleanly(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path)
    assert main(["--config", str(cfg_path), "status", "ARR_999", "blocked"]) == 1
    assert "FAIL" in capsys.readouterr().out


# --- log (BH_016) ---------------------------------------------------------------------------


def test_log_appends_entry_via_flag(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"])

    assert main(["--config", str(cfg_path), "log", "ARR_001", "--entry", "Started."]) == 0
    ticket_path = tmp_path / "Fronthaul" / "tickets" / "ARR_001_clean-the-car.md"
    body = frontmatter.parse(ticket_path).body
    lines = [l for l in body.splitlines() if l.startswith("- ")]
    assert lines[0].endswith(": Started.")
    assert lines[1].endswith(": Ticket opened.")


def test_log_appends_entry_via_entry_file(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"])

    entry_file = tmp_path / "entry.txt"
    entry_file.write_text("Multi-line.\nSecond line.", encoding="utf-8")
    assert main(["--config", str(cfg_path), "log", "ARR_001", "--entry-file", str(entry_file)]) == 0
    ticket_path = tmp_path / "Fronthaul" / "tickets" / "ARR_001_clean-the-car.md"
    body = frontmatter.parse(ticket_path).body
    assert "Multi-line.\n  Second line." in body


def test_log_unknown_id_fails_cleanly(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path)
    assert main(["--config", str(cfg_path), "log", "ARR_999", "--entry", "x"]) == 1
    assert "FAIL" in capsys.readouterr().out


# --- _find_one_ticket excludes the registry file, not just BOARD.md (BH_024) ----------------


def test_status_id_prefix_does_not_match_client_uids_registry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """A generic-enough id/prefix (here "c", lowercase) must not spuriously match
    client-uids.md just because it lives in tickets_root and ends in .md -- same exclusion
    _cmd_refresh's own sweep already gives BOARD.md/the registry, now shared by the id
    lookup every status/log/close command goes through."""
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"])

    assert main(["--config", str(cfg_path), "status", "c", "blocked"]) == 1
    assert "no ticket matching 'c'" in capsys.readouterr().out


# --- open length warning (BH_018) ------------------------------------------------------------


def test_open_warns_on_oversized_title(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path)
    long_title = "A" * 60
    assert main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", long_title]) == 0
    err = capsys.readouterr().err
    assert "warning" in err
    assert "60 chars" in err


def test_open_warns_on_oversized_context(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path)
    long_context = "x" * 150
    assert main([
        "--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Short",
        "--context", long_context,
    ]) == 0
    err = capsys.readouterr().err
    assert "context is 150 chars" in err


def test_open_no_warning_for_normal_length_fields(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path)
    assert main(["--config", str(cfg_path), "open", "--client", "Arryn", "--title", "Clean the car"]) == 0
    assert capsys.readouterr().err == ""
