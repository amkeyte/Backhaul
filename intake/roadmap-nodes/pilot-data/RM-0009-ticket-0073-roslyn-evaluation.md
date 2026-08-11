# RM-0009 — Evaluate Roslyn removal from the rule-compilation pipeline

**Kind:** work
**Status:** open
**Created:** 2026-08-05 (backfilled)
**Owner:** Amara
**DependsOn:** []
**Visualize:** <a href="../../ClaudeWiki/RoadmapGraph/Mockups/sample-visualization.html?focus=RM-0009" target="_blank" rel="noopener">Open in graph view ↗</a>

Roslyn compiles 1.d20's rule groups at ~14x the cost of the NRules Rete-build it feeds. Findings and
charted options in `rule-pipeline-compilation-cost.md`. Independent branch — nothing currently in
flight depends on this being resolved either way, but its ruling is a real input to `RM-0011`
(World Builder operational) once GM Overlay's live-reload cost model is in scope.

See [ticket 0073](../../ClaudeWiki/Processes/Handoffs/0073-rule-compilation-cost-and-runtime-mode.md).

## Required By

*(computed, hand-derived pending real tooling)* — none currently; no node yet names RM-0009 in its own
`DependsOn`. (The GM Overlay dependency this node's own body mentions runs the other direction — this
node explains that its *own* ruling will matter to a future node, which isn't the same as that node
existing yet and pointing back.)

## Related pages

- [RoadmapGraph proposal](../../ClaudeWiki/RoadmapGraph/proposal.md)
