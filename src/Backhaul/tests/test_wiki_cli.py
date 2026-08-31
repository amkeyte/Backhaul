"""Integration tests for the bhw CLI, run against synthetic tmp_path fixtures — never real
content. Mirrors tests/test_cli.py's structure for bht.
"""

import json
import re
from pathlib import Path

import pytest

from backhaul.foundation import frontmatter
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
    assert "[Wiki Index]" in doc.body


def test_index_includes_header_linking_back_to_dashboard(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--category", "meta", "--title", "About"])

    index_path = tmp_path / "content" / "WIKI_INDEX.md"
    content = index_path.read_text(encoding="utf-8")
    assert content.startswith("<!-- bh-header:start -->")
    assert "[Dashboard](../BACKHAUL.md)" in content


def test_refresh_recomputes_headers(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--category", "meta", "--title", "About"])

    page_path = tmp_path / "content" / "wiki" / "meta" / "about.md"
    doc = frontmatter.parse(page_path)
    doc.body = re.sub(
        r"<!-- bh-header:start -->.*?<!-- bh-header:end -->",
        "<!-- bh-header:start -->\n[Wiki Index](stale/path.md)\n<!-- bh-header:end -->",
        doc.body,
        flags=re.DOTALL,
    )
    frontmatter.write(doc)
    assert "stale/path.md" in page_path.read_text(encoding="utf-8")

    assert main(["--config", str(cfg_path), "refresh"]) == 0

    content = page_path.read_text(encoding="utf-8")
    assert "stale/path.md" not in content
    assert "[Wiki Index](../../WIKI_INDEX.md) · meta" in content


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
    assert content.startswith("<!-- bh-header:start -->")
    assert "# FrontierMode Wiki" in content
    assert "FM Overview" in content
    assert "Satchel Overview" not in content


def test_seed_meta_installs_from_source_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "source").mkdir()
    (tmp_path / "dest").mkdir()
    source_cfg = _write_config(tmp_path / "source")
    dest_cfg = _write_config(tmp_path / "dest")

    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"backhaul": str(source_cfg)}), encoding="utf-8")

    import backhaul.services.wiki.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    # Seed the canonical source project's own meta pages first.
    main(["--config", str(source_cfg), "new", "--category", "meta", "--title", "BHT — Ticket Conventions", "--slug", "bht"])

    assert main(["--config", str(dest_cfg), "seed-meta"]) == 0

    dest_page = tmp_path / "dest" / "content" / "wiki" / "meta" / "bht.md"
    assert dest_page.exists()

    index_content = (tmp_path / "dest" / "content" / "WIKI_INDEX.md").read_text(encoding="utf-8")
    assert "BHT" in index_content


def test_seed_meta_is_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "source").mkdir()
    (tmp_path / "dest").mkdir()
    source_cfg = _write_config(tmp_path / "source")
    dest_cfg = _write_config(tmp_path / "dest")

    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"backhaul": str(source_cfg)}), encoding="utf-8")

    import backhaul.services.wiki.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    main(["--config", str(source_cfg), "new", "--category", "meta", "--title", "BHT", "--slug", "bht"])
    assert main(["--config", str(dest_cfg), "seed-meta"]) == 0
    assert main(["--config", str(dest_cfg), "seed-meta"]) == 0  # should not raise or duplicate


# --- --project flag (config/projects.json) ------------------------------------------------


def test_project_flag_resolves_via_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_path = _write_config(tmp_path)
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"myproj": str(cfg_path)}), encoding="utf-8")

    import backhaul.services.wiki.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["--project", "myproj", "new", "--category", "meta", "--title", "About"]) == 0
    assert (tmp_path / "content" / "wiki" / "meta" / "about.md").exists()


def test_project_flag_unknown_name_fails_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """main() catches ProjectsError itself (BH_022) and reports it as a clean FAIL, rather than
    letting it propagate as a raw exception -- same treatment as a missing/malformed config."""
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"known": "x"}), encoding="utf-8")

    import backhaul.services.wiki.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["--project", "typo", "index"]) == 1
    assert "FAIL:" in capsys.readouterr().err


def test_missing_config_fails_cleanly_not_a_traceback(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    missing = tmp_path / "nope" / "config.local.json"
    assert main(["--config", str(missing), "index"]) == 1
    assert "FAIL:" in capsys.readouterr().err


def test_version_flag_prints_prog_and_package_version(capsys: pytest.CaptureFixture[str]):
    from backhaul import __version__ as package_version

    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "bhw" in out
    assert package_version in out


def test_projects_command_lists_registered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"alpha": "a.json"}), encoding="utf-8")

    import backhaul.services.wiki.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["projects"]) == 0
    assert "alpha: a.json" in capsys.readouterr().out
