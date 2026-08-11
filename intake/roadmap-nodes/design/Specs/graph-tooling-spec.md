# Spec: the graph-tooling script

> **WIP — draft complete, part of an unratified proposal.** See
> [`../../index.md`](../../index.md) for this space's status. **Built as of 2026-08-08** at
> [`scripts/roadmap/roadmap_graph.py`](../../../../scripts/roadmap/roadmap_graph.py) — Stage 0 of
> [`../migration-plan.md`](../migration-plan.md), all acceptance criteria below passing. Building the
> tool does **not** ratify the proposal; nothing about `Documents/Roadmap/roadmap.md` being the live
> source of truth has changed.

**Companion to:** [`../proposal.md`](../proposal.md) §6 and [`node-format-spec.md`](node-format-spec.md)
(the input this script reads). **Produces:** [`../Mockups/sample-generated-index.md`](../Mockups/sample-generated-index.md)-shaped
output and the JSON [`../Mockups/sample-visualization.html`](../Mockups/sample-visualization.html) consumes.

## Purpose

One script, one in-memory graph, several read-only queries against it. Loads every file under
`Documents/Roadmap/Nodes/`, parses the header block `node-format-spec.md` defines, builds a directed
graph (nodes = RM-IDs, edges = `DependsOn`), and answers questions against it. Never writes to a node
file. Never makes a judgment call — it computes lists for a human to judge, same boundary QA's own
tooling already holds (`qa.md`: "develops... scripts to keep verification lean... script output
becomes the evidence for verdicts, not raw code reads").

## Scope

**In:** parsing node files, building the graph, cycle detection, the five queries below, two output
renderers (`render` → markdown, `export-json` → structured data).

**Out:** editing node files, deciding whether a downstream node survives a deprecation, generating
the HTML visualization itself (that's a future consumer of `export-json`'s output — see
[`../proposal.md`](../proposal.md) §9's open questions), anything touching `Documents/ClaudeWiki/Processes/Handoffs/`
(a different ledger, untouched by this tool).

## Input

Every `Documents/Roadmap/Nodes/RM-*.md` file. Parse failure on any single file (malformed header,
unknown `Kind`, `DependsOn` referencing a nonexistent ID) is a hard error naming the offending file —
same fail-loud discipline `ContractSurfaceValidator` already holds itself to; a script that silently
skips a malformed node and produces a frontier missing an entry is worse than one that refuses to run.

**`DependsOn` entries are markdown links** (`node-format-spec.md`'s "Link, don't reference bare"
rule) — `[RM-0012](RM-0012-slug.md)`, not a bare ID. The parser extracts the RM-ID via pattern match
(`RM-\d{4}`) against the bracket text, not an exact-string match against the whole field, so it's
indifferent to which slug the link target uses — a stale link target (file renamed, slug edited) is a
cosmetic problem for a human to fix, not a parse failure, as long as the ID in the brackets is intact
and resolves to a real node.

## Queries

### `validate`

Walks the full graph for cycles (`DependsOn` chains that revisit a node still on the walk stack).
Throws naming every node in the cycle, not just that one exists — same bar
`ComponentRegistry`'s own cycle detector already holds. Every other query implicitly runs this first
and refuses to produce output against a graph that fails it.

### `frontier`

Every node where: (work node, `open`) or (convergence node, `WIP`), **and** every `DependsOn` entry
resolves to a node that's `resolved` or `reached`. This is the actionable menu — see
[`../Mockups/sample-generated-index.md`](../Mockups/sample-generated-index.md) for what it looks like
rendered.

### `dependents <RM-ID>`

**Direct, one-hop reverse of `DependsOn`** — every node that names `<RM-ID>` in its own `DependsOn`
list, nothing further. This is what node-format-spec.md's **Required By** section renders: the
flow-reading pair to a node's own `DependsOn` block, top says what it needs, bottom says what needs
it. Cheap, and deliberately shallow — for the full blast radius, see `downstream` below, which is
built by walking `dependents` recursively rather than being a separate implementation.

### `downstream <RM-ID>`

**Full transitive closure**, not just direct dependents — if RM-0030 depends on RM-0022 which depends
on RM-0012, then `downstream RM-0012` must include RM-0030 even though it never mentions RM-0012
directly. This is the deprecation/revert-impact query: point it at a node about to become
`superseded`, or a convergence node about to revert to `WIP`, and get back everything that might need
re-judging — in dependency order (closest to farthest), since a human reviewing the list may
themselves deprecate something partway through, and anything further downstream needs to already be
in view when that happens, not discovered in a second pass.

Output is a worklist, not a verdict: for each node in the closure, list it with its current status
and let the human decide "stands on its own" / "needs amendment" / "also superseded/reverts" — the
tool doesn't guess which.

### `blocking <RM-ID>`

The reverse of frontier for one node: every `DependsOn` entry that is *not yet* `resolved`/`reached`,
walked transitively — "why can't I start this yet," answered without hand-tracing the chain.

### `render`

Generates the crawlable markdown index: `frontier`'s output at the top (names only — no ticket
prose, this is a map, not a summary), then the full dependency structure below, indented/nested by
depth so it can be read top-to-bottom like an index rather than requiring the reader to already know
the graph. Exact shape: [`../Mockups/sample-generated-index.md`](../Mockups/sample-generated-index.md).

### `export-json`

The same graph — nodes with their stored fields, edges, computed actionable/blocked status — as
structured data. Exists specifically so the future HTML visualization
([`../Mockups/sample-visualization.html`](../Mockups/sample-visualization.html) mocks what it'd show)
is a second renderer over this same export, not a second parser reimplementing everything above.
Shape (illustrative, not final):

```json
{
  "nodes": [
    { "id": "RM-0007", "kind": "convergence", "status": "reached", "name": "ROM Developer operational" },
    { "id": "RM-0058", "kind": "work", "status": "open", "name": "Evaluate Roslyn removal" }
  ],
  "edges": [
    { "from": "RM-0058", "to": "RM-0012" }
  ]
}
```

`"from"` depends on `"to"` — same direction as `DependsOn` in the node file, so the JSON doesn't
introduce a second convention to keep straight against the markdown source.

## Deep-link contract for the future HTML consumer

Out of scope for this script to build (see Scope above), but a requirement on whatever consumes its
`export-json` output: it must honor `?focus=RM-NNNN` in its URL, highlighting and centering/scrolling
to that node on load. This is what lets `render`'s markdown output, and every node file's own
computed **Visualize** line (`node-format-spec.md`), link straight into the graph already centered on
the node the reader came from, instead of dumping them into the full graph to hunt for it by eye.
[`../Mockups/sample-visualization.html`](../Mockups/sample-visualization.html) already implements this
— as of 2026-08-08 against the real pilot's 11 nodes (hand-built HTML, hand-copied data), not just an
illustrative set. Proof of the mechanism and, until the real tool exists, the actual current target for
every real node's `Visualize` line — not the real consumer this contract ultimately describes.

## Acceptance criteria

All seven passing as of 2026-08-08 — see
[`scripts/roadmap/test_roadmap_graph.py`](../../../../scripts/roadmap/test_roadmap_graph.py) (nine
tests; each criterion below maps to one or more, named to match).

- [x] `validate` catches a synthetic cycle (three nodes, A→B→C→A) and names all three in the error.
      — `TestCycleDetection`
- [x] `frontier` against a small synthetic graph returns exactly the nodes with all deps satisfied —
      verified against a hand-computed expected set, not just "it returned something." —
      `TestFrontier`
- [x] `downstream` against a four-deep synthetic chain (A→B→C→D) returns B, C, and D when queried on
      A — the transitive case, not just direct dependents. — `TestDownstream`
- [x] `render`'s output matches the mockup's structure: frontier section first, names only, no ticket
      body text leaking into the index. — `TestRender`
- [x] `export-json`'s node/edge shape round-trips against a hand-built synthetic graph without loss.
      — `TestExportJson`
- [x] A malformed node file (bad `Kind`, or a `DependsOn` entry pointing at a nonexistent RM-ID)
      produces a named, specific error, not a silent skip or a generic crash. — `TestMalformedNodes`
      (three cases: bad `Kind`, dangling `DependsOn`, and confirming a malformed file aborts the
      whole load rather than being silently dropped)
- [x] Read-only against `Documents/Roadmap/Nodes/` — confirmed via a run that diffs the folder
      before/after and finds zero changes. — `TestReadOnly` (runs every query against a temp copy of
      the *real* pilot data, not just a synthetic graph, then hash-diffs before/after)

**Beyond the acceptance criteria:** every query was also run directly against the real 13-node pilot
and cross-checked against everything hand-computed during the pilot exercise — `frontier` returns
exactly RM-0007/RM-0008/RM-0009, `validate` finds no cycles, `downstream RM-0010` returns all eight
nodes past it, `dependents`/`blocking` match every node's own hand-written Required By section
exactly. Not required by this spec, but cheap to do and worth recording — it's the difference between
"passes its own tests" and "agrees with a human who did the same work by hand."

## Open implementation questions

- Language/runtime: not pinned here. Python fits the project's existing QA-tooling precedent
  (`scripts/qa/`); this could live at `scripts/roadmap/` alongside it as a sibling convention. Dev's
  call at build time, not a design constraint.
- Whether `render` overwrites a single generated file or is invoked on demand — a rollout-sequencing
  question, addressed in [`../migration-plan.md`](../migration-plan.md), not here.

## Related pages

- [RoadmapGraph space index](../../index.md)
- [Full proposal](../proposal.md)
- [Node format spec](node-format-spec.md)
- [Sample generated index (mockup)](../Mockups/sample-generated-index.md)
- [Sample visualization (mockup)](../Mockups/sample-visualization.html)
- [Migration plan](../migration-plan.md)
