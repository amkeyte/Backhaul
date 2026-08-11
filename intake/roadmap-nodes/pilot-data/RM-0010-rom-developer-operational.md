# RM-0010 — ROM Developer operational

**Kind:** convergence
**Status:** reached
**Created:** 2026-08-05 (backfilled)
**Owner:** Kofi
**DependsOn:** [RM-0003](RM-0003-phase-2-7-1.md)
**Visualize:** <a href="../../ClaudeWiki/RoadmapGraph/Mockups/sample-visualization.html?focus=RM-0010" target="_blank" rel="noopener">Open in graph view ↗</a>

The point at which a third party could author a new ROM against `Capability`/`IRom`/
`ComponentRegistry` without touching engine internals — proven across three real ROMs (GridMap,
D20System, Loot): a pure-sink shape, a capability consumed by two independent peers, and a
capability relay (`IEquippedWeapon`, landed in Phase 2.10). All three dependencies resolved with
independent QA verdicts.

**Pruned 2026-08-08: transitive reduction.** `RM-0001` and `RM-0002` removed from `DependsOn` —
`RM-0003` already requires `RM-0002`, which already requires `RM-0001`, so both were reachable without
a direct edge. Same reachability, same `downstream`/`blocking` results, one edge instead of three. The
underlying fact (this milestone needed all three phases) is unchanged and still true — it's just no
longer hand-duplicated as three separate direct edges when one implies the other two.

## ReachedLog

- 2026-08-02 — reached, on RM-0003's QA PASS (Phase 2.7.1, ticket 0056) — the third-ROM proof was the
  last piece.

## Required By

*(computed, hand-derived pending real tooling)* — [RM-0012](RM-0012-rulebook-tier-established.md)
only.

**2026-08-08, three passes.** Widened to list all of RM-0004 through RM-0011 (sequential-gating
pass), then pruned back to just RM-0004 (transitive reduction — everything else in the branch already
reached RM-0010 through it). Then RM-0012/RM-0013 were inserted between RM-0010 and RM-0004, so the
one remaining direct dependent is now RM-0012, not RM-0004 — RM-0004 still needs RM-0010, just three
hops away now instead of one. `downstream RM-0010` returns the same full branch throughout all three
passes; only what's written directly here has changed.

## Related pages

- [RoadmapGraph proposal](../../ClaudeWiki/RoadmapGraph/proposal.md)
