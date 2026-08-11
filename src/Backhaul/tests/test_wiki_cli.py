"""Integration tests for the bhw CLI, run against synthetic tmp_path fixtures — never real
content. Mirrors tests/test_cli.py's structure for bht.
"""

import json
import re
from pathlib import Path

import pytest

from backhaul.foundation import frontmatter
from backhaul.foundation.projects import ProjectsError
from backhaul.services.wiki.cli import main


def _write_config(tmp_path: Path) -> Path:
    cfg_path = tmp_path / "config.local.json"
    cfg_path.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": str(tmp_path / "content" / "tickets"),
                    "wiki": str(tmp_path / "content" / "wiki"),
                },
                "enabled_modules": [],
                "client_folders": {},
            }
        ),
        encoding="utf-8",
    )
    return cfg_path


def test_new_and_index(tmp_path: Path):
    cfg_path = _write_config(tmp_path)

    assert (
        main(
            [
                "--config",
                str(cfg_path),
                "new",
                "--category",
                "reference/conventions",
                "--title",
                "Wiki Style Guide",
                "--summary",
                "How pages are structured.",
            ]
        )
        == 0
    )

    page_path = tmp_path / "content" / "wiki" / "reference" / "conventions" / "wiki-style-guide.md"
    assert page_path.exists()

    index_path = tmp_path / "content" / "WIKI_INDEX.md"
    assert index_path.exists()
    assert "Wiki Style Guide" in index_path.read_text(encoding="utf-8")

    doc = frontmatter.parse(page_path)
    assert doc.frontmatter["status"] == "draft"
    assert "[Index]" in doc.body


def test_refresh_recomputes_breadcrumbs(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--category", "meta", "--title", "About"])

    page_path = tmp_path / "content" / "wiki" / "meta" / "about.md"
    doc = frontmatter.parse(page_path)
    doc.body = re.sub(
        r"<!-- breadcrumb:start -->.*?<!-- breadcrumb:end -->",
        "<!-- breadcrumb:start -->\n[Index](stale/path.md)\n<!-- breadcrumb:end -->",
        doc.body,
        flags=re.DOTALL,
    )
    frontmatter.write(doc)
    assert "stale/path.md" in page_path.read_text(encoding="utf-8")

    assert main(["--config", str(cfg_path), "refresh"]) == 0

    content = page_path.read_text(encoding="utf-8")
    assert "stale/path.md" not in content
    assert "[Index](../../WIKI_INDEX.md) / meta" in content


def test_index_category_flag_scopes_output(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--category", "frontiermode", "--title", "FM Overview"])
    main(["--config", str(cfg_path), "new", "--category", "satchel", "--title", "Satchel Overview"])

    out_path = tmp_path / "FRONTIERMODE_WIKI.md"
    assert (
        main(
            [
                "--config",
                str(cfg_path),
                "index",
                "--output",
                str(out_path),
                "--category",
                "frontiermode",
                "--title",
                "# FrontierMode Wiki",
            ]
        )
        == 0
    )

    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("# FrontierMode Wiki")
    assert "FM Overview" in content
    assert "Satchel Overview" not in content


# --- --project flag (config/projects.json) ------------------------------------------------


def test_project_flag_resolves_via_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_path = _write_config(tmp_path)
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"myproj": str(cfg_path)}), encoding="utf-8")

    import backhaul.services.wiki.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["--project", "myproj", "new", "--category", "meta", "--title", "About"]) == 0
    assert (tmp_path / "content" / "wiki" / "meta" / "about.md").exists()


def test_project_flag_unknown_name_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"known": "x"}), encoding="utf-8")

    import backhaul.services.wiki.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    with pytest.raises(ProjectsError):
        main(["--project", "typo", "index"])


def test_projects_command_lists_registered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"alpha": "a.json"}), encoding="utf-8")

    import backhaul.services.wiki.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["projects"]) == 0
    assert "alpha: a.json" in capsys.readouterr().out
