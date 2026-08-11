"""Integration tests for the bhrm CLI, run against synthetic tmp_path fixtures — never real
content. Mirrors tests/test_cli.py's structure for bht.
"""

import json
from pathlib import Path

import pytest

from backhaul.foundation import frontmatter
from backhaul.foundation.projects import ProjectsError
from backhaul.modules.roadmap.cli import main


def _write_config(tmp_path: Path, *, enabled: bool = True) -> Path:
    cfg_path = tmp_path / "config.local.json"
    cfg_path.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": str(tmp_path / "content" / "tickets"),
                    "wiki": str(tmp_path / "content" / "wiki"),
                    "roadmap": str(tmp_path / "content" / "roadmap"),
                },
                "enabled_modules": ["roadmap"] if enabled else [],
            }
        ),
        encoding="utf-8",
    )
    return cfg_path


def test_module_not_enabled_fails_clean(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path, enabled=False)
    rc = main(["--config", str(cfg_path), "frontier", "--uid", "RM_ARR"])
    assert rc == 1
    assert "not enabled" in capsys.readouterr().err


def test_new_and_frontier(tmp_path: Path):
    cfg_path = _write_config(tmp_path)

    assert (
        main(
            [
                "--config", str(cfg_path),
                "new", "--client", "Arryn", "--title", "Set up the shed", "--owner", "Arryn",
            ]
        )
        == 0
    )

    node_path = tmp_path / "content" / "roadmap" / "RM_ARR_001_set-up-the-shed.md"
    assert node_path.exists()

    doc = frontmatter.parse(node_path)
    assert doc.frontmatter["id"] == "RM_ARR_001"
    assert doc.frontmatter["status"] == "open"


def test_new_with_slug_override(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    assert main([
        "--config", str(cfg_path), "new", "--client", "Arryn",
        "--title", "A much longer descriptive title", "--owner", "Arryn", "--slug", "alma",
    ]) == 0
    assert (tmp_path / "content" / "roadmap" / "RM_ARR_001_alma.md").exists()


def test_new_writes_header(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--client", "Arryn", "--title", "Set up the shed", "--owner", "Arryn"])

    node_path = tmp_path / "content" / "roadmap" / "RM_ARR_001_set-up-the-shed.md"
    content = node_path.read_text(encoding="utf-8")
    assert "[Dashboard](" in content
    assert "[Roadmap Index](../ROADMAP_INDEX.md) · RM_ARR" in content


def test_refresh_recomputes_headers_and_rebuilds_index(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--client", "Arryn", "--title", "X", "--owner", "Arryn"])

    node_path = tmp_path / "content" / "roadmap" / "RM_ARR_001_x.md"
    doc = frontmatter.parse(node_path)
    import re

    doc.body = re.sub(
        r"<!-- bh-header:start -->.*?<!-- bh-header:end -->",
        "<!-- bh-header:start -->\n[Roadmap Index](stale/path.md)\n<!-- bh-header:end -->",
        doc.body,
        flags=re.DOTALL,
    )
    frontmatter.write(doc)
    assert "stale/path.md" in node_path.read_text(encoding="utf-8")

    assert main(["--config", str(cfg_path), "refresh"]) == 0

    content = node_path.read_text(encoding="utf-8")
    assert "stale/path.md" not in content
    assert "[Roadmap Index](../ROADMAP_INDEX.md) · RM_ARR" in content
    assert (tmp_path / "content" / "ROADMAP_INDEX.md").exists()


def test_refresh_fails_when_module_not_enabled(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path, enabled=False)
    rc = main(["--config", str(cfg_path), "refresh"])
    assert rc == 1
    assert "not enabled" in capsys.readouterr().err


def test_render_includes_links(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--client", "Arryn", "--title", "X", "--owner", "Arryn", "--slug", "alma"])

    out_path = tmp_path / "render.md"
    assert main(["--config", str(cfg_path), "render", "--uid", "RM_ARR", "--output", str(out_path)]) == 0
    content = out_path.read_text(encoding="utf-8")
    assert "[**RM_ARR_001**](" in content
    assert "RM_ARR_001_alma.md" in content


def test_index_includes_header_linking_back_to_dashboard(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--client", "Arryn", "--title", "X", "--owner", "Arryn"])

    out_path = tmp_path / "content" / "ROADMAP_INDEX.md"
    assert main(["--config", str(cfg_path), "index"]) == 0
    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("<!-- bh-header:start -->")
    assert "[Dashboard](../BACKHAUL.md)" in content


def test_index_includes_links(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--client", "Arryn", "--title", "X", "--owner", "Arryn", "--slug", "alma"])

    out_path = tmp_path / "ROADMAP_INDEX.md"
    assert main(["--config", str(cfg_path), "index", "--output", str(out_path)]) == 0
    content = out_path.read_text(encoding="utf-8")
    assert "[**RM_ARR_001**](" in content
    assert "RM_ARR_001_alma.md" in content


def test_new_with_depends_on_and_frontier_scoping(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path)

    main(["--config", str(cfg_path), "new", "--client", "Arryn", "--title", "Root", "--owner", "Arryn"])
    main([
        "--config", str(cfg_path), "new", "--client", "Arryn", "--title", "Depends on root",
        "--owner", "Arryn", "--depends-on", "RM_ARR_001",
    ])

    capsys.readouterr()
    assert main(["--config", str(cfg_path), "frontier", "--uid", "RM_ARR"]) == 0
    out = capsys.readouterr().out
    # RM_ARR_001 is open (not resolved), so RM_ARR_002 isn't satisfied yet — only 001 is actionable.
    assert "RM_ARR_001" in out
    assert "RM_ARR_002" not in out


def test_validate_detects_cycle(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path)
    roadmap_root = tmp_path / "content" / "roadmap"
    roadmap_root.mkdir(parents=True)

    def _write(number, depends_on):
        doc = frontmatter.ParsedDoc(
            frontmatter={
                "id": f"RM_ARR_{number:03d}",
                "uid": "RM_ARR",
                "number": number,
                "kind": "work",
                "status": "open",
                "title": f"Node {number}",
                "owner": "Arryn",
                "depends_on": depends_on,
            },
            body="\nbody\n",
            path=roadmap_root / f"RM_ARR_{number:03d}.md",
        )
        frontmatter.write(doc)

    _write(1, ["RM_ARR_002"])
    _write(2, ["RM_ARR_001"])

    rc = main(["--config", str(cfg_path), "validate", "--uid", "RM_ARR"])
    assert rc == 1
    assert "Cycle detected" in capsys.readouterr().err


def test_dependents_downstream_blocking(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--client", "Arryn", "--title", "A", "--owner", "Arryn"])
    main([
        "--config", str(cfg_path), "new", "--client", "Arryn", "--title", "B",
        "--owner", "Arryn", "--depends-on", "RM_ARR_001",
    ])

    capsys.readouterr()
    main(["--config", str(cfg_path), "dependents", "RM_ARR_001"])
    assert "RM_ARR_002" in capsys.readouterr().out

    main(["--config", str(cfg_path), "downstream", "RM_ARR_001"])
    assert "RM_ARR_002" in capsys.readouterr().out

    main(["--config", str(cfg_path), "blocking", "RM_ARR_002"])
    # RM_ARR_001 is "open", not resolved, so it's a blocker for RM_ARR_002.
    assert "RM_ARR_001" in capsys.readouterr().out


def test_render_and_export_json(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--client", "Arryn", "--title", "A", "--owner", "Arryn"])

    out_path = tmp_path / "render.md"
    assert main(["--config", str(cfg_path), "render", "--uid", "RM_ARR", "--output", str(out_path)]) == 0
    assert "RM_ARR_001" in out_path.read_text(encoding="utf-8")

    json_path = tmp_path / "graph.json"
    assert main(["--config", str(cfg_path), "export-json", "--uid", "RM_ARR", "--out", str(json_path)]) == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["nodes"][0]["id"] == "RM_ARR_001"


def test_index_command_sections_each_graph(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--client", "FrontierMode", "--title", "FM root", "--owner", "Arryn"])
    main(["--config", str(cfg_path), "new", "--client", "Satchel", "--title", "Satchel root", "--owner", "Arryn"])

    out_path = tmp_path / "ROADMAP_INDEX.md"
    assert main(["--config", str(cfg_path), "index", "--output", str(out_path)]) == 0

    content = out_path.read_text(encoding="utf-8")
    assert "## RM_FRO" in content
    assert "## RM_SAT" in content
    assert "FM root" in content
    assert "Satchel root" in content


def test_index_default_output_path(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--client", "Arryn", "--title", "X", "--owner", "Arryn"])
    assert main(["--config", str(cfg_path), "index"]) == 0
    # content_roots.roadmap's parent, per _index_path's convention.
    assert (tmp_path / "content" / "ROADMAP_INDEX.md").exists()


def test_cross_uid_dependency_fails_at_cli_level(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--client", "FrontierMode", "--title", "FM root", "--owner", "Arryn"])
    main([
        "--config", str(cfg_path), "new", "--client", "Satchel", "--title", "Satchel node",
        "--owner", "Arryn", "--depends-on", "RM_FRO_001",
    ])

    capsys.readouterr()
    rc = main(["--config", str(cfg_path), "frontier", "--uid", "RM_SAT"])
    assert rc == 1
    assert "different UID" in capsys.readouterr().err


# --- --project flag (config/projects.json) ------------------------------------------------


def test_project_flag_resolves_via_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_path = _write_config(tmp_path)
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"myproj": str(cfg_path)}), encoding="utf-8")

    import backhaul.modules.roadmap.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["--project", "myproj", "new", "--client", "Arryn", "--title", "X", "--owner", "Arryn"]) == 0
    assert (tmp_path / "content" / "roadmap" / "RM_ARR_001_x.md").exists()


def test_project_flag_unknown_name_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"known": "x"}), encoding="utf-8")

    import backhaul.modules.roadmap.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    with pytest.raises(ProjectsError):
        main(["--project", "typo", "frontier", "--uid", "RM_TEST"])


def test_projects_command_lists_registered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"alpha": "a.json"}), encoding="utf-8")

    import backhaul.modules.roadmap.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["projects"]) == 0
    assert "alpha: a.json" in capsys.readouterr().out
