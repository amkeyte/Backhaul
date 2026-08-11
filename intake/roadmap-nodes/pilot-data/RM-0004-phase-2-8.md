# RM-0004 — Phase 2.8: World Module extraction

**Kind:** work
**Status:** resolved
**Created:** 2026-08-05 (backfilled)
**Owner:** Kofi
**DependsOn:** [RM-0013](RM-0013-rulebook-author-operational.md)
**Visualize:** <a href="../../ClaudeWiki/RoadmapGraph/Mockups/sample-visualization.html?focus=RM-0004" target="_blank" rel="noopener">Open in graph view ↗</a>

`IOneD20WorldModule` extracted as the Rulebook-owned authoring contract; a second World Module
(Hollow Keep) proven against it live. QA PASS, gate ticket 0063.

See [`../phase-2-8.md`](../phase-2-8.md) and [`../../QA/phase-2-8-verdict.md`](../../QA/phase-2-8-verdict.md).

**Retargeted 2026-08-08 (supersedes both notes below): RM-0012/RM-0013 inserted between RM-0010 and
this node.** The tier boundary this node actually sits on isn't "ROM proven" — it's "a Rulebook exists
to extend," per `Documents/design/glossary.md`'s distinct **Rulebook Author** role. `RM-0013`
("Rulebook Author operational") is now the direct dependency; `RM-0010` is still required, just
transitively (`RM-0013` → `RM-0012` → `RM-0010`), same transitive-reduction discipline as everything
else in this branch.

*(Prior same-day notes, now superseded: "full ROM-tier encapsulation, not just an added gate... RM-0010
is now this node's only ROM-tier link," and before that, "RM-0010 added... layered on top of, not
replacing.")*

## Required By

*(computed, hand-derived pending real tooling)* — [RM-0005](RM-0005-phase-2-9.md),
[RM-0006](RM-0006-phase-2-10.md).

**Narrowed 2026-08-08 (transitive reduction):** RM-0008 and RM-0011 dropped as direct dependents.
RM-0008 now depends on RM-0005 only (which already requires RM-0004); RM-0011 now depends on RM-0007
and RM-0008 only (both already trace back to RM-0004). Still transitively required by both, just not
directly.

## Related pages

- [RoadmapGraph proposal](../../ClaudeWiki/RoadmapGraph/proposal.md)
