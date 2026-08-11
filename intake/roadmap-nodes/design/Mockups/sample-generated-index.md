# Roadmap Graph — generated index

> **MOCKUP.** This is a fake example of `render`'s output, built by hand to show the intended shape —
> it is not produced by real tooling, and the node IDs/edges below are illustrative, not the actual
> project graph. See [`../Specs/graph-tooling-spec.md`](../Specs/graph-tooling-spec.md) for what would
> really generate this. `RM-0059`/`RM-0080` in particular are hypothetical placeholders for a Phase 4 /
> GM Overlay concept that is still a design draft today, not a ratified node — included here only to
> show what a second, unrelated branch of the graph looks like once it exists.
>
> **Note (2026-08-08):** unlike this file, [`sample-visualization.html`](sample-visualization.html) was
> since rebuilt against the real pilot's 11 nodes (`RM-0001`...`RM-0011`, `Documents/Roadmap/Nodes/`) —
> the two mockups intentionally no longer share an ID space. This file stays illustrative because its
> job is showing `render`'s *shape*, not proving anything against real data.

*Generated 2026-08-04 — regenerate with `roadmap-graph render`, do not hand-edit.*

## Actionable now

Everything below has no unsatisfied dependency. This is the menu — pick from here, not from a line.

- **RM-0051** — Cross-ROM capability mechanism stress test
- **RM-0052** — Lua World Module authoring-surface stress test
- **RM-0058** — Evaluate Roslyn removal from the rule-compilation pipeline

## Dependency structure

Names only below this line — open the node file for detail. Indentation shows "depends on," read
top to bottom as "this feeds into that."

```
RM-0007 [convergence · reached] ROM Developer operational
├─ RM-0002 [resolved] Rule pipeline MVP
├─ RM-0003 [resolved] d20 vertical slice
├─ RM-0004 [resolved] ROM identity & cross-ROM interop
├─ RM-0005 [resolved] Multi-ROM composition
│
├─ RM-0031 [resolved] Loot ROM content expansion
├─ RM-0035 [resolved] World Module extraction
├─ RM-0044 [resolved] Lua World Module authoring
├─ RM-0050 [resolved] Content coverage stress test
├─ RM-0051 [open · ACTIONABLE] Cross-ROM capability stress test
└─ RM-0052 [open · ACTIONABLE] Lua World Module stress test
    │
    ▼
RM-0040 [convergence · WIP — blocked] World Builder operational
    blocked by: RM-0051, RM-0052 (not yet resolved)

RM-0058 [open · ACTIONABLE, no dependencies] Evaluate Roslyn removal
    │
    ▼
RM-0059 [open · blocked] Rework rule-compilation pipeline per RM-0058's ruling
    blocked by: RM-0058

RM-0040 ─┐
         ├──▶ RM-0080 [convergence · WIP — blocked] GM Overlay operational (illustrative)
RM-0059 ─┘        blocked by: RM-0040, RM-0059
```

## Reading this

- A convergence node shows `reached` or `WIP`, never anything in between — no partial credit, same
  as a phase not moving to `done` without a QA verdict today.
- `RM-0040` is blocked by two nodes currently sitting in the *actionable* list above — that's not a
  contradiction, it's the graph doing its job: World Builder can't be claimed solid until 2.11 and
  2.12 actually resolve, even though both are startable right now.
- `RM-0058`/`RM-0059` are a second, independent branch — nothing here claims Roslyn removal blocks
  anything already in flight. If `RM-0058`'s ruling changes what other nodes assumed true, that's
  what `downstream RM-0058` is for, not something this index tries to guess at.

## Related pages

- [RoadmapGraph space index](../index.md)
- [Graph tooling spec](../Specs/graph-tooling-spec.md)
- [Sample visualization (mockup)](sample-visualization.html)
