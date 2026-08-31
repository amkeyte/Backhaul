"""Tests for backhaul.dashboard (BACKHAUL.md) and the top-level `backhaul` CLI, against
synthetic tmp_path fixtures.
"""

import json
from pathlib import Path

import pytest

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


def test_render_dashboard_omits_build_status_by_default(tmp_path: Path):
    content = dashboard.render_dashboard(
        tickets_root=tmp_path / "backhaul" / "tickets", wiki_root=tmp_path / "backhaul" / "wiki",
        board_path=tmp_path / "backhaul" / "BOARD.md", index_path=tmp_path / "backhaul" / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
    )
    assert "Build status" not in content


def test_render_dashboard_shows_ready(tmp_path: Path):
    content = dashboard.render_dashboard(
        tickets_root=tmp_path / "backhaul" / "tickets", wiki_root=tmp_path / "backhaul" / "wiki",
        board_path=tmp_path / "backhaul" / "BOARD.md", index_path=tmp_path / "backhaul" / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
        build_ready="ready",
    )
    assert "**Build status: Ready**" in content


def test_render_dashboard_shows_not_ready(tmp_path: Path):
    content = dashboard.render_dashboard(
        tickets_root=tmp_path / "backhaul" / "tickets", wiki_root=tmp_path / "backhaul" / "wiki",
        board_path=tmp_path / "backhaul" / "BOARD.md", index_path=tmp_path / "backhaul" / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
        build_ready="notReady",
    )
    assert "**Build status: Not ready**" in content


def test_render_dashboard_build_status_appears_before_work_board_line(tmp_path: Path):
    content = dashboard.render_dashboard(
        tickets_root=tmp_path / "backhaul" / "tickets", wiki_root=tmp_path / "backhaul" / "wiki",
        board_path=tmp_path / "backhaul" / "BOARD.md", index_path=tmp_path / "backhaul" / "WIKI_INDEX.md",
        dashboard_dir=tmp_path,
        build_ready="ready",
    )
    assert content.index("Build status") < content.index("Work Board")


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


def test_cli_dashboard_shows_build_ready_when_configured(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["build_ready"] = "ready"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    assert main(["--config", str(cfg_path), "dashboard"]) == 0
    content = (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")
    assert "**Build status: Ready**" in content


def test_cli_dashboard_omits_build_ready_when_not_configured(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    assert main(["--config", str(cfg_path), "dashboard"]) == 0
    content = (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")
    assert "Build status" not in content


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


def test_cli_lint_clean_reports_ok(tmp_path: Path, capsys):
    cfg_path = _write_config(tmp_path)
    wiki_root = tmp_path / "backhaul" / "wiki" / "meta"
    wiki_root.mkdir(parents=True)
    (wiki_root / "hub.md").write_text("# Hub\n\n[Target](target.md)\n", encoding="utf-8")
    (wiki_root / "target.md").write_text("# Target\n\n[Back](hub.md)\n", encoding="utf-8")

    assert main(["--config", str(cfg_path), "lint"]) == 0
    assert "OK: no findings." in capsys.readouterr().out


def test_cli_lint_returns_1_and_lists_findings(tmp_path: Path, capsys):
    cfg_path = _write_config(tmp_path)
    wiki_root = tmp_path / "backhaul" / "wiki" / "meta"
    wiki_root.mkdir(parents=True)
    (wiki_root / "lonely.md").write_text("# Lonely\n", encoding="utf-8")

    assert main(["--config", str(cfg_path), "lint"]) == 1
    out = capsys.readouterr().out
    assert "orphaned" in out
    assert "lonely.md" in out


def test_cli_lint_check_flag_scopes_to_one_check(tmp_path: Path, capsys):
    cfg_path = _write_config(tmp_path)
    wiki_root = tmp_path / "backhaul" / "wiki" / "meta"
    wiki_root.mkdir(parents=True)
    (wiki_root / "page.md").write_text("# Page\n\n[Missing](nope.md)\n", encoding="utf-8")

    assert main(["--config", str(cfg_path), "lint", "--check", "links"]) == 1
    out = capsys.readouterr().out
    assert "links:" in out
    assert "orphaned:" not in out


def test_cli_lint_format_json(tmp_path: Path, capsys):
    cfg_path = _write_config(tmp_path)
    wiki_root = tmp_path / "backhaul" / "wiki" / "meta"
    wiki_root.mkdir(parents=True)
    (wiki_root / "lonely.md").write_text("# Lonely\n", encoding="utf-8")

    assert main(["--config", str(cfg_path), "lint", "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list)
    assert payload[0]["check"] == "orphaned"


def test_cli_lint_unknown_check_fails_loud(tmp_path: Path, capsys):
    cfg_path = _write_config(tmp_path)
    assert main(["--config", str(cfg_path), "lint", "--check", "not-a-check"]) == 2
    assert "unknown check" in capsys.readouterr().err


# --- ConfigError/ProjectsError surfaced as a clean FAIL, not a traceback (BH_022) ------------


def test_missing_config_fails_cleanly_not_a_traceback(tmp_path: Path, capsys):
    missing = tmp_path / "nope" / "config.local.json"
    assert main(["--config", str(missing), "dashboard"]) == 1
    assert "FAIL:" in capsys.readouterr().err


def test_unknown_project_fails_cleanly_not_a_traceback(tmp_path: Path, monkeypatch, capsys):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"known": "x.json"}), encoding="utf-8")

    import backhaul.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)
    assert main(["--project", "typo", "dashboard"]) == 1
    assert "FAIL:" in capsys.readouterr().err


# --- --version (branch-identification convention) -------------------------------------------


def test_version_flag_prints_prog_and_package_version(capsys):
    from backhaul import __version__ as package_version

    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "backhaul" in out
    assert package_version in out


# --- refresh (BH_014) -----------------------------------------------------------------------


def test_cli_refresh_rebuilds_board_wiki_and_dashboard(tmp_path: Path, capsys):
    cfg_path = _write_config(tmp_path)
    ticket_create.create_ticket(
        tickets_root=tmp_path / "backhaul" / "tickets",
        registry_path=tmp_path / "backhaul" / "tickets" / "client-uids.md",
        client="General", title="Open one",
    )
    wiki_create.create_page(wiki_root=tmp_path / "backhaul" / "wiki", category="meta", title="About")

    assert main(["--config", str(cfg_path), "refresh"]) == 0

    board = (tmp_path / "backhaul" / "BOARD.md").read_text(encoding="utf-8")
    assert "Open one" in board
    index = (tmp_path / "backhaul" / "WIKI_INDEX.md").read_text(encoding="utf-8")
    assert "About" in index
    dashboard_content = (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")
    assert "1 open ticket" in dashboard_content
    assert "OK: refreshed" in capsys.readouterr().out


def test_cli_refresh_skips_roadmap_and_roles_when_not_enabled(tmp_path: Path):
    cfg_path = _write_config(tmp_path, with_roadmap=True, with_roles=True)  # content roots present, module not enabled

    assert main(["--config", str(cfg_path), "refresh"]) == 0
    assert not (tmp_path / "backhaul" / "ROADMAP_INDEX.md").exists()
    assert not (tmp_path / "backhaul" / "ROLES_INDEX.md").exists()
    dashboard_content = (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")
    assert "Roadmap" not in dashboard_content
    assert "Team" not in dashboard_content


def test_cli_refresh_rebuilds_roadmap_and_roles_when_enabled(tmp_path: Path):
    cfg_path = _write_config(tmp_path, enabled_modules=["roadmap", "roles"], with_roadmap=True, with_roles=True)
    roadmap_create.create_node(
        nodes_root=tmp_path / "backhaul" / "roadmap",
        registry_path=tmp_path / "backhaul" / "tickets" / "client-uids.md",
        client="FrontierMode", title="FM root", owner="Arryn",
    )
    roles_create.create_role(roles_root=tmp_path / "backhaul" / "roles", title="QA", slug="qa")

    assert main(["--config", str(cfg_path), "refresh"]) == 0

    roadmap_index = (tmp_path / "backhaul" / "ROADMAP_INDEX.md").read_text(encoding="utf-8")
    assert "RM_FRO_001" in roadmap_index
    roles_index = (tmp_path / "backhaul" / "ROLES_INDEX.md").read_text(encoding="utf-8")
    assert "QA" in roles_index
    dashboard_content = (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")
    assert "[Roadmap](backhaul/ROADMAP_INDEX.md)" in dashboard_content
    assert "[Team](backhaul/ROLES_INDEX.md)" in dashboard_content


def test_cli_refresh_reports_lint_findings_but_still_succeeds(tmp_path: Path, capsys):
    cfg_path = _write_config(tmp_path)
    wiki_root = tmp_path / "backhaul" / "wiki" / "meta"
    wiki_root.mkdir(parents=True)
    (wiki_root / "lonely.md").write_text("# Lonely\n", encoding="utf-8")

    assert main(["--config", str(cfg_path), "refresh"]) == 0
    out = capsys.readouterr().out
    assert "lint: 1 finding(s)" in out
    assert "lonely.md" in out


def test_cli_refresh_shows_build_ready_when_configured(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["build_ready"] = "notReady"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    assert main(["--config", str(cfg_path), "refresh"]) == 0
    content = (tmp_path / "BACKHAUL.md").read_text(encoding="utf-8")
    assert "**Build status: Not ready**" in content


def test_cli_refresh_lint_clean_reports_ok(tmp_path: Path, capsys):
    cfg_path = _write_config(tmp_path)
    wiki_root = tmp_path / "backhaul" / "wiki" / "meta"
    wiki_root.mkdir(parents=True)
    (wiki_root / "hub.md").write_text("# Hub\n\n[Target](target.md)\n", encoding="utf-8")
    (wiki_root / "target.md").write_text("# Target\n\n[Back](hub.md)\n", encoding="utf-8")

    assert main(["--config", str(cfg_path), "refresh"]) == 0
    assert "lint: OK, no findings." in capsys.readouterr().out


def test_cli_projects_lists_registered(tmp_path: Path, monkeypatch, capsys):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"alpha": "a.json"}), encoding="utf-8")

    import backhaul.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["projects"]) == 0
    assert "alpha: a.json" in capsys.readouterr().out
