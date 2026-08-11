import json
from pathlib import Path

import pytest

from backhaul.foundation import config, filesafety, frontmatter, handler_uri, identity, markers, projects, rollup, slugify, templating


def test_frontmatter_roundtrip(tmp_path: Path):
    p = tmp_path / "doc.md"
    p.write_text("---\ntitle: Hello\nnumber: 3\n---\nSome body text.\n", encoding="utf-8")

    doc = frontmatter.parse(p)
    assert doc.frontmatter == {"title": "Hello", "number": 3}
    assert doc.body.strip() == "Some body text."

    doc.frontmatter["status"] = "open"
    frontmatter.write(doc)

    reparsed = frontmatter.parse(p)
    assert reparsed.frontmatter["status"] == "open"
    assert reparsed.frontmatter["title"] == "Hello"


def test_frontmatter_rejects_missing_block(tmp_path: Path):
    p = tmp_path / "bad.md"
    p.write_text("no frontmatter here\n", encoding="utf-8")
    with pytest.raises(frontmatter.FrontmatterError):
        frontmatter.parse(p)


def test_identity_next_number():
    assert identity.next_number("UW", []) == 1
    assert identity.next_number("UW", [1, 2, 3]) == 4
    assert identity.next_number("UW", [1, 5, 2]) == 6


def test_numbered_identity_str():
    ident = identity.NumberedIdentity(uid="UW", number=2)
    assert str(ident) == "UW_002"


def test_path_identity_str():
    ident = identity.PathIdentity(category="knowledge-base/clients", slug="uw-tacoma")
    assert str(ident) == "knowledge-base/clients/uw-tacoma"


# --- slugify -----------------------------------------------------------------------------


def test_slugify_basic():
    assert slugify.slugify("Hello, World!") == "hello-world"
    assert slugify.slugify("  Leading/trailing spaces  ") == "leading-trailing-spaces"


def test_slugify_truncates_without_dangling_hyphen():
    long_title = "a" * 38 + " b c d e"
    slug = slugify.slugify(long_title, maxlen=40)
    assert len(slug) <= 40
    assert not slug.endswith("-")


# --- filesafety ----------------------------------------------------------------------------


def test_safe_write_refuses_overwrite(tmp_path: Path):
    p = tmp_path / "doc.md"
    filesafety.safe_write(p, "first")
    assert p.read_text(encoding="utf-8") == "first"

    with pytest.raises(filesafety.UnsafeWriteError):
        filesafety.safe_write(p, "second")
    assert p.read_text(encoding="utf-8") == "first"

    filesafety.safe_write(p, "second", overwrite=True)
    assert p.read_text(encoding="utf-8") == "second"


def test_safe_write_creates_parent_dirs(tmp_path: Path):
    p = tmp_path / "nested" / "dir" / "doc.md"
    filesafety.safe_write(p, "content")
    assert p.read_text(encoding="utf-8") == "content"


def test_assert_within_root(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    inside = root / "sub" / "doc.md"
    outside = tmp_path / "elsewhere" / "doc.md"

    filesafety.assert_within_root(inside, root)
    with pytest.raises(filesafety.UnsafeWriteError):
        filesafety.assert_within_root(outside, root)


# --- templating ----------------------------------------------------------------------------


def test_render_template_substitutes_placeholders(tmp_path: Path):
    tmpl = tmp_path / "t.md.tmpl"
    tmpl.write_text("# {{ TITLE }}\n\nBy {{ AUTHOR }}.\n", encoding="utf-8")
    rendered = templating.render_template(tmpl, {"TITLE": "Hello", "AUTHOR": "Ziltoid"})
    assert rendered == "# Hello\n\nBy Ziltoid.\n"


def test_render_template_raises_on_unknown_key(tmp_path: Path):
    tmpl = tmp_path / "t.md.tmpl"
    tmpl.write_text("{{ MISSING }}", encoding="utf-8")
    with pytest.raises(templating.TemplateError):
        templating.render_template(tmpl, {})


# --- markers -------------------------------------------------------------------------------


def test_refresh_block_inserts_when_absent():
    text = "Body text.\n"
    result = markers.refresh_block(text, "board", "[Board](BOARD.md)")
    assert "<!-- board:start -->" in result
    assert "[Board](BOARD.md)" in result
    assert "<!-- board:end -->" in result
    assert result.startswith("Body text.\n")


def test_refresh_block_replaces_existing_idempotently():
    text = "before\n<!-- board:start -->\nold link\n<!-- board:end -->\nafter\n"
    once = markers.refresh_block(text, "board", "new link")
    twice = markers.refresh_block(once, "board", "new link")
    assert once == twice
    assert "old link" not in once
    assert "new link" in once
    assert "before" in once and "after" in once


# --- rollup --------------------------------------------------------------------------------


def _write_doc(path: Path, frontmatter_dict: dict, body: str = "body\n"):
    doc = frontmatter.ParsedDoc(frontmatter=frontmatter_dict, body=body, path=path)
    frontmatter.write(doc)


def test_collect_filters_and_groups(tmp_path: Path):
    _write_doc(tmp_path / "a.md", {"status": "open", "title": "A"})
    _write_doc(tmp_path / "b.md", {"status": "done", "title": "B"})
    _write_doc(tmp_path / "c.md", {"status": "open", "title": "C"})
    (tmp_path / "not-frontmatter.md").write_text("no frontmatter\n", encoding="utf-8")

    spec = rollup.CollectSpec(
        root=tmp_path,
        glob="*.md",
        filter_fn=lambda fm: fm.get("status") == "open",
        group_by="status",
    )
    grouped = rollup.collect(spec)
    assert set(grouped.keys()) == {"open"}
    assert {item["title"] for item in grouped["open"]} == {"A", "C"}


def test_collect_flat_list_without_group_by(tmp_path: Path):
    _write_doc(tmp_path / "a.md", {"status": "open", "title": "A"})
    spec = rollup.CollectSpec(root=tmp_path, glob="*.md")
    items = rollup.collect(spec)
    assert isinstance(items, list)
    assert items[0]["title"] == "A"
    assert items[0]["_path"] == tmp_path / "a.md"


# --- config --------------------------------------------------------------------------------


def test_load_config_missing_file(tmp_path: Path):
    with pytest.raises(config.ConfigError):
        config.load_config(tmp_path / "nope.json")


def test_load_config_invalid_json(tmp_path: Path):
    p = tmp_path / "config.local.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(config.ConfigError):
        config.load_config(p)


def test_load_config_missing_required_keys(tmp_path: Path):
    p = tmp_path / "config.local.json"
    p.write_text(json.dumps({"version": "0.1.0"}), encoding="utf-8")
    with pytest.raises(config.ConfigError):
        config.load_config(p)


def test_load_config_valid(tmp_path: Path):
    p = tmp_path / "config.local.json"
    p.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {"tickets": "T", "wiki": "W"},
                "enabled_modules": ["docx"],
            }
        ),
        encoding="utf-8",
    )
    cfg = config.load_config(p)
    assert cfg["content_roots"]["tickets"] == "T"
    assert config.get_enabled_modules(cfg) == ["docx"]


def test_get_enabled_modules_defaults_empty():
    assert config.get_enabled_modules({"version": "0.1.0", "content_roots": {"tickets": "T", "wiki": "W"}}) == []


# --- handler_uri -----------------------------------------------------------------------------


def test_build_uri_basic():
    uri = handler_uri.build_uri("editmd", r"C:\_local\Fronthaul\tickets\ARR_001_clean-the-car.md")
    assert uri == "editmd:///C:/_local/Fronthaul/tickets/ARR_001_clean-the-car.md"


def test_build_uri_encodes_spaces():
    uri = handler_uri.build_uri("openfolder", r"C:\Program Files\Notepad++")
    assert uri.startswith("openfolder:///C:/Program%20Files/Notepad")
    assert handler_uri.decode_uri("openfolder", uri) == r"C:\Program Files\Notepad++"


def test_decode_uri_round_trips():
    original = r"C:\_local\Fronthaul\tickets\ARR_001_clean-the-car.md"
    uri = handler_uri.build_uri("editmd", original)
    assert handler_uri.decode_uri("editmd", uri) == original


def test_decode_uri_round_trips_with_spaces():
    original = r"C:\Program Files\Notepad++\notepad++.exe"
    uri = handler_uri.build_uri("editmd", original)
    assert handler_uri.decode_uri("editmd", uri) == original


def test_decode_uri_rejects_wrong_scheme():
    uri = handler_uri.build_uri("editmd", r"C:\foo.md")
    with pytest.raises(ValueError):
        handler_uri.decode_uri("openfolder", uri)


# --- projects --------------------------------------------------------------------------


def test_load_projects_missing_file_returns_empty(tmp_path: Path):
    assert projects.load_projects(tmp_path / "nope.json") == {}


def test_load_projects_invalid_json(tmp_path: Path):
    p = tmp_path / "projects.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(projects.ProjectsError):
        projects.load_projects(p)


def test_load_projects_valid(tmp_path: Path):
    p = tmp_path / "projects.json"
    p.write_text(json.dumps({"personal": "C:\\personal\\config.local.json"}), encoding="utf-8")
    assert projects.load_projects(p) == {"personal": "C:\\personal\\config.local.json"}


def test_resolve_project_config_known_name(tmp_path: Path):
    p = tmp_path / "projects.json"
    p.write_text(json.dumps({"mcrepos": "C:\\mcRepos\\config.local.json"}), encoding="utf-8")
    assert projects.resolve_project_config(p, "mcrepos") == Path("C:\\mcRepos\\config.local.json")


def test_resolve_project_config_unknown_name_lists_known(tmp_path: Path):
    p = tmp_path / "projects.json"
    p.write_text(json.dumps({"personal": "C:\\a.json", "mcrepos": "C:\\b.json"}), encoding="utf-8")
    with pytest.raises(projects.ProjectsError, match="mcrepos, personal"):
        projects.resolve_project_config(p, "typo")
