"""Tests for backhaul.dashboard (BACKHAUL.md) and the top-level `backhaul` CLI, against
synthetic tmp_path fixtures.
"""

import json
from pathlib import Path

from backhaul import dashboard
from backhaul.cli import main
from backhaul.services.ticket import create as ticket_create
from backhaul.services.wiki import create as wiki_create


def test_render_dashboard_counts_and_links(tmp_path: Path):
    tickets_root = tmp_path / "backhaul" / "tickets"
    wiki_root = tmp_path / "backhaul" / "wiki"

    ticket_create.create_ticket(
        tickets_root=tickets_root, registry_path=tmp_path / "backhaul" / "tickets" / "client-uids.md",
        client="General", title="Open one",
    )
    wiki_create.create_page(wiki_root=wiki_root, category="meta", title="About")

    board_path = tickets_root.parent / "BOARD.md"
    index_path = wiki_root.parent / "WIKI_INDEX.md"
    dashboard_dir = tmp_path

    content = dashboard.render_dashboard(
        tickets_root=tickets_root, wiki_root=wiki_root,
        board_path=board_path, index_path=index_path,
        dashboard_dir=dashboard_dir,
    )

    assert "[Work Board](backhaul/BOARD.md)" in content
    assert "[Wiki Index](backhaul/WIKI_INDEX.md)" in content
    assert "1 open ticket" in content
    assert "1 page" in content


def test_render_dashboard_handles_missing_roots(tmp_path: Path):
    content = dashboard.render_dashboard(
        tickets_root=tmp_path / "backhaul" / "tickets",
        wiki_root=tmp_path / "backhaul" / "wiki",
        board_path=tmp_path / "backhaul" / "BOARD.md",
        index_path=tmp_path / "backhaul" / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
    )
    assert "0 open tickets" in content
    assert "0 pages" in content


def test_build_dashboard_overwrites(tmp_path: Path):
    out = tmp_path / "BACKHAUL.md"
    kwargs = dict(
        tickets_root=tmp_path / "backhaul" / "tickets",
        wiki_root=tmp_path / "backhaul" / "wiki",
        board_path=tmp_path / "backhaul" / "BOARD.md",
        index_path=tmp_path / "backhaul" / "WIKI_INDEX.md",
    )
    dashboard.build_dashboard(output_path=out, **kwargs)
    first = out.read_text(encoding="utf-8")
    dashboard.build_dashboard(output_path=out, **kwargs)  # should not raise UnsafeWriteError
    assert out.read_text(encoding="utf-8") == first


# --- CLI -----------------------------------------------------------------------------------


def _write_config(tmp_path: Path) -> Path:
    cfg_path = tmp_path / "backhaul" / "config.local.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": str(tmp_path / "backhaul" / "tickets"),
                    "wiki": str(tmp_path / "backhaul" / "wiki"),
                },
                "enabled_modules": [],
                "client_folders": {},
            }
        ),
        encoding="utf-8",
    )
    return cfg_path


def test_cli_dashboard_default_output_location(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    assert main(["--config", str(cfg_path), "dashboard"]) == 0

    # tickets_root.parent ("backhaul/") .parent (tmp_path) / BACKHAUL.md
    out = tmp_path / "BACKHAUL.md"
    assert out.exists()
    assert "Work Board" in out.read_text(encoding="utf-8")


def test_cli_projects_lists_registered(tmp_path: Path, monkeypatch, capsys):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"alpha": "a.json"}), encoding="utf-8")

    import backhaul.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["projects"]) == 0
    assert "alpha: a.json" in capsys.readouterr().out
