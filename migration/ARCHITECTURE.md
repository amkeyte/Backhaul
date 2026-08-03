# Architecture — foundation, services, modules

**Status:** Draft — resolves a naming/layering ambiguity left open in `MODULE_SYSTEM.md`.
**Supersedes:** the `core/` folder as described in `MODULE_SYSTEM.md` §2 and the flat
`src/backhaul/ticket|wiki|...` sketch in `PYTHON_PROJECT_SETUP.md`. Both get updated to match
this once it's confirmed.

## The question

"BHT and BHW are the point — everything else builds around those two. What happens when
there's three different modules — do they all get their own core?"

**No.** There's exactly one shared foundation. BHT and BHW aren't modules sitting next to it —
they're the first two **services** built on top of it. A third domain thing (docx, or
whatever comes after it) doesn't get its own foundation either; it sits on the same one,
either directly or by using BHT/BHW's own API if it needs ticket- or wiki-shaped behavior.
One foundation, however many services and modules get built on it.

## Three layers

```
foundation/            <- ONE. Generic, domain-agnostic. Nothing here knows what a "ticket"
                           or a "wiki page" is.
  config.py             <- reads config.local.json, resolves content_root, enabled_modules
  frontmatter.py         <- parse/write YAML frontmatter
  collection.py          <- the generic engine: numbering/slugging, templating, refuse-to-
                             overwrite file safety, index/registry building, cross-reference
                             tracking (see §3)
  version_check.py

services/
  ticket/    (BHT)      <- a SPECIALIZATION of foundation.collection: schema = ticket
                             frontmatter fields, lifecycle = open/in-progress/blocked/done,
                             access = per-client vs. global (UID-scoped numbering, board rollup)
  wiki/      (BHW)      <- another specialization: schema = wiki frontmatter fields,
                             lifecycle = draft/verified/published, access = category tree
                             (breadcrumbs, per-category index)

modules/
  docx/                 <- depends on foundation (config, maybe frontmatter). Does NOT need
                             its own foundation. Doesn't have collection/lifecycle semantics
                             at all — it's file transformation, not a collection of things.
  <whatever's next>/    <- same rule: if it's genuinely a new "collection of structured
                             content with a lifecycle," it's a SERVICE built on foundation,
                             same as BHT/BHW. If it's a utility/tool, it's a MODULE that
                             depends on foundation and optionally on a service.
```

## 1. Why BHT and BHW share so much

You called this correctly: ticket and wiki are mostly the same shape wearing different
clothes. Both are: a numbered/slugged markdown file, with YAML frontmatter, built from a
template, indexed into a rollup (board vs. category index), with basic file-safety rules
(don't silently overwrite). What differs is the *schema* (which frontmatter fields exist),
the *lifecycle* (ticket states vs. draft/verified/published), and the *access structure*
(client-scoped numbering + a global board vs. category-scoped + breadcrumbs).

So `foundation/collection.py` implements the shared mechanics once — numbering, templating,
index building, file safety — parameterized by a schema + lifecycle definition. `services/ticket`
and `services/wiki` are each a fairly small amount of code: they define their schema, their
lifecycle states, and their access rules, and hand the rest to the shared engine. This is
also exactly what fixes the duplication already spotted in the current Aaron K scripts (the
frontmatter regex and numbering logic independently reimplemented in `new_ticket.py` and
`build_board.py`).

**Decided (2026-07-31):** BHT and BHW are baseline — always present on every machine,
unconditionally. They're not gated by `enabled_modules` (see `MODULE_SYSTEM.md` §3); that
toggle is only for genuinely optional things under `modules/`. Whether a hypothetical future
service also gets baseline treatment or is itself optional is an open question for whenever
that's actually proposed — not decided now, since only BHT/BHW exist to reason about.

## 2. What a new service costs vs. what a new module costs

A **new service** (something else that's fundamentally "a collection of structured content
with a lifecycle") — costs: define a schema + lifecycle + access rules, get the rest for
free from `foundation.collection`. Reasonable to add over time.

A **new module** — costs: whatever the module actually needs to do (docx pack/unpack has
nothing to do with collections at all), plus a `manifest.json` declaring it depends on
`foundation` (and, if relevant, on a service — e.g. a future module that generates docx
reports *from* ticket data would depend on both `foundation` and `services/ticket`).

Neither one ever needs "its own core." That's the whole point of separating this out.

## 3. BHT and BHW knowing about each other

Per Aaron: they should be able to reference each other. This is already happening by
convention in the current Aaron K system — tickets link to wiki pages (e.g. PREC_003 links
the DAS lifecycle wiki page), wiki pages link back to the tickets that exemplify them (e.g.
the Canyon Pointe wiki page links PREC_003). Formalizing it: `foundation.collection` gets a
lightweight typed reference (`ref: ticket:PREC_003`, `ref: wiki:reference/das-project-lifecycle`),
so both services use the same mechanism instead of each hand-rolling relative markdown links.
Two things fall out of that almost for free once it exists: a **link-integrity check** (does
the referenced ticket/page actually exist — useful on its own, and it's the same idea flagged
earlier for keeping the two independent wikis from silently drifting), and eventually
auto-generated backlinks ("tickets that reference this wiki page") if that turns out to be
useful.

**See `FOUNDATION_DESIGN.md` for the actual interface design** — turns out `collection.py`
as sketched below is really a toolkit of several independent primitives, not one class, once
worked through against what BHT and BHW's legacy scripts actually do differently (numbered
vs. path-based identity, single vs. multi-document rollups).

## Next steps if this is right

- Rename `core/` → `foundation/` everywhere it appears in `MODULE_SYSTEM.md` and
  `PYTHON_PROJECT_SETUP.md`.
- Move BHT/BHW out from "inside core" to their own `services/` folder, each with its own
  `manifest.json` (`requires: ["foundation"]`).
- `modules/docx/manifest.json` becomes `requires: ["foundation"]` (not `["core"]`) — and stays
  that way unless/until something needs it to also depend on a service.
