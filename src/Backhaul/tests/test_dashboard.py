"""Tests for backhaul.dashboard (BACKHAUL.md) and the top-level `backhaul` CLI, against
synthetic tmp_path fixtures.
"""

import json
from pathlib import Path

from backhaul import dashboard
from backhaul.cli import main
from backhaul.modules.roadmap import create as roadmap_create
from backhaul.modules.roles import create as roles_create
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


def test_render_dashboard_includes_roadmap_when_given(tmp_path: Path):
    tickets_root = tmp_path / "backhaul" / "tickets"
    wiki_root = tmp_path / "backhaul" / "wiki"
    roadmap_root = tmp_path / "backhaul" / "roadmap"

    roadmap_create.create_node(
        nodes_root=roadmap_root, registry_path=tickets_root / "client-uids.md",
        client="FrontierMode", title="FM root", owner="Arryn",
    )
    roadmap_create.create_node(
        nodes_root=roadmap_root, registry_path=tickets_root / "client-uids.md",
        client="Satchel", title="Satchel root", owner="Arryn",
    )

    content = dashboard.render_dashboard(
        tickets_root=tickets_root, wiki_root=wiki_root,
        board_path=tickets_root.parent / "BOARD.md", index_path=wiki_root.parent / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
        roadmap_root=roadmap_root, roadmap_index_path=roadmap_root.parent / "ROADMAP_INDEX.md",
    )
    assert "[Roadmap](backhaul/ROADMAP_INDEX.md)" in content
    assert "2 graphs" in content
    assert "2 actionable" in content


def test_render_dashboard_includes_roles_when_given(tmp_path: Path):
    tickets_root = tmp_path / "backhaul" / "tickets"
    wiki_root = tmp_path / "backhaul" / "wiki"
    roles_root = tmp_path / "backhaul" / "roles"

    roles_create.create_role(roles_root=roles_root, title="QA", slug="qa")
    roles_create.create_role(roles_root=roles_root, title="Architect", slug="architect", status="retired")

    content = dashboard.render_dashboard(
        tickets_root=tickets_root, wiki_root=wiki_root,
        board_path=tickets_root.parent / "BOARD.md", index_path=wiki_root.parent / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
        roles_root=roles_root, roles_index_path=roles_root.parent / "ROLES_INDEX.md",
    )
    assert "[Team](backhaul/ROLES_INDEX.md)" in content
    # Only the active role counts — the retired one doesn't inflate the front-page number.
    assert "1 role" in content


def test_render_dashboard_omits_roles_when_not_given(tmp_path: Path):
    content = dashboard.render_dashboard(
        tickets_root=tmp_path / "backhaul" / "tickets", wiki_root=tmp_path / "backhaul" / "wiki",
        board_path=tmp_path / "backhaul" / "BOARD.md", index_path=tmp_path / "backhaul" / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
    )
    assert "Team" not in content


def test_render_dashboard_includes_header_with_project_name(tmp_path: Path):
    content = dashboard.render_dashboard(
        tickets_root=tmp_path / "backhaul" / "tickets", wiki_root=tmp_path / "backhaul" / "wiki",
        board_path=tmp_path / "backhaul" / "BOARD.md", index_path=tmp_path / "backhaul" / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
        project_name="Fronthaul",
    )
    assert content.startswith("<!-- bh-header:start -->\n**Fronthaul**\n<!-- bh-header:end -->")


def test_render_dashboard_header_defaults_to_backhaul(tmp_path: Path):
    content = dashboard.render_dashboard(
        tickets_root=tmp_path / "backhaul" / "tickets", wiki_root=tmp_path / "backhaul" / "wiki",
        board_path=tmp_path / "backhaul" / "BOARD.md", index_path=tmp_path / "backhaul" / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
    )
    assert "**Backhaul**" in content


def test_render_dashboard_omits_roadmap_when_not_given(tmp_path: Path):
    content = dashboard.render_dashboard(
        tickets_root=tmp_path / "backhaul" / "tickets", wiki_root=tmp_path / "backhaul" / "wiki",
        board_path=tmp_path / "backhaul" / "BOARD.md", index_path=tmp_path / "backhaul" / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
    )
    assert "Roadmap" not in content


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


def _write_config(
    tmp_path: Path, *, enabled_modules: list | None = None, with_roadmap: bool = False, with_roles: bool = False
) -> Path:
    cfg_path = tmp_path / "backhaul" / "config.local.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    content_roots = {
        "tickets": str(tmp_path / "backhaul" / "tickets"),
        "wiki": str(tmp_path / "backhaul" / "wiki"),
    }
    if with_roadmap:
        content_roots["roadmap"] = str(tmp_path / "backhaul" / "roadmap")
    if with_roles:
        content_roots["roles"] = str(tmp_path / "backhaul" / "roles")
    cfg_path.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": content_roots,
                "enabled_modules": enabled_modules or [],
                "client_folders": {},
            }
        ),
        encoding="utf-8",
    )
    return cfg_path


def test_cli_dashboard_uses_configured_project_name(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["project_name"] = "Fronthaul"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    assert main(["--config", str(cfg_path), "dashboard"]) == 0
    content = (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")
    assert "**Fronthaul**" in content


def test_cli_dashboard_default_output_location(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    assert main(["--config", str(cfg_path), "dashboard"]) == 0

    # tickets_root.parent ("backhaul/") .parent (tmp_path) / BACKHAUL.md
    out = tmp_path / "BACKHAUL.md"
    assert out.exists()
    assert "Work Board" in out.read_text(encoding="utf-8")


def test_cli_dashboard_omits_roadmap_without_config_root(tmp_path: Path):
    cfg_path = _write_config(tmp_path, enabled_modules=["roadmap"])  # enabled but no content_roots.roadmap
    assert main(["--config", str(cfg_path), "dashboard"]) == 0
    assert "Roadmap" not in (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")


def test_cli_dashboard_omits_roadmap_when_not_enabled(tmp_path: Path):
    cfg_path = _write_config(tmp_path, with_roadmap=True)  # content root present but module not enabled
    assert main(["--config", str(cfg_path), "dashboard"]) == 0
    assert "Roadmap" not in (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")


def test_cli_dashboard_includes_roadmap_when_enabled_and_configured(tmp_path: Path):
    cfg_path = _write_config(tmp_path, enabled_modules=["roadmap"], with_roadmap=True)
    assert main(["--config", str(cfg_path), "dashboard"]) == 0

    content = (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")
    assert "[Roadmap](backhaul/ROADMAP_INDEX.md)" in content
    assert "0 graphs" in content


def test_cli_dashboard_omits_roles_without_config_root(tmp_path: Path):
    cfg_path = _write_config(tmp_path, enabled_modules=["roles"])  # enabled but no content_roots.roles
    assert main(["--config", str(cfg_path), "dashboard"]) == 0
    assert "Team" not in (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")


def test_cli_dashboard_omits_roles_when_not_enabled(tmp_path: Path):
    cfg_path = _write_config(tmp_path, with_roles=True)  # content root present but module not enabled
    assert main(["--config", str(cfg_path), "dashboard"]) == 0
    assert "Team" not in (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")


def test_cli_dashboard_includes_roles_when_enabled_and_configured(tmp_path: Path):
    cfg_path = _write_config(tmp_path, enabled_modules=["roles"], with_roles=True)
    assert main(["--config", str(cfg_path), "dashboard"]) == 0

    content = (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")
    assert "[Team](backhaul/ROLES_INDEX.md)" in content
    assert "0 roles" in content


def test_cli_projects_lists_registered(tmp_path: Path, monkeypatch, capsys):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"alpha": "a.json"}), encoding="utf-8")

    import backhaul.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["projects"]) == 0
    assert "alpha: a.json" in capsys.readouterr().out
