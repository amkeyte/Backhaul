"""Integration tests for the bhrole CLI, run against synthetic tmp_path fixtures — never real
project data. Mirrors tests/test_roadmap_cli.py's structure for bhrm.
"""

import json
import re
import urllib.parse
from pathlib import Path

import pytest

from backhaul.foundation import frontmatter
from backhaul.foundation.projects import ProjectsError
from backhaul.modules.roles.cli import main


def _write_config(
    tmp_path: Path, *, enabled: bool = True, repo_url: str | None = None, host_root: str | None = None
) -> Path:
    cfg_path = tmp_path / "config.local.json"
    cfg: dict = {
        "version": "0.1.0",
        "content_roots": {
            "tickets": str(tmp_path / "content" / "tickets"),
            "wiki": str(tmp_path / "content" / "wiki"),
            "roles": str(tmp_path / "content" / "roles"),
        },
        "enabled_modules": ["roles"] if enabled else [],
    }
    if repo_url:
        cfg["repo_url"] = repo_url
    if host_root:
        cfg["host_root"] = host_root
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    return cfg_path


def test_module_not_enabled_fails_clean(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path, enabled=False)
    rc = main(["--config", str(cfg_path), "index"])
    assert rc == 1
    assert "not enabled" in capsys.readouterr().err


def test_new_creates_role_and_writes_header(tmp_path: Path):
    cfg_path = _write_config(tmp_path)

    assert main([
        "--config", str(cfg_path), "new", "--title", "QA / Verification",
        "--slug", "qa", "--persona", "Lothar", "--purpose", "Independent verifier.",
    ]) == 0

    role_path = tmp_path / "content" / "roles" / "qa.md"
    assert role_path.exists()

    doc = frontmatter.parse(role_path)
    assert doc.frontmatter["title"] == "QA / Verification"
    assert doc.frontmatter["persona"] == "Lothar"
    assert "[Roles Index]" in doc.body

    index_path = tmp_path / "content" / "ROLES_INDEX.md"
    assert index_path.exists()
    assert "QA / Verification" in index_path.read_text(encoding="utf-8")


def test_new_launch_link_includes_pip_install_when_repo_url_configured(tmp_path: Path):
    cfg_path = _write_config(tmp_path, repo_url="https://github.com/amkeyte/Backhaul")

    assert main([
        "--config", str(cfg_path), "new", "--title", "QA / Verification",
        "--slug", "qa", "--persona", "Lothar", "--purpose", "Independent verifier.",
    ]) == 0

    role_path = tmp_path / "content" / "roles" / "qa.md"
    doc = frontmatter.parse(role_path)
    doc.body = doc.body.replace(
        "(Write the actual bootstrap prompt here: what the role is, what persona it plays if any, what\n"
        "to read before doing anything else — orient, instruments, where the work currently stands —\n"
        "then \"hold your lane\" boundaries, then instructions to summarize back and wait for input\n"
        "rather than starting work immediately.)",
        "You are QA.",
    )
    frontmatter.write(doc)
    assert main(["--config", str(cfg_path), "refresh"]) == 0

    index_path = tmp_path / "content" / "ROLES_INDEX.md"
    decoded = urllib.parse.unquote(index_path.read_text(encoding="utf-8"))
    assert 'pip install "git+https://github.com/amkeyte/Backhaul.git#subdirectory=src/Backhaul"' in decoded


def test_new_uses_host_root_for_edit_link_and_launch_preamble(tmp_path: Path):
    cfg_path = _write_config(tmp_path, host_root=r"C:\_local\mcRepos")

    assert main([
        "--config", str(cfg_path), "new", "--title", "QA / Verification", "--slug", "qa",
    ]) == 0

    role_path = tmp_path / "content" / "roles" / "qa.md"
    doc = frontmatter.parse(role_path)
    doc.body = doc.body.replace(
        "(Write the actual bootstrap prompt here: what the role is, what persona it plays if any, what\n"
        "to read before doing anything else — orient, instruments, where the work currently stands —\n"
        "then \"hold your lane\" boundaries, then instructions to summarize back and wait for input\n"
        "rather than starting work immediately.)",
        "You are QA.",
    )
    frontmatter.write(doc)
    assert main(["--config", str(cfg_path), "refresh"]) == 0

    index_path = tmp_path / "content" / "ROLES_INDEX.md"
    content = index_path.read_text(encoding="utf-8")
    decoded = urllib.parse.unquote(content)

    # Edit link is re-rooted onto host_root, not the tmp_path runtime location.
    assert "editmd:///C:/_local/mcRepos/content/roles/qa.md" in content
    assert str(tmp_path) not in content
    # The Launch link's project-folder preamble names host_root directly, not the runtime path.
    assert "This role's project folder is C:\\_local\\mcRepos" in decoded


def test_index_command_writes_roster(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--title", "Architect", "--slug", "architect"])

    out_path = tmp_path / "content" / "ROLES_INDEX.md"
    assert main(["--config", str(cfg_path), "index"]) == 0
    content = out_path.read_text(encoding="utf-8")
    assert "Architect" in content
    assert "[Dashboard]" in content


def test_index_output_flag_and_title_override(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--title", "Architect", "--slug", "architect"])

    out_path = tmp_path / "TEAM.md"
    assert main([
        "--config", str(cfg_path), "index", "--output", str(out_path), "--title", "# Team",
    ]) == 0
    content = out_path.read_text(encoding="utf-8")
    assert "# Team" in content
    assert "Architect" in content


def test_refresh_recomputes_headers_and_rebuilds_roster(tmp_path: Path):
    cfg_path = _write_config(tmp_path)
    main(["--config", str(cfg_path), "new", "--title", "QA", "--slug", "qa"])

    role_path = tmp_path / "content" / "roles" / "qa.md"
    doc = frontmatter.parse(role_path)
    doc.body = re.sub(
        r"<!-- bh-header:start -->.*?<!-- bh-header:end -->",
        "<!-- bh-header:start -->\n[Roles Index](stale/path.md)\n<!-- bh-header:end -->",
        doc.body,
        flags=re.DOTALL,
    )
    frontmatter.write(doc)
    assert "stale/path.md" in role_path.read_text(encoding="utf-8")

    assert main(["--config", str(cfg_path), "refresh"]) == 0

    content = role_path.read_text(encoding="utf-8")
    assert "stale/path.md" not in content
    assert "[Roles Index](../ROLES_INDEX.md)" in content
    assert (tmp_path / "content" / "ROLES_INDEX.md").exists()


def test_refresh_fails_when_module_not_enabled(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = _write_config(tmp_path, enabled=False)
    rc = main(["--config", str(cfg_path), "refresh"])
    assert rc == 1
    assert "not enabled" in capsys.readouterr().err


def test_new_fails_without_content_roots_roles(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    cfg_path = tmp_path / "config.local.json"
    cfg_path.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": str(tmp_path / "content" / "tickets"),
                    "wiki": str(tmp_path / "content" / "wiki"),
                },
                "enabled_modules": ["roles"],
            }
        ),
        encoding="utf-8",
    )
    rc = main(["--config", str(cfg_path), "new", "--title", "QA"])
    assert rc == 1
    assert "content_roots.roles" in capsys.readouterr().err


# --- --project flag (config/projects.json) ------------------------------------------------


def test_project_flag_resolves_via_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_path = _write_config(tmp_path)
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"myproj": str(cfg_path)}), encoding="utf-8")

    import backhaul.modules.roles.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["--project", "myproj", "new", "--title", "QA", "--slug", "qa"]) == 0
    assert (tmp_path / "content" / "roles" / "qa.md").exists()


def test_project_flag_unknown_name_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"known": "x"}), encoding="utf-8")

    import backhaul.modules.roles.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    with pytest.raises(ProjectsError):
        main(["--project", "typo", "index"])


def test_projects_command_lists_registered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    registry_path = tmp_path / "projects.json"
    registry_path.write_text(json.dumps({"alpha": "a.json"}), encoding="utf-8")

    import backhaul.modules.roles.cli as cli_module

    monkeypatch.setattr(cli_module, "_PROJECTS_PATH", registry_path)

    assert main(["projects"]) == 0
    assert "alpha: a.json" in capsys.readouterr().out
