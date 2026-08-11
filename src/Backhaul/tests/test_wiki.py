"""Tests for services/wiki (BHW) — schema, page creation, breadcrumbs, and index rendering.

Only synthetic fixtures under tmp_path are used here, never real content, per
migration/PYTHON_PROJECT_SETUP.md's fixtures note.
"""

from pathlib import Path

import pytest

from backhaul.foundation import frontmatter
from backhaul.services.wiki import create, defaults, index
from backhaul.services.wiki.schema import WikiValidationError, validate

# --- schema ----------------------------------------------------------------------------


def test_validate_accepts_full_frontmatter():
    page = validate(
        {
            "category": "reference/conventions",
            "slug": "wiki-style",
            "title": "Wiki Style Guide",
            "status": "verified",
        }
    )
    assert page.id == "reference/conventions/wiki-style"
    assert page.status == "verified"


def test_validate_defaults_status_to_draft():
    page = validate({"category": "reference", "slug": "x", "title": "X"})
    assert page.status == "draft"


def test_validate_rejects_missing_fields():
    with pytest.raises(WikiValidationError):
        validate({"category": "reference", "title": "X"})


def test_validate_rejects_bad_status():
    with pytest.raises(WikiValidationError):
        validate({"category": "reference", "slug": "x", "title": "X", "status": "on-fire"})


# --- create_page -------------------------------------------------------------------------


def test_create_page_nested_category(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    path = create.create_page(
        wiki_root=wiki_root,
        category="reference/conventions",
        title="Wiki Style Guide",
        summary="How pages are structured.",
    )
    assert path == wiki_root / "reference" / "conventions" / "wiki-style-guide.md"
    assert path.exists()

    doc = frontmatter.parse(path)
    assert doc.frontmatter["category"] == "reference/conventions"
    assert doc.frontmatter["slug"] == "wiki-style-guide"
    assert doc.frontmatter["status"] == "draft"
    assert "Wiki Style Guide" in doc.body
    assert "How pages are structured." in doc.body


def test_create_page_flat_category(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    path = create.create_page(wiki_root=wiki_root, category="meta", title="About")
    assert path == wiki_root / "meta" / "about.md"


def test_create_page_refuses_overwrite(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    create.create_page(wiki_root=wiki_root, category="meta", title="About")
    from backhaul.foundation.filesafety import UnsafeWriteError

    with pytest.raises(UnsafeWriteError):
        create.create_page(wiki_root=wiki_root, category="meta", title="About")


def test_create_page_custom_slug(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    path = create.create_page(wiki_root=wiki_root, category="meta", title="About Us", slug="about")
    assert path == wiki_root / "meta" / "about.md"


# --- index -----------------------------------------------------------------------------


def test_build_index_groups_by_category(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    conv_path = create.create_page(wiki_root=wiki_root, category="reference/conventions", title="Style Guide")
    das_path = create.create_page(wiki_root=wiki_root, category="reference", title="DAS Lifecycle")

    index_path = tmp_path / "WIKI_INDEX.md"
    index.build_index(wiki_root, index_path)
    content = index_path.read_text(encoding="utf-8")

    assert "## reference/conventions" in content
    assert "## reference" in content
    assert "Style Guide" in content
    assert "DAS Lifecycle" in content
    assert f"wiki/reference/conventions/{conv_path.name}" in content
    assert f"wiki/reference/{das_path.name}" in content


def test_build_index_includes_all_statuses(tmp_path: Path):
    """Unlike the ticket board, nothing gets excluded by status."""
    wiki_root = tmp_path / "wiki"
    create.create_page(wiki_root=wiki_root, category="meta", title="Draft Page", status="draft")
    create.create_page(wiki_root=wiki_root, category="meta", title="Published Page", status="published")

    index_path = tmp_path / "WIKI_INDEX.md"
    index.build_index(wiki_root, index_path)
    content = index_path.read_text(encoding="utf-8")

    assert "Draft Page" in content
    assert "Published Page" in content


def test_build_index_overwrites_existing(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    create.create_page(wiki_root=wiki_root, category="meta", title="About")

    index_path = tmp_path / "WIKI_INDEX.md"
    index.build_index(wiki_root, index_path)
    first = index_path.read_text(encoding="utf-8")
    index.build_index(wiki_root, index_path)  # should not raise UnsafeWriteError
    assert index_path.read_text(encoding="utf-8") == first


def test_build_index_omits_header_without_dashboard_path(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    create.create_page(wiki_root=wiki_root, category="meta", title="About")

    index_path = tmp_path / "WIKI_INDEX.md"
    index.build_index(wiki_root, index_path)
    assert "bh-header" not in index_path.read_text(encoding="utf-8")


def test_build_index_includes_header_with_dashboard_path(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    create.create_page(wiki_root=wiki_root, category="meta", title="About")

    index_path = tmp_path / "WIKI_INDEX.md"
    dashboard_path = tmp_path / "BACKHAUL.md"
    index.build_index(wiki_root, index_path, dashboard_path=dashboard_path, project_name="Fronthaul")

    content = index_path.read_text(encoding="utf-8")
    assert content.startswith("<!-- bh-header:start -->")
    assert "**Fronthaul** — [Dashboard](BACKHAUL.md)" in content


def test_index_edit_link_uses_editmd_scheme(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    path = create.create_page(wiki_root=wiki_root, category="meta", title="About")

    index_path = tmp_path / "WIKI_INDEX.md"
    index.build_index(wiki_root, index_path)
    content = index_path.read_text(encoding="utf-8")
    assert f"editmd:///{path.as_posix()}" in content


def test_build_index_category_prefix_scopes_to_matching_and_nested(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    create.create_page(wiki_root=wiki_root, category="frontiermode", title="FM Overview")
    create.create_page(wiki_root=wiki_root, category="frontiermode/setup", title="FM Setup")
    create.create_page(wiki_root=wiki_root, category="satchel", title="Satchel Overview")

    index_path = tmp_path / "FRONTIERMODE_WIKI.md"
    index.build_index(wiki_root, index_path, category_prefix="frontiermode")
    content = index_path.read_text(encoding="utf-8")

    assert "FM Overview" in content
    assert "FM Setup" in content
    assert "Satchel Overview" not in content


def test_build_index_category_prefix_does_not_match_similar_names(tmp_path: Path):
    """A prefix of "front" must not accidentally match a category called "frontiermode2"."""
    wiki_root = tmp_path / "wiki"
    create.create_page(wiki_root=wiki_root, category="front", title="Front Page")
    create.create_page(wiki_root=wiki_root, category="frontiermode2", title="Decoy Page")

    index_path = tmp_path / "WIKI_INDEX.md"
    index.build_index(wiki_root, index_path, category_prefix="front")
    content = index_path.read_text(encoding="utf-8")

    assert "Front Page" in content
    assert "Decoy Page" not in content


def test_build_index_category_prefix_empty_scope_shows_no_pages_yet(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    create.create_page(wiki_root=wiki_root, category="satchel", title="Satchel Overview")

    index_path = tmp_path / "FRONTIERMODE_WIKI.md"
    index.build_index(wiki_root, index_path, category_prefix="frontiermode")
    content = index_path.read_text(encoding="utf-8")

    assert "_No pages yet._" in content
    assert "Satchel Overview" not in content


def test_build_index_custom_title_overrides_heading(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    create.create_page(wiki_root=wiki_root, category="frontiermode", title="FM Overview")

    index_path = tmp_path / "FRONTIERMODE_WIKI.md"
    index.build_index(wiki_root, index_path, category_prefix="frontiermode", title="# FrontierMode Wiki")
    content = index_path.read_text(encoding="utf-8")

    assert content.startswith("# FrontierMode Wiki")
    assert "# Wiki Index" not in content


def test_build_index_default_category_prefix_includes_everything(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    create.create_page(wiki_root=wiki_root, category="frontiermode", title="FM Overview")
    create.create_page(wiki_root=wiki_root, category="satchel", title="Satchel Overview")

    index_path = tmp_path / "WIKI_INDEX.md"
    index.build_index(wiki_root, index_path)
    content = index_path.read_text(encoding="utf-8")

    assert "FM Overview" in content
    assert "Satchel Overview" in content


# --- defaults (seed_meta_wiki) ------------------------------------------------------------


def test_seed_meta_wiki_copies_pages(tmp_path: Path):
    source_wiki = tmp_path / "source_wiki"
    create.create_page(wiki_root=source_wiki, category="meta", title="BHT — Ticket Conventions", slug="bht")
    create.create_page(wiki_root=source_wiki, category="meta", title="BHW — Wiki Conventions", slug="bhw")

    dest_wiki = tmp_path / "dest_wiki"
    result = defaults.seed_meta_wiki(dest_wiki, source_wiki)

    assert set(result["created"]) == {"bht", "bhw"}
    assert result["skipped"] == []
    assert (dest_wiki / "meta" / "bht.md").exists()
    assert (dest_wiki / "meta" / "bhw.md").exists()


def test_seed_meta_wiki_never_overwrites_existing(tmp_path: Path):
    source_wiki = tmp_path / "source_wiki"
    create.create_page(wiki_root=source_wiki, category="meta", title="BHT — Ticket Conventions", slug="bht")

    dest_wiki = tmp_path / "dest_wiki"
    create.create_page(wiki_root=dest_wiki, category="meta", title="My Customized BHT Notes", slug="bht")
    original = (dest_wiki / "meta" / "bht.md").read_text(encoding="utf-8")

    result = defaults.seed_meta_wiki(dest_wiki, source_wiki)
    assert result["created"] == []
    assert result["skipped"] == ["bht"]
    assert (dest_wiki / "meta" / "bht.md").read_text(encoding="utf-8") == original


def test_seed_meta_wiki_raises_on_missing_source_category(tmp_path: Path):
    source_wiki = tmp_path / "source_wiki"
    source_wiki.mkdir()
    with pytest.raises(defaults.DefaultsError):
        defaults.seed_meta_wiki(tmp_path / "dest_wiki", source_wiki)


# --- header -------------------------------------------------------------------------------


def test_refresh_header_nested_category(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    path = create.create_page(wiki_root=wiki_root, category="reference/conventions", title="Style Guide")
    index_path = tmp_path / "WIKI_INDEX.md"

    index.refresh_header(path, index_path)
    content = path.read_text(encoding="utf-8")
    assert "[Dashboard](BACKHAUL.md)" in content
    assert "[Wiki Index](../../../WIKI_INDEX.md) · reference / conventions" in content


def test_refresh_header_is_idempotent(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    path = create.create_page(wiki_root=wiki_root, category="meta", title="About")
    index_path = tmp_path / "WIKI_INDEX.md"

    index.refresh_header(path, index_path)
    once = path.read_text(encoding="utf-8")
    index.refresh_header(path, index_path)
    twice = path.read_text(encoding="utf-8")
    assert once == twice
    assert "[Wiki Index](../../WIKI_INDEX.md) · meta" in once


def test_refresh_header_no_category_omits_trail(tmp_path: Path):
    wiki_root = tmp_path / "wiki"
    path = create.create_page(wiki_root=wiki_root, category="", title="Root Page")
    index_path = tmp_path / "WIKI_INDEX.md"

    index.refresh_header(path, index_path)
    content = path.read_text(encoding="utf-8")
    assert "[Wiki Index](../WIKI_INDEX.md)" in content
    assert "[Wiki Index](../WIKI_INDEX.md) ·" not in content
