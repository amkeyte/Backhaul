import json
from datetime import date
from pathlib import Path

import pytest

from backhaul.foundation import body_log, build_info, claude_link, client_registry, config, filesafety, frontmatter, handler_uri, header, host_paths, identity, markers, projects, rollup, slugify, templating


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


def test_frontmatter_parse_raises_parse_error_naming_file_on_bad_yaml(tmp_path: Path):
    # An unquoted colon-space scalar -- the exact real-world crash BH_020/BKHL_016 hit.
    p = tmp_path / "FRO_051_border-load-count-mismatch.md"
    p.write_text(
        "---\ntitle: Border load count: client vs server\nstatus: open\n---\nBody.\n",
        encoding="utf-8",
    )
    with pytest.raises(frontmatter.FrontmatterParseError) as excinfo:
        frontmatter.parse(p)
    assert "FRO_051" in str(excinfo.value)


def test_frontmatter_parse_error_is_a_frontmatter_error(tmp_path: Path):
    # Existing `except FrontmatterError` call sites (e.g. _cmd_refresh's per-file skip loops)
    # must keep working unchanged against the new, more specific subclass.
    p = tmp_path / "bad.md"
    p.write_text("---\ntitle: a: b\n---\nBody.\n", encoding="utf-8")
    with pytest.raises(frontmatter.FrontmatterError):
        frontmatter.parse(p)


def test_frontmatter_serialize_auto_quotes_colon_scalar():
    # The writer-side half of BH_020: confirms yaml.safe_dump already quotes a colon-space
    # scalar, so anything written through this module's own serialize() can't reproduce the
    # crash the two tests above cover -- only a hand-edited file can.
    doc = frontmatter.ParsedDoc(frontmatter={"title": "Border load count: client vs server"}, body="Body.\n")
    text = frontmatter.serialize(doc)
    assert "title: 'Border load count: client vs server'" in text


def test_identity_next_number():
    assert identity.next_number("UW", []) == 1
    assert identity.next_number("UW", [1, 2, 3]) == 4
    assert identity.next_number("UW", [1, 5, 2]) == 6


def test_numbered_identity_str():
    ident = identity.NumberedIdentity(uid="UW", number=2)
    assert str(ident) == "UW_002"


# --- client_registry (extracted so modules, not just services/ticket, can share it) --------


def test_client_registry_register_find_load_roundtrip(tmp_path: Path):
    reg_path = tmp_path / "client-uids.md"
    assert client_registry.load_registry(reg_path) == {}

    client_registry.register_uid(reg_path, "UW", "University of Washington")
    assert client_registry.load_registry(reg_path) == {"UW": "University of Washington"}
    assert client_registry.find_uid(reg_path, "university of washington") == "UW"
    assert client_registry.find_uid(reg_path, "Nobody") is None


def test_client_registry_conflicting_uid_raises(tmp_path: Path):
    reg_path = tmp_path / "client-uids.md"
    client_registry.register_uid(reg_path, "UW", "University of Washington")
    with pytest.raises(client_registry.RegistryError):
        client_registry.register_uid(reg_path, "UW", "Some Other Client")


def test_client_registry_suggest_uid():
    assert client_registry.suggest_uid("University of Washington") == "UW"
    assert client_registry.suggest_uid("General") == "GEN"
    assert client_registry.suggest_uid("Precision Electric") == "PE"


def test_ticket_registry_reexports_client_registry(tmp_path: Path):
    """services/ticket/registry.py must keep working against the same public API after the
    extraction — existing BHT code and tests import `registry.<name>` directly."""
    from backhaul.services.ticket import registry as ticket_registry

    reg_path = tmp_path / "client-uids.md"
    ticket_registry.register_uid(reg_path, "GEN", "General")
    assert ticket_registry.load_registry(reg_path) == {"GEN": "General"}
    assert ticket_registry.find_uid(reg_path, "General") == "GEN"


# --- header --------------------------------------------------------------------------------


def test_render_header_core_only():
    text = header.render_header(
        project_name="mcRepos", dashboard_rel="../../BACKHAUL.md",
        indexer_label="Board", indexer_rel="../BOARD.md",
    )
    assert text == "**mcRepos** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md)"


def test_render_header_with_extra():
    text = header.render_header(
        project_name="mcRepos", dashboard_rel="../../BACKHAUL.md",
        indexer_label="Board", indexer_rel="../BOARD.md",
        extra="[Folder](openfolder:///C:/x)",
    )
    assert text == "**mcRepos** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/x)"


def test_render_header_dashboard_only_omits_indexer():
    """An indexer page (BOARD.md/WIKI_INDEX.md/ROADMAP_INDEX.md) links back to the dashboard
    but has no indexer link to itself."""
    text = header.render_header(project_name="Fronthaul", dashboard_rel="BACKHAUL.md")
    assert text == "**Fronthaul** — [Dashboard](BACKHAUL.md)"


def test_render_header_neither_dashboard_nor_indexer():
    """The dashboard itself (BACKHAUL.md) has neither — it's already the top of the tree."""
    text = header.render_header(project_name="Backhaul")
    assert text == "**Backhaul**"


def test_render_header_indexer_only_omits_dashboard():
    text = header.render_header(project_name="mcRepos", indexer_label="Board", indexer_rel="../BOARD.md")
    assert text == "**mcRepos** — [Board](../BOARD.md)"


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
    tickets_root = str(tmp_path / "tickets")
    wiki_root = str(tmp_path / "wiki")
    p.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {"tickets": tickets_root, "wiki": wiki_root},
                "enabled_modules": ["docx"],
            }
        ),
        encoding="utf-8",
    )
    cfg = config.load_config(p)
    assert cfg["content_roots"]["tickets"] == tickets_root
    assert config.get_enabled_modules(cfg) == ["docx"]


def test_load_config_rejects_non_absolute_content_root(tmp_path: Path):
    # A Windows-style path loaded on this (POSIX) machine isn't absolute here — pathlib
    # treats it as one opaque relative segment, and every write this config drives would
    # silently land relative to cwd instead of touching real content. Refuse to load rather
    # than risk that — see foundation/config.py's load_config docstring/comment.
    p = tmp_path / "config.local.json"
    p.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": r"C:\_local\mcRepos\backhaul\tickets",
                    "wiki": r"C:\_local\mcRepos\backhaul\wiki",
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(config.ConfigError, match="aren't absolute on this machine"):
        config.load_config(p)


def test_load_config_accepts_when_only_some_roots_are_relative_but_still_flags_them(tmp_path: Path):
    p = tmp_path / "config.local.json"
    p.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": str(tmp_path / "tickets"),  # absolute — fine
                    "wiki": r"C:\_local\mcRepos\backhaul\wiki",  # not absolute here — flagged
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(config.ConfigError) as excinfo:
        config.load_config(p)
    assert "wiki=" in str(excinfo.value)
    assert "tickets=" not in str(excinfo.value)


# --- BACKHAUL_LOCAL_ROOT / _remap_content_roots ---------------------------------------------


def test_remap_content_roots_rejoins_onto_local_root(tmp_path: Path):
    content_roots = {
        "tickets": r"C:\_local\mcRepos\backhaul\tickets",
        "wiki": r"C:\_local\mcRepos\backhaul\wiki",
        "roles": r"C:\_local\mcRepos\backhaul\roles",
    }
    local_root = str(tmp_path / "mcRepos")
    remapped = config._remap_content_roots(content_roots, local_root)
    assert remapped["tickets"] == str(Path(local_root, "backhaul", "tickets"))
    assert remapped["wiki"] == str(Path(local_root, "backhaul", "wiki"))
    assert remapped["roles"] == str(Path(local_root, "backhaul", "roles"))


def test_remap_content_roots_leaves_value_outside_project_root_unchanged():
    content_roots = {
        "tickets": r"C:\_local\mcRepos\backhaul\tickets",
        "wiki": r"D:\somewhere\else\wiki",
    }
    remapped = config._remap_content_roots(content_roots, r"/sandbox/mcRepos")
    assert remapped["wiki"] == r"D:\somewhere\else\wiki"


def test_load_config_applies_local_root_param_before_absolute_check(tmp_path: Path):
    p = tmp_path / "config.local.json"
    p.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": r"C:\_local\mcRepos\backhaul\tickets",
                    "wiki": r"C:\_local\mcRepos\backhaul\wiki",
                },
            }
        ),
        encoding="utf-8",
    )
    local_root = tmp_path / "mnt-mcrepos"
    cfg = config.load_config(p, local_root=str(local_root))
    assert cfg["content_roots"]["tickets"] == str(local_root / "backhaul" / "tickets")
    assert cfg["content_roots"]["wiki"] == str(local_root / "backhaul" / "wiki")


def test_load_config_reads_local_root_from_env_var(tmp_path: Path, monkeypatch):
    p = tmp_path / "config.local.json"
    p.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": r"C:\_local\mcRepos\backhaul\tickets",
                    "wiki": r"C:\_local\mcRepos\backhaul\wiki",
                },
            }
        ),
        encoding="utf-8",
    )
    local_root = tmp_path / "mnt-mcrepos"
    monkeypatch.setenv(config.LOCAL_ROOT_ENV_VAR, str(local_root))
    cfg = config.load_config(p)
    assert cfg["content_roots"]["tickets"] == str(local_root / "backhaul" / "tickets")


def test_load_config_explicit_local_root_param_overrides_env_var(tmp_path: Path, monkeypatch):
    p = tmp_path / "config.local.json"
    p.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": r"C:\_local\mcRepos\backhaul\tickets",
                    "wiki": r"C:\_local\mcRepos\backhaul\wiki",
                },
            }
        ),
        encoding="utf-8",
    )
    env_root = tmp_path / "from-env"
    param_root = tmp_path / "from-param"
    monkeypatch.setenv(config.LOCAL_ROOT_ENV_VAR, str(env_root))
    cfg = config.load_config(p, local_root=str(param_root))
    assert cfg["content_roots"]["tickets"] == str(param_root / "backhaul" / "tickets")


# --- find_config_upward / resolve_config_path (BH_019) --------------------------------------


def test_find_config_upward_finds_backhaul_config_in_ancestor(tmp_path: Path):
    project_root = tmp_path / "mcRepos"
    (project_root / "backhaul").mkdir(parents=True)
    cfg_path = project_root / "backhaul" / "config.local.json"
    cfg_path.write_text("{}", encoding="utf-8")

    deep = project_root / "FrontierMode" / "src" / "main"
    deep.mkdir(parents=True)

    assert config.find_config_upward(deep) == cfg_path


def test_find_config_upward_finds_config_when_cwd_is_backhaul_dir_itself(tmp_path: Path):
    backhaul_dir = tmp_path / "mcRepos" / "backhaul"
    backhaul_dir.mkdir(parents=True)
    cfg_path = backhaul_dir / "config.local.json"
    cfg_path.write_text("{}", encoding="utf-8")

    assert config.find_config_upward(backhaul_dir) == cfg_path


def test_find_config_upward_returns_none_when_nothing_found(tmp_path: Path):
    somewhere = tmp_path / "unrelated" / "dir"
    somewhere.mkdir(parents=True)
    assert config.find_config_upward(somewhere) is None


def test_find_config_upward_does_not_match_backhaul_self_hosting_layout(tmp_path: Path):
    # This repo's own config lives at <root>/config/config.local.json, not
    # <root>/backhaul/config.local.json -- the search deliberately doesn't match that shape
    # (see find_config_upward's docstring); resolve_config_path's own hardcoded default covers
    # the self-hosting case instead.
    repo_root = tmp_path / "Backhaul"
    (repo_root / "config").mkdir(parents=True)
    (repo_root / "config" / "config.local.json").write_text("{}", encoding="utf-8")
    (repo_root / "backhaul").mkdir()

    assert config.find_config_upward(repo_root) is None


class _Args:
    def __init__(self, project=None, config=None):
        self.project = project
        self.config = config


def test_resolve_config_path_prefers_project_flag(tmp_path: Path):
    registry_path = tmp_path / "projects.json"
    target = tmp_path / "somewhere" / "config.local.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")
    registry_path.write_text(json.dumps({"mcrepos": str(target)}), encoding="utf-8")

    resolved = config.resolve_config_path(
        _Args(project="mcrepos"),
        default_config_path=tmp_path / "default.json",
        projects_path=registry_path,
    )
    assert resolved == target


def test_resolve_config_path_prefers_config_flag_over_upward_search(tmp_path: Path):
    explicit = tmp_path / "explicit.json"
    resolved = config.resolve_config_path(
        _Args(config=str(explicit)),
        default_config_path=tmp_path / "default.json",
        projects_path=tmp_path / "projects.json",
    )
    assert resolved == explicit


def test_resolve_config_path_falls_back_to_default_when_nothing_found(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    default = tmp_path / "default.json"
    resolved = config.resolve_config_path(
        _Args(), default_config_path=default, projects_path=tmp_path / "projects.json"
    )
    assert resolved == default


def test_resolve_config_path_uses_upward_search_when_no_flags_given(tmp_path: Path, monkeypatch):
    project_root = tmp_path / "mcRepos"
    (project_root / "backhaul").mkdir(parents=True)
    cfg_path = project_root / "backhaul" / "config.local.json"
    cfg_path.write_text("{}", encoding="utf-8")

    cwd = project_root / "FrontierMode"
    cwd.mkdir()
    monkeypatch.chdir(cwd)

    resolved = config.resolve_config_path(
        _Args(), default_config_path=tmp_path / "default.json", projects_path=tmp_path / "projects.json"
    )
    assert resolved == cfg_path


# --- body_log (BH_016) -----------------------------------------------------------------------


def test_append_log_entry_inserts_newest_first_after_blank_line():
    body = "## Log\n\n- 2026-08-16: Ticket opened.\n"
    result = body_log.append_log_entry(
        body, "Closed.", today=date(2026, 8, 28)
    )
    assert result == "## Log\n\n- 2026-08-28: Closed.\n- 2026-08-16: Ticket opened.\n"


def test_append_log_entry_full_ticket_body():
    body = "<!-- board:start -->\n<!-- board:end -->\n\n## Summary\n\nDo the thing.\n\n## Log\n\n- 2026-08-16: Ticket opened.\n"
    result = body_log.append_log_entry(body, "In progress.", today=date(2026, 8, 28))
    assert "## Summary\n\nDo the thing.\n\n## Log\n\n- 2026-08-28: In progress.\n- 2026-08-16: Ticket opened.\n" in result


def test_append_log_entry_multiline_indents_continuation():
    body = "## Log\n\n- 2026-08-16: Ticket opened.\n"
    result = body_log.append_log_entry(
        body, "First line.\nSecond line.", today=date(2026, 8, 28)
    )
    assert "- 2026-08-28: First line.\n  Second line.\n" in result


def test_append_log_entry_raises_when_heading_missing():
    body = "## Summary\n\nNo log section here.\n"
    with pytest.raises(body_log.BodyLogError):
        body_log.append_log_entry(body, "entry")


def test_append_log_entry_uses_todays_date_by_default():
    body = "## Log\n\n- 2026-08-16: Ticket opened.\n"
    result = body_log.append_log_entry(body, "entry")
    assert f"- {date.today().isoformat()}: entry\n" in result


def test_load_config_without_local_root_still_rejects_non_absolute(tmp_path: Path, monkeypatch):
    """No local_root param and no env var set — behavior is unchanged from before this feature
    existed (task #76's fail-loud check still applies)."""
    monkeypatch.delenv(config.LOCAL_ROOT_ENV_VAR, raising=False)
    p = tmp_path / "config.local.json"
    p.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "content_roots": {
                    "tickets": r"C:\_local\mcRepos\backhaul\tickets",
                    "wiki": r"C:\_local\mcRepos\backhaul\wiki",
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(config.ConfigError, match="aren't absolute on this machine"):
        config.load_config(p)


def test_load_config_rejects_schema_version_mismatch(tmp_path: Path):
    p = tmp_path / "config.local.json"
    p.write_text(
        json.dumps(
            {
                "version": "9.9.9",
                "content_roots": {"tickets": "T", "wiki": "W"},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(config.ConfigError):
        config.load_config(p)


def test_get_project_name_uses_explicit_value():
    cfg = {"content_roots": {"tickets": "X/Y/backhaul/tickets"}, "project_name": "mcRepos"}
    assert config.get_project_name(cfg) == "mcRepos"


def test_get_project_name_falls_back_to_grandparent_folder_name(tmp_path: Path):
    tickets_root = tmp_path / "SomeProject" / "backhaul" / "tickets"
    cfg = {"content_roots": {"tickets": str(tickets_root)}}
    assert config.get_project_name(cfg) == "SomeProject"


def test_get_repo_url_uses_explicit_value():
    cfg = {"repo_url": "https://github.com/amkeyte/Backhaul"}
    assert config.get_repo_url(cfg) == "https://github.com/amkeyte/Backhaul"


def test_get_repo_url_none_when_absent():
    assert config.get_repo_url({}) is None


def test_get_host_root_uses_explicit_value():
    cfg = {"host_root": r"C:\_local\mcRepos"}
    assert config.get_host_root(cfg) == r"C:\_local\mcRepos"


def test_get_host_root_none_when_absent():
    assert config.get_host_root({}) is None


# --- get_build_ready (BH_007) ---------------------------------------------------------------


def test_get_build_ready_none_when_absent():
    assert config.get_build_ready({}) is None


def test_get_build_ready_returns_ready():
    assert config.get_build_ready({"build_ready": "ready"}) == "ready"


def test_get_build_ready_returns_not_ready():
    assert config.get_build_ready({"build_ready": "notReady"}) == "notReady"


def test_get_build_ready_rejects_unknown_value():
    with pytest.raises(config.ConfigError):
        config.get_build_ready({"build_ready": "kinda"})


# --- host_paths.to_host_path --------------------------------------------------------------


def test_to_host_path_returns_unchanged_without_host_root():
    path = "/sessions/sandbox/mnt/mcRepos/backhaul/tickets/T_1.md"
    assert host_paths.to_host_path(path, runtime_root="/sessions/sandbox/mnt/mcRepos", host_root=None) == path


def test_to_host_path_translates_nested_file():
    path = "/sessions/sandbox/mnt/mcRepos/backhaul/roles/qa.md"
    result = host_paths.to_host_path(
        path, runtime_root="/sessions/sandbox/mnt/mcRepos", host_root=r"C:\_local\mcRepos"
    )
    assert result == r"C:\_local\mcRepos\backhaul\roles\qa.md"


def test_to_host_path_uses_forward_slash_when_host_root_looks_posix():
    path = "/sessions/sandbox/mnt/mcRepos/backhaul/roles/qa.md"
    result = host_paths.to_host_path(
        path, runtime_root="/sessions/sandbox/mnt/mcRepos", host_root="/real/mcRepos"
    )
    assert result == "/real/mcRepos/backhaul/roles/qa.md"


def test_to_host_path_strips_trailing_separator_from_host_root():
    path = "/sessions/sandbox/mnt/mcRepos/backhaul/roles/qa.md"
    result = host_paths.to_host_path(
        path, runtime_root="/sessions/sandbox/mnt/mcRepos", host_root="C:\\_local\\mcRepos\\"
    )
    assert result == r"C:\_local\mcRepos\backhaul\roles\qa.md"


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


# --- claude_link -------------------------------------------------------------------------


def test_build_cowork_link_prompt_only():
    link = claude_link.build_cowork_link("Hello there")
    assert link == "claude://cowork/new?q=Hello%20there"


def test_build_cowork_link_with_folder():
    link = claude_link.build_cowork_link("Do the thing", folder=r"C:\_local\source\LunaFlow_A")
    assert link == (
        "claude://cowork/new?q=Do%20the%20thing"
        "&folder=C%3A%5C_local%5Csource%5CLunaFlow_A"
    )


def test_build_cowork_link_encodes_newlines_and_special_chars():
    link = claude_link.build_cowork_link("Line one\nLine two & \"quoted\"")
    assert "%0A" in link
    assert "\n" not in link
    assert " " not in link.split("?q=", 1)[1]


def test_build_code_link_uses_code_host():
    link = claude_link.build_code_link("fix the bug", folder=r"C:\repo")
    assert link.startswith("claude://code/new?q=fix%20the%20bug")
    assert "folder=C%3A%5Crepo" in link


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


# --- build_info (--version / branch-identification convention) -----------------------------


def test_get_git_info_returns_none_when_git_reports_not_a_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import subprocess as _subprocess

    class _FakeResult:
        returncode = 128
        stdout = ""

    monkeypatch.setattr(_subprocess, "run", lambda *a, **k: _FakeResult())
    assert build_info.get_git_info(tmp_path) == (None, None)


def test_get_git_info_returns_branch_and_commit_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import subprocess as _subprocess

    calls = iter([
        type("R", (), {"returncode": 0, "stdout": "dev\n"})(),
        type("R", (), {"returncode": 0, "stdout": "abc1234\n"})(),
    ])
    monkeypatch.setattr(_subprocess, "run", lambda *a, **k: next(calls))
    assert build_info.get_git_info(tmp_path) == ("dev", "abc1234")


def test_get_git_info_handles_missing_git_binary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import subprocess as _subprocess

    def _raise(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(_subprocess, "run", _raise)
    assert build_info.get_git_info(tmp_path) == (None, None)


def test_format_version_string_includes_prog_and_package_version():
    s = build_info.format_version_string("bht")
    assert s.startswith("bht ")
    assert build_info.PACKAGE_VERSION in s


def test_format_version_string_omits_git_info_when_unavailable(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(build_info, "get_git_info", lambda *a, **k: (None, None))
    s = build_info.format_version_string("bht")
    assert s == f"bht {build_info.PACKAGE_VERSION}"
    assert "@" not in s
