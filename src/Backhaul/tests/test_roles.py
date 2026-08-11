"""Tests for modules/roles (BHRole) — schema, page creation, header, index, and the
claude:// launch-link extraction.

Only synthetic fixtures under tmp_path are used here, never real project data, per
migration/PYTHON_PROJECT_SETUP.md's fixtures note.
"""

from pathlib import Path

import pytest

from backhaul.foundation import filesafety
from backhaul.foundation import frontmatter as _frontmatter
from backhaul.modules.roles import create as _create
from backhaul.modules.roles import header as _header
from backhaul.modules.roles import index as _index
from backhaul.modules.roles import launch as _launch
from backhaul.modules.roles.schema import RoleValidationError, validate


# --- schema ----------------------------------------------------------------------------


def test_validate_accepts_minimal_role():
    role = validate({"slug": "qa", "title": "QA / Verification"})
    assert role.id == "qa"
    assert role.status == "active"
    assert role.persona is None


def test_validate_accepts_full_role():
    role = validate(
        {
            "slug": "qa",
            "title": "QA / Verification",
            "persona": "Lothar",
            "purpose": "Independent verifier.",
            "authority": "Can block a phase from closing.",
            "reports_to": "pm",
            "status": "active",
        }
    )
    assert role.persona == "Lothar"
    assert role.authority == "Can block a phase from closing."
    assert role.reports_to == "pm"


def test_validate_rejects_missing_fields():
    with pytest.raises(RoleValidationError):
        validate({"slug": "qa"})


def test_validate_rejects_unknown_status():
    with pytest.raises(RoleValidationError):
        validate({"slug": "qa", "title": "QA", "status": "on-vacation"})


def test_validate_defaults_status_to_active():
    role = validate({"slug": "qa", "title": "QA"})
    assert role.status == "active"


# --- create_role -------------------------------------------------------------------------


def test_create_role_minimal(tmp_path: Path):
    roles_root = tmp_path / "roles"
    path = _create.create_role(roles_root=roles_root, title="QA / Verification")
    assert path.name == "qa-verification.md"
    assert path.exists()

    doc = _frontmatter.parse(path)
    assert doc.frontmatter["slug"] == "qa-verification"
    assert doc.frontmatter["id"] == "qa-verification"
    assert doc.frontmatter["status"] == "active"
    assert "# QA / Verification" in doc.body
    assert "## Session bootstrap prompt" in doc.body


def test_create_role_slug_override(tmp_path: Path):
    roles_root = tmp_path / "roles"
    path = _create.create_role(roles_root=roles_root, title="QA / Verification", slug="qa")
    assert path.name == "qa.md"


def test_create_role_slug_is_sanitized(tmp_path: Path):
    roles_root = tmp_path / "roles"
    path = _create.create_role(roles_root=roles_root, title="Whatever", slug="Not A Clean Slug!!")
    assert path.name == "not-a-clean-slug.md"


def test_create_role_full_frontmatter(tmp_path: Path):
    roles_root = tmp_path / "roles"
    path = _create.create_role(
        roles_root=roles_root,
        title="QA / Verification",
        slug="qa",
        persona="Lothar",
        purpose="Independent verifier.",
        authority="Can block a phase from closing.",
        reports_to="pm",
    )
    doc = _frontmatter.parse(path)
    assert doc.frontmatter["persona"] == "Lothar"
    assert doc.frontmatter["purpose"] == "Independent verifier."
    assert doc.frontmatter["authority"] == "Can block a phase from closing."
    assert doc.frontmatter["reports_to"] == "pm"
    assert "Independent verifier." in doc.body


def test_create_role_refuses_overwrite(tmp_path: Path):
    roles_root = tmp_path / "roles"
    _create.create_role(roles_root=roles_root, title="QA", slug="qa")
    with pytest.raises(filesafety.UnsafeWriteError):
        _create.create_role(roles_root=roles_root, title="QA Again", slug="qa")


# --- launch (bootstrap-prompt extraction + claude:// link building) ----------------------


def test_extract_bootstrap_prompt_finds_fenced_block():
    body = (
        "# Title\n\n"
        "## Session bootstrap prompt\n\n"
        "Paste this in.\n\n"
        "```\n"
        "You are QA.\nDo the thing.\n"
        "```\n\n"
        "## Related pages\n"
    )
    assert _launch.extract_bootstrap_prompt(body) == "You are QA.\nDo the thing."


def test_extract_bootstrap_prompt_is_case_insensitive_and_any_heading_level():
    body = "### session BOOTSTRAP Prompt\n```\nHello\n```\n"
    assert _launch.extract_bootstrap_prompt(body) == "Hello"


def test_extract_bootstrap_prompt_none_when_section_missing():
    assert _launch.extract_bootstrap_prompt("# Title\n\nJust some text.\n") is None


def test_extract_bootstrap_prompt_none_when_no_fence_follows():
    body = "## Session bootstrap prompt\n\nNo fenced block here.\n"
    assert _launch.extract_bootstrap_prompt(body) is None


def test_extract_bootstrap_prompt_ignores_earlier_fences():
    body = (
        "```\nnot this one\n```\n\n"
        "## Session bootstrap prompt\n\n"
        "```\nthis one\n```\n"
    )
    assert _launch.extract_bootstrap_prompt(body) == "this one"


def test_build_launch_link_from_role_page(tmp_path: Path):
    roles_root = tmp_path / "roles"
    path = _create.create_role(roles_root=roles_root, title="QA", slug="qa")
    doc = _frontmatter.parse(path)
    doc.body = doc.body.replace(
        "(Write the actual bootstrap prompt here: what the role is, what persona it plays if any, what\n"
        "to read before doing anything else — orient, instruments, where the work currently stands —\n"
        "then \"hold your lane\" boundaries, then instructions to summarize back and wait for input\n"
        "rather than starting work immediately.)",
        "You are QA.",
    )
    _frontmatter.write(doc)

    link = _launch.build_launch_link(path, project_root=r"C:\_local\source\LunaFlow_A")
    assert link is not None
    # No folder= param — observed to clear the composer when combined with q (see launch.py's
    # module docstring). The project root is folded into the q text itself instead.
    assert "folder=" not in link
    assert link.startswith("claude://cowork/new?q=")
    assert "This%20role%27s%20project%20folder%20is%20C%3A%5C_local%5Csource%5CLunaFlow_A" in link
    assert "You%20are%20QA." in link


def test_build_launch_link_omits_folder_line_without_project_root(tmp_path: Path):
    roles_root = tmp_path / "roles"
    path = _create.create_role(roles_root=roles_root, title="QA", slug="qa")
    doc = _frontmatter.parse(path)
    doc.body = doc.body.replace(
        "(Write the actual bootstrap prompt here: what the role is, what persona it plays if any, what\n"
        "to read before doing anything else — orient, instruments, where the work currently stands —\n"
        "then \"hold your lane\" boundaries, then instructions to summarize back and wait for input\n"
        "rather than starting work immediately.)",
        "You are QA.",
    )
    _frontmatter.write(doc)

    link = _launch.build_launch_link(path)
    assert link == "claude://cowork/new?q=You%20are%20QA."


def test_build_launch_link_none_without_bootstrap_prompt(tmp_path: Path):
    roles_root = tmp_path / "roles"
    path = roles_root / "empty.md"
    roles_root.mkdir(parents=True)
    doc = _frontmatter.ParsedDoc(
        frontmatter={"id": "empty", "slug": "empty", "title": "Empty"},
        body="# Empty\n\nNo bootstrap prompt section at all.\n",
        path=path,
    )
    _frontmatter.write(doc)

    assert _launch.build_launch_link(path) is None


# --- header --------------------------------------------------------------------------------


def test_refresh_header_inserts_block(tmp_path: Path):
    roles_root = tmp_path / "roles"
    path = _create.create_role(roles_root=roles_root, title="QA", slug="qa")
    index_path = tmp_path / "ROLES_INDEX.md"

    _header.refresh_header(path, index_path, project_name="LunaFlow_A")
    content = path.read_text(encoding="utf-8")
    assert "**LunaFlow_A** — [Dashboard](BACKHAUL.md) · [Roles Index](../ROLES_INDEX.md)" in content


def test_refresh_header_is_idempotent(tmp_path: Path):
    roles_root = tmp_path / "roles"
    path = _create.create_role(roles_root=roles_root, title="QA", slug="qa")
    index_path = tmp_path / "ROLES_INDEX.md"

    _header.refresh_header(path, index_path)
    once = path.read_text(encoding="utf-8")
    _header.refresh_header(path, index_path)
    assert path.read_text(encoding="utf-8") == once


# --- index -----------------------------------------------------------------------------


def test_build_index_lists_roles_sorted_by_title(tmp_path: Path):
    roles_root = tmp_path / "roles"
    _create.create_role(roles_root=roles_root, title="QA / Verification", slug="qa", persona="Lothar")
    _create.create_role(roles_root=roles_root, title="Architect", slug="architect", persona="Amara")

    out = tmp_path / "ROLES_INDEX.md"
    _index.build_index(roles_root, out)
    content = out.read_text(encoding="utf-8")

    assert content.index("Architect") < content.index("QA / Verification")
    assert "Amara" in content
    assert "Lothar" in content


def test_build_index_no_roles_yet(tmp_path: Path):
    roles_root = tmp_path / "roles"
    roles_root.mkdir()
    out = tmp_path / "ROLES_INDEX.md"
    _index.build_index(roles_root, out)
    assert "_No roles defined yet._" in out.read_text(encoding="utf-8")


def test_build_index_includes_launch_link_when_bootstrap_prompt_present(tmp_path: Path):
    roles_root = tmp_path / "roles"
    path = _create.create_role(roles_root=roles_root, title="QA", slug="qa")
    doc = _frontmatter.parse(path)
    doc.body = doc.body.replace(
        "(Write the actual bootstrap prompt here: what the role is, what persona it plays if any, what\n"
        "to read before doing anything else — orient, instruments, where the work currently stands —\n"
        "then \"hold your lane\" boundaries, then instructions to summarize back and wait for input\n"
        "rather than starting work immediately.)",
        "You are QA.",
    )
    _frontmatter.write(doc)

    out = tmp_path / "ROLES_INDEX.md"
    _index.build_index(roles_root, out, project_root=r"C:\_local\source\LunaFlow_A")
    content = out.read_text(encoding="utf-8")
    assert "[Launch](claude://cowork/new?q=" in content
    assert "folder=" not in content
    assert "You%20are%20QA." in content


def test_build_index_omits_launch_link_without_bootstrap_prompt(tmp_path: Path):
    roles_root = tmp_path / "roles"
    roles_root.mkdir(parents=True)
    path = roles_root / "empty.md"
    doc = _frontmatter.ParsedDoc(
        frontmatter={"id": "empty", "slug": "empty", "title": "Empty"},
        body="# Empty\n\nNo bootstrap prompt section at all.\n",
        path=path,
    )
    _frontmatter.write(doc)

    out = tmp_path / "ROLES_INDEX.md"
    _index.build_index(roles_root, out)
    content = out.read_text(encoding="utf-8")
    assert "claude://cowork/new" not in content
    assert "[Empty]" in content


def test_build_index_includes_header_with_dashboard_path(tmp_path: Path):
    roles_root = tmp_path / "roles"
    _create.create_role(roles_root=roles_root, title="QA", slug="qa")

    out = tmp_path / "ROLES_INDEX.md"
    dashboard_path = tmp_path / "BACKHAUL.md"
    _index.build_index(roles_root, out, dashboard_path=dashboard_path, project_name="mcRepos")
    content = out.read_text(encoding="utf-8")
    assert content.startswith("<!-- bh-header:start -->")
    assert "**mcRepos** — [Dashboard](BACKHAUL.md)" in content
