"""Unit tests for foundation.lint, against synthetic tmp_path content roots — no real content.
Covers both v1 checks (orphaned pages, broken links) plus the config-root gating (roadmap/roles
only counted when both configured and enabled, mirroring dashboard.py's own gating).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backhaul.foundation import lint


def _write(path: Path, text: str = "# doc\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _config(tmp_path: Path, *, enabled_modules: list | None = None, with_roadmap=False, with_roles=False) -> dict:
    content_roots = {
        "tickets": str(tmp_path / "backhaul" / "tickets"),
        "wiki": str(tmp_path / "backhaul" / "wiki"),
    }
    if with_roadmap:
        content_roots["roadmap"] = str(tmp_path / "backhaul" / "roadmap")
    if with_roles:
        content_roots["roles"] = str(tmp_path / "backhaul" / "roles")
    return {
        "version": "0.1.0",
        "content_roots": content_roots,
        "enabled_modules": enabled_modules or [],
    }


# --- orphaned pages --------------------------------------------------------------------------


def test_find_orphaned_satisfied_by_an_inbound_link(tmp_path: Path):
    wiki = tmp_path / "backhaul" / "wiki"
    _write(wiki / "meta" / "hub.md", "# Hub\n\n[Target](../overview/target.md)\n")
    _write(wiki / "overview" / "target.md", "# Target\n\n[Back](../meta/hub.md)\n")

    cfg = _config(tmp_path)
    # Each page links to the other -> neither is an orphan.
    assert lint.run_lint(cfg, checks=["orphaned"]) == []


def test_find_orphaned_flags_a_page_nothing_links_to(tmp_path: Path):
    wiki = tmp_path / "backhaul" / "wiki"
    _write(wiki / "meta" / "hub.md", "# Hub\n\n[Target](../overview/target.md)\n")
    _write(wiki / "overview" / "target.md", "# Target\n")
    _write(wiki / "overview" / "lonely.md", "# Lonely\n")  # nothing points at this one

    cfg = _config(tmp_path)
    findings = lint.run_lint(cfg, checks=["orphaned"])
    orphan_names = {f.path.name for f in findings}
    # hub.md is never linked TO (only from) -> also legitimately orphaned.
    assert orphan_names == {"hub.md", "lonely.md"}


def test_find_orphaned_exempts_client_uids_registry(tmp_path: Path):
    tickets = tmp_path / "backhaul" / "tickets"
    _write(tickets / "client-uids.md", "# Registry\n")
    _write(tickets / "BH_001_foo.md", "# BH_001\n")  # not linked from anywhere either

    cfg = _config(tmp_path)
    findings = lint.run_lint(cfg, checks=["orphaned"])
    orphan_names = {f.path.name for f in findings}
    assert "client-uids.md" not in orphan_names
    assert "BH_001_foo.md" in orphan_names  # a real ticket with no inbound link IS a finding


def test_find_orphaned_cross_root_link_counts(tmp_path: Path):
    """A ticket linking to a wiki page (or vice versa) satisfies the wiki page's orphan check —
    this is exactly why lint walks every content root together, not one service at a time."""
    tickets = tmp_path / "backhaul" / "tickets"
    wiki = tmp_path / "backhaul" / "wiki"
    _write(tickets / "BH_001_foo.md", "# BH_001\n\n[Design](../wiki/design/plan.md)\n")
    _write(wiki / "design" / "plan.md", "# Plan\n")

    cfg = _config(tmp_path)
    findings = lint.run_lint(cfg, checks=["orphaned"])
    orphan_names = {f.path.name for f in findings}
    # plan.md IS linked (from the ticket, a different content root) -> not an orphan.
    assert "plan.md" not in orphan_names
    # BH_001 itself has no inbound link from anywhere -> still a legitimate finding.
    assert "BH_001_foo.md" in orphan_names


# --- broken links -----------------------------------------------------------------------------


def test_find_broken_links_flags_missing_target(tmp_path: Path):
    wiki = tmp_path / "backhaul" / "wiki"
    _write(wiki / "meta" / "page.md", "# Page\n\n[Missing](../overview/nope.md)\n")

    cfg = _config(tmp_path)
    findings = lint.run_lint(cfg, checks=["links"])
    assert len(findings) == 1
    assert findings[0].check == "links"
    assert "nope.md" in findings[0].message


def test_find_broken_links_allows_existing_target(tmp_path: Path):
    wiki = tmp_path / "backhaul" / "wiki"
    _write(wiki / "meta" / "page.md", "# Page\n\n[Real](../overview/real.md)\n")
    _write(wiki / "overview" / "real.md", "# Real\n")

    cfg = _config(tmp_path)
    assert lint.run_lint(cfg, checks=["links"]) == []


def test_find_broken_links_ignores_non_local_schemes(tmp_path: Path):
    wiki = tmp_path / "backhaul" / "wiki"
    _write(
        wiki / "meta" / "page.md",
        "# Page\n\n"
        "[Web](https://example.com/x)\n"
        "[Mail](mailto:a@b.com)\n"
        "[Edit](editmd:///C:/nope/at/all.md)\n"
        "[Folder](openfolder:///C:/also/nope)\n",
    )

    cfg = _config(tmp_path)
    assert lint.run_lint(cfg, checks=["links"]) == []


def test_find_broken_links_handles_anchor_fragments(tmp_path: Path):
    wiki = tmp_path / "backhaul" / "wiki"
    _write(wiki / "meta" / "page.md", "# Page\n\n[Self anchor](#section)\n[Real anchor](../overview/real.md#top)\n")
    _write(wiki / "overview" / "real.md", "# Real\n")

    cfg = _config(tmp_path)
    assert lint.run_lint(cfg, checks=["links"]) == []


# --- content-root gating (mirrors dashboard.py's roadmap/roles gating) -----------------------


def test_roadmap_root_only_scanned_when_enabled_and_configured(tmp_path: Path):
    _write(tmp_path / "backhaul" / "roadmap" / "RM_X_001_lonely.md", "# lonely node\n")

    # content_root present, module NOT enabled -> not scanned, no finding.
    cfg = _config(tmp_path, with_roadmap=True, enabled_modules=[])
    assert lint.run_lint(cfg, checks=["orphaned"]) == []

    # module enabled, content_root missing -> not scanned either.
    cfg = _config(tmp_path, with_roadmap=False, enabled_modules=["roadmap"])
    assert lint.run_lint(cfg, checks=["orphaned"]) == []

    # both -> scanned, orphan found.
    cfg = _config(tmp_path, with_roadmap=True, enabled_modules=["roadmap"])
    findings = lint.run_lint(cfg, checks=["orphaned"])
    assert any(f.path.name == "RM_X_001_lonely.md" for f in findings)


# --- run_lint dispatch -------------------------------------------------------------------------


def test_run_lint_defaults_to_all_checks(tmp_path: Path):
    wiki = tmp_path / "backhaul" / "wiki"
    _write(wiki / "meta" / "lonely.md", "# Lonely\n")
    _write(wiki / "meta" / "broken.md", "# Broken\n\n[Nope](nope.md)\n")

    cfg = _config(tmp_path)
    findings = lint.run_lint(cfg)
    checks_seen = {f.check for f in findings}
    assert checks_seen == {"orphaned", "links"}


def test_run_lint_rejects_unknown_check(tmp_path: Path):
    cfg = _config(tmp_path)
    with pytest.raises(lint.LintError):
        lint.run_lint(cfg, checks=["not-a-real-check"])


def test_run_lint_findings_are_sorted(tmp_path: Path):
    wiki = tmp_path / "backhaul" / "wiki"
    _write(wiki / "b" / "second.md", "# second\n")
    _write(wiki / "a" / "first.md", "# first\n")

    cfg = _config(tmp_path)
    findings = lint.run_lint(cfg, checks=["orphaned"])
    paths = [str(f.path) for f in findings]
    assert paths == sorted(paths)


def test_finding_to_dict_and_str(tmp_path: Path):
    wiki = tmp_path / "backhaul" / "wiki"
    _write(wiki / "meta" / "lonely.md", "# Lonely\n")

    cfg = _config(tmp_path)
    findings = lint.run_lint(cfg, checks=["orphaned"])
    assert len(findings) == 1
    d = findings[0].to_dict()
    assert d["check"] == "orphaned"
    assert d["file"].endswith("lonely.md")
    assert json.dumps(d)  # round-trips through json without error
    assert "orphaned:" in str(findings[0])
