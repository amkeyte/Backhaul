---
id: design/bh010-021-architecture
category: design
slug: bh010-021-architecture
title: BH_010-021 Implementation Architecture
summary: Shared foundation-layer primitives and build order for the twelve tickets
  filed off tonight's BKHL audit.
keywords: null
status: draft
updated: '2026-08-28'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · design
<!-- bh-header:end -->

# BH_010-021 Implementation Architecture

Shared foundation-layer primitives and build order for the twelve tickets filed off tonight's BKHL audit.

**Purpose:** before touching any of BH_010–BH_021 individually, read this. Several of them share
a primitive or a file, two of them turn out to be narrower than filed once the actual code is
read, and one pair collapses into a single feature. This doc exists so that work happens once,
not five times, and so the build order avoids self-inflicted merge conflicts on `dev`.

## 0. What reading the actual code changed about scope

Two corrections worth making before writing any code, both found by reading the current
implementation rather than re-deriving from the ticket text alone:

**BH_010 and BH_017 are the same feature, seen from two ends.** BH_010 asked for "validate status
on write." `services/ticket/schema.py`'s `validate()` already rejects any status outside
`STATES = ("open", "in-progress", "blocked", "done")`, and `_cmd_close` already calls `validate()`
against the ticket's current frontmatter before writing — so a hand-typo like `status: closed`
already *cannot* be introduced by anything that goes through the CLI today. The six tickets BKHL_006
found got `status: closed` because they were never touched by `bht` at all — hand-edited directly,
which no amount of validating `bht open`/`close` more strictly can prevent, because those commands
never ran. The actual gap is BH_017's: there's no CLI command for `in-progress`/`blocked` at all, so
hand-editing frontmatter is the *only* option for two of four lifecycle states, not an accidental
path for one. **Build one command, `bht status <id> <value>`, gated through the same
`validate()`/`STATES` pattern `_cmd_close` already uses — this satisfies both tickets.** Close BH_010
as a duplicate once BH_017 lands, referencing this doc.

**BH_020's "writer-side quoting" half is already true.** Confirmed empirically:
`yaml.safe_dump(..., default_flow_style=False)` — what `foundation/frontmatter.py`'s `serialize()`
already uses for every write — correctly quotes a scalar containing `: ` (`title: 'Border load
count: client vs server'`, tested directly). Every ticket created through `bht open` (which builds
a `TicketFrontmatter` dataclass and serializes it, never hand-assembles YAML text — see
`services/ticket/create.py`'s own docstring, which calls this out on purpose) is already immune to
this crash. `FRO_051` broke because it was hand-edited outside the CLI, same root cause as the
status-vocabulary finding above. **BH_020 narrows to just its second half: hardening
`frontmatter.parse()` to raise a `FrontmatterParseError` naming the file on a `yaml.YAMLError`,
instead of letting a bare traceback surface.** The writer-side suggestion needs no code change —
worth closing that half of BH_020 as "already true" with a one-line note, not silently dropping it.

## 1. Shared foundation-layer primitives — build these first

Four things get reused across multiple tickets below. Building them once, in `foundation/`, before
starting the individual tickets avoids four services each growing a slightly different version.

1. **Consolidate `_resolve_config_path`.** Duplicated near-verbatim in five places
   (`cli.py`, `services/ticket/cli.py`, `services/wiki/cli.py`, `modules/roadmap/cli.py`,
   `modules/roles/cli.py`) — same `--project` / `--config` / fall-back-to-default logic, five
   copies. Move the shared part into `foundation/config.py` as one function taking the caller's own
   default path (each service still knows its own `_REPO_ROOT`-relative default), and have all five
   `cli.py` files call it. This needs to happen regardless of which direction BH_019 goes (§3) —
   whichever fix is chosen should be written once, not patched into five files.
2. **`frontmatter.parse()` error hardening**, per BH_020's narrowed scope above: catch
   `yaml.YAMLError` inside `parse()`, raise a new `FrontmatterParseError(FrontmatterError)` naming
   `path`. Every caller that already catches `FrontmatterError` (e.g. `_cmd_refresh`'s per-file
   `try/except`) keeps working unchanged since the new error is a subclass.
3. **Reuse `foundation/markers.py`'s `refresh_block()` for BH_011's Required By.** This is exactly
   the idempotent marked-region-replace primitive `bh-header` already uses — no new mechanism
   needed, just a new call site: a `<!-- required-by:start -->`/`:end` pair in the node template,
   populated from `dependents()`'s existing output.
4. **New log-append primitive, for BH_016.** Nothing today inserts content into a body given a
   heading to anchor on — `markers.py` replaces a marked *region*, this needs to insert *after* a
   heading (`## Log`) without a matching end-marker, since log entries accumulate and are never
   replaced wholesale. Suggest `foundation/body_log.py`: `append_log_entry(body: str, entry_text:
   str, *, heading: str = "## Log", date: date | None = None) -> str`, finding `heading` and
   inserting the new `- YYYY-MM-DD: {entry_text}` line immediately after it (before whatever was
   already there — this project's own convention, confirmed by every real ticket's log this
   session, is newest-first). Building this in `foundation` rather than `services/ticket/` is
   deliberate: roadmap nodes have the identical `## Log` convention and a future `bhrm log` could
   reuse it — not scoped to build this pass, just don't paint it into a ticket-only corner.

## 2. Per-ticket shape, in dependency order

**BH_017 (supersedes BH_010).** `bht status <id> <in-progress|blocked|open>` in
`services/ticket/cli.py`, argparse `choices=` restricting the value, then the same
parse-validate-mutate-write-rebuild-board shape `_cmd_close` already has. Depends on nothing new.

**BH_016 (log-append).** `bht log <id> --entry "..."` (and `--entry-file`/stdin for multi-
paragraph text, the common case per BKHL_011's own finding). Uses the new `body_log.py` primitive
from §1. Depends on §1.4.

**BH_018 (oversized title/context warning).** Soft stderr warning in `_cmd_open`, after
`create_ticket()` succeeds, checking `len(args.title)`/`len(args.context or "")` against the 40/100
guideline from `bht.md`. No dependency, smallest ticket in the batch — good candidate to pair with
whichever of BH_017/BH_016 lands first since it's the same file.

**BH_012 (render extension guard).** `modules/roadmap/cli.py`'s render command: if `--output` ends
in `.html`, error with a pointer to `bhrm index` instead of writing markdown into it. Self-
contained, no dependency.

**BH_011 (Required By regeneration).** Wire `dependents()` (already correct, already tested) into
node-template + `bhrm index`/`refresh`, writing through `markers.refresh_block()` per §1.3. One
open item carried from the original ticket, not resolved by this doc: does the marked block
replace today's freehand `Required By` prose entirely, or sit alongside author-written context —
worth deciding at implementation time by looking at what real nodes currently have there.

**BH_013 (convergence terminal status).** Per the project owner's decision, reuse `superseded` for
both kinds. Turns out to be a genuinely small change: add `"superseded"` to
`CONVERGENCE_STATES` in `modules/roadmap/schema.py` — the existing `if status == "superseded" and
not frontmatter.get("superseded_by")` check in `validate()` already runs unconditionally on kind,
so no new special-casing needed there. `graph.py`'s `is_actionable()` already checks
`node.status != OPEN_STATUS[node.kind]`, so a superseded convergence node is automatically excluded
from `frontier()` with zero graph.py changes. The only genuinely new code is the stale-reference
check: walk every node's `depends_on` plus every wiki/ticket link, flag any pointing at a node
whose `superseded_by` is set — a new function in `graph.py`, sibling to `find_convergence_bypasses`,
advisory (same non-blocking framing).

**BH_019 (default config resolution) — Decision (locked, 2026-08-28).** Upward cwd search, added
*in front of* today's hardcoded default rather than replacing it — additive, not a behavior
change for the one case that currently works.

One thing surfaced while deciding this that the original ticket didn't account for: this repo's
own config lives at `<repo_root>/config/config.local.json`, but every real consumer project
(mcRepos confirmed) puts it at `<project_root>/backhaul/config.local.json` — two different
layouts, not one. An upward search has to pick a convention to search for; picking wrong for
whichever project doesn't match would make things worse, not better. Resolved by searching for the
*consumer* layout only (`backhaul/config.local.json` in cwd or any ancestor, plus the case of
already being cd'd into the `backhaul/` directory itself) and falling back to each service's
existing hardcoded default — unchanged — when the search finds nothing. This means:

- A consumer project: `cd` anywhere inside it, run a bare `bht`/`bhrm` command, it now works —
  the exact fix `bht.md`'s current wording already (incorrectly) promises.
- This repo's own dogfooding case: cwd won't have a `backhaul/config.local.json` sitting directly
  under it (it's at `config/config.local.json` instead), so the search finds nothing and falls
  through to the existing `_DEFAULT_CONFIG_PATH` exactly as today — zero behavior change for the
  one case that currently works.
- `--project`/`--config` still take priority over both, unchanged.

Implementation: `foundation/config.py` gains `find_config_upward(start: Path) -> Path | None` —
walks `start` and each parent, checking `<candidate>/backhaul/config.local.json` and (for the case
`start` is already inside a directory named `backhaul`) `<candidate>/config.local.json` directly.
The consolidated `_resolve_config_path` from §1.1 calls this between the `--config` check and the
final hardcoded fallback. `bht.md` (and the equivalent line in `bhw.md`/`bhrm.md`/`bhrole.md`)
gets its wording corrected regardless — "this checkout's own default config" was never accurate
for the self-hosting case's actual directory layout either; correct wording: "omit both to search
upward from the current directory for a project's `backhaul/config.local.json`, falling back to
this checkout's own config if none is found."

**BH_015 (lint historical-link marker) — Decision (locked, 2026-08-28).** An HTML comment
immediately after the link on the same line: `[text](target) <!-- historical-link -->`. Chosen
over a markdown title attribute (`[text](target "historical")`, which `_LINK_RE` already parses
and discards, so it'd need zero regex changes) because a title attribute is meant to be a
human-readable tooltip and some renderers surface it as one — a machine sentinel showing up as
hover text on every historical link would read as broken/confusing to an actual reader. An HTML
comment renders invisibly everywhere, and this project already uses exactly this idiom for every
other machine-readable annotation (`<!-- board:start -->`, `<!-- bh-header:start -->`) — this is
the same pattern, not a new one.

Implementation: in `find_broken_links()`, after a `_LINK_RE` match, check whether the remainder of
that line (optionally preceded by whitespace) starts with the literal `<!-- historical-link -->`;
if so, skip the finding entirely (not just downgrade it — a historical link is not a defect).
Scoped to `find_broken_links()` only, not `find_orphaned()` — a historical link marks *that one
link* as intentionally dangling, it says nothing about whether the target page (if it still
exists) is orphaned, which is a separate, real question. Document the marker convention in
`wiki/meta/bhw.md` next to the "don't rewrite history" convention it exists to serve.

**BH_014 (`backhaul refresh` orchestrator).** Programmatic calls into each service's existing
build function — `services.ticket.board.build_board`, the wiki index builder, the roadmap index
builder, the roles index builder, then `foundation.lint.run_lint` (advisory, printed not blocking),
then `dashboard.build_dashboard` — all from one new `_cmd_refresh` in top-level `cli.py`. Should
skip cleanly (not error) on a project with `enabled_modules: []` for roadmap/roles, mirroring how
`lint.py`'s `_content_roots()` already gates on enabled modules. Sequence after BH_019 is decided,
since `backhaul refresh` becoming the recommended one-command entry point is exactly the case where
a broken default config resolution would be most visible/costly.

**BH_015 (lint historical-link marker) — open decision, not resolved by this doc.** The mechanism
(skip a marked link in `find_broken_links()`) is straightforward; the exact marker syntax isn't
decided and BH_015's own ticket body says so explicitly. Needs a concrete proposal — e.g. a
trailing inline comment convention immediately after the link on the same line — before writing the
regex. Worth deciding alongside BH_014 since `backhaul refresh` running lint by default (making it
routine rather than optional) is the thing that makes this marker convention actually necessary,
not just nice-to-have.

**BH_021 (epoch-maintenance-node backport) — docs-only this pass.** All three of its own open
questions (first-class `kind: maintenance`, a `bhrm new` shortcut, advisory checks if the schema
lands) are explicitly deferred in its own ticket body pending evidence from more than one project.
For this pass: backport the convention as documentation only into Backhaul's own default
`wiki/meta/bhrm.md` and node template comments, no schema/code change. Self-contained, no
dependency on anything else in this doc.

## 3. Suggested build order

Both decisions are locked as of 2026-08-28 (§2) — full build order, no remaining stops:

1. §1's four foundation primitives, including BH_019's `find_config_upward` (small, independent,
   everything else leans on at least one).
2. BH_017 + BH_018 (same file, `services/ticket/cli.py`) together; close BH_010 as a duplicate.
3. BH_016 (same file again, natural to batch with step 2).
4. BH_012 (small, standalone, any time).
5. BH_011 + BH_013 together (`modules/roadmap/graph.py`/`schema.py`, same files).
6. BH_020's parse-hardening half (foundation, already covered in §1.2 — nothing left to schedule
   separately once §1 lands).
7. BH_014 (`backhaul refresh`), now that BH_019 is settled.
8. BH_015 (lint marker), natural to pair with BH_014 since `backhaul refresh` is what makes lint
   routine enough to need the marker.
9. BH_021 (docs-only, no dependency — can happen any time, listed last only because it's lowest
   priority, not because anything blocks it).

## 4. Testing implications

Every item above touches code with existing test coverage (`test_dashboard.py`,
`test_roadmap.py`/`test_roadmap_cli.py`, and a new `test_foundation.py` case for the
`FrontmatterParseError` and `body_log.py` additions). No fixture/mock changes needed beyond what
BH_004/BH_005's existing test patterns already establish — full suite green before any ticket in
this batch is considered done, same standing rule as the rest of this repo.

## 5. Status

All twelve tickets closed; full suite green. A follow-up full-codebase review of this batch's
own result found (and fixed) three real bugs, filed one open question, and picked up two
unrelated long-open tickets in the same pass — see
[Dev Branch Handoff — 2026-08-30](dev-branch-handoff.md) for that batch and the branch's overall
status, including whether a version bump is needed before pushing (it isn't).

## Related pages

- [Dev Branch Handoff — 2026-08-30](dev-branch-handoff.md)
- [Version & Schema Compatibility Plan](version-compat.md)
