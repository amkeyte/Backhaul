# RM-0013 — Rulebook Author operational

**Kind:** convergence
**Status:** reached
**Created:** 2026-08-08 (backfilled)
**Owner:** Kofi
**DependsOn:** [RM-0012](RM-0012-rulebook-tier-established.md)
**Visualize:** <a href="../../ClaudeWiki/RoadmapGraph/Mockups/sample-visualization.html?focus=RM-0013" target="_blank" rel="noopener">Open in graph view ↗</a>

The point at which a Rulebook Author could build a specific game's rules — combat sequencing, win
conditions, the rest of `IRuleBook` — on top of ROM tools someone else built, without extending the
ROM itself (`Documents/design/glossary.md`'s **Rulebook Author** vs **ROM Developer** distinction).

**Honesty caveat, added 2026-08-08 — weaker evidence than RM-0010's bar.** RM-0010 ("ROM Developer
operational") required proof across *three* independent ROMs before being marked `reached`,
specifically because a pattern proven once could be an artifact of that one case. This node is marked
`reached` on a *single* case — OneD20, the only Rulebook that exists. Real multi-Rulebook reusability
is explicitly untested: `Documents/Roadmap/phase-2-7-1.md` states outright that "real multi-Rulebook
support is a distinct, real, and deferred need, not attempted here," and the same deferral repeats
across `Documents/design/non-goals.md`. Marked `reached` anyway at Arryn's direction — pragmatic
backfill, consistent with how RM-0001 treats its own missing earlier history — but this is the one
node in the pilot where `reached` rests on meaningfully weaker footing than its sibling convergence
nodes, and that's worth knowing before leaning on it for anything real.

## ReachedLog

- 2026-08-08 — reached, backfilled retroactively. Evidence: OneD20 exists and works
  (`Documents/design/glossary.md`). No independent QA verdict behind this entry, unlike RM-0010's — see
  the caveat above.

## Required By

*(computed, hand-derived pending real tooling)* — [RM-0004](RM-0004-phase-2-8.md),
[RM-0014](RM-0014-phase-2-11-1.md) (added 2026-08-08)

## Related pages

- [RoadmapGraph proposal](../../ClaudeWiki/RoadmapGraph/proposal.md)
