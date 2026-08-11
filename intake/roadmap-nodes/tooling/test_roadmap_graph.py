#!/usr/bin/env python3
"""
Acceptance-criteria tests for roadmap_graph.py, mirroring the checklist in
Documents/ClaudeWiki/RoadmapGraph/Specs/graph-tooling-spec.md's "## Acceptance criteria" section
one-for-one. Synthetic fixtures only — never touches the real Documents/Roadmap/Nodes/ pilot data
except in test_real_pilot_data_is_untouched, which copies it to a temp dir first.

Run with: python3 -m unittest scripts/roadmap/test_roadmap_graph.py -v
(or just: python3 scripts/roadmap/test_roadmap_graph.py)
"""

from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import roadmap_graph as rg  # noqa: E402


def write_node(
    directory: Path,
    node_id: str,
    slug: str,
    kind: str,
    status: str,
    depends_on: list[str],
    title: str = "Synthetic test node",
    owner: str = "Kofi",
    ticket_line: str = "",
    body: str = "Synthetic body text for a test fixture — not real project content.",
) -> Path:
    deps_str = ", ".join(f"[{d}]({d}-slug.md)" for d in depends_on) if depends_on else "[]"
    content = (
        f"# {node_id} — {title}\n\n"
        f"**Kind:** {kind}\n"
        f"**Status:** {status}\n"
        f"**Created:** 2026-08-08\n"
        f"**Owner:** {owner}\n"
        f"**DependsOn:** {deps_str}\n"
    )
    if ticket_line:
        content += f"**Ticket:** {ticket_line}\n"
    content += f"\n{body}\n"
    path = directory / f"{node_id}-{slug}.md"
    path.write_text(content, encoding="utf-8")
    return path


class TestCycleDetection(unittest.TestCase):
    """AC1: validate catches a synthetic cycle (three nodes, A->B->C->A) and names all three."""

    def test_three_node_cycle_named_in_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            write_node(d, "RM-9001", "a", "work", "open", ["RM-9002"])
            write_node(d, "RM-9002", "b", "work", "open", ["RM-9003"])
            write_node(d, "RM-9003", "c", "work", "open", ["RM-9001"])

            nodes = rg.load_graph(d)
            with self.assertRaises(rg.NodeParseError) as ctx:
                rg.validate(nodes)
            msg = str(ctx.exception)
            for nid in ("RM-9001", "RM-9002", "RM-9003"):
                self.assertIn(nid, msg, f"cycle error should name {nid}: {msg!r}")


class TestFrontier(unittest.TestCase):
    """AC2: frontier against a small synthetic graph returns exactly the nodes with all deps
    satisfied — verified against a hand-computed expected set."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        write_node(d, "RM-9010", "root-resolved", "work", "resolved", [])
        write_node(d, "RM-9011", "open-satisfied", "work", "open", ["RM-9010"])
        write_node(d, "RM-9012", "open-no-deps", "work", "open", [])
        write_node(d, "RM-9013", "open-blocked", "work", "open", ["RM-9014"])
        write_node(d, "RM-9014", "open-root", "work", "open", [])
        write_node(d, "RM-9015", "conv-blocked", "convergence", "WIP", ["RM-9011"])
        write_node(d, "RM-9016", "conv-satisfied", "convergence", "WIP", ["RM-9010"])
        write_node(d, "RM-9017", "conv-reached", "convergence", "reached", [])
        self.nodes = rg.load_graph(d)

    def tearDown(self):
        self.tmp.cleanup()

    def test_frontier_matches_hand_computed_set(self):
        # Hand-computed: 9010 is resolved (not open) -> not actionable itself.
        # 9011: open, dep 9010 resolved -> actionable.
        # 9012: open, no deps -> actionable.
        # 9013: open, dep 9014 is open (unsatisfied) -> NOT actionable.
        # 9014: open, no deps -> actionable.
        # 9015: convergence WIP, dep 9011 is open (unsatisfied) -> NOT actionable.
        # 9016: convergence WIP, dep 9010 resolved -> actionable.
        # 9017: convergence reached (not WIP) -> not actionable itself.
        expected = sorted(["RM-9011", "RM-9012", "RM-9014", "RM-9016"])
        self.assertEqual(rg.frontier(self.nodes), expected)


class TestDownstream(unittest.TestCase):
    """AC3: downstream against a four-deep synthetic chain (A->B->C->D) returns B, C, and D when
    queried on A — the transitive case, not just direct dependents."""

    def test_four_deep_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            write_node(d, "RM-9020", "chain-a", "work", "resolved", [])
            write_node(d, "RM-9021", "chain-b", "work", "resolved", ["RM-9020"])
            write_node(d, "RM-9022", "chain-c", "work", "resolved", ["RM-9021"])
            write_node(d, "RM-9023", "chain-d", "work", "open", ["RM-9022"])
            nodes = rg.load_graph(d)

            result = rg.downstream(nodes, "RM-9020")
            self.assertEqual(result, ["RM-9021", "RM-9022", "RM-9023"])
            # Direct dependents() must NOT include the transitive-only members.
            self.assertEqual(rg.dependents(nodes, "RM-9020"), ["RM-9021"])


class TestRender(unittest.TestCase):
    """AC4: render's output matches the mockup's structure — frontier section first, names only,
    no ticket body text leaking into the index."""

    def test_frontier_first_and_no_body_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            write_node(
                d,
                "RM-9030",
                "actionable-with-ticket",
                "work",
                "open",
                [],
                title="Something actionable",
                ticket_line="[9999](../fake/path.md) — in-review",
                body="SECRET_BODY_TEXT_MUST_NOT_APPEAR_IN_INDEX",
            )
            nodes = rg.load_graph(d)
            output = rg.render(nodes)

            frontier_pos = output.index("## Actionable now")
            structure_pos = output.index("## Dependency structure")
            self.assertLess(
                frontier_pos, structure_pos, "Actionable now must come before Dependency structure"
            )
            self.assertIn("RM-9030", output)
            self.assertIn("Something actionable", output)
            self.assertNotIn("SECRET_BODY_TEXT_MUST_NOT_APPEAR_IN_INDEX", output)
            self.assertNotIn("fake/path.md", output, "ticket path is body detail, not index content")


class TestExportJson(unittest.TestCase):
    """AC5: export-json's node/edge shape round-trips against a hand-built synthetic graph without
    loss."""

    def test_roundtrip_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            write_node(d, "RM-9040", "root", "work", "resolved", [], title="Root node")
            write_node(
                d, "RM-9041", "leaf", "convergence", "WIP", ["RM-9040"], title="Leaf convergence"
            )
            nodes = rg.load_graph(d)
            payload = rg.export_json(nodes)

            self.assertEqual(len(payload["nodes"]), 2)
            self.assertEqual(len(payload["edges"]), 1)
            self.assertEqual(payload["edges"][0], {"from": "RM-9041", "to": "RM-9040"})

            by_id = {n["id"]: n for n in payload["nodes"]}
            self.assertEqual(by_id["RM-9040"]["kind"], "work")
            self.assertEqual(by_id["RM-9040"]["status"], "resolved")
            self.assertEqual(by_id["RM-9040"]["name"], "Root node")
            self.assertFalse(by_id["RM-9040"]["actionable"])  # resolved, not open
            self.assertEqual(by_id["RM-9041"]["kind"], "convergence")
            self.assertTrue(by_id["RM-9041"]["actionable"])  # WIP, dep resolved

            # Round-trip through json.dumps/loads to prove nothing is lost in serialization.
            import json

            reloaded = json.loads(json.dumps(payload))
            self.assertEqual(reloaded, payload)


class TestMalformedNodes(unittest.TestCase):
    """AC6: a malformed node file (bad Kind, or a DependsOn entry pointing at a nonexistent
    RM-ID) produces a named, specific error, not a silent skip or a generic crash."""

    def test_bad_kind_names_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            path = write_node(d, "RM-9050", "bad-kind", "not-a-real-kind", "open", [])
            with self.assertRaises(rg.NodeParseError) as ctx:
                rg.load_graph(d)
            self.assertIn(str(path), str(ctx.exception))
            self.assertIn("Kind", str(ctx.exception))

    def test_dangling_dependson_names_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            path = write_node(d, "RM-9051", "dangling", "work", "open", ["RM-9999"])
            with self.assertRaises(rg.NodeParseError) as ctx:
                rg.load_graph(d)
            msg = str(ctx.exception)
            self.assertIn(str(path), msg)
            self.assertIn("RM-9999", msg)

    def test_no_silent_skip(self):
        """A malformed file must abort the whole load, not just be dropped from the graph."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            write_node(d, "RM-9052", "fine", "work", "open", [])
            write_node(d, "RM-9053", "broken", "work", "not-a-real-status", [])
            with self.assertRaises(rg.NodeParseError):
                rg.load_graph(d)


class TestReadOnly(unittest.TestCase):
    """AC7: read-only against Documents/Roadmap/Nodes/ — confirmed via a run that diffs the folder
    before/after and finds zero changes. Run against a temp copy of the real pilot data (never the
    live files), which also doubles as a structural sanity check against real data."""

    def _hash_dir(self, d: Path) -> dict:
        return {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(d.glob("RM-*.md"))
        }

    def test_real_pilot_copy_untouched_after_full_run(self):
        real_nodes_dir = rg.default_nodes_dir()
        if not real_nodes_dir.exists():
            self.skipTest(f"real nodes dir not found at {real_nodes_dir}")

        with tempfile.TemporaryDirectory() as tmp:
            copy_dir = Path(tmp) / "Nodes"
            shutil.copytree(real_nodes_dir, copy_dir)

            before = self._hash_dir(copy_dir)
            self.assertGreater(len(before), 0, "expected real node files to exist")

            nodes = rg.load_graph(copy_dir)
            rg.validate(nodes)
            rg.frontier(nodes)
            for nid in list(nodes)[:3]:
                rg.dependents(nodes, nid)
                rg.downstream(nodes, nid)
                rg.blocking(nodes, nid)
            rg.render(nodes)
            rg.export_json(nodes)

            after = self._hash_dir(copy_dir)
            self.assertEqual(before, after, "running every query must not modify any node file")


if __name__ == "__main__":
    unittest.main()
