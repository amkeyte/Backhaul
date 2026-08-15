"""Tests for modules/roadmap (BHRM) — schema, node creation, and graph queries.

Only synthetic fixtures under tmp_path are used here, never real content, per
migration/PYTHON_PROJECT_SETUP.md's fixtures note.
"""

from pathlib import Path

import pytest

from backhaul.foundation import frontmatter as _frontmatter
from backhaul.modules.roadmap import create as _create
from backhaul.modules.roadmap import graph as _graph
from backhaul.modules.roadmap import header as _header
from backhaul.modules.roadmap.schema import RoadmapValidationError, validate


def _write_node(
    root: Path,
    uid: str,
    number: int,
    *,
    kind: str = "work",
    status: str = "open",
    title: str = "A node",
    owner: str = "Owner",
    depends_on: list[str] | None = None,
    slug: str | None = None,
    superseded_by: str | None = None,
    corrupt: bool = False,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    node_id = f"{uid}_{number:03d}"
    filename = f"{node_id}_{slug}.md" if slug else f"{node_id}.md"
    path = root / filename

    if corrupt:
        path.write_text("not a valid frontmatter file at all\n", encoding="utf-8")
        return path

    fm: dict = {
        "id": node_id,
        "uid": uid,
        "number": number,
        "kind": kind,
        "status": status,
        "title": title,
        "owner": owner,
        "depends_on": depends_on or [],
    }
    if superseded_by:
        fm["superseded_by"] = superseded_by

    doc = _frontmatter.ParsedDoc(frontmatter=fm, body=f"\n{title}\n", path=path)
    _frontmatter.write(doc)
    return path


# --- schema ----------------------------------------------------------------------------


def test_validate_accepts_work_node():
    node = validate(
        {
            "uid": "RM_ARR",
            "number": 1,
            "kind": "work",
            "status": "open",
            "title": "Set up the shed",
            "owner": "Arryn",
        }
    )
    assert node.id == "RM_ARR_001"
    assert node.status == "open"
    assert node.depends_on == []


def test_validate_accepts_convergence_node():
    node = validate(
        {
            "uid": "RM_ARR",
            "number": 2,
            "kind": "convergence",
            "status": "WIP",
            "title": "House move-in ready",
            "owner": "Arryn",
            "depends_on": ["RM_ARR_001"],
        }
    )
    assert node.kind == "convergence"
    assert node.depends_on == ["RM_ARR_001"]


def test_validate_rejects_missing_fields():
    with pytest.raises(RoadmapValidationError):
        validate({"uid": "RM_ARR", "number": 1, "kind": "work", "status": "open"})


def test_validate_rejects_unknown_kind():
    with pytest.raises(RoadmapValidationError):
        validate(
            {
                "uid": "RM_ARR",
                "number": 1,
                "kind": "sidequest",
                "status": "open",
                "title": "X",
                "owner": "Arryn",
            }
        )


def test_validate_rejects_status_not_valid_for_kind():
    # "reached" is a convergence-only status; invalid on a work node.
    with pytest.raises(RoadmapValidationError):
        validate(
            {
                "uid": "RM_ARR",
                "number": 1,
                "kind": "work",
                "status": "reached",
                "title": "X",
                "owner": "Arryn",
            }
        )
    # "open" is a work-only status; invalid on a convergence node.
    with pytest.raises(RoadmapValidationError):
        validate(
            {
                "uid": "RM_ARR",
                "number": 1,
                "kind": "convergence",
                "status": "open",
                "title": "X",
                "owner": "Arryn",
            }
        )


def test_validate_superseded_requires_superseded_by():
    with pytest.raises(RoadmapValidationError):
        validate(
            {
                "uid": "RM_ARR",
                "number": 1,
                "kind": "work",
                "status": "superseded",
                "title": "X",
                "owner": "Arryn",
            }
        )

    node = validate(
        {
            "uid": "RM_ARR",
            "number": 1,
            "kind": "work",
            "status": "superseded",
            "title": "X",
            "owner": "Arryn",
            "superseded_by": "RM_ARR_002",
        }
    )
    assert node.superseded_by == "RM_ARR_002"


def test_validate_rejects_bad_depends_on_shape():
    with pytest.raises(RoadmapValidationError):
        validate(
            {
                "uid": "RM_ARR",
                "number": 1,
                "kind": "work",
                "status": "open",
                "title": "X",
                "owner": "Arryn",
                "depends_on": "RM_ARR_002",  # must be a list, not a bare string
            }
        )


# --- graph -------------------------------------------------------------------------------


def test_load_graph_basic(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="Root")
    _write_node(root, "RM_TST", 2, title="Second", depends_on=["RM_TST_001"])

    nodes = _graph.load_graph(root, "RM_TST")
    assert set(nodes) == {"RM_TST_001", "RM_TST_002"}
    assert nodes["RM_TST_002"].depends_on == ["RM_TST_001"]


def test_load_graph_ignores_other_uids(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="Mine")
    _write_node(root, "RM_OTHER", 1, title="Not mine")

    nodes = _graph.load_graph(root, "RM_TST")
    assert set(nodes) == {"RM_TST_001"}


def test_cycle_detection(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="A", depends_on=["RM_TST_003"])
    _write_node(root, "RM_TST", 2, title="B", depends_on=["RM_TST_001"])
    _write_node(root, "RM_TST", 3, title="C", depends_on=["RM_TST_002"])

    nodes = _graph.load_graph(root, "RM_TST")
    with pytest.raises(_graph.GraphError, match="Cycle detected"):
        _graph.validate_graph(nodes)


def test_frontier(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="Root", status="resolved")
    _write_node(root, "RM_TST", 2, title="Actionable", depends_on=["RM_TST_001"])
    _write_node(root, "RM_TST", 3, title="Blocked", status="open", depends_on=["RM_TST_002"])
    _write_node(
        root, "RM_TST", 4, title="Milestone", kind="convergence", status="WIP",
        depends_on=["RM_TST_002"],
    )

    nodes = _graph.load_graph(root, "RM_TST")
    assert _graph.frontier(nodes) == ["RM_TST_002"]


def test_downstream_transitive_closure(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="A")
    _write_node(root, "RM_TST", 2, title="B", depends_on=["RM_TST_001"])
    _write_node(root, "RM_TST", 3, title="C", depends_on=["RM_TST_002"])
    _write_node(root, "RM_TST", 4, title="D", depends_on=["RM_TST_003"])

    nodes = _graph.load_graph(root, "RM_TST")
    assert _graph.downstream(nodes, "RM_TST_001") == ["RM_TST_002", "RM_TST_003", "RM_TST_004"]


def test_dependents_is_direct_only(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="A")
    _write_node(root, "RM_TST", 2, title="B", depends_on=["RM_TST_001"])
    _write_node(root, "RM_TST", 3, title="C", depends_on=["RM_TST_002"])

    nodes = _graph.load_graph(root, "RM_TST")
    assert _graph.dependents(nodes, "RM_TST_001") == ["RM_TST_002"]


def test_blocking_lists_unsatisfied_ancestors(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="A", status="open")
    _write_node(root, "RM_TST", 2, title="B", status="resolved", depends_on=["RM_TST_001"])
    _write_node(root, "RM_TST", 3, title="C", depends_on=["RM_TST_002"])

    nodes = _graph.load_graph(root, "RM_TST")
    assert _graph.blocking(nodes, "RM_TST_003") == ["RM_TST_001"]


def test_render_lists_actionable_first(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="Doable")

    nodes = _graph.load_graph(root, "RM_TST")
    text = _graph.render(nodes)
    assert "## Actionable now" in text
    assert "RM_TST_001" in text
    assert "Doable" in text


def test_render_links_node_ids_to_their_files(tmp_path: Path):
    root = tmp_path / "roadmap"
    path = _write_node(root, "RM_TST", 1, title="Doable", slug="alma")

    nodes = _graph.load_graph(root, "RM_TST")
    # output_dir = tmp_path (one level above roadmap/) — matches the real ROADMAP.md convention.
    text = _graph.render(nodes, output_dir=tmp_path)
    assert f"[**RM_TST_001**](roadmap/{path.name})" in text
    # Appears twice: once in "Actionable now", once in "Dependency structure".
    assert text.count(f"](roadmap/{path.name})") == 2


def test_render_default_output_dir_is_first_nodes_own_directory(tmp_path: Path):
    root = tmp_path / "roadmap"
    path = _write_node(root, "RM_TST", 1, title="Doable", slug="alma")

    nodes = _graph.load_graph(root, "RM_TST")
    text = _graph.render(nodes)  # no output_dir given
    assert f"[**RM_TST_001**]({path.name})" in text


def test_render_index_links_node_ids_to_their_files(tmp_path: Path):
    root = tmp_path / "roadmap"
    path = _write_node(root, "RM_FRO", 1, title="FM root", slug="scaffold")

    text = _graph.render_index(root)  # default output_dir = root.parent = tmp_path
    assert f"[**RM_FRO_001**](roadmap/{path.name})" in text


def test_export_json_roundtrips_nodes_and_edges(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="A")
    _write_node(root, "RM_TST", 2, title="B", depends_on=["RM_TST_001"])

    nodes = _graph.load_graph(root, "RM_TST")
    payload = _graph.export_json(nodes)
    ids = {n["id"] for n in payload["nodes"]}
    assert ids == {"RM_TST_001", "RM_TST_002"}
    assert {"from": "RM_TST_002", "to": "RM_TST_001"} in payload["edges"]


def test_malformed_node_file_is_a_hard_error_not_a_silent_skip(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="Good")
    _write_node(root, "RM_TST", 2, corrupt=True)

    with pytest.raises(_graph.GraphError):
        _graph.load_graph(root, "RM_TST")


def test_dangling_depends_on_is_an_error(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="A", depends_on=["RM_TST_099"])

    with pytest.raises(_graph.GraphError, match="does not exist"):
        _graph.load_graph(root, "RM_TST")


def test_cross_uid_depends_on_is_rejected(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_FRO", 1, title="Frontier root")
    _write_node(root, "RM_SAT", 1, title="Satchel node", depends_on=["RM_FRO_001"])

    with pytest.raises(_graph.GraphError, match="different UID"):
        _graph.load_graph(root, "RM_SAT")


def test_duplicate_id_is_an_error(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="First", slug="a")
    _write_node(root, "RM_TST", 1, title="Duplicate", slug="b")

    with pytest.raises(_graph.GraphError, match="duplicate node ID"):
        _graph.load_graph(root, "RM_TST")


# --- create_node -------------------------------------------------------------------------


def test_create_node_mints_uid_and_registers_client(tmp_path: Path):
    nodes_root = tmp_path / "roadmap"
    registry_path = tmp_path / "client-uids.md"

    path = _create.create_node(
        nodes_root=nodes_root,
        registry_path=registry_path,
        client="Arryn",
        title="Set up the shed",
        owner="Arryn",
    )
    assert path.exists()
    assert path.name.startswith("RM_ARR_001_")

    doc = _frontmatter.parse(path)
    assert doc.frontmatter["id"] == "RM_ARR_001"
    assert doc.frontmatter["uid"] == "RM_ARR"
    assert doc.frontmatter["status"] == "open"
    assert doc.frontmatter["kind"] == "work"

    from backhaul.foundation import client_registry

    assert client_registry.load_registry(registry_path) == {"ARR": "Arryn"}


def test_create_node_shares_client_registry_with_tickets(tmp_path: Path):
    """base_uid comes from the same client-uids.md BHT already uses, so "ARR" means the same
    client for both a ticket and a roadmap node — registering it once via BHT is enough."""
    from backhaul.foundation import client_registry

    registry_path = tmp_path / "client-uids.md"
    client_registry.register_uid(registry_path, "ARR", "Arryn")

    nodes_root = tmp_path / "roadmap"
    path = _create.create_node(
        nodes_root=nodes_root,
        registry_path=registry_path,
        client="Arryn",
        title="Reuse the existing UID",
        owner="Arryn",
    )
    assert path.name.startswith("RM_ARR_001_")


def test_create_node_sequential_numbering_per_uid(tmp_path: Path):
    nodes_root = tmp_path / "roadmap"
    registry_path = tmp_path / "client-uids.md"

    first = _create.create_node(
        nodes_root=nodes_root, registry_path=registry_path, client="Arryn",
        title="First", owner="Arryn",
    )
    second = _create.create_node(
        nodes_root=nodes_root, registry_path=registry_path, client="Arryn",
        title="Second", owner="Arryn",
    )
    assert first.name.startswith("RM_ARR_001_")
    assert second.name.startswith("RM_ARR_002_")


def test_create_node_convergence_defaults_to_wip(tmp_path: Path):
    nodes_root = tmp_path / "roadmap"
    registry_path = tmp_path / "client-uids.md"

    path = _create.create_node(
        nodes_root=nodes_root, registry_path=registry_path, client="Arryn",
        title="House move-in ready", owner="Arryn", kind="convergence",
    )
    doc = _frontmatter.parse(path)
    assert doc.frontmatter["status"] == "WIP"


def test_create_node_same_title_twice_gets_distinct_files(tmp_path: Path):
    """Sequential numbering means two nodes with the same title never collide on disk —
    filesafety's overwrite guard is a defensive backstop, not something normal usage hits."""
    nodes_root = tmp_path / "roadmap"
    registry_path = tmp_path / "client-uids.md"

    first = _create.create_node(
        nodes_root=nodes_root, registry_path=registry_path, client="Arryn",
        title="Same title", owner="Arryn",
    )
    second = _create.create_node(
        nodes_root=nodes_root, registry_path=registry_path, client="Arryn",
        title="Same title", owner="Arryn",
    )
    assert first != second
    assert first.exists() and second.exists()


def test_create_node_slug_override(tmp_path: Path):
    nodes_root = tmp_path / "roadmap"
    registry_path = tmp_path / "client-uids.md"

    path = _create.create_node(
        nodes_root=nodes_root, registry_path=registry_path, client="Arryn",
        title="A much longer descriptive title than the code needs", owner="Arryn",
        slug="alma",
    )
    assert path.name == "RM_ARR_001_alma.md"


def test_create_node_slug_is_sanitized(tmp_path: Path):
    nodes_root = tmp_path / "roadmap"
    registry_path = tmp_path / "client-uids.md"

    path = _create.create_node(
        nodes_root=nodes_root, registry_path=registry_path, client="Arryn",
        title="Whatever", owner="Arryn", slug="Not A Clean Slug!!",
    )
    assert path.name == "RM_ARR_001_not-a-clean-slug.md"


def test_created_node_validates_and_loads_in_graph(tmp_path: Path):
    """A freshly created node must be a well-formed node from graph.load_graph's point of view
    too — not just pass schema.validate() in isolation."""
    nodes_root = tmp_path / "roadmap"
    registry_path = tmp_path / "client-uids.md"

    _create.create_node(
        nodes_root=nodes_root, registry_path=registry_path, client="Arryn",
        title="Root node", owner="Arryn",
    )
    nodes = _graph.load_graph(nodes_root, "RM_ARR")
    assert list(nodes) == ["RM_ARR_001"]


# --- render_index / discover_uids / build_index ------------------------------------------


def test_discover_uids_across_multiple_graphs(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_FRO", 1, title="FM root")
    _write_node(root, "RM_SAT", 1, title="Satchel root")
    _write_node(root, "RM_SAT", 2, title="Satchel second", depends_on=["RM_SAT_001"])

    assert _graph.discover_uids(root) == ["RM_FRO", "RM_SAT"]


def test_discover_uids_empty_dir_returns_empty(tmp_path: Path):
    assert _graph.discover_uids(tmp_path / "does-not-exist") == []


def test_render_index_sections_each_graph_separately(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_FRO", 1, title="FM root")
    _write_node(root, "RM_SAT", 1, title="Satchel root")

    text = _graph.render_index(root)
    assert "## RM_FRO" in text
    assert "## RM_SAT" in text
    assert "FM root" in text
    assert "Satchel root" in text
    # Graphs are sectioned, not merged: FRO's own subsection appears before SAT's.
    assert text.index("## RM_FRO") < text.index("## RM_SAT")


def test_render_index_links_html_graph_view_when_present(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_FRO", 1, title="FM root")

    # The conventional filename, sitting next to where the index itself renders to.
    (root.parent / _graph.html_graph_filename("RM_FRO")).write_text("<html></html>", encoding="utf-8")

    text = _graph.render_index(root)  # default output_dir = root.parent = tmp_path
    assert "**Graph view:** [Open in browser ↗](ROADMAP_GRAPH_RM_FRO.html)" in text


def test_render_index_omits_html_link_when_absent(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_FRO", 1, title="FM root")

    text = _graph.render_index(root)
    assert "Graph view" not in text


def test_render_index_html_link_is_per_uid(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_FRO", 1, title="FM root")
    _write_node(root, "RM_SAT", 1, title="Satchel root")

    (root.parent / _graph.html_graph_filename("RM_FRO")).write_text("<html></html>", encoding="utf-8")
    # No RM_SAT html file written.

    text = _graph.render_index(root)
    fro_section = text[text.index("## RM_FRO"):text.index("## RM_SAT")]
    sat_section = text[text.index("## RM_SAT"):]
    assert "Graph view" in fro_section
    assert "Graph view" not in sat_section


def test_render_index_no_graphs_yet(tmp_path: Path):
    root = tmp_path / "roadmap"
    root.mkdir()
    text = _graph.render_index(root)
    assert "_No roadmap graphs yet._" in text


def test_build_index_writes_and_overwrites(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_FRO", 1, title="FM root")

    out = tmp_path / "ROADMAP_INDEX.md"
    _graph.build_index(root, out)
    first = out.read_text(encoding="utf-8")
    assert "RM_FRO_001" in first

    _graph.build_index(root, out)  # should not raise UnsafeWriteError
    assert out.read_text(encoding="utf-8") == first


def test_build_index_omits_header_without_dashboard_path(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_FRO", 1, title="FM root")

    out = tmp_path / "ROADMAP_INDEX.md"
    _graph.build_index(root, out)
    assert "bh-header" not in out.read_text(encoding="utf-8")


def test_build_index_includes_header_with_dashboard_path(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_FRO", 1, title="FM root")

    out = tmp_path / "ROADMAP_INDEX.md"
    dashboard_path = tmp_path / "BACKHAUL.md"
    _graph.build_index(root, out, dashboard_path=dashboard_path, project_name="mcRepos")

    content = out.read_text(encoding="utf-8")
    assert content.startswith("<!-- bh-header:start -->")
    assert "**mcRepos** — [Dashboard](BACKHAUL.md)" in content


def test_build_index_custom_title(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_FRO", 1, title="FM root")

    out = tmp_path / "ROADMAP_INDEX.md"
    _graph.build_index(root, out, title="# mcRepos Roadmaps")
    assert out.read_text(encoding="utf-8").startswith("# mcRepos Roadmaps")


# --- render_html -----------------------------------------------------------------------------


def test_html_layout_orders_by_depth_then_id(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="A")
    _write_node(root, "RM_TST", 2, title="B", depends_on=["RM_TST_001"])
    _write_node(root, "RM_TST", 3, title="C", depends_on=["RM_TST_001"])

    nodes = _graph.load_graph(root, "RM_TST")
    positions, canvas_width, canvas_height = _graph._html_layout(nodes)

    # Depth 0 (RM_TST_001) is strictly left of depth 1 (RM_TST_002/003).
    assert positions["RM_TST_001"][0] < positions["RM_TST_002"][0]
    assert positions["RM_TST_001"][0] < positions["RM_TST_003"][0]
    # Same depth -> same x, ordered by ID within the layer (002 above 003).
    assert positions["RM_TST_002"][0] == positions["RM_TST_003"][0]
    assert positions["RM_TST_002"][1] < positions["RM_TST_003"][1]
    assert canvas_width > 0 and canvas_height > 0


def test_html_layout_is_deterministic(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="A")
    _write_node(root, "RM_TST", 2, title="B", depends_on=["RM_TST_001"])

    nodes = _graph.load_graph(root, "RM_TST")
    first = _graph.render_html(nodes)
    second = _graph.render_html(nodes)
    assert first == second


def test_html_color_work_resolved_is_green():
    node = _graph.Node(
        frontmatter=validate({
            "uid": "RM_TST", "number": 1, "kind": "work", "status": "resolved",
            "title": "X", "owner": "O",
        }),
        path=Path("x.md"),
    )
    fill, stroke, dash = _graph._html_color(node, actionable=False)
    assert fill == "#2e7d4a"
    assert dash == ""


def test_html_color_work_superseded_is_green():
    node = _graph.Node(
        frontmatter=validate({
            "uid": "RM_TST", "number": 1, "kind": "work", "status": "superseded",
            "title": "X", "owner": "O", "superseded_by": "RM_TST_002",
        }),
        path=Path("x.md"),
    )
    fill, _, _ = _graph._html_color(node, actionable=False)
    assert fill == "#2e7d4a"


def test_html_color_work_open_actionable_is_blue():
    node = _graph.Node(
        frontmatter=validate({
            "uid": "RM_TST", "number": 1, "kind": "work", "status": "open",
            "title": "X", "owner": "O",
        }),
        path=Path("x.md"),
    )
    fill, _, _ = _graph._html_color(node, actionable=True)
    assert fill == "#1565c0"


def test_html_color_work_open_blocked_is_gray():
    node = _graph.Node(
        frontmatter=validate({
            "uid": "RM_TST", "number": 1, "kind": "work", "status": "open",
            "title": "X", "owner": "O",
        }),
        path=Path("x.md"),
    )
    fill, _, _ = _graph._html_color(node, actionable=False)
    assert fill == "#4a4f58"


def test_html_color_convergence_reached_is_gold_solid():
    node = _graph.Node(
        frontmatter=validate({
            "uid": "RM_TST", "number": 1, "kind": "convergence", "status": "reached",
            "title": "X", "owner": "O",
        }),
        path=Path("x.md"),
    )
    fill, _, dash = _graph._html_color(node, actionable=False)
    assert fill == "#b8860b"
    assert dash == ""


def test_html_color_convergence_wip_is_orange_dashed():
    node = _graph.Node(
        frontmatter=validate({
            "uid": "RM_TST", "number": 1, "kind": "convergence", "status": "WIP",
            "title": "X", "owner": "O",
        }),
        path=Path("x.md"),
    )
    fill, _, dash = _graph._html_color(node, actionable=False)
    assert fill == "#a3450f"
    assert dash != ""


def test_render_html_contains_every_node_id_and_svg(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="Root")
    _write_node(root, "RM_TST", 2, title="Second", depends_on=["RM_TST_001"])

    nodes = _graph.load_graph(root, "RM_TST")
    html = _graph.render_html(nodes)
    assert "<svg" in html and "</svg>" in html
    assert 'data-id="RM_TST_001"' in html
    assert 'data-id="RM_TST_002"' in html
    assert "Root" in html and "Second" in html


def test_render_html_edge_drawn_prerequisite_to_dependent(tmp_path: Path):
    """The prerequisite (lower depth, RM_TST_001) must be the visual source, the dependent
    (RM_TST_002) the visual target — reversed from export_json's raw from/to field names, which
    are {"from": dependent, "to": prerequisite}. See BH_005's Design section."""
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="Root")
    _write_node(root, "RM_TST", 2, title="Second", depends_on=["RM_TST_001"])

    nodes = _graph.load_graph(root, "RM_TST")
    positions, _, _ = _graph._html_layout(nodes)
    sx, sy, sw, sh = positions["RM_TST_001"]
    tx, ty, tw, th = positions["RM_TST_002"]
    expected_x1 = f"{sx + sw:g}"
    expected_x2 = f"{tx:g}"

    html = _graph.render_html(nodes)
    # The edge path's "M{x1},{y1}" start and final "{x2},{y2}" end.
    assert f"M{expected_x1}," in html
    assert f" {expected_x2},{ty + th / 2:g}" in html


def test_render_html_title_override(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="Root")
    nodes = _graph.load_graph(root, "RM_TST")

    html = _graph.render_html(nodes, title="mcRepos — FrontierMode")
    assert "<title>mcRepos — FrontierMode</title>" in html
    assert "<h1>mcRepos — FrontierMode</h1>" in html


def test_render_html_frontier_banner_lists_actionable(tmp_path: Path):
    root = tmp_path / "roadmap"
    _write_node(root, "RM_TST", 1, title="Doable")
    nodes = _graph.load_graph(root, "RM_TST")

    html = _graph.render_html(nodes)
    assert "RM_TST_001" in html
    assert "Doable" in html


def test_render_html_is_read_only(tmp_path: Path):
    root = tmp_path / "roadmap"
    path = _write_node(root, "RM_TST", 1, title="A")
    before = path.read_bytes()

    nodes = _graph.load_graph(root, "RM_TST")
    _graph.render_html(nodes)
    assert path.read_bytes() == before


def test_load_graph_is_read_only(tmp_path: Path):
    root = tmp_path / "roadmap"
    path = _write_node(root, "RM_TST", 1, title="A", depends_on=[])
    before = path.read_bytes()

    nodes = _graph.load_graph(root, "RM_TST")
    _graph.validate_graph(nodes)
    _graph.frontier(nodes)
    _graph.render(nodes)
    _graph.export_json(nodes)

    assert path.read_bytes() == before


# --- header --------------------------------------------------------------------------------


def test_refresh_header_inserts_block(tmp_path: Path):
    root = tmp_path / "roadmap"
    path = _write_node(root, "RM_ARR", 1, title="A node")
    index_path = tmp_path / "ROADMAP_INDEX.md"

    _header.refresh_header(path, index_path)
    content = path.read_text(encoding="utf-8")
    assert "[Dashboard](BACKHAUL.md)" in content
    assert "[Roadmap Index](../ROADMAP_INDEX.md) · RM_ARR" in content


def test_refresh_header_is_idempotent(tmp_path: Path):
    root = tmp_path / "roadmap"
    path = _write_node(root, "RM_ARR", 1, title="A node")
    index_path = tmp_path / "ROADMAP_INDEX.md"

    _header.refresh_header(path, index_path)
    once = path.read_text(encoding="utf-8")
    _header.refresh_header(path, index_path)
    twice = path.read_text(encoding="utf-8")
    assert once == twice


def test_refresh_header_uses_project_name_and_dashboard_path(tmp_path: Path):
    root = tmp_path / "roadmap"
    path = _write_node(root, "RM_ARR", 1, title="A node")
    index_path = tmp_path / "ROADMAP_INDEX.md"
    dashboard_path = tmp_path / "BACKHAUL.md"

    _header.refresh_header(path, index_path, dashboard_path=dashboard_path, project_name="mcRepos")
    content = path.read_text(encoding="utf-8")
    assert "**mcRepos**" in content
    assert "[Dashboard](../BACKHAUL.md)" in content


def test_create_node_gets_header_via_cli_flow(tmp_path: Path):
    """create_node itself doesn't write the header (mirrors bht/bhw's create.py — header
    refresh is the caller's job, see modules/roadmap/cli.py's _cmd_new); this pins that a
    freshly created node has no header until refresh_header is applied to it."""
    nodes_root = tmp_path / "roadmap"
    registry_path = tmp_path / "client-uids.md"

    path = _create.create_node(
        nodes_root=nodes_root, registry_path=registry_path, client="Arryn",
        title="Set up the shed", owner="Arryn",
    )
    before = path.read_text(encoding="utf-8")
    assert "bh-header" in before  # empty marker block from the template
    assert "[Dashboard]" not in before

    _header.refresh_header(path, tmp_path / "ROADMAP_INDEX.md")
    after = path.read_text(encoding="utf-8")
    assert "[Dashboard](BACKHAUL.md)" in after
    assert "[Roadmap Index](../ROADMAP_INDEX.md) · RM_ARR" in after
