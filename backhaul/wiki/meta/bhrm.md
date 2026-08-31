---
id: meta/bhrm
category: meta
slug: bhrm
title: BHRM — Roadmap Conventions
summary: Roadmap node ID scheme, why short slugs matter here, and CLI cheatsheet.
keywords: null
status: draft
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · meta
<!-- bh-header:end -->

# BHRM — Roadmap Conventions

Roadmap node ID scheme, why short slugs matter here, and CLI cheatsheet.

BHRM (`bhrm`) is the dependency-graph roadmap module — optional, gated by `enabled_modules`.
Every unit of roadmap-load-bearing work is a node (`work` or `convergence`) with explicit
`depends_on` edges; `frontier` computes what's actionable instead of that being a memorized
position in a list.

## ID scheme

A node's ID is `RM_<uid>_<NNN>` (e.g. `RM_ARR_001`). The UID is `RM_` + a client's short code —
the *same* code BHT uses for that client (they share one `client-uids.md`), so `ARR` means the
same client whether it's a ticket or a node. **Each UID is its own fully independent graph** —
`validate`/`frontier`/`downstream`/etc. are always scoped to one UID, and a `depends_on` entry
naming a node under a different UID is a hard error, not a cross-project link. This is how one
shared `content_roots.roadmap` folder hosts multiple, unrelated roadmaps side by side (e.g. one
project hosting both FrontierMode's and Satchel's graphs).

## Filenames and --slug — use a short code here, not the description

A node's filename is `<ID>_<slug>.md`. **For roadmap nodes specifically, always pass
`--slug <code>` with a short, one-word mnemonic** (e.g. `alma`, `scaffold`) rather than letting
it default to the slugified title:

```
bhrm new --client FrontierMode --title "Set up the initial mod scaffolding and build pipeline" --owner Arryn --slug scaffold
```

This matters more here than for BHT/BHW: `depends_on` edges reference IDs directly
(`RM_FRO_003`), and a node's own body/render output is meant to be skimmed as a dependency
graph, not a flat list — a long descriptive slug makes both harder to eyeball and
tab-complete than a short code does. The ID itself never contains the slug (only the filename
does), so this is purely about keeping files easy to work with, not about identity.

## Title length

`ROADMAP_INDEX.md` renders each node's title as part of a one-line list entry — same reasoning
as BHT's length standard (see `meta/bht.md`). Target title length ≤ ~40 characters; put the
detail (specific classes/files/packages involved) in the node's body instead of stuffing it into
the title. Several nodes from the initial roadmap backfill run well over this — worth trimming
next time they're touched, not urgent enough to warrant a dedicated pass on its own.

## Status vocabulary (kind-dependent)

- **work**: `open` -> `resolved` | `superseded` (terminal once left `open`).
- **convergence**: `WIP` <-> `reached` (reversible — a milestone can un-converge on real
  evidence of a gap, with a `ReachedLog` recording every time it was reached, never erased), plus
  a third, terminal exit: `superseded` (see BH_013 below) for a convergence node kept on disk but
  no longer meaningful — reuses the same value work nodes already use for the equivalent case
  rather than a convergence-specific name.
- Whatever the kind, `status: superseded` always requires `superseded_by` to be set —
  `validate()` rejects a `superseded` node with no pointer to what replaced it.

## HTML graph view (bhrm render-html)

`bhrm render-html --uid RM_XXX [--output PATH] [--title "..."]` generates a standalone,
self-contained HTML/SVG view of one UID's graph — no external assets, no network calls, safe to
open as a local file. A real, data-driven successor to the original hand-laid-out mockup this
was ported from (`intake/roadmap-nodes/design/Mockups/sample-visualization.html`).

Layout: nodes are laid out left to right by `_depth()` (the same longest-path-from-root value
`render`'s markdown indentation already uses), top to bottom within a layer ordered by node ID —
deterministic, same graph always produces byte-identical output. Color: five buckets lifted from
the mockup's own legend — work/resolved-or-superseded green, work/open-and-actionable blue,
work/open-and-blocked gray, convergence/reached gold solid border, convergence/WIP orange dashed
border. Supports `?focus=RM_XXX_NNN` in the URL — highlights and scrolls to that node on load,
same behavior the mockup proved against real pilot data.

**Slug shown bold, after the ID, in each node's label (BH_009).** Not a new stored field — a
node's slug already lives in its own filename (`<ID>_<slug>.md`, set via `--slug` at `bhrm new`
or defaulted from the title), and `Node.slug` just reads it back from `self.path.name`. Lets a
human reference a node meaningfully ("the Betty node") instead of only by its `RM_FRO_011`-style
ID. Omitted entirely for the rare node whose filename has no slug part.

**`bhrm index`/`bhrm refresh` unconditionally rewrite every UID's HTML view, every run.** Not
gated on whether `ROADMAP_GRAPH_<uid>.html` already existed — every `index`/`refresh` call is a
full rebuild of both the markdown index and every discovered UID's HTML graph view, using the
conventional filename (`html_graph_filename(uid)`, e.g. `ROADMAP_GRAPH_RM_FRO.html`), same
directory as `ROADMAP_INDEX.md`. `render-html --output` is still available and fully
user-controlled for a one-off render elsewhere, but the index routine no longer needs it —
running `bhrm index`/`refresh` is enough to keep both current (BH_008). `render_index()` then
links to that freshly-written file — `**Graph view:** [Open in browser ↗]` under that UID's
section — since the HTML is written before the markdown index is rendered in the same call.

**A UID whose graph fails to load or validate aborts the whole `index`/`refresh` call — on
purpose.** No partial-failure or skip-and-continue mode: per the project owner, a broken graph
should surface loudly as part of the normal index/refresh routine, the same way it already
surfaces inside `render_index()` itself — this is the mechanism for finding invalid roadmap
state, not something to route around.

The full `Visualize` line from the original node-format-spec.md (wired into every node's own
header, not just the index) is still deliberately not built — a narrower version of that idea,
scoped to the index only, is what shipped here.

## render vs. index — different commands write different things (BH_012)

`render` always writes markdown, whether printed to stdout or sent to `--output`. `render`
refuses a `--output` path ending in `.html` rather than silently overwriting a generated graph
with markdown — this used to be possible and cost a real clobbered graph in a consumer project
before the guard existed (see BKHL_008). To regenerate a UID's HTML graph, use `bhrm index`
(§ HTML graph view above) — it's the only command that writes `ROADMAP_GRAPH_<uid>.html`.

## Required By regenerates automatically (BH_011)

Every node's `## Required By` section is a marked block (`<!-- required-by:start -->`/`:end`),
rewritten unconditionally on every `bhrm index`/`refresh` call — same "unconditional, every run"
discipline BH_008 already established for the HTML graph view. Lists every node whose own
`depends_on` names this one, computed from `dependents()` (already correct, already tested — the
only gap was that nothing wrote it back into the file). Shows the placeholder text (*"nothing
depends on this yet"*) when the list is empty. A node created before this shipped, with a
freehand (unmarked) `## Required By` section, gets migrated in place the first time `index`/
`refresh` touches it — the stale placeholder is replaced, not left duplicated alongside a new
block. Not wired into `bhrm new` — a brand-new node can't have existing dependents by definition,
so the template's own default state is already correct; run `index`/`refresh` after minting a node
with `--depends-on` to see the ancestor's Required By update.

## Convergence-bypass check (advisory)

`bhrm convergence-bypass --uid RM_XXX` lists `DependsOn` edges that reach back into a
convergence node's own prerequisite territory without ever routing through the convergence
node itself — "skipping the checkpoint." First formal definition of "bypass" in this codebase
(see BH_006) — the idea traces back to a hand-colored `.gate-edge` on the original pilot
mockup, never written down as a rule until this.

Precisely: for convergence node C, a node N is a bypass candidate when N isn't one of C's own
ancestors, isn't already gated by C (C itself or anything downstream of it), and N's own
ancestor closure shares at least one node with C's ancestor closure. Output is one line per
`(N, C, shared ancestors)` — same worklist style as `dependents`/`downstream`/`blocking`, never
a pass/fail verdict and never raises, even when it finds real candidates. A shared ancestor
doesn't automatically mean N *should* depend on C; it means it's worth a human looking at why
it doesn't. Deliberately does **not** factor in a node's `created` date to filter out nodes
that predate the convergence node — one clear rule for v1, not a second date-based heuristic.

This is separate from `bhrm validate` on purpose — `validate`'s contract is "raises on a cycle,
silent otherwise," a hard error; this is advisory and never blocks anything, so it stays its
own command rather than changing what `validate` means.

## Convergence terminal status + stale-reference check (BH_013)

A convergence node can now retire the same way a work node does: `status: superseded` +
`superseded_by: <replacement ID>`, permanent, same as work's own `superseded` exit. A superseded
convergence node is never actionable and never appears in `frontier` — same treatment `reached`
already gets, just one more terminal state `is_actionable`/`frontier` know to skip.

`bhrm superseded-refs --uid RM_XXX` lists every direct `DependsOn` edge that names a node — work
or convergence — whose own `status` is `superseded`. Output is one line per
`(referencing_id, superseded_id)` pair, same worklist style as `convergence-bypass`: advisory,
never raises, never blocks. This exists because `blocking()` alone doesn't distinguish an
ordinary open dependency from one that's permanently stuck — `SATISFYING_STATUS` never includes
`superseded`, so a stale edge just looks blocked forever unless something flags it explicitly.

Scoped to direct `depends_on` edges within one UID's graph only — it does not follow wiki or
ticket prose links that happen to mention a superseded node's ID (that would need
`foundation/lint.py`'s broken-link machinery, out of scope for this check).

## Epoch maintenance nodes (containers) (BH_021)

An **epoch** is the span of work between two convergence nodes, named for the one that opens it.
Real work inside an epoch isn't always feature-shaped: a ruling's blast radius turns out to reach
past the ticket that provoked it, a build turns up a bug against something unrelated, a later
node casts doubt on an earlier one's done bar. That work still needs a place to live on the
graph — otherwise it only exists by being found in the tickets folder, which is exactly the
"search to find it" problem this convention exists to remove. Backported from a consumer
project's live usage (mcRepos) rather than designed up front — see that project's own
`wiki/meta/bhrm.md#epoch-maintenance-nodes-containers` for the original writeup this section
condenses.

**A maintenance node (a "container") is an ordinary `kind: work` node that doesn't represent a
design goal.** No schema change — it gets a slug keyed to the epoch instead of a persona name:
`<epoch>-01`, `<epoch>-02`, etc., e.g. `susan-01`. It doesn't carry a `ticket:` field, the same
way a convergence node doesn't — `ticket: null` — since what actually landed on it is tracked in
its own log; a container can gather more than one ticket over its life, and a single frontmatter
pointer would misrepresent that. No new `kind` value for these — they render in the graph like
any other `work` node for now. A dedicated `kind: maintenance` (with its own reversible
`collecting <-> clear` status pair, mirroring convergence's `WIP <-> reached`, plus a distinct
color/shape in `bhrm index`'s HTML output) is worth revisiting once the pattern has proven out
across more than one project — deliberately not built yet.

**Every epoch gets two standing containers by default: a start container and an end container,**
opened together rather than waited on until something obviously needs one — cheap to have sitting
there empty, expensive to reconstruct after the fact once nobody remembers the epoch had a start.
The start container is where early-epoch rework tends to land; the end container is the epoch's
review/fix gate, where things too small or too unrelated to block whatever's currently being
built get dropped instead of stalling it — the epoch's next planned node depends on the end
container clearing, so nothing carries forward unaddressed. Additional containers get inserted in
the middle only when a set of tickets is big enough to warrant its own marker — a judgment call
each time, not an automatic trigger.

**Wiring is real, not decorative.** A `depends_on` edge onto a container means the dependent is
genuinely blocked on it clearing, same as any other node. Reopening a `resolved` node on real
evidence (a container's work casting doubt on an earlier node's done bar) is the intended
mechanism for regression work, not a violation of history — logged as a new dated entry on the
reopened node itself, cross-referenced from the container that forced it. Regression doubt is
chased back one hop only, for now; doubt about something further back gets named and logged as
accepted risk rather than triggering a deeper sweep.

**A container's `status` tracks whether it's currently blocking anything, not whether every
ticket ever logged on it is closed.** Flip `resolved` once nothing currently gating a dependent
remains open; non-blocking content can stay logged and open underneath that without holding the
flip back. **Required when that happens: a `Deferred, non-blocking:` callout at the top of the
container's body** — a short bullet list of what's still open and why it isn't holding the
status back, so a reader doesn't have to read the full log to find loose ends. This is a
body-content convention, not a schema field; nothing enforces it mechanically today (the
first-class `kind: maintenance` mentioned above would make it structural instead).

**Ticket-side signal: a `[<Container>]` prefix on the ticket's own `context`.** The container's
callout is the record that a ticket is attached, but it only reaches a reader who opens the
roadmap node — `BOARD.md` is what actually gets scanned day to day, and without a matching
signal there a container-attached ticket reads exactly like a loose one still waiting on someone.
Prepend `[<Epoch>_<NN>]` (the container's persona name, capitalized, plus its two-digit sequence,
matching its slug — `susan-02` -> `[Susan_02]`) to the front of the ticket's `context` field. This
is a BHT `context`-field convention, not a wiki-page one, and shares `bht.md`'s ~100-character
length standard — trim surrounding wording to make room rather than skip the tag.

Three things intentionally left open for now, matching the source ticket's own framing (worth an
opinion once more than one project has exercised the plain-`work` version, not decided
speculatively): whether this stays a documentation/naming convention or earns the first-class
`kind: maintenance` described above; whether `bhrm new` should grow an ergonomic shortcut for
minting the standing start+end pair together (today it's two ordinary `bhrm new --kind work`
calls); and what advisory checks (if any) would make sense once/if the schema lands.

## CLI cheatsheet

```
bhrm new --client <name> --title "..." --owner <name> [--kind work|convergence] [--slug code] [--depends-on ID,ID]
bhrm validate --uid RM_XXX
bhrm frontier --uid RM_XXX
bhrm dependents <ID>   |   bhrm downstream <ID>   |   bhrm blocking <ID>
bhrm convergence-bypass --uid RM_XXX
bhrm superseded-refs --uid RM_XXX
bhrm render --uid RM_XXX [--output PATH] [--title "..."]   # writes MARKDOWN -- refuses a .html --output (use `index` for that)
bhrm render-html --uid RM_XXX [--output PATH] [--title "..."]
bhrm export-json --uid RM_XXX [--out PATH]
bhrm index [--output PATH] [--title "..."]    # every UID's graph, its own section
bhrm projects
```

`--project <name>` / `--config <path>` selects the project. Every subcommand except `projects`
refuses to run if `"roadmap"` isn't in that project's `enabled_modules`.

## Related pages

- [BHT — Ticket Conventions](../meta/bht.md)
- [BHW — Wiki Conventions](../meta/bhw.md)
- [BHRole — Agent Role Conventions](../meta/bhrole.md)
- [Backhaul — Cross-Service Command Conventions](../meta/backhaul.md)
