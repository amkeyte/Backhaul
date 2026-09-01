---
id: BH_006
uid: BH
number: 6
client: BH
status: done
title: Detect DependsOn edges bypassing a convergence node
context: 'New bhrm check: node depends on a convergence node''s ancestor, not the
  node itself. See body.'
priority: low
opened: '2026-08-15'
closed: '2026-08-15'
---

## Summary

Detect DependsOn edges bypassing a convergence node

## Full report

Feature request: a new bhrm query that flags a DependsOn edge that reaches past a
convergence node's own prerequisites instead of depending on the convergence node itself --
"skipping the checkpoint."

Background -- this concept doesn't exist anywhere today, formally
Researched 2026-08-13/14 while looking into the roadmap HTML visualization (BH_005). The
"tier-boundary spine" idea -- some edges represent crossing a meaningful checkpoint and should be
visually/structurally distinct -- traces back entirely to intake/roadmap-nodes' hand-built mockup
(design/Mockups/sample-visualization.html): specific edges were manually colored gold and given a
`.gate-edge` CSS class where the author judged, by eye, that the edge crossed a tier boundary
(ROM -> Rulebook -> World-Builder). That's it -- pure visual annotation on one pilot graph, applied
after the fact. It was never written down as a rule anywhere (not node-format-spec.md, not
graph-tooling-spec.md), and nothing in Backhaul's own schema.py or graph.py treats a `kind:
convergence` node specially with respect to DependsOn edges -- a convergence node is just a
different status vocabulary (WIP/reached, reversible) than a work node (open/resolved/superseded,
terminal). Confirmed via `backhaul lint` (BH_004's implementation): its two checks (orphaned pages,
broken links) are pure markdown-file-link-graph problems, no awareness of DependsOn semantics at
all. `modules/roadmap/graph.py`'s `validate_graph()` only checks for cycles.

What "bypassing" means, precisely (first formal definition -- doesn't exist prior to this ticket)
For a convergence node C:
- `ancestors(C)` = every node C transitively depends on (walk DependsOn forward from C, all the
  way back) -- C's full prerequisite set, regardless of status.
- `gated_by_C` = {C} union every node that transitively depends on C (this is exactly `downstream`
  in reverse -- `downstream(nodes, C)` already computes "everything that depends on C, directly or
  transitively"; add C itself).

A node N is a **bypass candidate** for convergence node C when:
1. N is not in `ancestors(C)` (N isn't legitimately upstream of C -- of course C's own
   prerequisites don't depend on C, that's not a bypass), AND
2. N is not in `gated_by_C` (N doesn't already properly route through C), AND
3. N's own transitive DependsOn closure intersects `ancestors(C)` (N depends, directly or
   transitively, on something that is also one of C's prerequisites).

In other words: N reaches back into the same prerequisite territory C was built to gate, without
N itself ever routing through C.

This needs one new graph primitive: a full ancestor closure (walk DependsOn forward, transitively,
regardless of status -- NOT `blocking()`, which already exists but only returns the *unsatisfied*
subset of ancestors). Call it `ancestors(nodes, nid)`, sibling to `downstream()`.

Pseudocode
```
def ancestors(nodes, nid):
    # forward transitive closure of DependsOn, regardless of status -- mirror of downstream()
    ...

def find_convergence_bypasses(nodes):
    findings = []
    for c in (n for n in nodes.values() if n.kind == "convergence"):
        c_ancestors = ancestors(nodes, c.id)
        gated_by_c = {c.id} | set(downstream(nodes, c.id))
        for n in nodes.values():
            if n.id == c.id or n.id in c_ancestors or n.id in gated_by_c:
                continue
            n_ancestors = ancestors(nodes, n.id)
            overlap = n_ancestors & c_ancestors
            if overlap:
                findings.append((n.id, c.id, sorted(overlap)))
    return findings
```

Important caveat -- this is a candidate list, not a verdict, same discipline every other query in
this module already holds itself to ("computes lists for a human to judge," graph-tooling-spec.md's
Purpose section, echoed in graph.py's own module docstring). A shared ancestor doesn't automatically
mean N *should* route through C -- N's work might be genuinely unrelated to whatever guarantee C
represents, just coincidentally sharing an early prerequisite. This check produces "worth a human
look," not "this graph is invalid" -- unlike `validate_graph()`'s cycle check, which is a hard
error, this should never raise or block anything.

Open question, deliberately not resolved here: whether `created` (an existing optional schema
field) should factor in -- e.g. only flagging N if N was created *after* C already existed, on the
theory that a node predating the convergence node obviously wasn't written to bypass a checkpoint
that didn't exist yet. Left to the dev to decide at build time; noting it so it's not rediscovered
as a surprise false-positive source.

Suggested shape
- New function in modules/roadmap/graph.py: `ancestors()` (new primitive) and
  `find_convergence_bypasses()` (or similar name -- naming is implementation's call).
- New bhrm subcommand, sibling to frontier/dependents/downstream/blocking -- e.g.
  `bhrm convergence-bypass --uid RM_XXX` (exact verb is implementation's call; "gate" was never a
  real term in this codebase, "convergence-bypass" matches the actual schema vocabulary).
  Prints a list, one line per (N, C, shared ancestors) -- same worklist style as `downstream`'s
  output, not a pass/fail verdict.
- Does NOT get folded into `bhrm validate` -- that command's contract today is "raises on a cycle,
  silent otherwise," and this check is fundamentally advisory, not a hard-error condition. Keep
  them separate rather than changing validate's meaning.
- Tests: synthetic graph with a convergence node, a legitimate downstream node (properly gated,
  should NOT be flagged), an upstream/ancestor node (should NOT be flagged), and a genuine bypass
  candidate (shares an ancestor with the convergence node, doesn't depend on it) -- should be
  flagged. Also a graph with no convergence nodes at all (empty result, not an error).
- Docs: wiki/meta/bhrm.md -- new command in the cheatsheet, plus a short explanation of what
  "bypass candidate" means (the graph-tooling-spec.md / node-format-spec.md pages never defined
  this, so this ticket's own definition above is the first real spec for it).

Priority: low -- exploratory/advisory tooling, not blocking anything currently in flight.

## Log

- 2026-08-14: Ticket opened.
- 2026-08-15: Implemented per this ticket's own spec, verbatim — `ancestors()` (new primitive,
  mirrors `downstream()`) and `find_convergence_bypasses()` in `modules/roadmap/graph.py`,
  `bhrm convergence-bypass --uid RM_XXX` subcommand. Decided the one open question this ticket
  left explicit: does **not** factor in `created` to filter out nodes predating the convergence
  node — one clear rule for v1, not a second date-based heuristic, revisit if real usage shows
  noise. Tests: `ancestors()` full-closure-regardless-of-status, and the four-case fixture from
  this ticket's own scope (ancestor excluded, properly-gated-downstream excluded, unrelated
  excluded, genuine bypass flagged) plus a no-convergence-nodes empty case, in
  `tests/test_roadmap.py`; CLI tests in `tests/test_roadmap_cli.py`. Docs: `wiki/meta/bhrm.md`.
  Full suite green (310 passed). Closed.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_LocalFiles/source/repos/Backhaul)
<!-- bh-header:end -->
