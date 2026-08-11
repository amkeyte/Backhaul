# scripts/roadmap/

Real tooling for the RM node dependency graph, part of an **unratified, WIP proposal** — see
[`Documents/ClaudeWiki/RoadmapGraph/index.md`](../../Documents/ClaudeWiki/RoadmapGraph/index.md) for
the space's status. Building this script does not adopt the proposal; `Documents/Roadmap/roadmap.md`
is still the live source of truth.

Implements [`graph-tooling-spec.md`](../../Documents/ClaudeWiki/RoadmapGraph/Specs/graph-tooling-spec.md)
against the node format defined in
[`node-format-spec.md`](../../Documents/ClaudeWiki/RoadmapGraph/Specs/node-format-spec.md). Python
standard library only, no dependencies to install.

## Usage

```
python3 scripts/roadmap/roadmap_graph.py validate
python3 scripts/roadmap/roadmap_graph.py frontier
python3 scripts/roadmap/roadmap_graph.py dependents RM-0010
python3 scripts/roadmap/roadmap_graph.py downstream RM-0010
python3 scripts/roadmap/roadmap_graph.py blocking RM-0011
python3 scripts/roadmap/roadmap_graph.py render
python3 scripts/roadmap/roadmap_graph.py export-json [--out FILE]
```

Reads `Documents/Roadmap/Nodes/RM-*.md` by default (resolved relative to this script's own location,
so it works from any working directory). Override with `--nodes-dir` to point at a different folder —
the test suite uses this to run against synthetic fixtures and temp copies rather than the real data.

**Read-only.** Never writes to a node file. Never makes a judgment call — it computes lists for a
human to judge, same boundary QA's own tooling holds itself to (see `graph-tooling-spec.md`'s
Purpose section).

## Tests

```
python3 -m unittest scripts.roadmap.test_roadmap_graph -v
```

Nine tests, one per acceptance criterion in `graph-tooling-spec.md` (plus a couple of extra edge
cases). All synthetic fixtures except the read-only check, which copies the real pilot data to a temp
dir first and hash-diffs before/after — it never touches the live files.
